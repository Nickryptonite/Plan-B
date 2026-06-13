from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Header, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import httpx
import secrets
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta, date

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from emails import send_waitlist_confirmation, send_task_assigned, send_payment_cleared  # noqa: E402
from storage import put_object, get_object, init_storage, MIME_TYPES  # noqa: E402
from seed import build_seed  # noqa: E402


# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="SideQuest API")
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ============== CATEGORIES ==============
ALLOWED_CATEGORIES = {
    "Data Entry", "Research", "Social Media", "Canva Design", "Thumbnail Design",
    "Content Editing", "Translation", "AI Content Cleanup", "Excel Work",
    "Product Listing", "Audio Transcription",
}


# ============== MODELS ==============
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: Optional[str] = None  # 'worker' | 'client' | 'admin'
    skills: List[str] = []
    bio: Optional[str] = None
    earnings: float = 0.0
    spent: float = 0.0
    created_at: str
    is_approved: bool = True
    # Reliability counters (workers only)
    tasks_accepted: int = 0
    tasks_completed: int = 0
    tasks_rejected: int = 0
    on_time_completions: int = 0


class RoleUpdate(BaseModel):
    role: str
    skills: List[str] = []
    bio: Optional[str] = None

    @field_validator("role")
    @classmethod
    def _role(cls, v):
        if v not in ("worker", "client"):
            raise ValueError("role must be worker or client")
        return v

    @field_validator("bio")
    @classmethod
    def _bio(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError("bio too long (max 500 chars)")
        return v


class TaskCreate(BaseModel):
    title: str
    description: str
    category: str
    budget: float
    deadline: str
    required_skills: List[str] = []

    @field_validator("title")
    @classmethod
    def _title(cls, v):
        v = v.strip()
        if not (5 <= len(v) <= 200):
            raise ValueError("title must be 5-200 chars")
        return v

    @field_validator("description")
    @classmethod
    def _desc(cls, v):
        v = v.strip()
        if not (10 <= len(v) <= 2000):
            raise ValueError("description must be 10-2000 chars")
        return v

    @field_validator("category")
    @classmethod
    def _cat(cls, v):
        if v not in ALLOWED_CATEGORIES:
            raise ValueError("invalid category")
        return v

    @field_validator("budget")
    @classmethod
    def _budget(cls, v):
        if v <= 0 or v > 1_000_000:
            raise ValueError("budget must be > 0 and <= 1,000,000")
        return round(float(v), 2)

    @field_validator("deadline")
    @classmethod
    def _deadline(cls, v):
        try:
            d = date.fromisoformat(v)
        except Exception:
            raise ValueError("deadline must be YYYY-MM-DD")
        if d < date.today():
            raise ValueError("deadline cannot be in the past")
        return v


class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    task_id: str
    title: str
    description: str
    category: str
    budget: float
    deadline: str
    required_skills: List[str] = []
    status: str = "open"  # open, assigned, in_review, completed, cancelled
    client_id: str
    client_name: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    applicants: List[str] = []
    created_at: str


class SubmissionCreate(BaseModel):
    task_id: str
    submission_text: str
    submission_url: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None

    @field_validator("submission_text")
    @classmethod
    def _text(cls, v):
        v = v.strip()
        if not (5 <= len(v) <= 5000):
            raise ValueError("submission_text must be 5-5000 chars")
        return v


class Submission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    submission_id: str
    task_id: str
    task_title: str
    worker_id: str
    worker_name: str
    client_id: str
    submission_text: str
    submission_url: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    feedback: Optional[str] = None
    payment_status: str = "unpaid"  # unpaid, paid
    created_at: str


class WaitlistEntry(BaseModel):
    name: str
    email: EmailStr
    role: str  # 'worker' | 'client'
    interest: Optional[str] = None
    ref: Optional[str] = None  # referral code of the inviter


class FeedbackEntry(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    message: str


# ============== AUTH HELPERS ==============
async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> User:
    # Cookie first, then Authorization header
    token = request.cookies.get("session_token")
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    user_doc = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_doc)


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


# ============== RELIABILITY SCORE ==============
def compute_reliability(u: dict) -> dict:
    """Compute reliability fields. Mutates a copy and returns it."""
    accepted = u.get("tasks_accepted", 0) or 0
    completed = u.get("tasks_completed", 0) or 0
    rejected = u.get("tasks_rejected", 0) or 0
    on_time = u.get("on_time_completions", 0) or 0
    total_reviewed = completed + rejected
    approval_rate = round((completed / total_reviewed) * 100, 1) if total_reviewed > 0 else None
    on_time_rate = round((on_time / completed) * 100, 1) if completed > 0 else None

    # Trust level
    if completed == 0:
        trust_level = "new"
    elif completed >= 10 and (approval_rate or 0) >= 90 and (on_time_rate or 0) >= 90:
        trust_level = "verified"
    elif completed >= 4 and (approval_rate or 0) >= 80:
        trust_level = "trusted"
    elif completed >= 1 and (approval_rate or 0) >= 75:
        trust_level = "rising"
    else:
        trust_level = "new"

    # Reliability score 0-100
    if accepted == 0:
        score = 0
    else:
        a = approval_rate or 0
        o = on_time_rate or 0
        # Weight: 60% approval, 30% on-time, 10% volume (capped at 10 tasks)
        volume = min(completed, 10) * 10
        score = round(a * 0.6 + o * 0.3 + volume * 0.1)
    return {
        **u,
        "approval_rate": approval_rate,
        "on_time_rate": on_time_rate,
        "trust_level": trust_level,
        "reliability_score": score,
    }


# ============== AUTH ROUTES ==============
@api_router.post("/auth/session")
async def auth_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # Call Emergent Auth from backend
    async with httpx.AsyncClient() as http:
        r = await http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id},
            timeout=10.0,
        )
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    data = r.json()

    email = data["email"]
    existing = await db.users.find_one({"email": email}, {"_id": 0})

    # Admin allowlist: first user, or specific admin email
    admin_emails = os.environ.get("ADMIN_EMAILS", "").split(",")
    is_admin = email in [e.strip() for e in admin_emails if e.strip()]

    if existing:
        user_id = existing["user_id"]
        update_set = {"name": data.get("name"), "picture": data.get("picture")}
        # If user matches admin allowlist and isn't already admin, promote
        if is_admin and existing.get("role") != "admin":
            update_set["role"] = "admin"
        await db.users.update_one({"user_id": user_id}, {"$set": update_set})
        user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": user_id,
            "email": email,
            "name": data.get("name", email.split("@")[0]),
            "picture": data.get("picture"),
            "role": "admin" if is_admin else None,
            "skills": [],
            "bio": None,
            "earnings": 0.0,
            "spent": 0.0,
            "tasks_accepted": 0,
            "tasks_completed": 0,
            "tasks_rejected": 0,
            "on_time_completions": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_approved": True,
        }
        await db.users.insert_one(new_user)
        user_doc = new_user

    # Create session
    session_token = data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {
            "user_id": user_doc["user_id"],
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 3600,
    )
    return {"user": user_doc, "session_token": session_token}


