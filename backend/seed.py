"""Realistic seed data for SideQuest MVP validation."""
import random
import uuid
from datetime import datetime, timezone, timedelta


CATEGORIES = [
    "Data Entry", "Research", "Social Media", "Canva Design", "Thumbnail Design",
    "Content Editing", "Translation", "AI Content Cleanup", "Excel Work",
    "Product Listing", "Audio Transcription",
]

WORKER_PROFILES = [
    # name, college email, skills, bio
    ("Priya Sharma", "priya@du.ac.in", ["Canva Design", "Social Media", "Content Editing"], "Final year DU. UPSC aspirant."),
    ("Arjun Patel", "arjun@iitg.ac.in", ["Excel Work", "Data Entry", "Research"], "IIT Guwahati, B.Tech CSE."),
    ("Sneha Reddy", "sneha@iiit-h.ac.in", ["Translation", "Content Editing"], "IIIT Hyderabad, fluent in Telugu, Hindi, English."),
    ("Vikram Singh", "vikram@nit-trichy.ac.in", ["Thumbnail Design", "Canva Design"], "NIT Trichy. Designer + side gigs since 2024."),
    ("Aanya Kapoor", "aanya@lsr.du.ac.in", ["AI Content Cleanup", "Content Editing", "Translation"], "LSR English Hons. Loves crisp copy."),
    ("Rahul Joshi", "rahul@bits-pilani.ac.in", ["Excel Work", "Research"], "BITS Pilani, finance club lead."),
    ("Meera Nair", "meera@cusat.ac.in", ["Audio Transcription", "Translation"], "CUSAT MA Linguistics."),
    ("Karthik Iyer", "karthik@anna.edu.in", ["Product Listing", "Data Entry"], "Anna Univ, e-commerce hustle."),
    ("Ritika Bansal", "ritika@nift.ac.in", ["Canva Design", "Thumbnail Design", "Social Media"], "NIFT Delhi, design student."),
    ("Aditya Verma", "aditya@iitb.ac.in", ["Research", "AI Content Cleanup"], "IIT Bombay, Mech Engg, GATE aspirant."),
    ("Pooja Menon", "pooja@christ.edu", ["Social Media", "Canva Design"], "Christ Univ, marketing minor."),
    ("Saif Khan", "saif@jamia.ac.in", ["Translation", "Content Editing"], "Jamia, Urdu/Hindi/English."),
    ("Anjali Das", "anjali@jadavpuruniversity.in", ["Excel Work", "Data Entry", "Research"], "JU Kolkata, Stats Hons."),
    ("Devansh Gupta", "devansh@vit.ac.in", ["Thumbnail Design", "Canva Design"], "VIT Vellore, YouTuber on the side."),
    ("Nisha Pillai", "nisha@manipal.edu", ["AI Content Cleanup", "Content Editing"], "Manipal Mass Comm."),
    ("Karan Ahuja", "karan@srm.edu.in", ["Social Media", "Canva Design", "Thumbnail Design"], "SRM, social media nerd."),
    ("Tanvi Joshi", "tanvi@symbiosis.ac.in", ["Product Listing", "Excel Work"], "Symbiosis Pune, BBA."),
    ("Harsh Mehta", "harsh@nitk.ac.in", ["Audio Transcription", "Translation"], "NIT Karnataka, fluent in 4 languages."),
    ("Ishita Roy", "ishita@presidency.edu.in", ["Research", "AI Content Cleanup"], "Presidency Kolkata, English major."),
    ("Mohit Yadav", "mohit@iitd.ac.in", ["Excel Work", "Research", "Data Entry"], "IIT Delhi, B.Tech ECE."),
]

