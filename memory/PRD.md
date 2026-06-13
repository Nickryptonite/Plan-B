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

## Implemented (Feb 2026)
- Landing page (hero, problem/solution, how-it-works, worker + client benefits, categories grid, marquee, testimonials placeholder, FAQ accordion, waitlist CTA, footer).
- Google OAuth login + AuthCallback + role selection (worker/client).
- Worker dashboard: available tasks (filter by category), assigned tasks, submit work modal, history, profile + skills.
- Client dashboard: post task modal, active tasks, submissions review modal (approve/reject + feedback), completed tasks, spent stat.
- Admin dashboard: stats overview with charts (BarChart by category, PieChart user mix), Users table with role editor, Tasks table, Submissions list, Payments (mark paid), Waitlist, Feedback tabs.
- Roadmap page (Now/Next/Soon/Vision).
- Seeded demo data (5 users, 8 tasks, 1 submission, 3 waitlist entries) on first startup.
- 28/28 backend pytest tests passing.

## Backlog
### P0 (next iteration)
- Pin CORS to actual origin (prod hardening).
- Worker can't see why a task "apply" silently joined applicants list — return `{assigned: bool}`.

### P1
- Email notifications via Resend (waitlist confirmation, task assigned, payment cleared).
- Search bar + sort on task list.
- Image/file upload via object storage for submission attachments.
- Per-worker skill badges as real DB entities + history.

### P2 (Roadmap on landing)
- AI task matching (LLM-powered).
- Automated payments (Stripe / Razorpay).
- Skill certifications.
- Worker ratings & reviews.
- Client subscriptions.
- Mobile app.

## Next Actions
1. Collect waitlist signups, validate demand.
2. Onboard first batch of workers + clients manually.
3. Promote real admin user via `ADMIN_EMAILS` env var or update DB role.