@api_router.get("/auth/me")
async def auth_me(user: User = Depends(get_current_user)):
    return compute_reliability(user.model_dump())


@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


@api_router.post("/auth/role")
async def set_role(payload: RoleUpdate, user: User = Depends(get_current_user)):
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"role": payload.role, "skills": payload.skills, "bio": payload.bio}},
    )
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return compute_reliability(user_doc)


@api_router.get("/auth/role")
async def get_role(user: User = Depends(get_current_user)):
    return {"role": user.role}


@api_router.get("/users/{target_user_id}/public")
async def public_user_profile(target_user_id: str, user: User = Depends(get_current_user)):
    """Public-ish user profile (reliability + skills) — visible to any authed user."""
    doc = await db.users.find_one({"user_id": target_user_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    enriched = compute_reliability(doc)
    return {
        "user_id": enriched["user_id"],
        "name": enriched["name"],
        "picture": enriched.get("picture"),
        "role": enriched.get("role"),
        "skills": enriched.get("skills", []),
        "bio": enriched.get("bio"),
        "trust_level": enriched["trust_level"],
        "reliability_score": enriched["reliability_score"],
        "tasks_completed": enriched.get("tasks_completed", 0),
        "approval_rate": enriched["approval_rate"],
        "on_time_rate": enriched["on_time_rate"],
    }


# ============== TASKS ==============
@api_router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    mine: Optional[str] = None,  # 'posted' | 'assigned' | 'completed'
    q: Optional[str] = None,
    sort: Optional[str] = "newest",  # newest | budget_desc | budget_asc | deadline
    user: User = Depends(get_current_user),
):
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    if mine == "posted":
        query["client_id"] = user.user_id
    elif mine == "assigned":
        query["assigned_to"] = user.user_id
    elif mine == "completed":
        query["assigned_to"] = user.user_id
        query["status"] = "completed"
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}},
        ]

    sort_map = {
        "newest": ("created_at", -1),
        "budget_desc": ("budget", -1),
        "budget_asc": ("budget", 1),
        "deadline": ("deadline", 1),
    }
    sort_field, sort_dir = sort_map.get(sort or "newest", ("created_at", -1))
    tasks = await db.tasks.find(query, {"_id": 0}).sort(sort_field, sort_dir).to_list(500)
    return tasks


