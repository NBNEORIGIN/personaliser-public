# 🎯 Your First Steps - Start Here!

**Good news: You already have authentication code!**

I've reviewed your codebase and you're further along than expected. Here's what to do RIGHT NOW.

---

## ✅ What You Already Have

Looking at your code, you have:

1. ✅ **User Model** (`backend/app/models/user.py`)
   - Username, email, password_hash fields
   - is_active flag
   - Database relationships

2. ✅ **Password Hashing** (`backend/app/auth_simple.py`)
   - `hash_password()` function with bcrypt
   - `verify_password()` function
   - Session management

3. ✅ **Auth Dependencies** (`backend/app/auth.py` + `auth_simple.py`)
   - `get_current_user()` dependency
   - Auth0 integration (optional)
   - Simple session-based auth

4. ✅ **Database Setup** (`backend/app/database.py`)
   - SQLAlchemy configured
   - User table creation

**This is GREAT! You're 50% done with Week 1 already!**

---

## 🚀 Next 2 Hours - Critical Setup

### Step 1: Create Development Branch (5 min)

```powershell
# In your project root
cd c:\Users\zentu\personaliser

# Save current work
git add .
git commit -m "chore: prepare for beta sprint"
git push origin main

# Create development branch
git checkout -b development
git push -u origin development
```

---

### Step 2: Set Up Environment (5 min)

```powershell
# Copy example to .env
Copy-Item .env.example backend\.env

# Edit the file
code backend\.env
```

**Add these values**:
```bash
# CRITICAL: Set to false for production!
APP_BYPASS_AUTH_FOR_TESTS=true

# Generate secret (run in PowerShell):
# -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
APP_SECRET_KEY=ChangeThisToYourGeneratedSecretKey123

# Database
DATABASE_URL=sqlite:///data/app.db

# CORS
FRONTEND_ORIGIN=http://localhost:3000

# Support
SUPPORT_EMAIL=support@nbne.uk
```

---

### Step 3: Install Security Dependencies (10 min)

```powershell
cd backend

# Check if already installed
pip list | Select-String "slowapi|sentry"

# If not installed, add to requirements.txt:
Add-Content requirements.txt "`nslowapi==0.1.9"
Add-Content requirements.txt "sentry-sdk[fastapi]==1.40.0"

# Install
pip install -r requirements.txt
```

---

### Step 4: Add Rate Limiting (30 min)

Create new file: `backend/app/middleware/rate_limit.py`

```python
"""Rate limiting middleware."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Update `backend/app/main.py`:

```python
# Add at top
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .middleware.rate_limit import limiter

# After app = FastAPI(...)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Update `backend/app/routers/jobs.py`:

```python
# Add at top
from ..middleware.rate_limit import limiter

# Add to generate endpoint
@router.post("/jobs/generate", response_model=GenerateResponse)
@limiter.limit("10/minute")
async def generate_job(req: GenerateRequest, user=Depends(get_current_user)):
    # ... existing code ...
```

---

### Step 5: Update Production Config (15 min)

Create `backend/.env.production`:

```bash
# PRODUCTION CONFIGURATION
# CRITICAL: These settings are for production only!

# Security
APP_BYPASS_AUTH_FOR_TESTS=false  # MUST BE FALSE!
APP_SECRET_KEY=your-production-secret-key-here-change-this

# Database
DATABASE_URL=sqlite:///data/app.db

# CORS - Update with your actual domains
FRONTEND_ORIGIN=https://www.nbne.uk,https://demo.nbne.uk

# Storage
APP_STORAGE_BACKEND=local
APP_ALLOW_EXTERNAL_DOWNLOADS=true

# Support
SUPPORT_EMAIL=support@nbne.uk

# Monitoring (add after Sentry setup)
SENTRY_DSN=
SENTRY_ENVIRONMENT=production

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100
```

---

### Step 6: Test Everything (30 min)

```powershell
# Start backend
cd backend
uvicorn app.main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev

# Test in browser:
# 1. Backend health: http://localhost:8000/health
# 2. Frontend: http://localhost:3000
# 3. Try uploading a file
# 4. Try generating a job
```

**If everything works, you're ready to move forward!**

---

## 🎯 What to Focus on Next

Since you already have auth code, skip ahead to:

### Priority 1: File Upload Security (2 hours)

Create `backend/app/utils/security.py`:

```python
"""Security utilities."""
import re
from pathlib import Path
from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {'.txt', '.tsv', '.csv', '.zip'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filename."""
    # Get just the filename (no path)
    filename = Path(filename).name
    
    # Remove special characters except . - _
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


