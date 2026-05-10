"""
EduVerify backend test suite.
Tests: authentication, student CRUD, face enrolment pipeline, admin dashboard, security.

Run:  cd backend && python -m pytest tests/ -v
"""
import io
from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import pytest_asyncio

from core.security import (
    create_access_token,
    decrypt_embedding,
    encrypt_embedding,
    hash_password,
)
from models.biometric_profile import BiometricProfile
from models.exam_session import ExamSession, SessionStatus
from models.student import Student
from models.system_user import SystemUser, UserRole
from models.verification_attempt import VerificationAttempt, VerificationOutcome


# ── Helpers ───────────────────────────────────────────────────────────────────

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def fake_jpeg() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(128, 128, 128)).save(buf, format="JPEG")
    return buf.getvalue()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_user(db):
    user = SystemUser(
        Username="admin@tut.ac.za",
        Email="admin@tut.ac.za",
        FirstName="Admin",
        LastName="User",
        PasswordHash=hash_password("Admin123!"),
        Role=UserRole.ADMIN,
        IsActive=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def invig_user(db):
    user = SystemUser(
        Username="invig@tut.ac.za",
        Email="invig@tut.ac.za",
        FirstName="Invigilator",
        LastName="User",
        PasswordHash=hash_password("Invig123!"),
        Role=UserRole.INVIGILATOR,
        IsActive=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
def admin_token(admin_user):
    return create_access_token(str(admin_user.id), UserRole.ADMIN.value)


@pytest_asyncio.fixture
def invig_token(invig_user):
    return create_access_token(str(invig_user.id), UserRole.INVIGILATOR.value)


@pytest_asyncio.fixture
async def sample_student(db):
    student = Student(
        StudentNumber="223895956",
        FirstName="Thlong",
        LastName="KE",
        Email="thlong@tut4life.ac.za",
        programme="Software Engineering",
        year_of_study=3,
        ConsentGiven=True,
        EnrollmentStatus="Active",
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@pytest_asyncio.fixture
async def enrolled_student(db, sample_student, admin_user):
    profile = BiometricProfile(
        student_id=sample_student.id,
        encrypted_embedding=encrypt_embedding([0.1] * 512),
        face_quality_score=0.92,
        enrolled_by=admin_user.id,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(sample_student)
    return sample_student


@pytest_asyncio.fixture
async def exam_session(db, admin_user):
    now = datetime.now(timezone.utc)
    session = ExamSession(
        ModuleCode="SFG117V",
        ModuleName="Software Engineering Project",
        VenueLocation="Hall A",
        ExamDate=date.today(),
        StartTime=(now - timedelta(minutes=30)).time(),
        EndTime=(now + timedelta(hours=2)).time(),
        CreatedBy=admin_user.id,
        Status=SessionStatus.ACTIVE,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


# ══════════════════════════════════════════════════════════════════════════════
# AUTH TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAuth:
    async def test_login_success(self, client, admin_user):
        r = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@tut.ac.za", "password": "Admin123!"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"

    async def test_login_wrong_password(self, client, admin_user):
        r = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin@tut.ac.za", "password": "wrongpass"},
        )
        assert r.status_code == 401

    async def test_login_unknown_user(self, client):
        r = await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody@tut.ac.za", "password": "passw0rd"},
        )
        assert r.status_code == 401

    async def test_protected_route_no_token(self, client):
        r = await client.get("/api/v1/admin/stats")
        assert r.status_code in (401, 403)

    async def test_protected_route_bad_token(self, client):
        r = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert r.status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT PROFILE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestStudentProfiles:
    async def test_register_student(self, client, admin_token):
        r = await client.post(
            "/api/v1/students/register",
            json={
                "student_number": "220000001",
                "full_name": "Jane Doe",
                "email": "jane@tut4life.ac.za",
                "programme": "Computer Science",
                "year_of_study": 2,
                "biometric_consent": True,
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["student_number"] == "220000001"
        assert data["biometric_consent"] is True

    async def test_register_duplicate_student_number(self, client, admin_token, sample_student):
        r = await client.post(
            "/api/v1/students/register",
            json={
                "student_number": "223895956",
                "full_name": "Clone Student",
                "email": "clone@tut4life.ac.za",
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 409

    async def test_list_students(self, client, admin_token, sample_student):
        r = await client.get("/api/v1/students/", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    async def test_get_student_by_number(self, client, invig_token, sample_student):
        r = await client.get(
            "/api/v1/students/by-number/223895956",
            headers=auth(invig_token),
        )
        assert r.status_code == 200
        assert r.json()["student_number"] == "223895956"

    async def test_get_student_by_id(self, client, admin_token, sample_student):
        r = await client.get(
            f"/api/v1/students/{sample_student.id}",
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["student_number"] == "223895956"

    async def test_update_student(self, client, admin_token, sample_student):
        r = await client.put(
            f"/api/v1/students/{sample_student.id}",
            json={"year_of_study": 4},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["year_of_study"] == 4

    async def test_invigilator_cannot_register(self, client, invig_token):
        r = await client.post(
            "/api/v1/students/register",
            json={"student_number": "999", "full_name": "X", "email": "x@x.com"},
            headers=auth(invig_token),
        )
        assert r.status_code == 403

    async def test_record_consent(self, client, admin_token, sample_student):
        r = await client.post(
            f"/api/v1/students/{sample_student.id}/consent?consented=true",
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["biometric_consent"] is True

    async def test_delete_biometric(self, client, admin_token, enrolled_student):
        r = await client.delete(
            f"/api/v1/students/{enrolled_student.id}/face",
            headers=auth(admin_token),
        )
        assert r.status_code == 204

    async def test_search_students(self, client, admin_token, sample_student):
        r = await client.get(
            "/api/v1/students/?search=Thlong",
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# FACE RECOGNITION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def _mock_face_svc(detected=True, quality=0.9, liveness_live=True,
                   liveness_conf=0.95, similarity=0.85):
    from services.face_service import DetectionResult, LivenessResult
    svc = MagicMock()
    svc.detect_and_align.return_value = DetectionResult(
        face_detected=detected,
        face_count=1 if detected else 0,
        quality_score=quality if detected else None,
        aligned_face=np.zeros((112, 112, 3), dtype=np.uint8) if detected else None,
        full_image=None,
        message="ok",
    )
    svc.check_liveness.return_value = LivenessResult(
        is_live=liveness_live, confidence=liveness_conf
    )
    svc.compute_embedding.return_value = [0.1] * 512
    svc.compare_embeddings.return_value = similarity
    return svc


class TestFaceRecognition:
    async def test_capture_face(self, client, invig_token):
        svc = _mock_face_svc()
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/capture",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                headers=auth(invig_token),
            )
        assert r.status_code == 200
        assert r.json()["face_detected"] is True

    async def test_liveness_check(self, client, invig_token):
        svc = _mock_face_svc()
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/liveness-check",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                headers=auth(invig_token),
            )
        assert r.status_code == 200
        data = r.json()
        assert data["is_live"] is True
        assert data["confidence"] == 0.95

    async def test_enroll_student(self, client, admin_token, sample_student):
        svc = _mock_face_svc()
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/enroll",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                data={"student_number": "223895956"},
                headers=auth(admin_token),
            )
        assert r.status_code == 200
        assert r.json()["enrolled"] is True

    async def test_enroll_no_consent_blocked(self, client, admin_token, db, sample_student):
        sample_student.ConsentGiven = False
        await db.commit()
        svc = _mock_face_svc()
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/enroll",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                data={"student_number": "223895956"},
                headers=auth(admin_token),
            )
        assert r.status_code == 403

    async def test_verify_granted(self, client, invig_token, enrolled_student, exam_session):
        svc = _mock_face_svc(similarity=0.90)
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/verify",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                data={
                    "student_number": "223895956",
                    "exam_session_id": str(exam_session.id),
                },
                headers=auth(invig_token),
            )
        assert r.status_code == 200
        assert r.json()["outcome"] == "granted"

    async def test_verify_denied_liveness(self, client, invig_token, enrolled_student):
        svc = _mock_face_svc(liveness_live=False, liveness_conf=0.2)
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/verify",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                data={"student_number": "223895956"},
                headers=auth(invig_token),
            )
        assert r.status_code == 200
        assert r.json()["outcome"] == "denied_liveness"

    async def test_verify_denied_face_mismatch(self, client, invig_token, enrolled_student):
        svc = _mock_face_svc(similarity=0.30)
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/verify",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                data={"student_number": "223895956"},
                headers=auth(invig_token),
            )
        assert r.status_code == 200
        assert r.json()["outcome"] == "denied_identity"

    async def test_verify_no_face_detected(self, client, invig_token, enrolled_student):
        svc = _mock_face_svc(detected=False)
        with patch("endpoints.face.get_face_service", return_value=svc):
            r = await client.post(
                "/api/v1/face/verify",
                files={"image": ("face.jpg", fake_jpeg(), "image/jpeg")},
                data={"student_number": "223895956"},
                headers=auth(invig_token),
            )
        assert r.status_code == 200
        assert r.json()["outcome"] == "denied_identity"
        assert r.json()["face_detected"] is False


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminDashboard:
    async def test_get_stats(self, client, admin_token):
        r = await client.get("/api/v1/admin/stats", headers=auth(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert "total_students" in data
        assert "false_acceptance_rate" in data
        assert "active_exam_sessions" in data

    async def test_stats_counts_students(self, client, admin_token, sample_student):
        r = await client.get("/api/v1/admin/stats", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["total_students"] >= 1

    async def test_create_exam_session(self, client, admin_token):
        now = datetime.now(timezone.utc)
        r = await client.post(
            "/api/v1/admin/exam-session",
            json={
                "module_code": "ISE117V",
                "module_name": "Software Engineering",
                "venue": "Hall B",
                "scheduled_start": (now + timedelta(hours=1)).isoformat(),
                "scheduled_end": (now + timedelta(hours=3)).isoformat(),
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 201
        assert r.json()["module_code"] == "ISE117V"

    async def test_venue_clash_rejected(self, client, admin_token, exam_session):
        now = datetime.now(timezone.utc)
        r = await client.post(
            "/api/v1/admin/exam-session",
            json={
                "module_code": "COS111",
                "module_name": "Programming",
                "venue": "Hall A",
                "scheduled_start": (now - timedelta(minutes=10)).isoformat(),
                "scheduled_end": (now + timedelta(hours=1)).isoformat(),
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 409

    async def test_list_exam_sessions(self, client, invig_token, exam_session):
        r = await client.get("/api/v1/admin/exam-sessions", headers=auth(invig_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_list_venues(self, client, invig_token, exam_session):
        r = await client.get("/api/v1/admin/venues", headers=auth(invig_token))
        assert r.status_code == 200

    async def test_attempt_log(self, client, admin_token):
        r = await client.get("/api/v1/admin/reports/attempts", headers=auth(admin_token))
        assert r.status_code == 200
        assert "attempts" in r.json()

    async def test_attendance_register(self, client, admin_token, exam_session):
        r = await client.get(
            f"/api/v1/admin/reports/attendance/{exam_session.id}",
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["module_code"] == "SFG117V"

    async def test_create_user(self, client, admin_token):
        r = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "new_invig@tut.ac.za",
                "full_name": "New Invigilator",
                "role": "invigilator",
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 201
        assert r.json()["role"] == "invigilator"

    async def test_list_users(self, client, admin_token, admin_user):
        r = await client.get("/api/v1/admin/users", headers=auth(admin_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    async def test_invigilator_cannot_list_users(self, client, invig_token):
        r = await client.get("/api/v1/admin/users", headers=auth(invig_token))
        assert r.status_code == 403

    async def test_invigilator_cannot_create_exam_session(self, client, invig_token):
        now = datetime.now(timezone.utc)
        r = await client.post(
            "/api/v1/admin/exam-session",
            json={
                "module_code": "XYZ999",
                "module_name": "Test",
                "venue": "Hall Z",
                "scheduled_start": (now + timedelta(hours=1)).isoformat(),
                "scheduled_end": (now + timedelta(hours=3)).isoformat(),
            },
            headers=auth(invig_token),
        )
        assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY / ENCRYPTION UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurity:
    def test_aes_encrypt_decrypt_roundtrip(self):
        original = list(np.random.uniform(-1, 1, 512).astype(float))
        ciphertext = encrypt_embedding(original)
        assert isinstance(ciphertext, str)
        assert ciphertext != str(original)
        recovered = decrypt_embedding(ciphertext)
        assert len(recovered) == 512
        assert abs(recovered[0] - original[0]) < 1e-6

    def test_different_nonces_each_call(self):
        emb = [0.5] * 512
        c1 = encrypt_embedding(emb)
        c2 = encrypt_embedding(emb)
        assert c1 != c2

    def test_access_token_has_role(self):
        token = create_access_token("42", "admin")
        from core.security import decode_token
        payload = decode_token(token)
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
        assert payload["sub"] == "42"

    def test_hash_password_is_bcrypt(self):
        import bcrypt
        hashed = hash_password("Secret123!")
        assert bcrypt.checkpw(b"Secret123!", hashed.encode())

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        import bcrypt
        assert not bcrypt.checkpw(b"wrong", hashed.encode())
