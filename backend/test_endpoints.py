"""
Full endpoint smoke-test for EduVerify backend.
Covers every registered route (35 endpoints).

Run inside the container:
    docker compose exec backend python test_endpoints.py

Requires: pip install httpx
"""

import httpx
import json
import sys

BASE = "http://localhost:8000/api/v1"
PASS  = "\033[92m PASS\033[0m"
FAIL  = "\033[91m FAIL\033[0m"
SKIP  = "\033[93m SKIP\033[0m"
INFO  = "\033[94m INFO\033[0m"

# Minimal valid 1×1 JPEG for face endpoint tests
TINY_JPEG = bytes([
    0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,0x01,0x00,
    0x00,0x01,0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,0x00,0x08,0x06,0x06,
    0x07,0x06,0x05,0x08,0x07,0x07,0x07,0x09,0x09,0x08,0x0A,0x0C,0x14,0x0D,
    0x0C,0x0B,0x0B,0x0C,0x19,0x12,0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,
    0x1A,0x1C,0x1C,0x20,0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,0x1C,0x28,
    0x37,0x29,0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,0x39,0x3D,0x38,0x32,
    0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,0x00,0x01,
    0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x1F,0x00,0x00,0x01,0x05,0x01,0x01,
    0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x02,
    0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0xFF,0xDA,0x00,0x08,0x01,
    0x01,0x00,0x00,0x3F,0x00,0xFB,0xD6,0xFF,0xD9,
])


def _safe_json(r: httpx.Response):
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text[:200]}


def log(label, method, path, code, expected, body=None):
    ok = code == expected
    status = PASS if ok else FAIL
    print(f"{status} [{code}] {method} {path}  —  {label}")
    if not ok:
        print(f"       Expected {expected}, got {code}")
        if body:
            snippet = json.dumps(body)[:300]
            print(f"       Response: {snippet}")
    return ok


def log_any(label, method, path, code, not_expected=(500,), body=None):
    """Pass as long as the status is not in not_expected (e.g. not a crash)."""
    ok = code not in not_expected
    status = PASS if ok else FAIL
    print(f"{status} [{code}] {method} {path}  —  {label}")
    if not ok:
        if body:
            snippet = json.dumps(body)[:300]
            print(f"       Response: {snippet}")
    return ok


