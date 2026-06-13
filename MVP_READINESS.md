# SideQuest — MVP Readiness Report (Feb 2026)

> Tagline: *Your side quest to financial independence.*
> Purpose: Micro-jobs platform for students, freshers, and exam aspirants in India.
> Stack: React 19 + FastAPI + MongoDB. Emergent Google OAuth.

---

## ✅ What works

### Core flows (end-to-end, tested)
- **Auth**: Google OAuth (Emergent), role selection (worker/client), admin auto-promote via `ADMIN_EMAILS`, 7-day session cookies, server-side `/api/auth/me` verification.
- **Worker**: Browse 14+ open tasks, debounced search, sort (newest / budget / deadline), 11 category filters, apply (atomic assignment), submit work with file uploads (≤25MB) + URL, history with feedback, profile with skills + Reliability Score + skill badges.
- **Client**: Post task (with full input validation), see active/completed tasks, review pending submissions (approve+pay or reject), see worker's trust badge and reliability score in the review modal.
- **Admin**: Polished Analytics dashboard (total users, workers, clients, total tasks, completion rate, pending reviews, task funnel, submission quality funnel, top reliable workers), Users CRUD with role dropdown + reliability columns, Tasks table, Submissions list, Payments mark-paid, Waitlist with referral counts, Feedback inbox.
- **Reliability Score (new)**: Tracks tasks_accepted, tasks_completed, tasks_rejected, on_time_completions. Computes approval_rate, on_time_rate, 0–100 score, and trust_level (New → Rising → Trusted → Verified). Visible on worker profile, in client review modal, and admin users table.
- **Referrals**: Each waitlist signup gets a unique 8-char code + shareable link, `?ref=` URL params auto-credit inviters, admin sees referral counts.
- **File uploads**: Emergent object storage with backend-mediated downloads (`/api/files/download?path=...`) — only uploader, admin, or related client/worker can access.
- **Demo data**: 1 admin + 10 clients + 20 workers + 50 tasks + 30 submissions + 15 skill badges + 6 waitlist entries, auto-seeded on first start; force re-seed via `POST /api/seed?force=true`.

### Code quality
- **Input validation**: Pydantic field validators on title (5-200), description (10-2000), budget (>0 ≤ 1M), deadline (not in past, YYYY-MM-DD), category (whitelisted), submission_text (5-5000), bio (≤500), role (worker/client only).
- **Atomic state transitions**: Reviewing already-reviewed submission → 400. Applying to non-open task → 400. Applying twice → 400.
- **Authorization**: Per-route role checks. Cross-user access blocked (e.g. clients can't review others' tasks).
- **Resend integration**: Gracefully no-ops when `RESEND_API_KEY` is empty — never crashes the route. Add the key and emails start flowing automatically.

---

## ⚠️ Known limitations (acceptable for MVP)

1. **Payments are manual**: Admin clicks "Mark paid" → status flips. No Stripe/UPI auto-payout yet (roadmap).
2. **No notifications inside the app**: Workers learn about assignments via email (Resend) once a key is added. No bell icon / activity feed.
3. **First-applicant-wins**: Workers who apply to an already-assigned task get added to the applicants list but not assigned. UI shows assigned status; no in-app re-bidding.
4. **No chat/messaging**: Clients and workers can attach files + leave feedback in the review flow, but cannot DM.
5. **Object storage sync calls**: `requests` library blocks the event loop briefly during upload. Fine at MVP scale; refactor to `httpx.AsyncClient` if upload concurrency grows.
6. **CORS = '*'**: Acceptable since frontend and backend share the same ingress domain; pin in production env when promoting.
7. **No password fallback**: Login is Google-only. Acceptable for students (all have Gmail) but rejects users without Google accounts.
8. **No image preview for uploaded files**: Files download as attachments; no inline preview.
9. **Worker can be rejected & resubmit unlimited times**: No cap on retries. Could add a hard limit (e.g., 3 attempts) post-validation.
10. **Deadlines not enforced after start**: Once assigned, late submissions are still accepted (just hurt `on_time_rate`).

---

## 🔬 What should be tested with real users