@api_router.get("/tasks/public")
async def list_tasks_public(category: Optional[str] = None, limit: int = 12):
    """Public preview of open tasks for landing page (no auth)."""
    query = {"status": "open"}
    if category:
        query["category"] = category
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return tasks


@api_router.get("/tasks/{task_id}")
async def get_task(task_id: str, user: User = Depends(get_current_user)):
    task = await db.tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@api_router.post("/tasks", response_model=Task)
async def create_task(payload: TaskCreate, user: User = Depends(get_current_user)):
    if user.role not in ("client", "admin"):
        raise HTTPException(status_code=403, detail="Only clients can post tasks")
    task = {
        "task_id": f"task_{uuid.uuid4().hex[:12]}",
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "budget": payload.budget,
        "deadline": payload.deadline,
        "required_skills": payload.required_skills,
        "status": "open",
        "client_id": user.user_id,
        "client_name": user.name,
        "assigned_to": None,
        "assigned_to_name": None,
        "applicants": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.tasks.insert_one(task)
    return Task(**task)


@api_router.post("/tasks/{task_id}/apply")
async def apply_to_task(task_id: str, user: User = Depends(get_current_user)):
    if user.role != "worker":
        raise HTTPException(status_code=403, detail="Only workers can apply")
    task = await db.tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "open":
        raise HTTPException(status_code=400, detail="Task not open for applications")
    # Auto-assign first applicant for MVP simplicity
    if user.user_id in task.get("applicants", []):
        raise HTTPException(status_code=400, detail="Already applied")
    if task.get("assigned_to"):
        # Already assigned, just add to applicants list
        await db.tasks.update_one(
            {"task_id": task_id},
            {"$addToSet": {"applicants": user.user_id}},
        )
        return {"ok": True, "assigned": False}
    else:
        await db.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "assigned_to": user.user_id,
                    "assigned_to_name": user.name,
                    "status": "assigned",
                },
                "$addToSet": {"applicants": user.user_id},
            },
        )
        # Track reliability: tasks_accepted
        await db.users.update_one(
            {"user_id": user.user_id}, {"$inc": {"tasks_accepted": 1}}
        )
        # Fire-and-forget assignment email
        asyncio.create_task(send_task_assigned(user.name, user.email, task["title"], task["deadline"]))
        return {"ok": True, "assigned": True}


