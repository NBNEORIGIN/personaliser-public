# Week 1: Security & Stability Sprint

**Goal**: Make the demo secure and stable enough for external beta testers

**Time Required**: 40 hours (full-time) or 8 hours/day

---

## 🎯 Daily Breakdown

### Day 1 (Today): Setup & Authentication Foundation

#### Morning (4 hours)
- [x] ✅ Create development branch
- [ ] Set up .env files
- [ ] Install security dependencies
- [ ] Create user authentication models

#### Afternoon (4 hours)
- [ ] Implement password hashing
- [ ] Create registration endpoint
- [ ] Create login endpoint (JWT)
- [ ] Test authentication flow

**End of Day Goal**: Users can register and login

---

### Day 2: Complete Authentication System

#### Morning (4 hours)
- [ ] Add password reset flow
- [ ] Add email validation
- [ ] Add session management
- [ ] Create protected route decorator

#### Afternoon (4 hours)
- [ ] Update frontend with login UI
- [ ] Add JWT token storage
- [ ] Add logout functionality
- [ ] Test complete auth flow

**End of Day Goal**: Full authentication system working

---

### Day 3: Security Hardening

#### Morning (4 hours)
- [ ] Add rate limiting middleware
- [ ] Implement file upload validation
- [ ] Add filename sanitization
- [ ] Path traversal protection

#### Afternoon (4 hours)
- [ ] Update CORS configuration
- [ ] Add HTTPS redirect (production)
- [ ] Remove auth bypass in production config
- [ ] Security testing with sample attacks

**End of Day Goal**: All critical security issues fixed

---

### Day 4: Error Handling & Monitoring

#### Morning (4 hours)
- [ ] Sign up for Sentry (free tier)
- [ ] Install Sentry SDK in backend
- [ ] Add Sentry to frontend
- [ ] Configure error tracking

#### Afternoon (4 hours)
- [ ] Add user-friendly error messages
- [ ] Create error boundaries in React
- [ ] Add retry logic for network calls
- [ ] Test error scenarios

**End of Day Goal**: Comprehensive error tracking active

---

### Day 5: Testing & Deployment

#### Morning (4 hours)
- [ ] Run full test suite
- [ ] Fix any failing tests
- [ ] Test all workflows end-to-end
- [ ] Test on different browsers

#### Afternoon (4 hours)
- [ ] Deploy to staging (dev-api.nbne.uk)
- [ ] Verify staging deployment
- [ ] Update production with security fixes
- [ ] Document changes in CHANGELOG.md

**End of Day Goal**: Secure version deployed to staging

---

## 📋 Detailed Task Checklist

### Setup Tasks (Day 1 Morning)

#### 1. Create Development Branch
```powershell
# Commit current state
git add .
git commit -m "chore: snapshot before beta sprint"
git push origin main

# Create development branch
git checkout -b development
git push -u origin development

# Protect main branch on GitHub
# Settings → Branches → Add rule for 'main'
# ✓ Require pull request reviews
```

#### 2. Environment Configuration
```powershell
# Copy example env file
cp .env.example .env

# Edit .env with your values
# CRITICAL: Set APP_BYPASS_AUTH_FOR_TESTS=false for production
```

#### 3. Install Security Dependencies
```powershell
cd backend

# Add to requirements.txt:
# python-jose[cryptography]==3.3.0  (already installed)
# passlib[bcrypt]==1.7.4  (already installed)
# slowapi==0.1.9  (NEW - for rate limiting)
# sentry-sdk[fastapi]==1.40.0  (NEW - for error tracking)

pip install slowapi sentry-sdk[fastapi]
```

---

### Authentication Tasks (Day 1-2)

#### 1. Create User Model
**File**: `backend/app/models/user.py` (already exists)

Check if it has:
- [ ] Email field (unique)
- [ ] Hashed password field
- [ ] Created/updated timestamps
- [ ] Active/verified flags

#### 2. Password Hashing Utilities
**File**: `backend/app/auth.py` or `backend/app/auth_simple.py`

Add functions:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

#### 3. Registration Endpoint
**File**: `backend/app/routers/auth_router.py`

Add endpoint:
```python
@router.post("/auth/register")
async def register(email: str, password: str, db: Session = Depends(get_db)):
    # Check if user exists
    # Hash password
    # Create user
    # Return success
```

#### 4. Login Endpoint
**File**: `backend/app/routers/auth_router.py`

Add endpoint:
```python
@router.post("/auth/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    # Verify credentials
    # Create JWT token
    # Return token
```

#### 5. Frontend Login UI
**File**: `frontend/components/LoginForm.tsx` (NEW)

Create simple login form:
- Email input
- Password input
- Login button
- Error display

---

### Security Hardening Tasks (Day 3)

#### 1. Rate Limiting
**File**: `backend/app/main.py`

Add rate limiting:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to routes:
@router.post("/jobs/generate")
@limiter.limit("10/minute")
async def generate_job(...):
    ...