CLIENT_PROFILES = [
    ("Rohit Mehra", "rohit@brewlabs.in", "Founder, BrewLabs"),
    ("Anita Rao", "anita@pixelfarm.studio", "Creative Director, PixelFarm"),
    ("Shubham Joshi", "shubham@crisply.app", "PM, Crisply"),
    ("Divya Iyer", "divya@hippiesnacks.in", "Co-founder, Hippie Snacks"),
    ("Karan Bhatia", "karan@nuvolabs.io", "CTO, Nuvo Labs"),
    ("Megha Kapoor", "megha@notableagency.in", "Founder, Notable Agency"),
    ("Ankit Verma", "ankit@stackr.tech", "Engineering Lead, Stackr"),
    ("Sara Khan", "sara@bloomwear.in", "Marketing Manager, BloomWear"),
    ("Rajat Sinha", "rajat@finmate.in", "Operations, FinMate"),
    ("Neha Saxena", "neha@learnflow.school", "Content Head, LearnFlow"),
]

TASK_TEMPLATES = {
    "Data Entry": [
        ("Move 500 leads from Google Form to HubSpot", "We have 500 lead form responses that need to be cleaned, deduplicated, and added to HubSpot with proper tags."),
        ("Clean and dedupe customer email list (3k rows)", "Excel/CSV of 3k contacts. Remove duplicates, fix capitalization, validate email format."),
        ("Tag 1000 product images by attribute", "Spreadsheet mapping image filename → category/color/size."),
    ],
    "Research": [
        ("Research top 50 D2C skincare brands in India", "Compile a spreadsheet with brand name, founder, year, funding, products, website, Instagram handle."),
        ("Find 30 micro-influencers in food space (10-50k followers)", "Need handle, follower count, engagement %, contact email/DM."),
        ("Compile competitor pricing pages (8 SaaS tools)", "Screenshot + summary of pricing tiers, free trial, key feature gaps."),
    ],
    "Social Media": [
        ("Schedule 30 LinkedIn posts in Buffer", "Copy provided. Need them queued for the next 4 weeks with proper hashtags."),
        ("Find & engage on 100 relevant tweets", "Reply with helpful comments on tweets in fintech niche, daily limit."),
        ("Write 10 Instagram captions for fitness brand", "Tone: encouraging, slightly cheeky. ~100 words each."),
    ],
    "Canva Design": [
        ("Design 5 Instagram carousel posts for product launch", "We're launching a new productivity app and need 5 carousel posts (10 slides each) for Instagram. Brand colors and copy will be provided."),
        ("Make 20 quote cards for motivation page", "Square format, brand template provided."),
        ("Design pitch deck (15 slides) for seed round", "Outline provided. Need clean, investor-ready visuals."),
    ],
    "Thumbnail Design": [
        ("Create 10 YouTube thumbnails for tech channel", "Click-worthy thumbnails for tech review videos. Reference channels will be shared."),
        ("4 thumbnails for educational shorts", "Quick turnaround. Each thumbnail with face + bold text."),
    ],
    "Content Editing": [
        ("Edit 5 blog posts (1500w each) for clarity", "Light copy edit — grammar, flow, simplify jargon."),
        ("Edit 8 LinkedIn newsletter editions", "Drafts are good but need tightening + better hooks."),
    ],
    "Translation": [
        ("Translate product descriptions (Eng → Hindi)", "30 products. Friendly, casual tone."),
        ("Translate user testimonials (Eng → Tamil)", "12 short paragraphs."),
        ("Translate 10 FAQ entries (Eng → Bengali)", "App support FAQ."),
    ],
    "AI Content Cleanup": [
        ("Humanize 5 AI-generated essays for content marketing", "Make them sound natural, remove robotic phrasing, add personality."),
        ("Edit 3 chatbot scripts to feel less canned", "Make responses warmer, contextual."),
    ],
    "Excel Work": [
        ("Build financial model for SaaS startup (3-yr)", "Revenue, MRR/ARR, churn, CAC, LTV. Template provided."),
        ("Excel dashboard from sales CSV (formulas + charts)", "Need pivot tables, conditional formatting, charts."),
        ("Compile expense report from 4 sources into one sheet", "Bank statements, Razorpay, Stripe. Categorize and total."),
    ],
    "Product Listing": [
        ("Upload 200 SKUs to Shopify with images & specs", "Data provided in CSV + image folder. Need clean titles, tags, descriptions."),
        ("Amazon listing: 50 products with A+ content basics", "Title, bullets, description. Style guide provided."),
    ],
    "Audio Transcription": [
        ("Transcribe 3 podcast episodes (45 min each)", "Accurate English transcriptions with timestamps every 30s. Delivery in .docx."),
        ("Transcribe customer interview calls (90 min total)", "Verbatim, with speaker labels."),
    ],
}


