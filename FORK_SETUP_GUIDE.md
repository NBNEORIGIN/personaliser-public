# Development Fork Setup Guide

## Overview

This guide walks you through creating a clean separation between your stable demo and active development work.

---

## Strategy: Git Branch Workflow

We'll use a **branch-based approach** rather than a separate repository. This allows you to:
- Keep demo stable on `main` branch
- Develop new features on `development` branch
- Cherry-pick bug fixes between branches
- Maintain single codebase with version control

---

## Step-by-Step Setup

### 1. Commit Current State

First, ensure all current work is committed:

```powershell
# Check current status
git status

# Add any uncommitted changes
git add .
git commit -m "chore: snapshot before creating development branch"

# Push to remote
git push origin main
```

### 2. Create Development Branch

```powershell
# Create and switch to development branch
git checkout -b development

# Push to remote
git push -u origin development
```

### 3. Protect Main Branch

On GitHub/GitLab:
1. Go to Settings → Branches
2. Add branch protection rule for `main`
3. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass
   - ✅ Include administrators (optional)

### 4. Set Up Branch Policies

Create `.github/BRANCH_POLICY.md`:

```markdown
# Branch Policy

## main (Protected)
- **Purpose**: Stable demo for beta testing
- **Deployment**: https://demo.nbne.uk
- **Changes**: Bug fixes only
- **Merge**: Requires PR + review + passing tests

## development
- **Purpose**: Active feature development
- **Deployment**: https://dev.nbne.uk (staging)
- **Changes**: All new features
- **Merge**: Can commit directly or use feature branches

## Feature Branches
- **Naming**: `feature/description` or `fix/description`
- **Base**: Branch from `development`
- **Merge**: PR to `development` when ready
```

---

## Deployment Configuration

### Current (Demo) - Main Branch

**Backend**: Render.com
- Update `render.yaml` to deploy from `main` branch only
- Domain: demo.nbne.uk

**Frontend**: Vercel
- Configure to deploy from `main` branch
- Domain: www.nbne.uk

### New (Development) - Development Branch

**Backend**: Render.com (separate service)
- Create new service: `personaliser-api-dev`
- Deploy from `development` branch
- Domain: dev-api.nbne.uk

**Frontend**: Vercel (preview deployment)
- Automatic preview deployments for `development` branch
- Domain: dev.nbne.uk or personaliser-dev.vercel.app

---

## Environment Configuration

### Main Branch (.env.production)

```bash
# Production (Demo)
APP_STORAGE_BACKEND=local
APP_ALLOW_EXTERNAL_DOWNLOADS=true
APP_BYPASS_AUTH_FOR_TESTS=false  # CRITICAL: Set to false
APP_CLEAN_PHOTOS_ON_START=true

# Database
DATABASE_URL=sqlite:///data/app.db

# CORS
FRONTEND_ORIGIN=https://www.nbne.uk

# Monitoring
SENTRY_DSN=your-production-sentry-dsn
SENTRY_ENVIRONMENT=production
```

### Development Branch (.env.development)

```bash
# Development/Staging
APP_STORAGE_BACKEND=local
APP_ALLOW_EXTERNAL_DOWNLOADS=true
APP_BYPASS_AUTH_FOR_TESTS=true  # OK for dev
APP_CLEAN_PHOTOS_ON_START=false

# Database
DATABASE_URL=sqlite:///data/app-dev.db

# CORS
FRONTEND_ORIGIN=https://dev.nbne.uk,http://localhost:3000

# Monitoring
SENTRY_DSN=your-development-sentry-dsn
SENTRY_ENVIRONMENT=development
```

---

## Workflow Examples

### Scenario 1: Bug Fix in Demo

```powershell
# Start from main
git checkout main
git pull origin main

# Create fix branch
git checkout -b fix/photo-upload-error

# Make changes
# ... edit files ...

# Commit
git add .
git commit -m "fix: handle null photo URLs in upload"

# Push and create PR to main
git push -u origin fix/photo-upload-error

# After PR merged to main, also apply to development
git checkout development
git cherry-pick <commit-hash>
git push origin development
```

### Scenario 2: New Feature Development

```powershell
# Start from development
git checkout development
git pull origin development

# Create feature branch
git checkout -b feature/amazon-integration

# Make changes over multiple commits
git add .
git commit -m "feat: add Amazon MWS authentication"

git add .
git commit -m "feat: implement order webhook listener"

# Push and create PR to development
git push -u origin feature/amazon-integration

# After PR merged, feature is in development only
# Will be merged to main when ready for beta
```

### Scenario 3: Merging Development to Main

```powershell
# When ready to promote features to demo
git checkout main
git pull origin main

# Create release branch
git checkout -b release/v1.1.0

# Merge development (or cherry-pick specific commits)
git merge development

# Test thoroughly
# ... run tests ...

# Push and create PR to main
git push -u origin release/v1.1.0

# After review and approval, merge to main
```

---

## File Structure Differences

Some files should differ between branches:

### Main Branch (Demo)
```
personaliser/
├── .env.production          # Production config
├── README.md                # User-facing docs
├── docker-compose.yml       # Production setup
└── render.yaml              # Deploy from main
```