```

#### 2. File Upload Validation
**File**: `backend/app/routers/ingest_amazon.py`

Add validation:
```python
ALLOWED_EXTENSIONS = {'.txt', '.tsv', '.csv', '.zip'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

async def validate_upload(file: UploadFile):
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    
    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    
    return True
```

#### 3. Filename Sanitization
**File**: `backend/app/utils/security.py` (NEW)

Create utility:
```python
import re
from pathlib import Path

def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filename."""
    # Remove path traversal attempts
    filename = Path(filename).name
    
    # Remove special characters except . - _
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1)
        filename = name[:250] + '.' + ext
    
    return filename
```

#### 4. Update CORS
**File**: `backend/app/main.py`

Update CORS for production:
```python
# Use environment variable
import os

allowed_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 5. Production Config
**File**: `backend/app/settings.py`

Update:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    BYPASS_AUTH_FOR_TESTS: bool = False  # Default to secure
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100
```

---

### Monitoring Tasks (Day 4)

#### 1. Sentry Setup
**File**: `backend/app/main.py`

Add Sentry:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )
```

#### 2. Frontend Sentry
**File**: `frontend/app/layout.tsx`

Add Sentry:
```typescript
import * as Sentry from "@sentry/nextjs";

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NODE_ENV,
  });
}
```

#### 3. Error Boundaries
**File**: `frontend/components/ErrorBoundary.tsx` (NEW)

Create error boundary component

#### 4. User-Friendly Errors
**File**: `backend/app/routers/*.py`

Replace generic errors:
```python
# Before:
raise HTTPException(400, "Bad request")

# After:
raise HTTPException(
    400, 
    detail={
        "message": "Unable to process file",
        "hint": "Please ensure your file is a valid Amazon TSV format",
        "code": "INVALID_FILE_FORMAT"
    }
)
```

---

### Testing Tasks (Day 5)

#### 1. Run Test Suite
```powershell
cd backend
pytest -v

# Fix any failing tests
```

#### 2. Manual Testing Checklist
- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Login with wrong credentials (should fail)
- [ ] Upload valid Amazon file
- [ ] Upload invalid file (should reject)
- [ ] Generate job
- [ ] Download results
- [ ] Test rate limiting (make 15 requests quickly)
- [ ] Test on Chrome, Firefox, Edge

#### 3. Deploy to Staging
```powershell
# Push development branch
git add .
git commit -m "feat: add authentication and security hardening"
git push origin development

# Render will auto-deploy to dev-api.nbne.uk
# Verify deployment at https://dev-api.nbne.uk/health
```

---

## 🚨 Critical Security Checklist

Before deploying to production:

- [ ] `BYPASS_AUTH_FOR_TESTS=false` in production .env
- [ ] Strong `SECRET_KEY` set (32+ random characters)
- [ ] Rate limiting active
- [ ] File upload validation working
- [ ] CORS restricted to production domains
- [ ] HTTPS enforced
- [ ] Sentry error tracking active
- [ ] All tests passing

---

## 📝 Documentation Updates

Create/update these files:

- [ ] `CHANGELOG.md` - Document security changes
- [ ] `README.md` - Update setup instructions
- [ ] `.env.example` - Document all variables
- [ ] `SECURITY.md` - Security policy and reporting

---

## 🎯 Success Criteria for Week 1

By Friday evening, you should have:

✅ **Authentication system** - Users can register/login
✅ **Security hardened** - Rate limiting, validation, sanitization
✅ **Error tracking** - Sentry monitoring all errors
✅ **Staging deployed** - dev-api.nbne.uk running secure version
✅ **Tests passing** - All automated tests green
✅ **Manual testing** - All workflows verified

---

## 🆘 If You Get Stuck

### Authentication Issues
- Check `backend/app/auth.py` and `auth_simple.py` - you already have auth code
- Review `backend/app/models/user.py` - User model exists
- Test with curl or Postman before frontend

### Rate Limiting Issues
- Start with generous limits (100/min) then tighten
- Test with curl in a loop
- Check Slowapi documentation

### Sentry Issues
- Free tier is fine for beta
- Can skip if time-constrained (add later)
- Alternative: Just use good logging

### Deployment Issues
- Check Render logs for errors
- Verify environment variables set
- Test locally first with production settings

---

## 📞 Need Help?

If stuck on any task:
1. Check existing code - many features already implemented
2. Google the specific error
3. Check library documentation
4. Ask in relevant Discord/Slack communities
5. Can skip non-critical items (Sentry, etc.) if time-constrained

---

## ⏭️ Next Week Preview

Week 2 will focus on:
- User documentation (Quick Start Guide)
- Video tutorials (3 videos)
- Support infrastructure (email, status page)
- Beta tester recruitment

But first, let's nail Week 1! 🚀

---

**Start Time**: Today
**End Time**: Friday 5pm
**Status**: Ready to begin
**First Task**: Create development branch (15 minutes)

Let's do this! 💪
