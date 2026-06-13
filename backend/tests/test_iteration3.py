"""Iteration 3 backend tests:
- Reliability fields on /api/auth/me
- /api/admin/analytics schema + 403 for non-admin
- /api/users/{id}/public for any authed user + 404 + 401
- Pydantic validation on TaskCreate (title/desc/budget/deadline/category)
- SubmissionCreate text validation
- Reviewing already-reviewed submission returns 400
- Reliability counter increments (accepted/completed/rejected/on_time)
- Seed data verification (20 workers, 10 clients, 1 admin, 50 tasks, 30+ submissions)
"""
import os
import uuid
import requests
import pytest
from datetime import datetime, timezone, timedelta, date
from pymongo import MongoClient

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
_db = MongoClient(MONGO_URL)[DB_NAME]


def _mk_session(user_id):
    token = f"test_session_{user_id}_{uuid.uuid4().hex[:8]}"
    _db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return token


@pytest.fixture(scope="module")
def worker_token():
    t = _mk_session("user_demo_worker1")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


@pytest.fixture(scope="module")
def worker3_token():
    t = _mk_session("user_demo_worker3")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


@pytest.fixture(scope="module")
def client_token():
    t = _mk_session("user_demo_client2")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


@pytest.fixture(scope="module")
def admin_token():
    t = _mk_session("user_demo_admin")
    yield t
    _db.user_sessions.delete_one({"session_token": t})


def _auth(t):
    return {"Authorization": f"Bearer {t}"}


# ============== RELIABILITY ON /auth/me ==============
class TestAuthMeReliability:
    def test_me_returns_reliability_fields(self, worker_token):
        r = requests.get(f"{API}/auth/me", headers=_auth(worker_token))
        assert r.status_code == 200
        d = r.json()
        for k in ("trust_level", "reliability_score", "approval_rate", "on_time_rate",
                  "tasks_accepted", "tasks_completed"):
            assert k in d, f"missing field {k} in /auth/me"
        assert d["trust_level"] in ("new", "rising", "trusted", "verified")
        assert isinstance(d["reliability_score"], (int, float))
        assert 0 <= d["reliability_score"] <= 100


# ============== /admin/analytics ==============
class TestAdminAnalytics:
    def test_non_admin_blocked(self, worker_token):
        r = requests.get(f"{API}/admin/analytics", headers=_auth(worker_token))
        assert r.status_code == 403

    def test_unauthenticated_401(self):
        r = requests.get(f"{API}/admin/analytics")
        assert r.status_code == 401

    def test_admin_returns_schema(self, admin_token):
        r = requests.get(f"{API}/admin/analytics", headers=_auth(admin_token))
        assert r.status_code == 200
        d = r.json()
        for k in ("total_users", "workers", "clients", "total_tasks", "open_tasks",
                  "assigned_tasks", "in_review_tasks", "completed_tasks",
                  "completion_rate", "pending_submissions", "top_workers"):
            assert k in d, f"analytics missing {k}"
        assert isinstance(d["top_workers"], list)
        assert len(d["top_workers"]) <= 5
        if d["top_workers"]:
            tw = d["top_workers"][0]
            for k in ("user_id", "name", "reliability_score", "trust_level", "tasks_completed"):
                assert k in tw


# ============== /users/{id}/public ==============
class TestPublicProfile:
    def test_unauthenticated_401(self):
        r = requests.get(f"{API}/users/user_demo_worker1/public")
        assert r.status_code == 401

    def test_returns_reliability_snapshot(self, worker_token):
        r = requests.get(f"{API}/users/user_demo_worker1/public", headers=_auth(worker_token))
        assert r.status_code == 200
        d = r.json()
        for k in ("user_id", "name", "trust_level", "reliability_score",
                  "tasks_completed", "approval_rate", "on_time_rate"):
            assert k in d
        assert d["user_id"] == "user_demo_worker1"

    def test_unknown_user_404(self, worker_token):
        r = requests.get(f"{API}/users/user_does_not_exist_xyz/public", headers=_auth(worker_token))
        assert r.status_code == 404


# ============== VALIDATION ==============
class TestTaskCreateValidation:
    def test_title_too_short(self, client_token):
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "ab", "description": "Valid description here.",
            "category": "Research", "budget": 100.0, "deadline": "2026-08-01"
        })
        assert r.status_code == 422

    def test_budget_zero(self, client_token):
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_valid title", "description": "Valid description here.",
            "category": "Research", "budget": 0, "deadline": "2026-08-01"
        })
        assert r.status_code == 422

    def test_past_deadline(self, client_token):
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_valid title", "description": "Valid description here.",
            "category": "Research", "budget": 100.0, "deadline": "2020-01-01"
        })
        assert r.status_code == 422

    def test_invalid_category(self, client_token):
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_valid title", "description": "Valid description here.",
            "category": "InvalidCat", "budget": 100.0, "deadline": "2026-08-01"
        })
        assert r.status_code == 422

    def test_description_too_short(self, client_token):
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_valid title", "description": "short",
            "category": "Research", "budget": 100.0, "deadline": "2026-08-01"
        })
        assert r.status_code == 422


class TestSubmissionValidation:
    def test_text_too_short(self, client_token, worker3_token):
        # Create a task and assign worker3
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_sub_validate task",
            "description": "Submission text too short validation.",
            "category": "Research", "budget": 100.0, "deadline": "2026-08-05"
        })
        assert r.status_code == 200
        tid = r.json()["task_id"]
        requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(worker3_token))
        sr = requests.post(f"{API}/submissions", headers=_auth(worker3_token), json={
            "task_id": tid, "submission_text": "hi"
        })
        assert sr.status_code == 422


