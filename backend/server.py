from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="SideQuest API")
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ============== MODELS ==============
class User(BaseModel):
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


class RoleUpdate(BaseModel):
    role: str
    skills: List[str] = []
    bio: Optional[str] = None


class TaskCreate(BaseModel):
    title: str
    description: str
    category: str
    budget: float
    deadline: str
    required_skills: List[str] = []


class Task(BaseModel):
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


class Submission(BaseModel):
    submission_id: str
    task_id: str
    task_title: str
    worker_id: str
    worker_name: str
    client_id: str
    submission_text: str
    submission_url: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    feedback: Optional[str] = None
    payment_status: str = "unpaid"  # unpaid, paid
    created_at: str


class WaitlistEntry(BaseModel):
    name: str
    email: EmailStr
    role: str  # 'worker' | 'client'
    interest: Optional[str] = None


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
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": data.get("name"), "picture": data.get("picture")}},
        )
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


@api_router.get("/auth/me", response_model=User)
async def auth_me(user: User = Depends(get_current_user)):
    return user


@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


@api_router.post("/auth/role", response_model=User)
async def set_role(payload: RoleUpdate, user: User = Depends(get_current_user)):
    if payload.role not in ("worker", "client"):
        raise HTTPException(status_code=400, detail="Invalid role")
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"role": payload.role, "skills": payload.skills, "bio": payload.bio}},
    )
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return User(**user_doc)


