# Account Approval System - Quick Setup Guide

**Created**: November 26, 2025  
**Purpose**: Enable controlled beta access for blog post signups

---

## ✅ What Was Implemented

### Account Approval System
- ✅ New users require admin approval before accessing the system
- ✅ Users can register but can't login until approved
- ✅ Admin endpoints to manage user approvals
- ✅ Perfect for blog post beta signups

### Changes Made

**Database Model** (`backend/app/models/user.py`):
- Added `is_approved` field (default: False)
- Added `is_admin` field (default: False)
- Added `approved_at` timestamp

**Authentication** (`backend/app/auth_simple.py`):
- Updated `get_current_user()` to check approval status
- Added `get_current_admin()` dependency for admin endpoints
- Users get 403 error if not approved

**API Endpoints** (`backend/app/routers/auth_router.py`):
- Updated registration to set `is_approved=False`
- Updated login to check approval status
- Added admin endpoints:
  - `GET /api/auth/admin/pending-users` - List pending users
  - `POST /api/auth/admin/approve-user/{id}` - Approve user
  - `POST /api/auth/admin/reject-user/{id}` - Reject user
  - `GET /api/auth/admin/all-users` - List all users

---

## 🚀 Setup Steps (Before Blog Post)

### Step 1: Database Migration (5 minutes)

**Option A: Fresh Start** (if no important data):
```bash
# Stop server
# Delete database
rm backend/app/data/personaliser.db

# Restart server - new schema will be created
cd backend
uvicorn app.main:app --reload
```

**Option B: Keep Existing Data**:
```sql
-- Connect to database and run:
ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN approved_at DATETIME;

-- Approve existing users (optional)
UPDATE users SET is_approved = 1, approved_at = datetime('now');
```

### Step 2: Create Admin Account (2 minutes)

```bash
cd backend
python create_admin.py
```

Follow the prompts:
- Enter your username
- Enter your email
- Enter password (min 8 characters)
- Confirm password

**Done!** You now have an admin account.

### Step 3: Test the System (5 minutes)

**Test 1: Register a test user**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Test 2: Try to login (should fail)**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# Should return: "Account pending approval"
```

**Test 3: Login as admin**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-admin-username",
    "password": "your-admin-password"
  }' \
  -c cookies.txt
```

**Test 4: View pending users**
```bash
curl http://localhost:8000/api/auth/admin/pending-users -b cookies.txt
```

**Test 5: Approve the test user**
```bash
curl -X POST http://localhost:8000/api/auth/admin/approve-user/2 -b cookies.txt
```

**Test 6: Login as test user (should work now)**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# Should return success!
```

---

## 📝 Blog Post Integration

### What to Say in Your Blog Post

```markdown
## Join the Beta Program

I'm looking for local beta testers to try NBNE Personaliser!

**How to Join:**
1. Visit https://www.nbne.uk
2. Click "Register" and create an account
3. Wait for approval (usually within 24 hours)
4. Start automating your order processing!

**What You Get:**
- 3 months free trial
- 50% lifetime discount
- Priority support
- Help shape the product

**I'm especially interested in:**
- Local businesses (for in-person support)
- UV printing businesses
- 10-100 orders per month
- Willing to provide feedback

**Note:** Accounts require approval to ensure quality beta testing.
```

### After Someone Registers

**Daily Routine:**
1. Check pending users: `GET /api/auth/admin/pending-users`
2. Review their details (username, email)
3. Approve: `POST /api/auth/admin/approve-user/{id}`
4. Send welcome email (manual for now)

**Welcome Email Template:**
```
Subject: Your NBNE Personaliser Account is Approved! 🎉

Hi [username],

Great news! Your account has been approved.

You can now login at: https://www.nbne.uk
Username: [username]

Next steps:
1. Login to your account
2. Check out the Quick Start Guide
3. Process your first order
4. Let me know how it goes!

I'm excited to have you in the beta program!

Best,
[Your Name]
```

---

## 🎯 Using the Admin Endpoints

### Check Pending Users
```http
GET /api/auth/admin/pending-users
Cookie: session_token=<your_admin_session>

Response:
{
  "count": 2,
  "users": [
    {
      "id": 2,
      "username": "johndoe",
      "email": "john@example.com",
      "created_at": "2025-11-26T14:30:00",
      "is_approved": false
    }
  ]
}
```

### Approve a User
```http
POST /api/auth/admin/approve-user/2
Cookie: session_token=<your_admin_session>

Response:
{
  "success": true,
  "message": "User johndoe approved successfully"
}
```

### Reject a User
```http
POST /api/auth/admin/reject-user/3
Cookie: session_token=<your_admin_session>

Response:
{
  "success": true,
  "message": "User spammer rejected and removed"
}
```

### View All Users
```http
GET /api/auth/admin/all-users
Cookie: session_token=<your_admin_session>

Response:
{
  "count": 5,
  "users": [...]
}
```

---

## 🔧 Frontend Updates Needed

### Registration Page
Update to show after successful registration:
```javascript
// After registration success
"Account created! Your account is pending approval. 
You'll receive an email when approved (usually within 24 hours)."
```

### Login Page
Handle 403 error:
```javascript
// If login returns 403
"Your account is pending approval. Please wait for admin approval."
```

### Admin Dashboard (Future)
Create a simple admin page:
- List pending users
- Approve/Reject buttons
- View all users
- User statistics

---

## 📊 Tracking Beta Signups

Create a simple spreadsheet:

| ID | Username | Email | Registered | Approved | Status | Notes |
|----|----------|-------|------------|----------|--------|-------|
| 2 | johndoe | john@... | 2025-11-26 | 2025-11-26 | Active | Local tester |
| 3 | janedoe | jane@... | 2025-11-27 | Pending | - | Follow up |

---

## 🎉 Benefits

### For You
- ✅ Control who gets access
- ✅ Screen users before approval
- ✅ Prioritize local testers
- ✅ Professional beta management

### For Users
- ✅ Clear expectations (approval required)
- ✅ Feels exclusive
- ✅ Shows you're serious
- ✅ Quality control

---

## 📚 Documentation

Full documentation: `docs/ACCOUNT_APPROVAL_SYSTEM.md`

Includes:
- Detailed API documentation
- Frontend integration guide
- Email templates
- Troubleshooting
- Testing procedures

---

## ✅ Checklist Before Blog Post

- [ ] Database migrated (new columns added)
- [ ] Admin account created
- [ ] System tested (register → approve → login)
- [ ] Frontend updated (registration message)
- [ ] Frontend updated (login error handling)
- [ ] Welcome email template ready
- [ ] Tracking spreadsheet created
- [ ] Blog post written
- [ ] Ready to publish!

---

## 🚀 You're Ready!

When you publish your blog post:
1. Users can register
2. You'll see them in pending users
3. Approve the ones you want
4. Send them a welcome email
5. They can login and use the system

**Perfect for controlled beta access!** 🎯

---

**Questions?** Check `docs/ACCOUNT_APPROVAL_SYSTEM.md` for full details.