### Development Branch
```
personaliser/
├── .env.development         # Dev config
├── README.md                # Developer docs
├── docker-compose.dev.yml   # Dev setup with hot reload
├── render.yaml              # Deploy from development
└── DEVELOPMENT_PLAN.md      # Roadmap (dev only)
```

---

## Render.com Setup

### Demo Service (Main Branch)

1. **Create Service**
   - Name: `personaliser-api`
   - Branch: `main`
   - Auto-deploy: Yes

2. **Environment Variables**
   ```
   PYTHON_VERSION=3.11.0
   STORAGE_BACKEND=local
   BYPASS_AUTH_FOR_TESTS=false
   ```

3. **Custom Domain**
   - demo.nbne.uk → personaliser-api

### Dev Service (Development Branch)

1. **Create Service**
   - Name: `personaliser-api-dev`
   - Branch: `development`
   - Auto-deploy: Yes

2. **Environment Variables**
   ```
   PYTHON_VERSION=3.11.0
   STORAGE_BACKEND=local
   BYPASS_AUTH_FOR_TESTS=true
   ```

3. **Custom Domain**
   - dev-api.nbne.uk → personaliser-api-dev

---

## Vercel Setup

### Production (Main Branch)

1. **Project Settings**
   - Production Branch: `main`
   - Domain: www.nbne.uk

2. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://demo.nbne.uk
   NODE_ENV=production
   ```

### Preview (Development Branch)

1. **Automatic Previews**
   - Every push to `development` creates preview
   - URL: personaliser-dev.vercel.app

2. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://dev-api.nbne.uk
   NODE_ENV=development
   ```

---

## Testing Strategy

### Main Branch (Demo)
- **Manual testing** before merge
- **Smoke tests** after deployment
- **Beta tester validation**

### Development Branch
- **Automated tests** on every commit
- **CI/CD pipeline** (GitHub Actions)
- **Integration tests** before merge to main

---

## CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/test.yml`:

```yaml
name: Test

on:
  push:
    branches: [main, development]
  pull_request:
    branches: [main, development]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest -v

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Build
        run: |
          cd frontend
          npm run build
```

---

## Migration Checklist

### Before Creating Development Branch
- [ ] Commit all current changes
- [ ] Tag current state: `git tag v1.0.0-demo`
- [ ] Push to remote
- [ ] Document current deployment URLs
- [ ] Backup database and files

### Creating Development Branch
- [ ] Create `development` branch
- [ ] Push to remote
- [ ] Set up branch protection on `main`
- [ ] Update README with branch strategy

### Setting Up Development Environment
- [ ] Create separate Render service
- [ ] Configure development environment variables
- [ ] Set up dev subdomain (dev-api.nbne.uk)
- [ ] Test deployment

### Documentation
- [ ] Create BRANCH_POLICY.md
- [ ] Update README with workflow
- [ ] Document environment differences
- [ ] Create PR templates

### Testing
- [ ] Verify main branch still deploys correctly
- [ ] Verify development branch deploys to staging
- [ ] Test PR workflow
- [ ] Test cherry-pick workflow for bug fixes

---

## Troubleshooting

### Issue: Changes in development affecting demo

**Solution**: Ensure deployments are configured for correct branches
```powershell
# Check which branch is deployed
git branch -r

# Verify Render/Vercel settings point to correct branch
```

### Issue: Merge conflicts between branches

**Solution**: Regularly sync development with main
```powershell
# Update development with main changes
git checkout development
git merge main
git push origin development
```

### Issue: Accidentally committed to wrong branch

**Solution**: Move commit to correct branch
```powershell
# If committed to main but meant for development
git checkout main
git log  # Find commit hash
git reset --hard HEAD~1  # Remove from main

git checkout development
git cherry-pick <commit-hash>  # Add to development
```

---

## Best Practices

1. **Never commit directly to main** - Always use PRs
2. **Keep development in sync** - Regularly merge main into development
3. **Test before merging** - Run full test suite
4. **Document breaking changes** - Update CHANGELOG.md
5. **Tag releases** - Use semantic versioning (v1.0.0, v1.1.0, etc.)
6. **Review PRs promptly** - Don't let them go stale
7. **Keep commits atomic** - One logical change per commit
8. **Write good commit messages** - Use conventional commits format

---

## Conventional Commits Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(auth): add email/password authentication

Implements basic auth with bcrypt password hashing.
Includes login, logout, and password reset flows.

Closes #123
```

```
fix(upload): handle null photo URLs

Previously crashed when photo_url was null.
Now gracefully handles missing photos.

Fixes #456
```

---

## Summary

**Branch Strategy**:
- `main` = Stable demo (protected)
- `development` = Active development
- `feature/*` = New features
- `fix/*` = Bug fixes

**Deployment**:
- Main → demo.nbne.uk (production)
- Development → dev-api.nbne.uk (staging)

**Workflow**:
- Develop on `development` or feature branches
- PR to `development` for review
- Cherry-pick bug fixes to `main`
- Merge `development` to `main` for releases

**Next Steps**:
1. Run migration checklist
2. Set up CI/CD pipeline
3. Create first feature branch
4. Test workflow with small change

---

**Created**: 2025-11-19
**Status**: Ready to implement
**Estimated Setup Time**: 2-3 hours
