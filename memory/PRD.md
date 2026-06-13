# SideQuest — PRD

**Tagline:** Your side quest to financial independence.

## Original Problem Statement
Build a modern, mobile-first web app ("Plan B" — branded as SideQuest) that helps students, freshers, and government exam aspirants earn money via flexible online micro-jobs. Businesses post small digital tasks; students complete them remotely. MVP for validating demand. Manual ops, simple, scalable.

## User Personas
- **Worker** — student/fresher/aspirant. Wants money + experience.
- **Client** — startup/creator/agency. Wants small digital tasks done fast & cheap.
- **Admin** — SideQuest team. Moderates, tracks payments, runs analytics.

## Architecture
- Frontend: React 19 + React Router + Tailwind + Phosphor icons + Sonner + Recharts. Pastel-brutalist UI (Outfit + Plus Jakarta Sans).
- Backend: FastAPI + Motor (MongoDB). All routes `/api/*`.
- Auth: Emergent Google OAuth (`/api/auth/session`, cookie + Bearer token). Admin allowlist via `ADMIN_EMAILS` env var.
- Storage: MongoDB (`users`, `user_sessions`, `tasks`, `submissions`, `waitlist`, `feedback`).

## Implemented
### Iteration 1 (Feb 12, 2026)
- Landing page (hero, problem/solution, how-it-works, worker + client benefits, categories grid, marquee, testimonials placeholder, FAQ accordion, waitlist CTA, footer).
- Google OAuth login + AuthCallback + role selection (worker/client).
- Worker dashboard: available tasks (filter by category), assigned tasks, submit work modal, history, profile + skills.
- Client dashboard: post task modal, active tasks, submissions review modal (approve/reject + feedback), completed tasks, spent stat.
- Admin dashboard: stats overview with charts (BarChart by category, PieChart user mix), Users table with role editor, Tasks table, Submissions list, Payments (mark paid), Waitlist, Feedback tabs.
- Roadmap page (Now/Next/Soon/Vision).
- Seeded demo data (5 users, 8 tasks, 1 submission, 3 waitlist entries) on first startup.
- 28/28 backend pytest tests passing.

### Iteration 2 (Feb 13, 2026) — P1 features
- **Admin email**: `niteshk582@gmail.com` added to `ADMIN_EMAILS` env (auto-promotes on first Google login).
- **Email notifications** (Resend): waitlist confirmation, task assigned, payment cleared. Wired up; gracefully no-ops when `RESEND_API_KEY` is blank.
- **Search + sort** on worker task list (query string + 4 sort modes, debounced).
- **File uploads** via Emergent object storage on work submissions (25MB cap, multipart, signed downloads).
- **Skill badges** as real DB entities with auto-incremented `completed_count`, `total_earned`, and computed `level` (1–5).
- **Referral system**: every waitlist signup gets a unique 8-char code + shareable link, `?ref=` recognized on landing, `referrals_count` incremented on each redemption, leaderboard endpoint, admin table shows referrals.
- 50/50 backend tests passing (22 new + 28 regression).

## Backlog
### P0 (next iteration)
- Pin CORS to actual origin (prod hardening).
- Move synchronous `requests` calls in storage.py to async/threadpool.

### P1
- Provide RESEND_API_KEY so emails actually deliver.
- Featured client/partner logos on landing.
- Per-task application limit / closing date.

### P2 (Roadmap on landing)
- AI task matching (LLM-powered).
- Automated payments (Stripe / Razorpay).
- Skill certifications.
- Worker ratings & reviews.
- Client subscriptions.
- Mobile app.

## Next Actions
1. User to log in with `niteshk582@gmail.com` → lands on Admin dashboard.
2. Add `RESEND_API_KEY` to `/app/backend/.env` to enable real email delivery.
3. Collect waitlist signups + referrals; identify top referrers manually.
