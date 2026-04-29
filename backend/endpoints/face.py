"""
Face recognition endpoints.

POST /face/capture        — detect face in frame, return quality score
POST /face/verify         — full 4-stage verification pipeline
POST /face/liveness-check — isolated DINOv2 PAD liveness test
POST /face/enroll         — enrol student biometric (admin only)
POST /face/override       — invigilator manual override
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import encrypt_embedding
from database import get_db
from endpoints.deps import get_current_user, require_admin, require_invigilator_or_admin
from models.biometric_profile import BiometricProfile
from models.exam_session import ExamSession
from models.student import Student
from models.system_user import SystemUser
from models.verification_attempt import VerificationAttempt, VerificationOutcome
from schemas.schemas import (
    EnrollmentResponse, FaceCaptureResponse, LivenessResult,
    OverrideRequest, OverrideResponse, VerificationResult,
)
from services.face_service import get_face_service

router = APIRouter(prefix="/face", tags=["Face Recognition"])
MAX_IMAGE_BYTES = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024


# ── Image helper ──────────────────────────────────────────────────────────────

async def _read_image(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Image must be under {settings.MAX_IMAGE_SIZE_MB} MB",
        )
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="File must be an image (JPEG or PNG)")
    return data


# ── POST /face/capture ────────────────────────────────────────────────────────

@router.post("/capture", response_model=FaceCaptureResponse,
             summary="Detect face in frame and return quality score")
async def capture_face(
    image: UploadFile = File(...),
    _: SystemUser = Depends(require_invigilator_or_admin),
):
    image_bytes = await _read_image(image)
    svc = get_face_service()
    result = svc.detect_and_align(image_bytes)
    return FaceCaptureResponse(
        face_detected=result.face_detected,
        face_count=result.face_count,
        quality_score=result.quality_score,
        message=result.message,
    )


# ── POST /face/liveness-check ─────────────────────────────────────────────────

@router.post("/liveness-check", response_model=LivenessResult,
             summary="Run DINOv2 PAD anti-spoofing check")
async def liveness_check(
    image: UploadFile = File(...),
    _: SystemUser = Depends(require_invigilator_or_admin),
):
    image_bytes = await _read_image(image)
    svc = get_face_service()
    detection = svc.detect_and_align(image_bytes)
    if not detection.face_detected or detection.aligned_face is None:
        raise HTTPException(status_code=422, detail="No face detected in image")
    result = svc.check_liveness(detection.aligned_face)
    return LivenessResult(
        is_live=result.is_live,
        confidence=result.confidence,
        method=result.method,
    )


# ── POST /face/verify ─────────────────────────────────────────────────────────

@router.post("/verify", response_model=VerificationResult,
             summary="Full 4-stage student verification pipeline")
async def verify_student(
    image: UploadFile = File(...),
    student_number: Optional[str] = Form(None),
    exam_session_id: Optional[str] = Form(None),
    terminal_id: Optional[str] = Form(None),
    current_user: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    t_start = time.perf_counter()
    image_bytes = await _read_image(image)
    svc = get_face_service()
    attempt_id = uuid.uuid4()

    # Normalise optional fields — treat empty strings as None
    student_number = student_number.strip() if student_number and student_number.strip() else None
    exam_session_id = exam_session_id.strip() if exam_session_id and exam_session_id.strip() else None

    attempt_kwargs: dict = {"id": attempt_id, "terminal_id": terminal_id}
    if exam_session_id:
        attempt_kwargs["exam_session_id"] = exam_session_id

    # ── Stage 1+2: detect + align ─────────────────────────────────────────
    detection = svc.detect_and_align(image_bytes)
    attempt_kwargs["face_detected"] = detection.face_detected

    if not detection.face_detected or detection.aligned_face is None:
        elapsed_ms = int((time.perf_counter() - t_start) * 1000)
        await _write_attempt(db, attempt_kwargs,
                             VerificationOutcome.denied_identity, "No face detected", elapsed_ms)
        return _make_result(attempt_id, None, None, None, None, None,
                            False, VerificationOutcome.denied_identity, "No face detected", elapsed_ms)

    # ── Stage 2: liveness ─────────────────────────────────────────────────
    liveness = svc.check_liveness(detection.aligned_face)
    attempt_kwargs["liveness_score"] = liveness.confidence

    liveness_schema = LivenessResult(
        is_live=liveness.is_live,
        confidence=liveness.confidence,
        method=liveness.method,
    )

    if not liveness.is_live:
        elapsed_ms = int((time.perf_counter() - t_start) * 1000)
        await _write_attempt(db, attempt_kwargs,
                             VerificationOutcome.denied_liveness, "Liveness check failed", elapsed_ms)
        return _make_result(attempt_id, None, None, None, None, liveness_schema,
                            True, VerificationOutcome.denied_liveness,
                            "Presentation attack detected", elapsed_ms)

    # ── Stage 3: embedding + match ────────────────────────────────────────
    probe_embedding = svc.compute_embedding(detection)
    similarity: Optional[float] = None

    # Placeholders — extracted from ORM while session is still open
    s_id: Optional[UUID] = None
    s_number: Optional[str] = None
    s_name: Optional[str] = None

    if student_number:
        # 1:1 match
        res = await db.execute(
            select(Student).where(
                Student.student_number == student_number.upper(),
                Student.is_active == True,
            )
        )
        student = res.scalar_one_or_none()

        if not student or not student.biometric_profile:
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            await _write_attempt(db, attempt_kwargs,
                                 VerificationOutcome.denied_identity,
                                 "Student not found or not enrolled", elapsed_ms)
            return _make_result(attempt_id, None, None, None, None, liveness_schema,
                                True, VerificationOutcome.denied_identity,
                                "Student not found or not enrolled", elapsed_ms)

        # Extract all values from ORM object WHILE SESSION IS OPEN
        s_id = student.id
        s_number = student.student_number
        s_name = student.full_name
        encrypted = student.biometric_profile.encrypted_embedding
        attempt_kwargs["student_id"] = s_id

        similarity = svc.compare_embeddings(probe_embedding, encrypted)
        attempt_kwargs["face_similarity_score"] = similarity

        if similarity < settings.FACE_SIMILARITY_THRESHOLD:
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            await _write_attempt(db, attempt_kwargs,
                                 VerificationOutcome.denied_identity,
                                 f"Face mismatch (score {similarity:.2f})", elapsed_ms)
            return _make_result(attempt_id, s_id, s_number, s_name, similarity, liveness_schema,
                                True, VerificationOutcome.denied_identity,
                                f"Face mismatch — similarity {similarity:.2f}", elapsed_ms)

    else:
        # 1:N search
        res = await db.execute(
            select(BiometricProfile, Student)
            .join(Student)
            .where(Student.is_active == True)
        )
        rows = res.all()

        if not rows:
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            await _write_attempt(db, attempt_kwargs,
                                 VerificationOutcome.denied_identity,
                                 "No enrolled students in database", elapsed_ms)
            return _make_result(attempt_id, None, None, None, None, liveness_schema,
                                True, VerificationOutcome.denied_identity,
                                "No enrolled students in database", elapsed_ms)

        enrolled = [
            {
                "student_id": p.student_id,
                "student_number": s.student_number,
                "encrypted_embedding": p.encrypted_embedding,
            }
            for p, s in rows
        ]

        match = svc.search_1_to_n(probe_embedding, enrolled)
        similarity = match.similarity
        attempt_kwargs["face_similarity_score"] = similarity

        if not match.matched:
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            await _write_attempt(db, attempt_kwargs,
                                 VerificationOutcome.denied_identity,
                                 "No matching student found", elapsed_ms)
            return _make_result(attempt_id, None, None, None, similarity, liveness_schema,
                                True, VerificationOutcome.denied_identity,
                                "No matching student found", elapsed_ms)

        res2 = await db.execute(
            select(Student).where(Student.student_number == match.student_number)
        )
        matched = res2.scalar_one_or_none()
        if not matched:
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            return _make_result(attempt_id, None, None, None, similarity, liveness_schema,
                                True, VerificationOutcome.error,
                                "Internal error — matched record missing", elapsed_ms)

        # Extract values while session is open
        s_id = matched.id
        s_number = matched.student_number
        s_name = matched.full_name
        attempt_kwargs["student_id"] = s_id

    # ── Stage 4: eligibility ──────────────────────────────────────────────
    eligibility = await _check_eligibility(exam_session_id, db)
    attempt_kwargs.update(eligibility)

    if not eligibility["sis_eligible"]:
        reason = _eligibility_reason(eligibility)
        elapsed_ms = int((time.perf_counter() - t_start) * 1000)
        await _write_attempt(db, attempt_kwargs,
                             VerificationOutcome.denied_eligibility, reason, elapsed_ms)
        return _make_result(attempt_id, s_id, s_number, s_name, similarity, liveness_schema,
                            True, VerificationOutcome.denied_eligibility, reason, elapsed_ms)

    # ── GRANT ─────────────────────────────────────────────────────────────
    elapsed_ms = int((time.perf_counter() - t_start) * 1000)
    await _write_attempt(db, attempt_kwargs,
                         VerificationOutcome.granted, "All checks passed", elapsed_ms)
    return _make_result(attempt_id, s_id, s_number, s_name, similarity, liveness_schema,
                        True, VerificationOutcome.granted, "Access granted", elapsed_ms)


# ── POST /face/enroll ─────────────────────────────────────────────────────────

@router.post("/enroll", response_model=EnrollmentResponse,
             summary="Enrol or update a student's facial biometric (admin only)")
async def enroll_face(
    image: UploadFile = File(...),
    student_number: str = Form(...),
    current_user: SystemUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Student).where(
            Student.student_number == student_number.upper().strip(),
            Student.is_active == True,
        )
    )
    student = res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_number} not found")
    if not student.biometric_consent:
        raise HTTPException(
            status_code=403,
            detail="Biometric consent has not been recorded for this student",
        )

    # Extract id before any async boundary
    student_id = student.id
    student_number_out = student.student_number

    image_bytes = await _read_image(image)
    svc = get_face_service()

    detection = svc.detect_and_align(image_bytes)
    if not detection.face_detected or detection.aligned_face is None:
        raise HTTPException(
            status_code=422,
            detail="No face detected — use a clear, well-lit frontal photo",
        )

    embedding = svc.compute_embedding(detection)
    encrypted = encrypt_embedding(embedding)
    quality = detection.quality_score or 0.0

    profile = student.biometric_profile
    if profile:
        profile.encrypted_embedding = encrypted
        profile.face_quality_score = quality
        profile.enrolled_by = current_user.id
        profile.last_updated = datetime.now(timezone.utc)
    else:
        db.add(BiometricProfile(
            student_id=student_id,
            encrypted_embedding=encrypted,
            face_quality_score=quality,
            enrolled_by=current_user.id,
        ))

    await db.commit()

    return EnrollmentResponse(
        student_id=student_id,
        student_number=student_number_out,
        enrolled=True,
        face_quality_score=round(quality, 3),
        message="Biometric profile enrolled successfully",
    )


# ── POST /face/override ───────────────────────────────────────────────────────

@router.post("/override", response_model=OverrideResponse, tags=["Access Control"],
             summary="Invigilator manual override of a failed attempt")
async def override_attempt(
    body: OverrideRequest,
    current_user: SystemUser = Depends(require_invigilator_or_admin),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(VerificationAttempt).where(VerificationAttempt.id == body.attempt_id)
    )
    attempt = res.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Verification attempt not found")
    if attempt.outcome == VerificationOutcome.granted:
        raise HTTPException(status_code=409, detail="Attempt was already granted")
    if attempt.was_overridden:
        raise HTTPException(status_code=409, detail="Attempt has already been overridden")

    # Extract user name while session is open
    overridden_by_name = current_user.full_name

    now = datetime.now(timezone.utc)
    attempt.was_overridden = True
    attempt.overridden_by = current_user.id
    attempt.override_reason = body.reason
    attempt.overridden_at = now
    attempt.outcome = VerificationOutcome.overridden
    await db.commit()

    return OverrideResponse(
        attempt_id=attempt.id,
        overridden=True,
        overridden_by=overridden_by_name,
        overridden_at=now,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _check_eligibility(exam_session_id: Optional[str], db: AsyncSession) -> dict:
    result = {
        "sis_eligible": True,
        "predicate_met": True,
        "registered_for_exam": True,
        "correct_venue": True,
    }
    if exam_session_id:
        try:
            res = await db.execute(
                select(ExamSession).where(ExamSession.id == exam_session_id)
            )
            if not res.scalar_one_or_none():
                result["registered_for_exam"] = False
                result["sis_eligible"] = False
        except Exception:
            pass   # Invalid UUID format — treat as no session
    return result


def _eligibility_reason(eligibility: dict) -> str:
    if not eligibility.get("predicate_met"):
        return "Predicate requirement not met"
    if not eligibility.get("registered_for_exam"):
        return "Not registered for this exam"
    if not eligibility.get("correct_venue"):
        return "Wrong exam venue"
    return "Eligibility check failed"


async def _write_attempt(
    db: AsyncSession,
    kwargs: dict,
    outcome: VerificationOutcome,
    reason: str,
    elapsed_ms: int,
) -> None:
    allowed = {c.key for c in VerificationAttempt.__table__.columns}
    filtered = {k: v for k, v in kwargs.items() if k in allowed}
    db.add(VerificationAttempt(
        outcome=outcome,
        outcome_reason=reason,
        processing_time_ms=elapsed_ms,
        **filtered,
    ))
    try:
        await db.commit()
    except Exception:
        await db.rollback()


def _make_result(
    attempt_id: uuid.UUID,
    student_id: Optional[UUID],
    student_number: Optional[str],
    student_name: Optional[str],
    similarity: Optional[float],
    liveness: Optional[LivenessResult],
    face_detected: bool,
    outcome: VerificationOutcome,
    reason: str,
    elapsed_ms: int,
) -> VerificationResult:
    """
    Build the response from plain Python values only — NO ORM objects.
    This prevents SQLAlchemy from trying to lazy-load expired attributes
    outside of an async context.
    """
    return VerificationResult(
        student_id=student_id,
        student_number=student_number,
        student_name=student_name,
        face_detected=face_detected,
        face_similarity_score=similarity,
        liveness=liveness,
        sis_eligible=None,
        predicate_met=None,
        registered_for_exam=None,
        correct_venue=None,
        outcome=outcome.value,
        outcome_reason=reason,
        processing_time_ms=elapsed_ms,
        attempt_id=attempt_id,
    )