### Acquisition
- Does the landing copy ("Your side quest to financial independence") resonate with students? Track waitlist conversion.
- Which 2–3 categories drive the most signups? (Track interest field on waitlist.)
- Referral coefficient: does ≥1 friend join per signup? (Aim K > 0.4 by week 4.)

### Worker activation
- Time from sign-up → first apply. Target: < 10 minutes.
- Drop-off after seeing 0 matching tasks. (We added empty-state CTAs to mitigate.)
- Are 20 seeded tasks + a few real ones enough to keep the dashboard feeling alive?

### Client activation
- Time from sign-up → first task posted. Target: same session.
- Do post-task form validation errors confuse them? (Watch for 422 spikes.)
- Quality of submissions vs. expectations — are workers actually delivering?

### Quality & trust
- Do trust badges (New/Rising/Trusted/Verified) influence client approval decisions?
- Approval rate after first week (target: ≥70%).
- Time-to-review (client SLA on pending submissions). Target: < 48h.

### Operations
- Can the admin keep up with payments manually at ~10 completed tasks/day?
- Do admins find Analytics tab actionable? (Are they checking it weekly?)

---

## 🚀 Recommended next steps after validation

### If demand is hot (>200 waitlist signups in 30 days)
1. **Add RESEND_API_KEY** → email delivery for waitlist + assignments + payment cleared. Already wired.
2. **Automated UPI payouts** (Razorpay X / Cashfree Payouts). Replace manual mark-paid.
3. **Worker → Client messaging** (simple thread per task, not chat).
4. **Push notifications** via web push (free, no SMS cost).
5. **Profile completeness gate**: workers must have bio + 3 skills + verified college email before applying.

### If supply is hot but demand is low (lots of workers, few clients)
1. **Cold outbound** to founders/agencies (use admin/waitlist data — `role=client` interest field).
2. **Featured client logos** on landing (social proof).
3. **Case studies** from completed tasks (with worker + client permission).
4. **Lower the price floor** to attract first-time clients.

### If demand is hot but supply is low
1. **Campus ambassador program**: incentivize one student per campus with ₹500/qualified worker referred.
2. **LinkedIn outreach** to specific colleges (BITS, IITs, DU, top NITs).
3. **WhatsApp groups** by category (Canva designers, Excel folks, transcribers).

### If both are stuck (most likely scenario)
1. **Get on calls with 10 workers + 10 clients** — what stopped them?
2. **Manually source 5 tasks/week** as concierge until organic flow starts.
3. **Iterate on the categories**: drop the 3 lowest-engagement ones, double down on top 3.
4. **Consider scoping down**: pick ONE category (e.g., Canva Design for D2C brands) and own it before broadening.

### Technical hardening (only after PMF signals)
1. Move to httpx.AsyncClient in storage.py (concurrency).
2. Pin CORS to actual production domain.
3. Add rate limiting on `/api/waitlist` and `/api/feedback` (spam protection).
4. Add Sentry / Posthog event tracking (currently only Posthog session recording is on).
5. Per-task application cap + "X applied" counter.
6. Mobile app (React Native or Capacitor) — students live on phones.

---

## 📊 Numbers to track weekly

| Metric | Target by Week 4 | How to check |
| --- | --- | --- |
| Waitlist signups | 100+ | Admin → Waitlist tab |
| Active workers (≥1 apply) | 30+ | Admin → Users (filter by `tasks_accepted > 0`) |
| Tasks posted by real clients | 15+ | Admin → Tasks (exclude `task_demo_*`) |
| Completion rate | ≥40% | Admin → Analytics |
| Submission approval rate | ≥70% | Admin → Analytics |
| Avg time to review (hours) | <48 | Manual / log timestamps |
| Verified-trust-level workers | 3+ | Admin → Users (filter `trust_level=verified`) |

---

## ✅ Final verdict

The MVP is **validation-ready**:

- ✅ All three user flows work end-to-end.
- ✅ Reliability + badges + referrals add depth without bloating scope.
- ✅ 50 tasks + 30 submissions makes the app feel alive on first login.
- ✅ Manual admin tooling is sufficient to run the platform for the first ~100 tasks.
- ✅ Input validation, authorization, and graceful degradation (Resend without key, storage without key) are in place.

**Ship it.** Get 10 real users in by Friday. Use the testing checklist (`/app/TESTING_CHECKLIST.md`) one final time before promoting.
