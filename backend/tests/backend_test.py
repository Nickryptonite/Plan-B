"""SideQuest backend pytest suite.
Covers: public endpoints, auth, worker/client/admin flows and role enforcement.
Session tokens are created via direct MongoDB insertion (Emergent OAuth shortcut).
"""
import os
import time
import uuid
import requests
import pytest
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://planb-work.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

_mongo = MongoClient(MONGO_URL)
_db = _mongo[DB_NAME]


def _mk_session(user_id: str) -> str:
    token = f"test_session_{user_id}_{uuid.uuid4().hex[:8]}"
    _db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return token


@pytest.fixture(scope="session")
def worker_token():
    t = _mk_session("user_demo_worker1")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


@pytest.fixture(scope="session")
def worker2_token():
    t = _mk_session("user_demo_worker2")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


@pytest.fixture(scope="session")
def client_token():
    t = _mk_session("user_demo_client1")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


@pytest.fixture(scope="session")
def admin_token():
    t = _mk_session("user_demo_admin")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ============ Public ============
class TestPublic:
    def test_root(self):
        r = requests.get(f"{API}/")
        assert r.status_code == 200
        data = r.json()
        assert data.get("version") == "1.0"
        assert "SideQuest" in data.get("message", "")

    def test_seed_idempotent(self):
        r = requests.post(f"{API}/seed")
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert data.get("already_seeded") is True

    def test_tasks_public(self):
        r = requests.get(f"{API}/tasks/public")
        assert r.status_code == 200
        tasks = r.json()
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        for t in tasks:
            assert t["status"] == "open"

    def test_waitlist_accepts(self):
        email = f"TEST_wl_{uuid.uuid4().hex[:6]}@example.com"
        r = requests.post(f"{API}/waitlist", json={
            "name": "TEST WL", "email": email, "role": "worker", "interest": "Canva"
        })
        assert r.status_code == 200
        assert r.json().get("ok") is True
        _db.waitlist.delete_one({"email": email})

    def test_feedback_accepts(self):
        r = requests.post(f"{API}/feedback", json={
            "name": "TEST FB", "email": "test@example.com", "message": "great"
        })
        assert r.status_code == 200
        assert r.json().get("ok") is True
        _db.feedback.delete_many({"name": "TEST FB"})


# ============ Auth ============
class TestAuth:
    def test_session_invalid(self):
        r = requests.post(f"{API}/auth/session", json={"session_id": "definitely_invalid_xyz"})
        assert r.status_code == 401

    def test_me_no_auth(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_me_with_bearer(self, worker_token):
        r = requests.get(f"{API}/auth/me", headers=_auth(worker_token))
        assert r.status_code == 200
        assert r.json()["user_id"] == "user_demo_worker1"

    def test_me_with_cookie(self, worker_token):
        r = requests.get(f"{API}/auth/me", cookies={"session_token": worker_token})
        assert r.status_code == 200
        assert r.json()["email"] == "priya@du.ac.in"


# ============ Worker flow ============
class TestWorker:
    def test_list_open_tasks(self, worker_token):
        r = requests.get(f"{API}/tasks?status=open", headers=_auth(worker_token))
        assert r.status_code == 200
        tasks = r.json()
        assert any(t["status"] == "open" for t in tasks)

    def test_apply_assigns_task(self, worker_token):
        # Pick an open task not already assigned to worker1
        tasks = requests.get(f"{API}/tasks?status=open", headers=_auth(worker_token)).json()
        assert tasks, "Need at least one open task"
        tid = tasks[0]["task_id"]
        r = requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(worker_token))
        assert r.status_code == 200
        # Verify status
        t = requests.get(f"{API}/tasks/{tid}", headers=_auth(worker_token)).json()
        assert t["status"] == "assigned"
        assert t["assigned_to"] == "user_demo_worker1"

    def test_submit_work(self, worker_token):
        # find assigned task
        t = _db.tasks.find_one({"assigned_to": "user_demo_worker1", "status": "assigned"})
        assert t, "Need assigned task"
        r = requests.post(f"{API}/submissions", headers=_auth(worker_token), json={
            "task_id": t["task_id"], "submission_text": "TEST_submission", "submission_url": "https://example.com"
        })
        assert r.status_code == 200
        sub = r.json()
        assert sub["status"] == "pending"
        # task status now in_review
        t2 = requests.get(f"{API}/tasks/{t['task_id']}", headers=_auth(worker_token)).json()
        assert t2["status"] == "in_review"

    def test_list_my_submissions(self, worker_token):
        r = requests.get(f"{API}/submissions?mine=worker", headers=_auth(worker_token))
        assert r.status_code == 200
        subs = r.json()
        assert all(s["worker_id"] == "user_demo_worker1" for s in subs)
        assert any(s.get("submission_text") == "TEST_submission" for s in subs)


