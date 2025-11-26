# Account Approval System - Documentation

**Created**: November 26, 2025  
**Purpose**: Control beta access through admin-approved user accounts

---

## 🎯 Overview

The account approval system ensures that only approved users can access the NBNE Personaliser application. This is perfect for:
- **Beta testing**: Control who gets access during beta period
- **Blog post signups**: Accept registrations but approve manually
- **Quality control**: Screen users before granting access
- **Local community**: Approve local beta testers from your blog

---

## 🔐 How It Works

### User Flow
1. **User registers** → Account created but `is_approved = False`
2. **User tries to login** → Gets "Account pending approval" message
3. **Admin approves** → User can now login and use the system
4. **User logs in** → Full access to all features

### Admin Flow
1. **Check pending users** → See list of users awaiting approval
2. **Review details** → Username, email, registration date
3. **Approve or reject** → Grant access or remove account
4. **User notified** → (You can send email manually for now)

---

## 🚀 Database Changes

### User Model Updates
New fields added to `User` model:

```python
is_approved = Column(Boolean, default=False)  # Requires admin approval
is_admin = Column(Boolean, default=False)     # Admin privileges
approved_at = Column(DateTime, nullable=True) # When approved
```

**Migration Required**: Yes, you'll need to recreate the database or add these columns.

---

## 🛠️ Setting Up Your First Admin Account

### Option 1: Direct Database Access (Recommended for First Admin)

After the database is recreated with new schema:

```python
# Run this in a Python shell or create a script
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.auth_simple import hash_password

db = SessionLocal()

# Create admin user
admin = User(
    username="admin",  # Your username
    email="your-email@example.com",
    password_hash=hash_password("your-secure-password"),
    is_approved=True,
    is_admin=True
)

db.add(admin)
db.commit()
print(f"Admin user created: {admin.username}")
```

### Option 2: Modify First Registration

Temporarily modify the registration endpoint to make the first user an admin, then remove the code.

---

## 📡 API Endpoints

### User Endpoints

#### Register (Public)
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword123"
}

Response:
{
  "id": 2,
  "username": "testuser",
  "email": "test@example.com",
  "is_approved": false,  # ← Not approved yet
  "is_admin": false
}
```

#### Login (Public)
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "securepassword123"
}

# If not approved:
Response: 403 Forbidden
{
  "detail": "Account pending approval. Please wait for admin approval."
}

# If approved:
Response: 200 OK
{
  "success": true,
  "user": {
    "id": 2,
    "username": "testuser",
    "email": "test@example.com",
    "is_approved": true,
    "is_admin": false
  }
}
```

### Admin Endpoints (Require Admin Login)

#### Get Pending Users
```http
GET /api/auth/admin/pending-users
Cookie: session_token=<admin_session>

Response:
{
  "count": 3,
  "users": [
    {
      "id": 2,
      "username": "testuser1",
      "email": "test1@example.com",
      "created_at": "2025-11-26T12:30:00",
      "is_approved": false
    },
    {
      "id": 3,
      "username": "testuser2",
      "email": "test2@example.com",
      "created_at": "2025-11-26T13:15:00",
      "is_approved": false
    }
  ]
}
```

#### Approve User
```http
POST /api/auth/admin/approve-user/2
Cookie: session_token=<admin_session>

Response:
{
  "success": true,
  "message": "User testuser1 approved successfully",
  "user": {
    "id": 2,
    "username": "testuser1",
    "email": "test1@example.com",
    "is_approved": true
  }
}
```

#### Reject User
```http
POST /api/auth/admin/reject-user/3
Cookie: session_token=<admin_session>

Response:
{
  "success": true,
  "message": "User testuser2 rejected and removed"
}
```

#### Get All Users
```http
GET /api/auth/admin/all-users
Cookie: session_token=<admin_session>

Response:
{
  "count": 5,
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_approved": true,
      "is_admin": true,
      "is_active": true,
      "created_at": "2025-11-20T10:00:00",
      "approved_at": "2025-11-20T10:00:00"
    },
    {
      "id": 2,
      "username": "testuser1",
      "email": "test1@example.com",
      "is_approved": true,
      "is_admin": false,
      "is_active": true,
      "created_at": "2025-11-26T12:30:00",
      "approved_at": "2025-11-26T14:00:00"
    }
  ]
}
```

---

## 🎨 Frontend Integration (To Do)

You'll need to update your frontend to:

### Registration Page
- Show message after registration: "Account created! Awaiting admin approval."
- Don't auto-login after registration (session created but user can't access features)

### Login Page
- Handle 403 error gracefully
- Show: "Your account is pending approval. You'll receive an email when approved."

### Admin Dashboard (New Page)
Create an admin page with:
- List of pending users
- Approve/Reject buttons
- View all users
- User statistics

---

## 📧 Email Notifications (Manual for Now)

When you approve a user, send them an email:

**Subject**: Your NBNE Personaliser Account Has Been Approved! 🎉

**Body**:
```
Hi [username],

Great news! Your NBNE Personaliser account has been approved.

You can now log in and start using the system:
https://www.nbne.uk

Username: [username]

If you have any questions, reply to this email or check out our Quick Start Guide.

Welcome to the beta program!

Best regards,
[Your Name]
NBNE Personaliser Team
```

---

## 🔧 Testing the System

