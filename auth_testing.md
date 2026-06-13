# Auth Testing Playbook for SideQuest

This app uses Emergent Google OAuth. For automated testing, you can simulate authenticated sessions by directly inserting session records into MongoDB.

## Step 1: Create Test User & Session
```bash
mongosh "mongodb://localhost:27017/test_database" --eval '
var userId = "test-user-" + Date.now();
var sessionToken = "test_session_" + Date.now();
db.users.insertOne({
  user_id: userId,
  email: "test.user." + Date.now() + "@example.com",
  name: "Test User",
  picture: "https://api.dicebear.com/7.x/avataaars/svg?seed=Test",
  role: "worker",
  skills: ["Canva Design"],
  earnings: 0,
  spent: 0,
  bio: null,
  is_approved: true,
  created_at: new Date().toISOString()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
});
print("Session: " + sessionToken);
print("User: " + userId);
'
```

For admin role, change role to "admin". For client role, change to "client".

## Step 2: Test backend APIs
```bash
TOKEN="your_session_token"
BASE="https://7e6af37a-2f05-4a08-876c-8c95640638c2.preview.emergentagent.com/api"

curl -X GET "$BASE/auth/me" -H "Authorization: Bearer $TOKEN"
curl -X GET "$BASE/tasks" -H "Authorization: Bearer $TOKEN"
curl -X GET "$BASE/admin/stats" -H "Authorization: Bearer $TOKEN"   # needs admin role
```

## Step 3: Browser testing
```python
await page.context.add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "7e6af37a-2f05-4a08-876c-8c95640638c2.preview.emergentagent.com",
    "path": "/",
    "httpOnly": True,
    "secure": True,
    "sameSite": "None"
}])
await page.goto("https://7e6af37a-2f05-4a08-876c-8c95640638c2.preview.emergentagent.com/dashboard")
```

The `/dashboard` route auto-redirects to the right dashboard for the user's role.

## Demo users already seeded
- user_demo_admin (admin)
- user_demo_client1 / user_demo_client2 (client)
- user_demo_worker1 / user_demo_worker2 (worker)

You can attach a session_token to any of these via the script in Step 1 by changing the user_id.

## Checklist
- [ ] /api/auth/me returns user data with `Authorization: Bearer <token>`
- [ ] /api/tasks list (all 3 roles)
- [ ] Worker can apply to a task → status becomes 'assigned'
- [ ] Worker can submit work → status becomes 'in_review'
- [ ] Client can approve/reject → status becomes 'completed'/'assigned'
- [ ] Admin /api/admin/stats returns aggregated numbers
- [ ] Public /api/waitlist accepts new entries (no auth)
- [ ] Public /api/tasks/public lists open tasks (no auth)
