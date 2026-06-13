# SideQuest — MVP Testing Checklist

Use this before sending the link to real users. Cover all 3 personas end-to-end.

---

## A. Worker flow (most critical)

### Onboarding
- [ ] Visit `/` → landing renders, hero + categories + FAQ all interactive.
- [ ] Click "Sign in with Google" → Google OAuth flow → land on `/select-role`.
- [ ] Pick **Worker** → select 2-3 skills → add a bio → land on `/worker`.
- [ ] Refresh page → still authenticated, dashboard loads.

### Browse & apply
- [ ] **Available** tab: 14+ open tasks visible.
- [ ] Type "podcast" in search box → list filters in ~300ms.
- [ ] Click category chip (e.g., "Canva Design") → list filters.
- [ ] Change sort to "Budget: high → low" → top task is the largest.
- [ ] Click **Clear filters** in empty state → reset.
- [ ] Open a task card → modal shows description, budget, deadline, client name.
- [ ] Click **Apply for this quest** → task moves to Assigned tab, toast confirms.

### Submit work
- [ ] **Assigned** tab: shows the just-applied task with "Submit Work" button.
- [ ] Click Submit Work → modal opens.
- [ ] Type submission text → paste a URL → upload a small file (PDF/PNG, <25MB).
- [ ] Click **Submit for review** → toast confirms, task moves to "In Review".

### Profile & reliability
- [ ] Switch to **Profile** tab.
- [ ] Reliability card shows score 0-100, trust badge (New/Rising/Trusted/Verified).
- [ ] Counters visible: Accepted, Completed, Approval %, On-time %.
- [ ] After a completed task, a skill badge appears with level + progress bar + ₹earned.

### Empty states
- [ ] New worker with 0 actions sees "No active quests yet" with CTA to browse.
- [ ] History tab when empty shows "No submissions yet" guidance.

---

## B. Client flow

### Post task
- [ ] Sign in as a client → land on `/client`.
- [ ] Click **Post a task** → modal opens.
- [ ] Try invalid inputs:
  - Title < 5 chars → 422 from backend.
  - Budget = 0 → 422.
  - Deadline in past → 422.
- [ ] Submit valid task → toast confirms, task appears in Active tab.

### Review submissions
- [ ] When a worker submits, **Review (N)** tab badge updates.
- [ ] Click **Review** → modal shows submission text, link, file (if any).
- [ ] Worker name shows next to **Trust Badge** + reliability score.
- [ ] Click **Reject** with feedback → status returns to "assigned", worker can resubmit.
- [ ] Click **Approve & Pay** → task marked completed, worker earnings updated, badge granted.

### Empty states
- [ ] New client with 0 posted tasks sees "Post your first task" CTA.
- [ ] No pending reviews → "All caught up!" message.

---

## C. Admin flow

### Sign in as admin
- [ ] Email is in `ADMIN_EMAILS` (e.g. `niteshk582@gmail.com`).
- [ ] After Google login → land on `/admin`.

### Analytics tab
- [ ] Top metrics: total_users, workers, clients, total_tasks, completion %, pending reviews.
- [ ] Task funnel (Open/Assigned/In Review/Completed) bars + percentages.
- [ ] Submission quality (Approved/Pending/Rejected) + platform approval %.
- [ ] Top reliable workers list (with trust badge + score).

### Overview tab (charts)
- [ ] BarChart: earnings by category.
- [ ] PieChart: user role mix.

### Users tab
- [ ] Table with Trust + Score + Done columns for each worker.
- [ ] Change role dropdown → instantly updates.

### Tasks tab
- [ ] All 50 seeded tasks visible with status badges.

### Submissions tab
- [ ] All 30 submissions shown with status, worker, date.
- [ ] Pending submissions show **Review** button.

### Payments tab
- [ ] Approved + unpaid submissions show **Mark paid** button.
- [ ] Click → status updates to "paid".

### Waitlist tab
- [ ] Shows seeded waitlist entries with Referrals + Code columns.

### Feedback tab
- [ ] Shows submitted feedback (or empty state).

---

## D. Cross-cutting

### Security & validation
- [ ] Logged-out user hitting `/worker` → redirect to `/login`.
- [ ] Worker hitting `/api/tasks` (POST) → 403.
- [ ] Client hitting `/api/tasks/{id}/apply` → 403.
- [ ] Worker hitting `/api/admin/users` → 403.
- [ ] Unauthenticated `/api/upload` → 401.
- [ ] Task creation with budget = -100 → 422.
- [ ] Submission text < 5 chars → 422.

### Referrals (waitlist)
- [ ] Submit waitlist on landing → see referral link in success modal.
- [ ] Open link in new tab `/?ref=CODE` → toast "You were invited!".
- [ ] Sign up with a fresh email → inviter's referrals_count increments.

### File uploads
- [ ] Upload a file > 25MB → 413 error.
- [ ] Upload a normal file → success, filename shows in submit modal.
- [ ] Client clicking download chip → file streams correctly.

### Resend (no key)
- [ ] Backend logs show "[email skipped: no RESEND_API_KEY]" but never crash.

### Mobile
- [ ] Resize to 375px width → landing readable, dashboard tabs scroll, modals fit.

---

## E. Smoke commands (CLI quickies)

```bash
BASE="https://7e6af37a-2f05-4a08-876c-8c95640638c2.preview.emergentagent.com"
# Public APIs
curl "$BASE/api/" && echo
curl "$BASE/api/tasks/public?limit=5" | head -c 200 && echo
# Waitlist
curl -X POST "$BASE/api/waitlist" -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"t@e.com","role":"worker"}'
# Leaderboard
curl "$BASE/api/waitlist/leaderboard"
```

If all checkboxes pass → ready for real users.