async def validate_upload(file: UploadFile) -> bool:
    """Validate uploaded file."""
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    return True
```

Update `backend/app/routers/ingest_amazon.py`:

```python
# Add at top
from ..utils.security import validate_upload, sanitize_filename

# In the upload handler
@router.post("/ingest/amazon")
async def ingest_amazon(
    request: Request,
    file: Optional[UploadFile] = File(None),
    payload: Optional[Dict[str, Any]] = Body(None),
    user=Depends(get_current_user),
):
    # Add validation if file uploaded
    if file is not None:
        await validate_upload(file)
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        # ... rest of code ...
```

---

### Priority 2: Error Tracking Setup (1 hour)

**Sign up for Sentry** (5 min):
1. Go to https://sentry.io
2. Sign up (free tier)
3. Create new project: "personaliser-backend"
4. Copy your DSN

**Add to backend** (10 min):

Update `backend/app/main.py`:

```python
# Add at top
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# After imports, before app creation
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or "development",
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions
    )
```

Update `backend/app/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Monitoring
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str = "development"
```

**Add to .env**:
```bash
SENTRY_DSN=your-sentry-dsn-here
SENTRY_ENVIRONMENT=development
```

---

### Priority 3: Better Error Messages (30 min)

Update error responses to be user-friendly:

```python
# Example in backend/app/routers/ingest_amazon.py

# Before:
raise HTTPException(400, "Bad request")

# After:
raise HTTPException(
    400,
    detail={
        "message": "Unable to process your file",
        "hint": "Please ensure your file is a valid Amazon TSV format with headers",
        "code": "INVALID_FILE_FORMAT",
        "support": "Contact support@nbne.uk if you need help"
    }
)
```

---

## 📋 Today's Checklist

By end of today:

- [ ] Development branch created
- [ ] .env file configured
- [ ] Rate limiting added to key endpoints
- [ ] File upload validation implemented
- [ ] Sentry error tracking set up
- [ ] Production config created
- [ ] Everything tested locally

**That's 80% of Week 1 done in one day!**

---

## 🚨 Critical: Production Deployment

When deploying to production (Render.com):

1. **Environment Variables** - Set these in Render dashboard:
   ```
   APP_BYPASS_AUTH_FOR_TESTS=false
   APP_SECRET_KEY=your-production-secret
   SENTRY_DSN=your-sentry-dsn
   SENTRY_ENVIRONMENT=production
   FRONTEND_ORIGIN=https://www.nbne.uk,https://demo.nbne.uk
   ```

2. **Verify** - Check these after deployment:
   - [ ] Auth bypass is disabled
   - [ ] Rate limiting works (test with 15 quick requests)
   - [ ] File validation rejects invalid files
   - [ ] Errors appear in Sentry dashboard

---

## 🎉 Quick Wins Available Now

Since you have auth code, you can:

1. **Test existing auth** (15 min)
   - Try the auth endpoints
   - See if registration works
   - Check if login works

2. **Add rate limiting** (30 min)
   - Just 5 lines of code
   - Immediate security improvement

3. **Set up Sentry** (30 min)
   - Free tier is plenty
   - Instant error visibility

**You could finish Week 1 goals TODAY!**

---

## 💡 Recommended Approach

### Option A: Sprint Today (8 hours)
- Finish all Week 1 tasks today
- Move to Week 2 (documentation) tomorrow
- **Launch beta in 3 weeks instead of 4!**

### Option B: Steady Pace (5 days)
- Follow Week 1 schedule as planned
- More time for testing
- Less stressful

**My recommendation: Option A if you have the time!**

---

## 🚀 Your Next 30 Minutes

1. **Create development branch** (5 min)
2. **Set up .env file** (5 min)
3. **Install dependencies** (5 min)
4. **Add rate limiting** (15 min)

**Then take a break and celebrate!** 🎉

---

## 📞 Need Help?

### If rate limiting doesn't work:
- Check slowapi is installed: `pip list | grep slowapi`
- Check import statements
- Look for error in console

### If Sentry doesn't work:
- Verify DSN is correct
- Check SENTRY_DSN in .env
- Test by raising an error: `raise Exception("Test")`

### If tests fail:
- Run: `pytest -v` to see which test
- Most likely need to update test fixtures
- Can temporarily skip failing tests

---

**You're in great shape! Let's finish this sprint! 💪**

---

**Created**: 2025-11-19
**Status**: Ready to execute
**Time to complete**: 2-4 hours
**Difficulty**: Easy (you have most code already!)