# ============== TASKS ==============
@api_router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    mine: Optional[str] = None,  # 'posted' | 'assigned' | 'completed'
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
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
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
    return {"ok": True}


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
    if action == "approve":
        await db.submissions.update_one(
            {"submission_id": submission_id},
            {"$set": {"status": "approved", "feedback": feedback}},
        )
        # Mark task completed, update worker earnings + client spent
        task = await db.tasks.find_one({"task_id": sub["task_id"]}, {"_id": 0})
        if task:
            await db.tasks.update_one(
                {"task_id": sub["task_id"]}, {"$set": {"status": "completed"}}
            )
            await db.users.update_one(
                {"user_id": sub["worker_id"]},
                {"$inc": {"earnings": task["budget"]}},
            )
            await db.users.update_one(
                {"user_id": sub["client_id"]},
                {"$inc": {"spent": task["budget"]}},
            )
    elif action == "reject":
        await db.submissions.update_one(
            {"submission_id": submission_id},
            {"$set": {"status": "rejected", "feedback": feedback}},
        )
        await db.tasks.update_one(
            {"task_id": sub["task_id"]}, {"$set": {"status": "assigned"}}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
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
    return users


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


# ============== WAITLIST / FEEDBACK (PUBLIC) ==============
@api_router.post("/waitlist")
async def join_waitlist(payload: WaitlistEntry):
    entry = {
        "waitlist_id": f"wl_{uuid.uuid4().hex[:12]}",
        "name": payload.name,
        "email": payload.email,
        "role": payload.role,
        "interest": payload.interest,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    exists = await db.waitlist.find_one({"email": payload.email})
    if exists:
        return {"ok": True, "already": True}
    await db.waitlist.insert_one(entry)
    return {"ok": True}


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
@api_router.post("/seed")
async def seed_data():
    """Seed demo data — idempotent. Returns if already seeded."""
    existing = await db.tasks.count_documents({})
    if existing > 0:
        return {"ok": True, "already_seeded": True}

    now = datetime.now(timezone.utc)

    # Demo users
    demo_users = [
        {"user_id": "user_demo_admin", "email": "admin@sidequest.dev", "name": "SideQuest Admin",
         "picture": None, "role": "admin", "skills": [], "earnings": 0.0, "spent": 0.0,
         "bio": None, "is_approved": True, "created_at": now.isoformat()},
        {"user_id": "user_demo_client1", "email": "rohit@brewlabs.in", "name": "Rohit Mehra",
         "picture": "https://api.dicebear.com/7.x/avataaars/svg?seed=Rohit", "role": "client",
         "skills": [], "earnings": 0.0, "spent": 4500.0, "bio": "Founder, BrewLabs",
         "is_approved": True, "created_at": now.isoformat()},
        {"user_id": "user_demo_client2", "email": "anita@pixelfarm.studio", "name": "Anita Rao",
         "picture": "https://api.dicebear.com/7.x/avataaars/svg?seed=Anita", "role": "client",
         "skills": [], "earnings": 0.0, "spent": 2800.0, "bio": "Creative Director, PixelFarm",
         "is_approved": True, "created_at": now.isoformat()},
        {"user_id": "user_demo_worker1", "email": "priya@du.ac.in", "name": "Priya Sharma",
         "picture": "https://api.dicebear.com/7.x/avataaars/svg?seed=Priya", "role": "worker",
         "skills": ["Canva Design", "Social Media", "Content Editing"], "earnings": 3200.0,
         "spent": 0.0, "bio": "Final year DU. UPSC aspirant.", "is_approved": True,
         "created_at": now.isoformat()},
        {"user_id": "user_demo_worker2", "email": "arjun@iitg.ac.in", "name": "Arjun Patel",
         "picture": "https://api.dicebear.com/7.x/avataaars/svg?seed=Arjun", "role": "worker",
         "skills": ["Excel Work", "Data Entry", "Research"], "earnings": 1800.0, "spent": 0.0,
         "bio": "IIT Guwahati, B.Tech CSE.", "is_approved": True, "created_at": now.isoformat()},
    ]
    await db.users.insert_many(demo_users)

    # Demo tasks
    demo_tasks = [
        {"task_id": "task_demo_1", "title": "Design 5 Instagram carousel posts for product launch",
         "description": "We're launching a new productivity app and need 5 carousel posts (10 slides each) for Instagram. Brand colors and copy will be provided.",
         "category": "Canva Design", "budget": 1500.0, "deadline": "2026-03-15",
         "required_skills": ["Canva Design", "Social Media"], "status": "open",
         "client_id": "user_demo_client1", "client_name": "Rohit Mehra",
         "assigned_to": None, "assigned_to_name": None, "applicants": [],
         "created_at": now.isoformat()},
        {"task_id": "task_demo_2", "title": "Transcribe 3 podcast episodes (45 min each)",
         "description": "Need accurate English transcriptions with timestamps every 30 seconds. Final delivery in .docx format.",
         "category": "Audio Transcription", "budget": 1200.0, "deadline": "2026-03-10",
         "required_skills": ["Audio Transcription"], "status": "open",
         "client_id": "user_demo_client2", "client_name": "Anita Rao",
         "assigned_to": None, "assigned_to_name": None, "applicants": [],
         "created_at": now.isoformat()},
        {"task_id": "task_demo_3", "title": "Research top 50 D2C skincare brands in India",
         "description": "Compile a spreadsheet with brand name, founder, year, funding, products, website, and Instagram handle.",
         "category": "Research", "budget": 2000.0, "deadline": "2026-03-20",
         "required_skills": ["Research", "Excel Work"], "status": "assigned",
         "client_id": "user_demo_client1", "client_name": "Rohit Mehra",
         "assigned_to": "user_demo_worker2", "assigned_to_name": "Arjun Patel",
         "applicants": ["user_demo_worker2"], "created_at": now.isoformat()},
        {"task_id": "task_demo_4", "title": "Clean up AI-generated blog draft (2000 words)",
         "description": "Make it sound human, remove robotic phrases, add personality. Topic: remote work for students.",
         "category": "AI Content Cleanup", "budget": 800.0, "deadline": "2026-03-08",
         "required_skills": ["Content Editing", "AI Content Cleanup"], "status": "completed",
         "client_id": "user_demo_client2", "client_name": "Anita Rao",
         "assigned_to": "user_demo_worker1", "assigned_to_name": "Priya Sharma",
         "applicants": ["user_demo_worker1"], "created_at": now.isoformat()},
        {"task_id": "task_demo_5", "title": "Translate product description (English → Hindi)",
         "description": "Translate 30 product descriptions for an e-commerce store. Tone: friendly and casual.",
         "category": "Translation", "budget": 1000.0, "deadline": "2026-03-12",
         "required_skills": ["Translation"], "status": "open",
         "client_id": "user_demo_client1", "client_name": "Rohit Mehra",
         "assigned_to": None, "assigned_to_name": None, "applicants": [],
         "created_at": now.isoformat()},
        {"task_id": "task_demo_6", "title": "Create 10 YouTube thumbnails for tech channel",
         "description": "Click-worthy thumbnails for tech review videos. Reference channels will be shared.",
         "category": "Thumbnail Design", "budget": 1500.0, "deadline": "2026-03-18",
         "required_skills": ["Thumbnail Design", "Canva Design"], "status": "open",
         "client_id": "user_demo_client2", "client_name": "Anita Rao",
         "assigned_to": None, "assigned_to_name": None, "applicants": [],
         "created_at": now.isoformat()},
        {"task_id": "task_demo_7", "title": "Data entry: 500 product listings on Shopify",
         "description": "Upload product images, titles, descriptions, prices, and tags. Data provided in CSV.",
         "category": "Product Listing", "budget": 2500.0, "deadline": "2026-03-25",
         "required_skills": ["Data Entry", "Product Listing"], "status": "open",
         "client_id": "user_demo_client1", "client_name": "Rohit Mehra",
         "assigned_to": None, "assigned_to_name": None, "applicants": [],
         "created_at": now.isoformat()},
        {"task_id": "task_demo_8", "title": "Build a financial model in Excel for SaaS startup",
         "description": "3-year revenue projection, MRR/ARR, churn, CAC, LTV. Template will be provided.",
         "category": "Excel Work", "budget": 3000.0, "deadline": "2026-03-30",
         "required_skills": ["Excel Work"], "status": "open",
         "client_id": "user_demo_client2", "client_name": "Anita Rao",
         "assigned_to": None, "assigned_to_name": None, "applicants": [],
         "created_at": now.isoformat()},
    ]
    await db.tasks.insert_many(demo_tasks)

    # Demo submission
    demo_subs = [
        {"submission_id": "sub_demo_1", "task_id": "task_demo_4",
         "task_title": "Clean up AI-generated blog draft (2000 words)",
         "worker_id": "user_demo_worker1", "worker_name": "Priya Sharma",
         "client_id": "user_demo_client2", "submission_text": "Cleaned up the draft, removed all robotic phrases, added 3 personal anecdotes from student life. Word count: 2150.",
         "submission_url": "https://docs.google.com/document/d/demo", "status": "approved",
         "feedback": "Excellent work! Very natural voice.", "payment_status": "paid",
         "created_at": now.isoformat()},
    ]
    await db.submissions.insert_many(demo_subs)

    # Demo waitlist
    await db.waitlist.insert_many([
        {"waitlist_id": "wl_1", "name": "Karan", "email": "karan@srm.edu.in", "role": "worker",
         "interest": "Canva, social media", "created_at": now.isoformat()},
        {"waitlist_id": "wl_2", "name": "Nisha", "email": "nisha@manipal.edu", "role": "worker",
         "interest": "Translation, content", "created_at": now.isoformat()},
        {"waitlist_id": "wl_3", "name": "Ashish (Founder, Crisply)", "email": "a@crisply.in",
         "role": "client", "interest": "Need help with social media posts", "created_at": now.isoformat()},
    ])

    return {"ok": True, "seeded": True}


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
    # Auto-seed on first boot for MVP demo experience
    try:
        existing = await db.tasks.count_documents({})
        if existing == 0:
            await seed_data()
            logger.info("Seeded demo data on startup")
    except Exception as e:
        logger.warning(f"Seed on startup failed: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