def _random_skill_subset(category):
    base = [category]
    extra = random.sample([c for c in CATEGORIES if c != category], k=random.randint(0, 2))
    return base + extra


def build_seed():
    """Generate the full seed dataset. Returns dicts ready to insert."""
    now = datetime.now(timezone.utc)
    random.seed(42)  # deterministic

    # ===== USERS =====
    users = []

    # Admin
    users.append({
        "user_id": "user_demo_admin", "email": "admin@sidequest.dev",
        "name": "SideQuest Admin", "picture": None, "role": "admin",
        "skills": [], "earnings": 0.0, "spent": 0.0, "bio": "Platform admin.",
        "tasks_accepted": 0, "tasks_completed": 0, "tasks_rejected": 0, "on_time_completions": 0,
        "is_approved": True, "created_at": now.isoformat(),
    })

    # Clients
    for i, (name, email, bio) in enumerate(CLIENT_PROFILES, start=1):
        users.append({
            "user_id": f"user_demo_client{i}",
            "email": email, "name": name,
            "picture": f"https://api.dicebear.com/7.x/avataaars/svg?seed={name.split()[0]}",
            "role": "client", "skills": [], "earnings": 0.0, "spent": 0.0, "bio": bio,
            "tasks_accepted": 0, "tasks_completed": 0, "tasks_rejected": 0, "on_time_completions": 0,
            "is_approved": True,
            "created_at": (now - timedelta(days=random.randint(5, 60))).isoformat(),
        })

    # Workers
    for i, (name, email, skills, bio) in enumerate(WORKER_PROFILES, start=1):
        users.append({
            "user_id": f"user_demo_worker{i}",
            "email": email, "name": name,
            "picture": f"https://api.dicebear.com/7.x/avataaars/svg?seed={name.split()[0]}",
            "role": "worker", "skills": skills, "earnings": 0.0, "spent": 0.0, "bio": bio,
            "tasks_accepted": 0, "tasks_completed": 0, "tasks_rejected": 0, "on_time_completions": 0,
            "is_approved": True,
            "created_at": (now - timedelta(days=random.randint(2, 90))).isoformat(),
        })

    # ===== TASKS (50 total) =====
    tasks = []
    client_ids = [f"user_demo_client{i+1}" for i in range(len(CLIENT_PROFILES))]
    client_names = {f"user_demo_client{i+1}": p[0] for i, p in enumerate(CLIENT_PROFILES)}
    worker_ids = [f"user_demo_worker{i+1}" for i in range(len(WORKER_PROFILES))]
    worker_names = {f"user_demo_worker{i+1}": p[0] for i, p in enumerate(WORKER_PROFILES)}

    task_counter = 1
    for category, templates in TASK_TEMPLATES.items():
        # 4-5 tasks per category
        for _ in range(random.choice([4, 5])):
            if task_counter > 50:
                break
            title, desc = random.choice(templates)
            client_id = random.choice(client_ids)
            # Status distribution: 30% open, 20% assigned, 10% in_review, 35% completed, 5% cancelled
            r = random.random()
            if r < 0.30:
                status = "open"
            elif r < 0.50:
                status = "assigned"
            elif r < 0.60:
                status = "in_review"
            elif r < 0.95:
                status = "completed"
            else:
                status = "cancelled"

            assigned_to = None
            assigned_to_name = None
            applicants = []
            if status in ("assigned", "in_review", "completed"):
                # Pick a worker who has this skill
                eligible = [w for w in WORKER_PROFILES if category in w[2]] or WORKER_PROFILES
                picked = random.choice(eligible)
                # Find index
                idx = WORKER_PROFILES.index(picked) + 1
                assigned_to = f"user_demo_worker{idx}"
                assigned_to_name = picked[0]
                applicants = [assigned_to]
                # Add 0-3 other applicants
                others = random.sample([w for w in worker_ids if w != assigned_to], k=random.randint(0, 3))
                applicants.extend(others)

            deadline_days = random.randint(7, 45)
            created_days_ago = random.randint(1, 30)
            tasks.append({
                "task_id": f"task_demo_{task_counter}",
                "title": title,
                "description": desc,
                "category": category,
                "budget": float(random.choice([500, 800, 1000, 1200, 1500, 2000, 2500, 3000])),
                "deadline": (now + timedelta(days=deadline_days)).date().isoformat(),
                "required_skills": _random_skill_subset(category),
                "status": status,
                "client_id": client_id,
                "client_name": client_names[client_id],
                "assigned_to": assigned_to,
                "assigned_to_name": assigned_to_name,
                "applicants": applicants,
                "created_at": (now - timedelta(days=created_days_ago)).isoformat(),
            })
            task_counter += 1
        if task_counter > 50:
            break

    # If we have fewer than 50, top up with random opens
    while len(tasks) < 50:
        category = random.choice(CATEGORIES)
        title, desc = random.choice(TASK_TEMPLATES[category])
        client_id = random.choice(client_ids)
        tasks.append({
            "task_id": f"task_demo_{len(tasks)+1}",
            "title": title, "description": desc, "category": category,
            "budget": float(random.choice([500, 800, 1000, 1200, 1500, 2000])),
            "deadline": (now + timedelta(days=random.randint(7, 30))).date().isoformat(),
            "required_skills": [category], "status": "open",
            "client_id": client_id, "client_name": client_names[client_id],
            "assigned_to": None, "assigned_to_name": None, "applicants": [],
            "created_at": (now - timedelta(days=random.randint(1, 15))).isoformat(),
        })

    # ===== SUBMISSIONS (30 total) =====
    # All in_review + completed tasks should have a submission; rejected adds extras
    submissions = []
    badges_inc = {}  # (worker_id, category) -> {count, earned}
    sub_counter = 1

    for t in tasks:
        if t["status"] in ("in_review", "completed") and len(submissions) < 30:
            # Submitted somewhere around 1-7 days before now
            sub_date = datetime.fromisoformat(t["created_at"]) + timedelta(days=random.randint(1, 5))
            on_time = sub_date.date() <= datetime.fromisoformat(t["deadline"]).date() if isinstance(t["deadline"], str) else True
            if t["status"] == "completed":
                status = "approved"
                feedback = random.choice([
                    "Great work, very polished.",
                    "Exactly what we needed. Thanks!",
                    "Fast turnaround and clean output.",
                    "Loved the attention to detail.",
                    None,
                ])
                payment = random.choice(["paid", "paid", "unpaid"])
            else:
                status = "pending"
                feedback = None
                payment = "unpaid"

            submissions.append({
                "submission_id": f"sub_demo_{sub_counter}",
                "task_id": t["task_id"], "task_title": t["title"],
                "worker_id": t["assigned_to"], "worker_name": t["assigned_to_name"],
                "client_id": t["client_id"],
                "submission_text": random.choice([
                    "Completed the work as discussed. Files attached.",
                    "Done. Detailed notes in the linked doc.",
                    "Finished. Let me know if anything needs tweaks.",
                    "Submitted v1. Happy to iterate.",
                ]),
                "submission_url": f"https://docs.google.com/document/d/demo_{sub_counter}",
                "file_path": None, "file_name": None,
                "status": status, "feedback": feedback, "payment_status": payment,
                "created_at": sub_date.isoformat(),
            })
            sub_counter += 1

            if status == "approved":
                key = (t["assigned_to"], t["category"])
                if key not in badges_inc:
                    badges_inc[key] = {"count": 0, "earned": 0.0}
                badges_inc[key]["count"] += 1
                badges_inc[key]["earned"] += t["budget"]

    # Add a few rejected submissions for realism
    rejected_count = 0
    for t in tasks:
        if rejected_count >= 5 or len(submissions) >= 35:
            break
        if t["status"] == "assigned" and t["assigned_to"]:
            submissions.append({
                "submission_id": f"sub_demo_{sub_counter}",
                "task_id": t["task_id"], "task_title": t["title"],
                "worker_id": t["assigned_to"], "worker_name": t["assigned_to_name"],
                "client_id": t["client_id"],
                "submission_text": "First attempt — let me know what needs to change.",
                "submission_url": None, "file_path": None, "file_name": None,
                "status": "rejected",
                "feedback": "Needs more polish. Please revise based on feedback in the doc.",
                "payment_status": "unpaid",
                "created_at": (datetime.fromisoformat(t["created_at"]) + timedelta(days=2)).isoformat(),
            })
            sub_counter += 1
            rejected_count += 1

    # ===== Update worker reliability counters based on submissions =====
    worker_stats = {wid: {"accepted": 0, "completed": 0, "rejected": 0, "on_time": 0, "earnings": 0.0}
                    for wid in worker_ids}
    for t in tasks:
        if t["assigned_to"] and t["status"] in ("assigned", "in_review", "completed"):
            worker_stats[t["assigned_to"]]["accepted"] += 1
    for s in submissions:
        if s["status"] == "approved":
            worker_stats[s["worker_id"]]["completed"] += 1
            # Look up budget
            task = next((x for x in tasks if x["task_id"] == s["task_id"]), None)
            if task:
                worker_stats[s["worker_id"]]["earnings"] += task["budget"]
                # On-time check
                try:
                    sub_d = datetime.fromisoformat(s["created_at"]).date()
                    deadline_d = datetime.fromisoformat(task["deadline"] + "T00:00:00").date() if "T" not in task["deadline"] else datetime.fromisoformat(task["deadline"]).date()
                    if sub_d <= deadline_d:
                        worker_stats[s["worker_id"]]["on_time"] += 1
                except Exception:
                    pass
        elif s["status"] == "rejected":
            worker_stats[s["worker_id"]]["rejected"] += 1

    for u in users:
        if u["role"] == "worker":
            stats = worker_stats.get(u["user_id"], {})
            u["tasks_accepted"] = stats.get("accepted", 0)
            u["tasks_completed"] = stats.get("completed", 0)
            u["tasks_rejected"] = stats.get("rejected", 0)
            u["on_time_completions"] = stats.get("on_time", 0)
            u["earnings"] = round(stats.get("earnings", 0.0), 2)
        elif u["role"] == "client":
            # spend = sum of budgets of completed tasks for this client
            u["spent"] = round(sum(t["budget"] for t in tasks if t["client_id"] == u["user_id"] and t["status"] == "completed"), 2)

    # ===== Badges =====
    badges = []
    for (worker_id, category), v in badges_inc.items():
        badges.append({
            "badge_id": f"bdg_demo_{uuid.uuid4().hex[:8]}",
            "user_id": worker_id, "category": category,
            "completed_count": v["count"], "total_earned": round(v["earned"], 2),
            "created_at": now.isoformat(), "last_at": now.isoformat(),
        })

    # ===== Waitlist =====
    waitlist = [
        {"waitlist_id": f"wl_demo_{i}", "name": n, "email": e, "role": r,
         "interest": interest,
         "referral_code": f"DEMO{i:04d}", "referred_by": None,
         "referrals_count": random.randint(0, 4),
         "created_at": (now - timedelta(days=random.randint(1, 30))).isoformat()}
        for i, (n, e, r, interest) in enumerate([
            ("Tushar", "tushar@iitr.ac.in", "worker", "Want to do Canva + design tasks"),
            ("Priyanka", "priyanka@nitk.ac.in", "worker", "Translation and content"),
            ("Akash (Founder, Crisply)", "a@crisply.in", "client", "Need help with social media"),
            ("Pranav", "pranav@thapar.edu", "worker", "Excel models & data entry"),
            ("Riya", "riya@xim.edu.in", "worker", "Audio transcription"),
            ("Yash (Founder, GoBuddy)", "yash@gobuddy.in", "client", "Multiple ongoing tasks"),
        ], start=1)
    ]

    return users, tasks, submissions, badges, waitlist