# ============ Client flow ============
class TestClient:
    created_task_id = None
    created_sub_id = None

    def test_create_task(self, client_token):
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_Task Logo work",
            "description": "Need a logo",
            "category": "Canva Design",
            "budget": 500.0,
            "deadline": "2026-04-01",
            "required_skills": ["Canva Design"],
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["title"] == "TEST_Task Logo work"
        assert data["client_id"] == "user_demo_client1"
        TestClient.created_task_id = data["task_id"]

    def test_list_mine_posted(self, client_token):
        r = requests.get(f"{API}/tasks?mine=posted", headers=_auth(client_token))
        assert r.status_code == 200
        assert any(t["task_id"] == TestClient.created_task_id for t in r.json())

    def test_approve_flow(self, worker_token, client_token):
        # Worker applies + submits on created task
        tid = TestClient.created_task_id
        r = requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(worker_token))
        assert r.status_code == 200
        r = requests.post(f"{API}/submissions", headers=_auth(worker_token), json={
            "task_id": tid, "submission_text": "TEST_done"
        })
        assert r.status_code == 200
        sub_id = r.json()["submission_id"]
        TestClient.created_sub_id = sub_id

        # capture earnings before
        before = _db.users.find_one({"user_id": "user_demo_worker1"})["earnings"]

        r = requests.post(f"{API}/submissions/{sub_id}/review", headers=_auth(client_token), json={
            "action": "approve", "feedback": "good"
        })
        assert r.status_code == 200

        # verify task completed
        t = requests.get(f"{API}/tasks/{tid}", headers=_auth(client_token)).json()
        assert t["status"] == "completed"

        after = _db.users.find_one({"user_id": "user_demo_worker1"})["earnings"]
        assert after == before + 500.0

    def test_reject_flow(self, worker2_token, client_token):
        # Create task, w2 applies+submits, client rejects
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_Task Reject", "description": "x", "category": "Research",
            "budget": 100.0, "deadline": "2026-04-10", "required_skills": []
        })
        tid = r.json()["task_id"]
        requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(worker2_token))
        r = requests.post(f"{API}/submissions", headers=_auth(worker2_token), json={
            "task_id": tid, "submission_text": "TEST_reject_me"
        })
        sub_id = r.json()["submission_id"]
        r = requests.post(f"{API}/submissions/{sub_id}/review", headers=_auth(client_token), json={
            "action": "reject", "feedback": "redo"
        })
        assert r.status_code == 200
        t = requests.get(f"{API}/tasks/{tid}", headers=_auth(client_token)).json()
        assert t["status"] == "assigned"


# ============ Admin ============
class TestAdmin:
    def test_stats(self, admin_token):
        r = requests.get(f"{API}/admin/stats", headers=_auth(admin_token))
        assert r.status_code == 200
        d = r.json()
        for k in ["total_users", "workers", "clients", "total_tasks", "by_category"]:
            assert k in d
        assert isinstance(d["by_category"], list)

    def test_users_list(self, admin_token):
        r = requests.get(f"{API}/admin/users", headers=_auth(admin_token))
        assert r.status_code == 200
        users = r.json()
        assert any(u["user_id"] == "user_demo_admin" for u in users)

    def test_update_role(self, admin_token):
        # Toggle worker2 role to worker (should still succeed)
        r = requests.post(f"{API}/admin/users/user_demo_worker2/role",
                          headers=_auth(admin_token), json={"role": "worker"})
        assert r.status_code == 200

    def test_invalid_role(self, admin_token):
        r = requests.post(f"{API}/admin/users/user_demo_worker2/role",
                          headers=_auth(admin_token), json={"role": "ceo"})
        assert r.status_code == 400

    def test_mark_paid(self, admin_token):
        # Use seeded submission
        r = requests.post(f"{API}/submissions/sub_demo_1/mark-paid", headers=_auth(admin_token))
        assert r.status_code == 200
        sub = _db.submissions.find_one({"submission_id": "sub_demo_1"})
        assert sub["payment_status"] == "paid"

    def test_waitlist(self, admin_token):
        r = requests.get(f"{API}/admin/waitlist", headers=_auth(admin_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_feedback(self, admin_token):
        r = requests.get(f"{API}/admin/feedback", headers=_auth(admin_token))
        assert r.status_code == 200

    def test_non_admin_blocked(self, worker_token):
        r = requests.get(f"{API}/admin/stats", headers=_auth(worker_token))
        assert r.status_code == 403


# ============ Role enforcement ============
class TestRoleEnforcement:
    def test_worker_cannot_post_task(self, worker_token):
        r = requests.post(f"{API}/tasks", headers=_auth(worker_token), json={
            "title": "TEST nope", "description": "x", "category": "Research",
            "budget": 100.0, "deadline": "2026-04-01", "required_skills": []
        })
        assert r.status_code == 403

    def test_client_cannot_apply(self, client_token):
        # find an open task
        tasks = _db.tasks.find({"status": "open"}).limit(1)
        tid = list(tasks)[0]["task_id"]
        r = requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(client_token))
        assert r.status_code == 403

    def test_worker_cannot_submit_others_task(self, worker2_token):
        # Find a task assigned to worker1
        t = _db.tasks.find_one({"assigned_to": "user_demo_worker1"})
        if not t:
            pytest.skip("no worker1 assigned task")
        r = requests.post(f"{API}/submissions", headers=_auth(worker2_token), json={
            "task_id": t["task_id"], "submission_text": "shouldn't work"
        })
        assert r.status_code == 403


def teardown_module(module):
    # Clean TEST_ data
    _db.tasks.delete_many({"title": {"$regex": "^TEST_"}})
    _db.submissions.delete_many({"submission_text": {"$regex": "^TEST_"}})
