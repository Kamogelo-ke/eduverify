"""
EduVerify test suite
Tests: authentication, student CRUD, face enrolment, verification pipeline, admin dashboard.
Run: pytest tests/ -v
"""
from app.main import app
import io
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, encrypt_embedding, decrypt_embedding, hash_password
from app.db.session import get_db
from app.models.models import Base, Student, User, UserRole, BiometricProfile, ExamSession

SQLALCHEMY_TEST_URL = "sqlite:///./test_eduverify.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={
                       "check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate all tables between tests (faster than drop/create)."""
    yield
    db = TestingSession()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    user = User(
        id=uuid.uuid4(),
        email="admin@tut.ac.za",
        full_name="Admin User",
        hashed_password=hash_password("Adm1nP@ss"),
        role=UserRole.admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def invigilator_user(db):
    user = User(
        id=uuid.uuid4(),
        email="invig@tut.ac.za",
        full_name="Invigilator User",
        hashed_password=hash_password("Inv1gP@ss"),
        role=UserRole.invigilator,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(str(admin_user.id), "admin")


@pytest.fixture
def invig_token(invigilator_user):
    return create_access_token(str(invigilator_user.id), "invigilator")


@pytest.fixture
def sample_student(db):
    student = Student(
        id=uuid.uuid4(),
        student_number="223895956",
        full_name="Thlong KE",
        email="thlong@tut.ac.za",
        programme="Software Engineering",
        year_of_study=3,
        biometric_consent=True,
        consent_date=datetime.now(timezone.utc),
        is_active=True,
    )
    db.add(student)
    db.commit()
    return student


@pytest.fixture
def enrolled_student(db, sample_student):
    embedding = [0.1] * 512
    profile = BiometricProfile(
        student_id=sample_student.id,
        encrypted_embedding=encrypt_embedding(embedding),
        face_quality_score=0.92,
    )
    db.add(profile)
    db.commit()
    db.refresh(sample_student)
    return sample_student


@pytest.fixture
def exam_session(db, admin_user):
    now = datetime.now(timezone.utc)
    session = ExamSession(
        id=uuid.uuid4(),
        module_code="SFG117V",
        module_name="Software Engineering Project",
        venue="Hall A",
        campus="TUT Pretoria",
        scheduled_start=now - timedelta(minutes=30),
        scheduled_end=now + timedelta(hours=2),
        created_by=admin_user.id,
    )
    db.add(session)
    db.commit()
    return session


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fake_image() -> bytes:
    """Minimal valid JPEG bytes for upload tests."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(
        128, 128, 128)).save(buf, format="JPEG")
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# AUTH TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAuth:
    def test_login_success(self, client, admin_user):
        r = client.post("/api/v1/auth/login",
                        json={"email": "admin@tut.ac.za", "password": "Adm1nP@ss"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["role"] == "admin"

    def test_login_wrong_password(self, client, admin_user):
        r = client.post("/api/v1/auth/login",
                        json={"email": "admin@tut.ac.za", "password": "wrong"})
        assert r.status_code == 401

    def test_get_me(self, client, admin_user, admin_token):
        r = client.get("/api/v1/auth/me", headers=_auth_headers(admin_token))
        assert r.status_code == 200
        assert r.json()["email"] == "admin@tut.ac.za"

    def test_protected_route_no_token(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT PROFILE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestStudentProfiles:
    def test_register_student(self, client, admin_token):
        r = client.post("/api/v1/students/register",
                        json={
                            "student_number": "220000001",
                            "full_name": "Jane Doe",
                            "email": "jane@tut.ac.za",
                            "programme": "Computer Science",
                            "year_of_study": 2,
                            "biometric_consent": True,
                        },
                        headers=_auth_headers(admin_token))
        assert r.status_code == 201
        data = r.json()
        assert data["student_number"] == "220000001"
        assert data["biometric_consent"] is True

    def test_register_duplicate_student_number(self, client, admin_token, sample_student):
        r = client.post("/api/v1/students/register",
                        json={
                            "student_number": "223895956",
                            "full_name": "Clone Student",
                            "email": "clone@tut.ac.za",
                        },
                        headers=_auth_headers(admin_token))
        assert r.status_code == 409

    def test_list_students(self, client, admin_token, sample_student):
        r = client.get("/api/v1/students/", headers=_auth_headers(admin_token))
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_get_student_by_id(self, client, admin_token, sample_student):
        r = client.get(f"/api/v1/students/{sample_student.id}",
                       headers=_auth_headers(admin_token))
        assert r.status_code == 200
        assert r.json()["student_number"] == "223895956"

    def test_get_student_by_number(self, client, invig_token, sample_student):
        r = client.get("/api/v1/students/by-number/223895956",
                       headers=_auth_headers(invig_token))
        assert r.status_code == 200

    def test_update_student(self, client, admin_token, sample_student):
        r = client.put(f"/api/v1/students/{sample_student.id}",
                       json={"year_of_study": 4},
                       headers=_auth_headers(admin_token))
        assert r.status_code == 200
        assert r.json()["year_of_study"] == 4

    def test_invigilator_cannot_register(self, client, invig_token):
        r = client.post("/api/v1/students/register",
                        json={"student_number": "999",
                              "full_name": "X", "email": "x@x.com"},
                        headers=_auth_headers(invig_token))
        assert r.status_code == 403

    def test_record_consent(self, client, admin_token, sample_student):
        r = client.post(f"/api/v1/students/{sample_student.id}/consent?consented=true",
                        headers=_auth_headers(admin_token))
        assert r.status_code == 200
        assert r.json()["biometric_consent"] is True

    def test_delete_biometric(self, client, admin_token, enrolled_student):
        r = client.delete(f"/api/v1/students/{enrolled_student.id}/face",
                          headers=_auth_headers(admin_token))
        assert r.status_code == 204


# ══════════════════════════════════════════════════════════════════════════════
# FACE RECOGNITION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestFaceRecognition:
    def _mock_svc(self, detected=True, quality=0.9, liveness_live=True, liveness_conf=0.95,
                  similarity=0.85):
        from app.services.face_service import DetectionResult, LivenessResult
        import numpy as np
        svc = MagicMock()
        svc.detect_and_align.return_value = DetectionResult(
            face_detected=detected, face_count=1 if detected else 0,
            quality_score=quality if detected else None,
            aligned_face=np.zeros(
                (112, 112, 3), dtype=np.uint8) if detected else None,
            message="ok",
        )
        svc.check_liveness.return_value = LivenessResult(
            is_live=liveness_live, confidence=liveness_conf)
        svc.compute_embedding.return_value = [0.1] * 512
        svc.compare_embeddings.return_value = similarity
        return svc

    def test_enroll_student(self, client, admin_token, sample_student):
        svc = self._mock_svc()
        with patch("app.api.v1.endpoints.face.get_face_service", return_value=svc):
            r = client.post("/api/v1/face/enroll",
                            files={
                                "image": ("face.jpg", _fake_image(), "image/jpeg")},
                            data={"student_number": "223895956"},
                            headers=_auth_headers(admin_token))
        assert r.status_code == 200
        assert r.json()["enrolled"] is True

    def test_enroll_no_consent_blocked(self, client, admin_token, db, sample_student):
        sample_student.biometric_consent = False
        db.commit()
        svc = self._mock_svc()
        with patch("app.api.v1.endpoints.face.get_face_service", return_value=svc):
            r = client.post("/api/v1/face/enroll",
                            files={
                                "image": ("face.jpg", _fake_image(), "image/jpeg")},
                            data={"student_number": "223895956"},
                            headers=_auth_headers(admin_token))
        assert r.status_code == 403

    def test_capture_face(self, client, invig_token):
        svc = self._mock_svc()
        with patch("app.api.v1.endpoints.face.get_face_service", return_value=svc):
            r = client.post("/api/v1/face/capture",
                            files={
                                "image": ("cam.jpg", _fake_image(), "image/jpeg")},
                            headers=_auth_headers(invig_token))
        assert r.status_code == 200
        assert r.json()["face_detected"] is True

    def test_liveness_check(self, client, invig_token):
        svc = self._mock_svc()
        with patch("app.api.v1.endpoints.face.get_face_service", return_value=svc):
            r = client.post("/api/v1/face/liveness-check",
                            files={
                                "image": ("cam.jpg", _fake_image(), "image/jpeg")},
                            headers=_auth_headers(invig_token))
        assert r.status_code == 200
        data = r.json()
        assert data["is_live"] is True
        assert data["confidence"] == 0.95

    def test_verify_granted(self, client, invig_token, enrolled_student, exam_session):
        svc = self._mock_svc(similarity=0.90)
        with patch("app.api.v1.endpoints.face.get_face_service", return_value=svc):
            r = client.post("/api/v1/face/verify",
                            files={
                                "image": ("cam.jpg", _fake_image(), "image/jpeg")},
                            data={
                                "student_number": "223895956",
                                "exam_session_id": str(exam_session.id),
                            },
                            headers=_auth_headers(invig_token))
        assert r.status_code == 200
        assert r.json()["outcome"] == "granted"

    def test_verify_denied_liveness(self, client, invig_token, enrolled_student):
        svc = self._mock_svc(liveness_live=False, liveness_conf=0.2)
        with patch("app.api.v1.endpoints.face.get_face_service", return_value=svc):
            r = client.post("/api/v1/face/verify",
                            files={
                                "image": ("cam.jpg", _fake_image(), "image/jpeg")},
                            data={"student_number": "223895956"},
                            headers=_auth_headers(invig_token))
        assert r.status_code == 200
        assert r.json()["outcome"] == "denied_liveness"

    def test_verify_denied_face_mismatch(self, client, invig_token, enrolled_student):
        svc = self._mock_svc(similarity=0.30)
        with patch("app.api.v1.endpoints.face.get_face_service", return_value=svc):
            r = client.post("/api/v1/face/verify",
                            files={
                                "image": ("cam.jpg", _fake_image(), "image/jpeg")},
                            data={"student_number": "223895956"},
                            headers=_auth_headers(invig_token))
        assert r.status_code == 200
        assert r.json()["outcome"] == "denied_identity"


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminDashboard:
    def test_get_stats(self, client, admin_token):
        r = client.get("/api/v1/admin/stats",
                       headers=_auth_headers(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert "total_students" in data
        assert "false_acceptance_rate" in data

    def test_create_exam_session(self, client, admin_token):
        now = datetime.now(timezone.utc)
        r = client.post("/api/v1/admin/exam-session",
                        json={
                            "module_code": "ISE117V",
                            "module_name": "Software Engineering",
                            "venue": "Hall B",
                            "campus": "TUT Pretoria",
                            "scheduled_start": (now + timedelta(hours=1)).isoformat(),
                            "scheduled_end": (now + timedelta(hours=3)).isoformat(),
                        },
                        headers=_auth_headers(admin_token))
        assert r.status_code == 201
        assert r.json()["module_code"] == "ISE117V"

    def test_venue_clash_rejected(self, client, admin_token, exam_session):
        now = datetime.now(timezone.utc)
        r = client.post("/api/v1/admin/exam-session",
                        json={
                            "module_code": "COS111",
                            "module_name": "Programming",
                            "venue": "Hall A",
                            "campus": "TUT Pretoria",
                            "scheduled_start": (now - timedelta(minutes=10)).isoformat(),
                            "scheduled_end": (now + timedelta(hours=1)).isoformat(),
                        },
                        headers=_auth_headers(admin_token))
        assert r.status_code == 409

    def test_list_exam_sessions(self, client, invig_token, exam_session):
        r = client.get("/api/v1/admin/exam-sessions",
                       headers=_auth_headers(invig_token))
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_venues(self, client, invig_token, exam_session):
        r = client.get("/api/v1/admin/venues",
                       headers=_auth_headers(invig_token))
        assert r.status_code == 200

    def test_attempt_log(self, client, admin_token):
        r = client.get("/api/v1/admin/reports/attempts",
                       headers=_auth_headers(admin_token))
        assert r.status_code == 200
        assert "attempts" in r.json()

    def test_attendance_register(self, client, admin_token, exam_session):
        r = client.get(f"/api/v1/admin/reports/attendance/{exam_session.id}",
                       headers=_auth_headers(admin_token))
        assert r.status_code == 200
        data = r.json()
        assert data["module_code"] == "SFG117V"

    def test_create_user(self, client, admin_token):
        r = client.post("/api/v1/admin/users",
                        json={
                            "email": "new_invig@tut.ac.za",
                            "full_name": "New Invigilator",
                            "password": "Secure123!",
                            "role": "invigilator",
                        },
                        headers=_auth_headers(admin_token))
        assert r.status_code == 201
        assert r.json()["role"] == "invigilator"

    def test_invigilator_cannot_access_user_list(self, client, invig_token):
        r = client.get("/api/v1/admin/users",
                       headers=_auth_headers(invig_token))
        assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# SECURITY / ENCRYPTION UNIT TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurity:
    def test_aes_encrypt_decrypt_roundtrip(self):
        original = list(np.random.uniform(-1, 1, 512).astype(float))
        ciphertext = encrypt_embedding(original)
        assert isinstance(ciphertext, str)
        assert ciphertext != str(original)   # must not store plaintext
        recovered = decrypt_embedding(ciphertext)
        assert len(recovered) == 512
        assert abs(recovered[0] - original[0]) < 1e-6

    def test_different_nonces_each_call(self):
        emb = [0.5] * 512
        c1 = encrypt_embedding(emb)
        c2 = encrypt_embedding(emb)
        assert c1 != c2   # nonce must be random each time

    def test_access_token_structure(self, admin_user):
        token = create_access_token(str(admin_user.id), "admin")
        from app.core.security import decode_token
        payload = decode_token(token)
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