# ============== ALREADY REVIEWED ==============
class TestReReview:
    def test_cannot_re_review(self, client_token, worker3_token):
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_re_review task",
            "description": "Already reviewed re-review test.",
            "category": "Research", "budget": 150.0, "deadline": "2026-08-12"
        })
        assert r.status_code == 200
        tid = r.json()["task_id"]
        requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(worker3_token))
        sr = requests.post(f"{API}/submissions", headers=_auth(worker3_token), json={
            "task_id": tid, "submission_text": "TEST_done please review"
        })
        sub_id = sr.json()["submission_id"]
        # first review
        r1 = requests.post(f"{API}/submissions/{sub_id}/review",
                           headers=_auth(client_token),
                           json={"action": "approve", "feedback": "ok"})
        assert r1.status_code == 200
        # second review
        r2 = requests.post(f"{API}/submissions/{sub_id}/review",
                           headers=_auth(client_token),
                           json={"action": "approve", "feedback": "again"})
        assert r2.status_code == 400
        assert "already reviewed" in r2.json().get("detail", "").lower()


# ============== RELIABILITY FLOW ==============
class TestReliabilityFlow:
    def test_apply_increments_accepted_and_approve_increments_completed_on_time(
        self, client_token, worker3_token
    ):
        # snapshot
        before = _db.users.find_one({"user_id": "user_demo_worker3"})
        before_acc = before.get("tasks_accepted", 0)
        before_done = before.get("tasks_completed", 0)
        before_ontime = before.get("on_time_completions", 0)

        # client creates task with deadline in future
        future_deadline = (date.today() + timedelta(days=20)).isoformat()
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_reliability flow task",
            "description": "Reliability counters increments test.",
            "category": "Research", "budget": 100.0, "deadline": future_deadline
        })
        assert r.status_code == 200, r.text
        tid = r.json()["task_id"]
        # apply
        a = requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(worker3_token))
        assert a.status_code == 200

        after_apply = _db.users.find_one({"user_id": "user_demo_worker3"})
        assert after_apply.get("tasks_accepted", 0) == before_acc + 1

        # submit (now, well before deadline)
        sr = requests.post(f"{API}/submissions", headers=_auth(worker3_token), json={
            "task_id": tid, "submission_text": "TEST_reliability submit done"
        })
        assert sr.status_code == 200
        sub_id = sr.json()["submission_id"]

        # approve
        rev = requests.post(f"{API}/submissions/{sub_id}/review",
                            headers=_auth(client_token),
                            json={"action": "approve", "feedback": "ok"})
        assert rev.status_code == 200

        after_done = _db.users.find_one({"user_id": "user_demo_worker3"})
        assert after_done.get("tasks_completed", 0) == before_done + 1
        # on-time, because submitted now and deadline +20d
        assert after_done.get("on_time_completions", 0) == before_ontime + 1

    def test_reject_increments_rejected(self, client_token, worker3_token):
        before = _db.users.find_one({"user_id": "user_demo_worker3"})
        before_rej = before.get("tasks_rejected", 0)

        future_deadline = (date.today() + timedelta(days=20)).isoformat()
        r = requests.post(f"{API}/tasks", headers=_auth(client_token), json={
            "title": "TEST_reject counter task",
            "description": "Rejected counter increments test.",
            "category": "Research", "budget": 100.0, "deadline": future_deadline
        })
        tid = r.json()["task_id"]
        requests.post(f"{API}/tasks/{tid}/apply", headers=_auth(worker3_token))
        sr = requests.post(f"{API}/submissions", headers=_auth(worker3_token), json={
            "task_id": tid, "submission_text": "TEST_reject flow submit"
        })
        sub_id = sr.json()["submission_id"]
        rv = requests.post(f"{API}/submissions/{sub_id}/review",
                           headers=_auth(client_token),
                           json={"action": "reject", "feedback": "redo"})
        assert rv.status_code == 200

        after = _db.users.find_one({"user_id": "user_demo_worker3"})
        assert after.get("tasks_rejected", 0) == before_rej + 1


# ============== SEED VERIFICATION ==============
class TestSeed:
    def test_seed_idempotent_noop(self):
        r = requests.post(f"{API}/seed")
        assert r.status_code == 200
        d = r.json()
        # either already seeded or just seeded
        assert d.get("ok") is True

    def test_counts_match_spec(self):
        workers = _db.users.count_documents({"user_id": {"$regex": "^user_demo_worker"}, "role": "worker"})
        clients = _db.users.count_documents({"user_id": {"$regex": "^user_demo_client"}, "role": "client"})
        admins = _db.users.count_documents({"user_id": "user_demo_admin"})
        tasks = _db.tasks.count_documents({"task_id": {"$regex": "^task_demo_"}})
        subs = _db.submissions.count_documents({"submission_id": {"$regex": "^sub_demo_"}})
        assert workers == 20, f"expected 20 workers, got {workers}"
        assert clients == 10, f"expected 10 clients, got {clients}"
        assert admins == 1
        assert tasks == 50, f"expected 50 tasks, got {tasks}"
        assert subs >= 30, f"expected >=30 submissions, got {subs}"


# ============== CLEANUP ==============
def teardown_module(module):
    _db.tasks.delete_many({"title": {"$regex": "^TEST_"}})
    _db.submissions.delete_many({"submission_text": {"$regex": "^TEST_"}})