# ============== SUBMISSIONS ==============
@api_router.post("/submissions", response_model=Submission)
async def create_submission(payload: SubmissionCreate, user: User = Depends(get_current_user)):
    task = await db.tasks.find_one({"task_id": payload.task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.get("assigned_to") != user.user_id:
        raise HTTPException(status_code=403, detail="Not assigned to you")
    sub = {
        "submission_id": f"sub_{uuid.uuid4().hex[:12]}",
        "task_id": payload.task_id,
        "task_title": task["title"],
        "worker_id": user.user_id,
        "worker_name": user.name,
        "client_id": task["client_id"],
        "submission_text": payload.submission_text,
        "submission_url": payload.submission_url,
        "file_path": payload.file_path,
        "file_name": payload.file_name,
        "status": "pending",
        "feedback": None,
        "payment_status": "unpaid",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.submissions.insert_one(sub)
    await db.tasks.update_one(
        {"task_id": payload.task_id}, {"$set": {"status": "in_review"}}
    )
    return Submission(**sub)


@api_router.get("/submissions")
async def list_submissions(
    mine: Optional[str] = None,  # 'worker' | 'client'
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    query = {}
    if mine == "worker":
        query["worker_id"] = user.user_id
    elif mine == "client":
        query["client_id"] = user.user_id
    if status:
        query["status"] = status
    subs = await db.submissions.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return subs


@api_router.post("/submissions/{submission_id}/review")
async def review_submission(
    submission_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    body = await request.json()
    action = body.get("action")  # 'approve' | 'reject'
    feedback = body.get("feedback")
    sub = await db.submissions.find_one({"submission_id": submission_id}, {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.role != "admin" and sub["client_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Invalid action")
    if sub["status"] != "pending":
        raise HTTPException(status_code=400, detail="Submission already reviewed")

    if action == "approve":
        await db.submissions.update_one(
            {"submission_id": submission_id},
            {"$set": {"status": "approved", "feedback": feedback}},
        )
        # Mark task completed, update worker earnings + client spent, award skill badge
        task = await db.tasks.find_one({"task_id": sub["task_id"]}, {"_id": 0})
        if task:
            await db.tasks.update_one(
                {"task_id": sub["task_id"]}, {"$set": {"status": "completed"}}
            )
            # Check on-time delivery: submitted before deadline
            on_time_inc = 0
            try:
                deadline_d = date.fromisoformat(task["deadline"])
                sub_dt = datetime.fromisoformat(sub["created_at"])
                if sub_dt.date() <= deadline_d:
                    on_time_inc = 1
            except Exception:
                pass
            await db.users.update_one(
                {"user_id": sub["worker_id"]},
                {"$inc": {
                    "earnings": task["budget"],
                    "tasks_completed": 1,
                    "on_time_completions": on_time_inc,
                }},
            )
            await db.users.update_one(
                {"user_id": sub["client_id"]},
                {"$inc": {"spent": task["budget"]}},
            )
            # Award / increment skill badge
            await db.badges.update_one(
                {"user_id": sub["worker_id"], "category": task["category"]},
                {
                    "$inc": {"completed_count": 1, "total_earned": task["budget"]},
                    "$set": {"last_at": datetime.now(timezone.utc).isoformat()},
                    "$setOnInsert": {
                        "badge_id": f"bdg_{uuid.uuid4().hex[:10]}",
                        "user_id": sub["worker_id"],
                        "category": task["category"],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                },
                upsert=True,
            )
            # Email the worker
            worker = await db.users.find_one({"user_id": sub["worker_id"]}, {"_id": 0})
            if worker:
                asyncio.create_task(send_payment_cleared(
                    worker["name"], worker["email"], task["title"], task["budget"]
                ))
    elif action == "reject":
        await db.submissions.update_one(
            {"submission_id": submission_id},
            {"$set": {"status": "rejected", "feedback": feedback}},
        )
        await db.tasks.update_one(
            {"task_id": sub["task_id"]}, {"$set": {"status": "assigned"}}
        )
        await db.users.update_one(
            {"user_id": sub["worker_id"]}, {"$inc": {"tasks_rejected": 1}}
        )
    return {"ok": True}


@api_router.post("/submissions/{submission_id}/mark-paid")
async def mark_paid(submission_id: str, user: User = Depends(require_admin)):
    await db.submissions.update_one(
        {"submission_id": submission_id}, {"$set": {"payment_status": "paid"}}
    )
    return {"ok": True}


# ============== ADMIN ==============
@api_router.get("/admin/users")
async def admin_users(user: User = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return [compute_reliability(u) for u in users]


@api_router.get("/admin/analytics")
async def admin_analytics(user: User = Depends(require_admin)):
    """Focused MVP analytics: counts, completion rate, pending reviews."""
    total_users = await db.users.count_documents({})
    workers = await db.users.count_documents({"role": "worker"})
    clients = await db.users.count_documents({"role": "client"})
    admins = await db.users.count_documents({"role": "admin"})
    total_tasks = await db.tasks.count_documents({})
    open_tasks = await db.tasks.count_documents({"status": "open"})
    assigned_tasks = await db.tasks.count_documents({"status": "assigned"})
    in_review_tasks = await db.tasks.count_documents({"status": "in_review"})
    completed_tasks = await db.tasks.count_documents({"status": "completed"})
    total_subs = await db.submissions.count_documents({})
    pending = await db.submissions.count_documents({"status": "pending"})
    approved = await db.submissions.count_documents({"status": "approved"})
    rejected = await db.submissions.count_documents({"status": "rejected"})
    completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0
    approval_rate = round((approved / (approved + rejected)) * 100, 1) if (approved + rejected) > 0 else 0
    waitlist_count = await db.waitlist.count_documents({})
    paid = await db.submissions.count_documents({"payment_status": "paid"})
    unpaid_approved = await db.submissions.count_documents({"payment_status": "unpaid", "status": "approved"})
    # Top workers by reliability
    all_workers = await db.users.find({"role": "worker"}, {"_id": 0}).to_list(500)
    enriched = [compute_reliability(w) for w in all_workers]
    top_workers = sorted(enriched, key=lambda x: x.get("reliability_score", 0), reverse=True)[:5]
    return {
        "total_users": total_users,
        "workers": workers,
        "clients": clients,
        "admins": admins,
        "total_tasks": total_tasks,
        "open_tasks": open_tasks,
        "assigned_tasks": assigned_tasks,
        "in_review_tasks": in_review_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": completion_rate,
        "total_submissions": total_subs,
        "pending_submissions": pending,
        "approved_submissions": approved,
        "rejected_submissions": rejected,
        "submission_approval_rate": approval_rate,
        "waitlist_count": waitlist_count,
        "paid_submissions": paid,
        "unpaid_approved": unpaid_approved,
        "top_workers": [
            {"user_id": w["user_id"], "name": w["name"], "email": w["email"],
             "reliability_score": w["reliability_score"], "trust_level": w["trust_level"],
             "tasks_completed": w["tasks_completed"], "earnings": w.get("earnings", 0)}
            for w in top_workers
        ],
    }


@api_router.post("/admin/users/{user_id}/approve")
async def admin_approve_user(user_id: str, user: User = Depends(require_admin)):
    await db.users.update_one({"user_id": user_id}, {"$set": {"is_approved": True}})
    return {"ok": True}


@api_router.post("/admin/users/{user_id}/role")
async def admin_set_role(user_id: str, request: Request, user: User = Depends(require_admin)):
    body = await request.json()
    role = body.get("role")
    if role not in ("worker", "client", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    await db.users.update_one({"user_id": user_id}, {"$set": {"role": role}})
    return {"ok": True}


@api_router.get("/admin/stats")
async def admin_stats(user: User = Depends(require_admin)):
    total_users = await db.users.count_documents({})
    workers = await db.users.count_documents({"role": "worker"})
    clients = await db.users.count_documents({"role": "client"})
    total_tasks = await db.tasks.count_documents({})
    open_tasks = await db.tasks.count_documents({"status": "open"})
    completed_tasks = await db.tasks.count_documents({"status": "completed"})
    total_subs = await db.submissions.count_documents({})
    pending_subs = await db.submissions.count_documents({"status": "pending"})

    # Earnings by category
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$category", "total": {"$sum": "$budget"}, "count": {"$sum": 1}}},
    ]
    by_category = await db.tasks.aggregate(pipeline).to_list(50)

    total_paid = sum(t["total"] for t in by_category)
    waitlist_count = await db.waitlist.count_documents({})

    return {
        "total_users": total_users,
        "workers": workers,
        "clients": clients,
        "total_tasks": total_tasks,
        "open_tasks": open_tasks,
        "completed_tasks": completed_tasks,
        "total_submissions": total_subs,
        "pending_submissions": pending_subs,
        "total_paid": total_paid,
        "waitlist_count": waitlist_count,
        "by_category": [{"category": x["_id"], "total": x["total"], "count": x["count"]} for x in by_category],
    }


@api_router.get("/admin/waitlist")
async def admin_waitlist(user: User = Depends(require_admin)):
    items = await db.waitlist.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return items


@api_router.get("/admin/feedback")
async def admin_feedback(user: User = Depends(require_admin)):
    items = await db.feedback.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return items


# ============== FILES / UPLOADS ==============
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    """Upload a file (work submission attachment). Returns storage path + filename."""
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 25MB)")
    ext = (file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "bin")
    content_type = file.content_type or MIME_TYPES.get(ext, "application/octet-stream")
    path = f"sidequest/uploads/{user.user_id}/{uuid.uuid4().hex}.{ext}"
    try:
        result = put_object(path, data, content_type)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")
    await db.files.insert_one({
        "file_id": f"file_{uuid.uuid4().hex[:12]}",
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": content_type,
        "size": result.get("size", len(data)),
        "uploaded_by": user.user_id,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"path": result["path"], "filename": file.filename, "size": result.get("size", len(data))}


@api_router.get("/files/download")
async def download_file(path: str, user: User = Depends(get_current_user)):
    """Stream a file by storage path. Worker who uploaded or related client/admin can access."""
    record = await db.files.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    # Authorization: uploader, admin, or a related submission's client/worker
    allowed = user.role == "admin" or record["uploaded_by"] == user.user_id
    if not allowed:
        sub = await db.submissions.find_one({"file_path": path}, {"_id": 0})
        if sub and (sub["client_id"] == user.user_id or sub["worker_id"] == user.user_id):
            allowed = True
    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        data, content_type = get_object(path)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail="Download failed")
    return Response(content=data, media_type=record.get("content_type", content_type))


# ============== BADGES ==============
@api_router.get("/badges")
async def list_badges(user: User = Depends(get_current_user)):
    badges = await db.badges.find({"user_id": user.user_id}, {"_id": 0}).to_list(100)
    # Compute level from completed_count: 1 (1-2), 2 (3-5), 3 (6-10), 4 (11-24), 5 (25+)
    for b in badges:
        c = b.get("completed_count", 0)
        b["level"] = 5 if c >= 25 else 4 if c >= 11 else 3 if c >= 6 else 2 if c >= 3 else 1
    return badges


# ============== WAITLIST / FEEDBACK (PUBLIC) ==============
@api_router.post("/waitlist")
async def join_waitlist(payload: WaitlistEntry):
    # Generate unique referral code for this user
    ref_code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].upper()
    while await db.waitlist.find_one({"referral_code": ref_code}):
        ref_code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].upper()

    # Resolve inviter
    referred_by = None
    if payload.ref:
        inviter = await db.waitlist.find_one({"referral_code": payload.ref.upper()})
        if inviter:
            referred_by = inviter["waitlist_id"]
            await db.waitlist.update_one(
                {"waitlist_id": inviter["waitlist_id"]},
                {"$inc": {"referrals_count": 1}},
            )

    exists = await db.waitlist.find_one({"email": payload.email}, {"_id": 0})
    if exists:
        base = os.environ.get("APP_BASE_URL", "")
        return {
            "ok": True,
            "already": True,
            "referral_code": exists.get("referral_code"),
            "referral_link": f"{base}/?ref={exists.get('referral_code')}" if exists.get("referral_code") else None,
        }

    entry = {
        "waitlist_id": f"wl_{uuid.uuid4().hex[:12]}",
        "name": payload.name,
        "email": payload.email,
        "role": payload.role,
        "interest": payload.interest,
        "referral_code": ref_code,
        "referred_by": referred_by,
        "referrals_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.waitlist.insert_one(entry)

    base = os.environ.get("APP_BASE_URL", "")
    referral_link = f"{base}/?ref={ref_code}" if base else f"?ref={ref_code}"
    # Fire-and-forget welcome email
    asyncio.create_task(send_waitlist_confirmation(payload.name, payload.email, referral_link))

    return {"ok": True, "referral_code": ref_code, "referral_link": referral_link}


@api_router.get("/waitlist/leaderboard")
async def waitlist_leaderboard(limit: int = 10):
    items = await db.waitlist.find(
        {"referrals_count": {"$gt": 0}}, {"_id": 0, "email": 0}
    ).sort("referrals_count", -1).limit(limit).to_list(limit)
    return items


@api_router.post("/feedback")
async def submit_feedback(payload: FeedbackEntry):
    entry = {
        "feedback_id": f"fb_{uuid.uuid4().hex[:12]}",
        "name": payload.name,
        "email": payload.email,
        "message": payload.message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.feedback.insert_one(entry)
    return {"ok": True}


# ============== SEED ==============
async def _seed_internal(force: bool = False):
    """Internal seed (no auth). Returns dict result."""
    existing = await db.tasks.count_documents({})
    if existing > 0 and not force:
        return {"ok": True, "already_seeded": True}

    if force:
        await db.users.delete_many({"user_id": {"$regex": "^user_demo_"}})
        await db.tasks.delete_many({"task_id": {"$regex": "^task_demo_"}})
        await db.submissions.delete_many({"submission_id": {"$regex": "^sub_demo_"}})
        await db.badges.delete_many({"badge_id": {"$regex": "^bdg_demo_"}})
        await db.waitlist.delete_many({"waitlist_id": {"$regex": "^wl_demo_"}})

    users, tasks, submissions, badges, waitlist = build_seed()
    if users:
        await db.users.insert_many(users)
    if tasks:
        await db.tasks.insert_many(tasks)
    if submissions:
        await db.submissions.insert_many(submissions)
    if badges:
        await db.badges.insert_many(badges)
    if waitlist:
        await db.waitlist.insert_many(waitlist)

    return {
        "ok": True, "seeded": True,
        "counts": {
            "users": len(users), "tasks": len(tasks),
            "submissions": len(submissions), "badges": len(badges),
            "waitlist": len(waitlist),
        },
    }


@api_router.post("/seed")
async def seed_data(request: Request, force: bool = False, authorization: Optional[str] = Header(None)):
    """Seed demo data. Idempotent unless ?force=true (admin only, clears + reseeds)."""
    if force:
        user = await get_current_user(request, authorization)
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
    return await _seed_internal(force=force)


# ============== HEALTH ==============
@api_router.get("/")
async def root():
    return {"message": "SideQuest API", "version": "1.0"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # Init object storage (no-op if no key — logs warning)
    try:
        init_storage()
    except Exception as e:
        logger.warning(f"Storage init failed (uploads will be disabled): {e}")
    # Auto-seed on first boot for MVP demo experience
    try:
        existing = await db.tasks.count_documents({})
        if existing == 0:
            await _seed_internal()
            logger.info("Seeded demo data on startup")
    except Exception as e:
        logger.warning(f"Seed on startup failed: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