### 1. Create Admin Account
```bash
# Use the Python script above or direct database access
```

### 2. Test Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 3. Test Login (Should Fail)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# Should return 403 Forbidden
```

### 4. Login as Admin
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-admin-password"
  }' \
  -c cookies.txt  # Save session cookie
```

### 5. View Pending Users
```bash
curl -X GET http://localhost:8000/api/auth/admin/pending-users \
  -b cookies.txt  # Use saved session cookie
```

### 6. Approve User
```bash
curl -X POST http://localhost:8000/api/auth/admin/approve-user/2 \
  -b cookies.txt
```

### 7. Test Login Again (Should Work)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'

# Should return 200 OK with user details
```

---

## 🗄️ Database Migration

### Option 1: Fresh Start (Development)
If you don't have important data:

```bash
# Delete existing database
rm backend/app/data/personaliser.db

# Restart server - database will be recreated with new schema
cd backend
uvicorn app.main:app --reload
```

### Option 2: Manual Migration (Production)
If you have existing users:

```sql
-- Add new columns to users table
ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN approved_at DATETIME;

-- Approve all existing users (optional)
UPDATE users SET is_approved = 1, approved_at = datetime('now');

-- Make your account an admin (replace with your user ID)
UPDATE users SET is_admin = 1 WHERE id = 1;
```

---

## 📊 Blog Post Integration

### What to Include in Your Blog Post

**Registration Call-to-Action**:
```markdown
## Join the Beta Program

Interested in trying NBNE Personaliser? Sign up for early access!

**How to Join:**
1. Visit [https://www.nbne.uk](https://www.nbne.uk)
2. Click "Register" and create an account
3. Wait for approval (usually within 24 hours)
4. Start processing orders!

**What You Get:**
- 3 months free trial
- 50% lifetime discount ($49.50/month vs $99)
- Priority support
- Influence the roadmap

**Requirements:**
- UV printer
- 10-100 orders per month
- Willingness to provide feedback

**Local Beta Testers Preferred** - I'm especially looking for testers 
in [your area] for potential in-person support.
```

### After Publishing

1. **Check daily** for new registrations:
   - Visit `/api/auth/admin/pending-users`
   - Or create a simple admin dashboard

2. **Review applications**:
   - Check username and email
   - Google their business if needed
   - Prioritize local testers

3. **Approve or reject**:
   - Approve: `/api/auth/admin/approve-user/{id}`
   - Reject: `/api/auth/admin/reject-user/{id}`

4. **Send welcome email** (manual for now)

5. **Track in spreadsheet**:
   - Username, email, approved date
   - Follow up for onboarding call

---

## 🎯 Next Steps

### Immediate (Before Blog Post)
1. ✅ Database migration (add new columns)
2. ✅ Create your admin account
3. ✅ Test the approval flow
4. ⏳ Update frontend registration message
5. ⏳ Update frontend login error handling

### Short Term (Week 1)
1. Create simple admin dashboard page
2. Add email notification system
3. Test with a friend's registration

### Medium Term (Week 2-3)
1. Automated email notifications
2. Admin dashboard improvements
3. User statistics and tracking

---

## 🐛 Troubleshooting

### "Account pending approval" but I'm admin
- Check `is_admin = True` in database
- Check `is_approved = True` in database
- Clear cookies and login again

### Can't access admin endpoints
- Verify you're logged in as admin
- Check session cookie is being sent
- Verify `is_admin = True` in database

### Database errors after update
- Delete database and recreate (dev only)
- Or run manual migration SQL (production)

### Users not showing in pending list
- Check they registered successfully
- Verify `is_approved = False` in database
- Check they're not admin users

---

## 📝 Code Changes Summary

### Files Modified
1. `backend/app/models/user.py` - Added `is_approved`, `is_admin`, `approved_at`
2. `backend/app/auth_simple.py` - Added approval check, `get_current_admin()`
3. `backend/app/routers/auth_router.py` - Updated responses, added admin endpoints

### New Endpoints
- `GET /api/auth/admin/pending-users` - List pending users
- `POST /api/auth/admin/approve-user/{id}` - Approve user
- `POST /api/auth/admin/reject-user/{id}` - Reject user
- `GET /api/auth/admin/all-users` - List all users

### Database Schema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    is_approved BOOLEAN DEFAULT 0,  -- NEW
    is_admin BOOLEAN DEFAULT 0,     -- NEW
    created_at DATETIME,
    approved_at DATETIME            -- NEW
);
```

---

## 🎉 Benefits

### For You
- **Control access** - Only approved users can use the system
- **Screen users** - Review before granting access
- **Local focus** - Prioritize local beta testers
- **Quality control** - Ensure serious users only

### For Users
- **Clear expectations** - Know approval is required
- **Professional** - Shows you're serious about the beta
- **Exclusive** - Feels special to be approved
- **Trusted** - You're vetting who gets access

---

## 💡 Pro Tips

1. **Respond quickly** - Approve within 24 hours to maintain momentum
2. **Send personal emails** - Make approved users feel valued
3. **Track everything** - Use spreadsheet to track approvals
4. **Be selective** - Quality over quantity for beta
5. **Local first** - Prioritize local testers for in-person support

---

**You're all set for controlled beta access!** 🚀

When you publish your blog post, users can register but won't get access until you approve them. Perfect for managing your beta program!