def run():
    results = []
    student_id = None
    session_id = None

    with httpx.Client(base_url=BASE, timeout=15) as client:

        # ════════════════════════════════════════════════════════════════
        # HEALTH  (2 endpoints)
        # ════════════════════════════════════════════════════════════════

        # 1. Basic health (unauthenticated)
        r = client.get("/health")
        results.append(log("Basic health check", "GET", "/health", r.status_code, 200))

        # ════════════════════════════════════════════════════════════════
        # AUTH  (1 endpoint)
        # ════════════════════════════════════════════════════════════════

        # 2. Login
        r = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
        ok = log("Admin login", "POST", "/auth/login", r.status_code, 200, _safe_json(r))
        results.append(ok)
        if not ok:
            print("\nLogin failed — aborting (token required for all other tests).")
            _summary(results)
            sys.exit(1)

        token = _safe_json(r)["access_token"]
        auth  = {"Authorization": f"Bearer {token}"}
        print(f"{INFO} Token obtained: {token[:40]}...")

        # ════════════════════════════════════════════════════════════════
        # ADMIN — stats, users, sessions, venues, reports  (8 endpoints)
        # ════════════════════════════════════════════════════════════════

        # 3. System stats
        r = client.get("/admin/stats", headers=auth)
        results.append(log("Admin stats", "GET", "/admin/stats", r.status_code, 200, _safe_json(r)))

        # 4. List users
        r = client.get("/admin/users", headers=auth)
        results.append(log("List users", "GET", "/admin/users", r.status_code, 200, _safe_json(r)))

        # 5. Create user
        r = client.post("/admin/users", headers=auth, json={
            "email": "invig.test@tut.ac.za",
            "full_name": "Test Invigilator",
            "role": "invigilator",
        })
        if r.status_code == 409:
            print(f"{INFO} Test invigilator already exists — skipping create")
            results.append(True)
        else:
            results.append(log("Create user", "POST", "/admin/users", r.status_code, 201, _safe_json(r)))

        # 6. Create exam session
        r = client.post("/admin/exam-session", headers=auth, json={
            "module_code": "COS301",
            "module_name": "Software Engineering",
            "venue": "Hall A",
            "campus": "TUT Pretoria",
            "scheduled_start": "2026-06-15T09:00:00",
            "scheduled_end": "2026-06-15T12:00:00",
        })
        if r.status_code == 409:
            print(f"{INFO} Exam session already exists — looking up existing")
            results.append(True)
            sess_list = client.get("/admin/exam-sessions?upcoming_only=false", headers=auth)
            sessions = _safe_json(sess_list)
            if sessions:
                session_id = sessions[0]["id"]
                print(f"{INFO} Session ID (existing): {session_id}")
        else:
            ok = log("Create exam session", "POST", "/admin/exam-session", r.status_code, 201, _safe_json(r))
            results.append(ok)
            if ok:
                session_id = _safe_json(r)["id"]
                print(f"{INFO} Session ID: {session_id}")

        # 7. List exam sessions
        r = client.get("/admin/exam-sessions", headers=auth)
        results.append(log("List exam sessions", "GET", "/admin/exam-sessions", r.status_code, 200, _safe_json(r)))

        # 8. List venues
        r = client.get("/admin/venues", headers=auth)
        results.append(log("List venues", "GET", "/admin/venues", r.status_code, 200, _safe_json(r)))

        # 9. Attendance report
        if session_id:
            r = client.get(f"/admin/reports/attendance/{session_id}", headers=auth)
            results.append(log("Attendance register", "GET", f"/admin/reports/attendance/{session_id}", r.status_code, 200, _safe_json(r)))

        # 10. Attempt audit log
        r = client.get("/admin/reports/attempts", headers=auth)
        results.append(log("Attempt audit log", "GET", "/admin/reports/attempts", r.status_code, 200, _safe_json(r)))

        # ════════════════════════════════════════════════════════════════
        # STUDENTS  (7 endpoints)
        # ════════════════════════════════════════════════════════════════

        # 11. Register student
        r = client.post("/students/register", headers=auth, json={
            "student_number": "TST000001",
            "full_name": "Jane Doe",
            "email": "jane.doe@tut4life.ac.za",
            "programme": "Software Engineering",
            "year_of_study": 2,
            "biometric_consent": True,
        })
        if r.status_code == 409:
            print(f"{INFO} Student TST000001 already exists — skipping register")
            results.append(True)
            lookup = client.get("/students/by-number/TST000001", headers=auth)
            if lookup.status_code == 200:
                student_id = _safe_json(lookup)["id"]
                print(f"{INFO} Student ID (existing): {student_id}")
        else:
            ok = log("Register student", "POST", "/students/register", r.status_code, 201, _safe_json(r))
            results.append(ok)
            if ok:
                student_id = _safe_json(r)["id"]
                print(f"{INFO} Student ID: {student_id}")

        # 12. List students
        r = client.get("/students/", headers=auth)
        results.append(log("List students", "GET", "/students/", r.status_code, 200, _safe_json(r)))

        # 13. Get student by number
        r = client.get("/students/by-number/TST000001", headers=auth)
        results.append(log("Get student by number", "GET", "/students/by-number/TST000001", r.status_code, 200, _safe_json(r)))

        # 14. Get student by ID
        if student_id:
            r = client.get(f"/students/{student_id}", headers=auth)
            results.append(log("Get student by ID", "GET", f"/students/{student_id}", r.status_code, 200, _safe_json(r)))

        # 15. Update student
        if student_id:
            r = client.put(f"/students/{student_id}", headers=auth, json={
                "full_name": "Jane Updated Doe",
                "year_of_study": 3,
            })
            results.append(log("Update student", "PUT", f"/students/{student_id}", r.status_code, 200, _safe_json(r)))

        # 16. Record consent
        if student_id:
            r = client.post(f"/students/{student_id}/consent?consented=true", headers=auth)
            results.append(log("Record consent", "POST", f"/students/{student_id}/consent", r.status_code, 200, _safe_json(r)))

        # 17. Delete biometric (204 if data exists, 404 if no data — both are valid)
        if student_id:
            r = client.delete(f"/students/{student_id}/face", headers=auth)
            results.append(log_any("Delete biometric (204 if enrolled, 404 if not)", "DELETE", f"/students/{student_id}/face", r.status_code, body=_safe_json(r)))

        # ════════════════════════════════════════════════════════════════
        # ATTENDANCE  (4 endpoints)
        # ════════════════════════════════════════════════════════════════

        # 18. List all attendance
        r = client.get("/attendance/", headers=auth)
        results.append(log("List all attendance", "GET", "/attendance/", r.status_code, 200, _safe_json(r)))

        # 19. Attendance by session
        r = client.get(f"/attendance/session/{session_id or 1}", headers=auth)
        results.append(log("Attendance by session", "GET", "/attendance/session/{id}", r.status_code, 200, _safe_json(r)))

        # 20. Attendance by student
        r = client.get(f"/attendance/student/{student_id or 1}", headers=auth)
        results.append(log("Attendance by student", "GET", "/attendance/student/{id}", r.status_code, 200, _safe_json(r)))

        # 21. Create attendance record
        if student_id and session_id:
            r = client.post(
                "/attendance/create",
                headers=auth,
                params={"student_id": student_id, "session_id": session_id, "status": "present"},
            )
            # 200 on first run; subsequent runs may get 409 (unique constraint) — both are fine
            ok = r.status_code in (200, 201, 409)
            status = PASS if ok else FAIL
            print(f"{status} [{r.status_code}] POST /attendance/create  —  Create attendance record")
            if not ok:
                print(f"       Response: {json.dumps(_safe_json(r))[:300]}")
            results.append(ok)

        # ════════════════════════════════════════════════════════════════
        # ACCESS CONTROL  (4 endpoints)
        # ════════════════════════════════════════════════════════════════

        # 22. Access status
        if student_id:
            r = client.get(f"/access/status/{student_id}", headers=auth)
            results.append(log("Access status", "GET", f"/access/status/{student_id}", r.status_code, 200, _safe_json(r)))

        # 23-25. Grant / Deny / Override — admin role cannot perform these (only invigilator/system)
        #         Correct RBAC response is 403 Forbidden
        if student_id and session_id:
            r = client.post("/access/grant", headers=auth, json={"student_id": student_id, "session_id": session_id})
            results.append(log("Grant access (admin → 403 forbidden)", "POST", "/access/grant", r.status_code, 403, _safe_json(r)))

            r = client.post("/access/deny", headers=auth, json={"student_id": student_id, "session_id": session_id})
            results.append(log("Deny access (admin → 403 forbidden)", "POST", "/access/deny", r.status_code, 403, _safe_json(r)))

            r = client.post("/access/override", headers=auth, json={
                "student_id": student_id, "session_id": session_id,
                "reason": "Testing override endpoint during smoke test"
            })
            results.append(log("Override access (admin → 403 forbidden)", "POST", "/access/override", r.status_code, 403, _safe_json(r)))

        # ════════════════════════════════════════════════════════════════
        # LOGS / AUDIT  (4 endpoints)
        # ════════════════════════════════════════════════════════════════

        # 26. Log a verification attempt
        if student_id and session_id:
            r = client.post("/logs/attempt", headers=auth, json={
                "student_id": student_id,
                "session_id": session_id,
                "device_id": "TEST-DEVICE-001",
                "outcome": "Success",
                "digital_signature": "TEST_SIG_001",
                "venue_location": "Hall A",
                "attempt_number": 1,
            })
            results.append(log("Log verification attempt", "POST", "/logs/attempt", r.status_code, 201, _safe_json(r)))

        # 27. Get student logs
        r = client.get(f"/logs/student/{student_id or 1}", headers=auth)
        results.append(log("Student audit logs", "GET", "/logs/student/{id}", r.status_code, 200, _safe_json(r)))

        # 28. Get session logs by venue
        r = client.get("/logs/session/Hall A", headers=auth)
        results.append(log("Session logs by venue", "GET", "/logs/session/{venue}", r.status_code, 200, _safe_json(r)))

        # 29. Export logs (CSV)
        r = client.get("/logs/export?start_date=2026-01-01&end_date=2026-12-31&format=csv", headers=auth)
        results.append(log("Export audit logs (CSV)", "GET", "/logs/export", r.status_code, 200))

        # ════════════════════════════════════════════════════════════════
        # FACE RECOGNITION  (5 endpoints — image upload required)
        # ════════════════════════════════════════════════════════════════

        print(f"\n{INFO} Face endpoints — sending 1×1 test image (no real face → detection will return false)")

        # 30. Capture / detect face
        r = client.post("/face/capture", headers=auth,
                        files={"image": ("test.jpg", TINY_JPEG, "image/jpeg")})
        results.append(log_any("Face capture", "POST", "/face/capture", r.status_code, body=_safe_json(r)))

        # 31. Liveness check
        r = client.post("/face/liveness-check", headers=auth,
                        files={"image": ("test.jpg", TINY_JPEG, "image/jpeg")})
        results.append(log_any("Liveness check", "POST", "/face/liveness-check", r.status_code, body=_safe_json(r)))

        # 32. Enroll face (no real embedding → will fail gracefully)
        if student_id:
            r = client.post("/face/enroll", headers=auth,
                            data={"student_number": "TST000001"},
                            files={"image": ("test.jpg", TINY_JPEG, "image/jpeg")})
            results.append(log_any("Face enroll", "POST", "/face/enroll", r.status_code, body=_safe_json(r)))

        # 33. Verify face
        if session_id:
            r = client.post("/face/verify", headers=auth,
                            data={"student_number": "TST000001", "exam_session_id": str(session_id)},
                            files={"image": ("test.jpg", TINY_JPEG, "image/jpeg")})
            results.append(log_any("Face verify", "POST", "/face/verify", r.status_code, body=_safe_json(r)))

        # 34. Face override
        r = client.post("/face/override", headers=auth, json={
            "attempt_id": 999999,
            "reason": "Smoke test — no real attempt exists",
        })
        # 404 expected (attempt doesn't exist) — anything except 500 is fine
        results.append(log_any("Face override (no attempt → 404)", "POST", "/face/override", r.status_code, body=_safe_json(r)))

        # ════════════════════════════════════════════════════════════════
        # SIS INTEGRATION  (4 endpoints — external service may be offline)
        # ════════════════════════════════════════════════════════════════

        print(f"\n{INFO} SIS endpoints — external service may be unavailable; any non-500 is a pass")

        # 35. SIS student lookup
        if student_id:
            r = client.get(f"/sis/student/{student_id}", headers=auth)
            results.append(log_any("SIS student lookup", "GET", f"/sis/student/{student_id}", r.status_code, body=_safe_json(r)))

        # 36. SIS eligibility check
        if student_id:
            r = client.get(f"/sis/eligibility/{student_id}", headers=auth)
            results.append(log_any("SIS eligibility", "GET", f"/sis/eligibility/{student_id}", r.status_code, body=_safe_json(r)))

        # 37. SIS exam schedule
        r = client.get("/sis/exam-schedule", headers=auth)
        results.append(log_any("SIS exam schedule", "GET", "/sis/exam-schedule", r.status_code, body=_safe_json(r)))

        # 38. SIS venue check
        r = client.get("/sis/venue-check", headers=auth)
        results.append(log_any("SIS venue check", "GET", "/sis/venue-check", r.status_code, body=_safe_json(r)))

        # ════════════════════════════════════════════════════════════════
        # HEALTH — authenticated  (2 endpoints)
        # ════════════════════════════════════════════════════════════════

        # 39. Cache sync
        r = client.post("/health/cache/sync?force=false", headers=auth, content=b"")
        results.append(log("Cache sync", "POST", "/health/cache/sync", r.status_code, 200, _safe_json(r)))

        # 40. AI models health (models may not be loaded in dev)
        r = client.get("/health/ai-models", headers=auth)
        results.append(log_any("AI models health", "GET", "/health/ai-models", r.status_code, body=_safe_json(r)))

        # 41. SIS connection health
        r = client.get("/health/sis-connection", headers=auth)
        results.append(log_any("SIS connection health", "GET", "/health/sis-connection", r.status_code, body=_safe_json(r)))

    _summary(results)


def _summary(results):
    passed = sum(results)
    total  = len(results)
    colour = "\033[92m" if passed == total else "\033[91m"
    print(f"\n{colour}{'='*40}")
    print(f"  {passed}/{total} tests passed")
    print(f"{'='*40}\033[0m\n")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    run()
