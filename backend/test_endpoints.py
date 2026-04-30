"""
Quick endpoint smoke-test for EduVerify backend.
Run from the project root:
    python backend/test_endpoints.py

Requires: pip install httpx
"""

import httpx
import json
import sys

BASE = "http://localhost:8000/api/v1"
PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"
INFO = "\033[94m INFO\033[0m"


def _safe_json(r: httpx.Response):
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text[:200]}


def log(label: str, method: str, path: str, code: int, expected: int, body=None):
    ok = code == expected
    status = PASS if ok else FAIL
    print(f"{status} [{code}] {method} {path}  —  {label}")
    if not ok:
        print(f"       Expected {expected}, got {code}")
        if body:
            print(f"       Response: {json.dumps(body, indent=2)[:300]}")
    return ok


def run():
    results = []
    token = None
    student_id = None
    session_id = None

    with httpx.Client(base_url=BASE, timeout=10) as client:

        # ── 1. Health check (unauthenticated) ──────────────────────────────────
        r = client.get("/health")
        results.append(log("Basic health check", "GET", "/health", r.status_code, 200))

        # ── 2. Login ───────────────────────────────────────────────────────────
        r = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
        ok = log("Admin login", "POST", "/auth/login", r.status_code, 200, _safe_json(r))
        results.append(ok)
        if not ok:
            print("\nLogin failed — aborting remaining tests (token required).")
            _summary(results)
            sys.exit(1)

        token = _safe_json(r)["access_token"]
        auth = {"Authorization": f"Bearer {token}"}
        print(f"{INFO} Token obtained: {token[:40]}...")

        # ── 3. System stats ────────────────────────────────────────────────────
        r = client.get("/admin/stats", headers=auth)
        results.append(log("Admin stats", "GET", "/admin/stats", r.status_code, 200, _safe_json(r)))

        # ── 5. List users ──────────────────────────────────────────────────────
        r = client.get("/admin/users", headers=auth)
        results.append(log("List users", "GET", "/admin/users", r.status_code, 200, _safe_json(r)))

        # ── 6. Register a student ──────────────────────────────────────────────
        r = client.post("/students/register", headers=auth, json={
            "student_number": "TST000001",
            "full_name": "Jane Doe",
            "email": "jane.doe@tut4life.ac.za",
            "programme": "Software Engineering",
            "year_of_study": 2,
            "biometric_consent": True,
        })
        if r.status_code == 409:
            # Already registered from a previous test run — treat as pass, look up existing
            print(f"{INFO} Student TST000001 already exists — skipping register (not a failure)")
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

        # ── 7. List students ───────────────────────────────────────────────────
        r = client.get("/students/", headers=auth)
        results.append(log("List students", "GET", "/students/", r.status_code, 200, _safe_json(r)))

        # ── 8. Get student by number ───────────────────────────────────────────
        r = client.get("/students/by-number/TST000001", headers=auth)
        results.append(log("Get student by number", "GET", "/students/by-number/TST000001", r.status_code, 200, _safe_json(r)))

        # ── 9. Get student by ID ───────────────────────────────────────────────
        if student_id:
            r = client.get(f"/students/{student_id}", headers=auth)
            results.append(log("Get student by ID", "GET", f"/students/{student_id}", r.status_code, 200, _safe_json(r)))

        # ── 10. Create exam session ────────────────────────────────────────────
        r = client.post("/admin/exam-session", headers=auth, json={
            "module_code": "COS301",
            "module_name": "Software Engineering",
            "venue": "Hall A",
            "campus": "TUT Pretoria",
            "scheduled_start": "2026-05-15T09:00:00",
            "scheduled_end": "2026-05-15T12:00:00",
        })
        if r.status_code == 409:
            print(f"{INFO} Exam session already exists — skipping create (not a failure)")
            results.append(True)
            # Grab first session from list to use its ID downstream
            sess_list = client.get("/admin/exam-sessions?upcoming_only=false", headers=auth)
            if sess_list.status_code == 200:
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

        # ── 11. List exam sessions ─────────────────────────────────────────────
        r = client.get("/admin/exam-sessions", headers=auth)
        results.append(log("List exam sessions", "GET", "/admin/exam-sessions", r.status_code, 200, _safe_json(r)))

        # ── 12. List venues ────────────────────────────────────────────────────
        r = client.get("/admin/venues", headers=auth)
        results.append(log("List venues", "GET", "/admin/venues", r.status_code, 200, _safe_json(r)))

        # ── 13. Cache sync ─────────────────────────────────────────────────────
        r = client.post("/health/cache/sync?force=false", headers=auth, content=b"")
        results.append(log("Cache sync", "POST", "/health/cache/sync", r.status_code, 200, _safe_json(r)))

        # ── 14. Attendance report ──────────────────────────────────────────────
        if session_id:
            r = client.get(f"/admin/reports/attendance/{session_id}", headers=auth)
            results.append(log("Attendance register", "GET", f"/admin/reports/attendance/{session_id}", r.status_code, 200, _safe_json(r)))

        # ── 15. Attempt log ────────────────────────────────────────────────────
        r = client.get("/admin/reports/attempts", headers=auth)
        results.append(log("Attempt audit log", "GET", "/admin/reports/attempts", r.status_code, 200, _safe_json(r)))

    _summary(results)


def _summary(results):
    passed = sum(results)
    total = len(results)
    colour = "\033[92m" if passed == total else "\033[91m"
    print(f"\n{colour}{'='*40}")
    print(f"  {passed}/{total} tests passed")
    print(f"{'='*40}\033[0m\n")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    run()
