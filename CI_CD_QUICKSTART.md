# 🚀 Quick Start - CI/CD Pipeline

## ⚡ TL;DR - What Was Fixed

```diff
# 1. Fixed Frontend Build Path
- context: ./services/frontend  ❌
+ context: ./frontend            ✅

# 2. Fixed Smoke Test
- kubectl wait --for=condition=complete job/smoke-test  ❌
+ kubectl wait --for=condition=ready pod/smoke-test     ✅

# 3. Created Missing Files
+ tests/integration/test_services.py     ✅
+ tests/integration/requirements.txt     ✅
+ tests/performance/requirements.txt     ✅
```

---

## 🎯 Before First Pipeline Run

### 1. Configure GitHub Secrets

Go to: **Repository → Settings → Secrets and variables → Actions**

Click **"New repository secret"** and add:

```
Name:  AWS_ACCESS_KEY_ID
Value: your-aws-access-key

Name:  AWS_SECRET_ACCESS_KEY
Value: your-aws-secret-key

Name:  STAGING_API_ENDPOINT
Value: https://staging.your-domain.com

Name:  SLACK_WEBHOOK (optional)
Value: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 2. Create GitHub Environments

Go to: **Repository → Settings → Environments**

Create two environments:
- **staging** (auto-deploy)
- **production** (require reviewers)

---

## 🧪 Test Locally Before Pushing

```bash
# 1. Test linting
cd services/data-ingestion
pip install flake8
flake8 . --count --select=E9,F63,F7,F82

# 2. Test unit tests
pip install pytest pytest-cov
pytest tests/ --cov=.

# 3. Build Docker image
docker build -t test-image .

# 4. Test integration tests
cd ../../tests/integration
pip install -r requirements.txt
export API_ENDPOINT="http://localhost:8001"
pytest test_services.py -v

# 5. Test load tests
cd ../performance
pip install -r requirements.txt
locust -f locustfile.py --headless -u 10 -r 2 --run-time 30s --host http://localhost:8001
```

---

## 📊 Pipeline Triggers

| Branch    | On Push | On PR | Deploys To |
|-----------|---------|-------|------------|
| `develop` | ✅ Yes  | ➖ No | Staging    |
| `main`    | ✅ Yes  | ➖ No | Production |
| `feature/*` | ➖ No | ✅ Yes | None (tests only) |

---

## 🔄 Typical Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-feature develop

# 2. Make changes
# ... edit code ...

# 3. Test locally
pytest tests/
docker build -t test .

# 4. Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature

# 5. Create Pull Request
# GitHub Actions will run tests automatically

# 6. Merge to develop (after approval)
# Pipeline deploys to staging automatically

# 7. Test in staging
# Verify everything works

# 8. Merge develop to main
# Pipeline deploys to production (requires approval)
```

---

## 🔍 Monitor Pipeline

### View Pipeline Runs
```
Repository → Actions → Select workflow run
```

### Check Logs
```
Click on any job → View detailed logs
```

### View Security Alerts
```
Repository → Security → Code scanning alerts
```

---

## 🐛 Common Issues

### Build fails: "requirements.txt not found"
```bash
# Ensure service has requirements.txt
cd services/your-service
touch requirements.txt
```

### Deploy fails: "cluster not found"
```bash
# Check AWS credentials secret names match:
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

### Tests fail: "connection refused"
```bash
# Ensure API_ENDPOINT is correct
export API_ENDPOINT="http://your-staging-api.com"
pytest tests/integration/
```

---

## 📚 Full Documentation

For complete details, see: **CI_CD_CONFIGURATION.md**

---

## ✅ Checklist

- [ ] Configure AWS secrets in GitHub
- [ ] Create staging environment
- [ ] Create production environment (with required reviewers)
- [ ] Test pipeline locally
- [ ] Push to develop branch to test staging deployment
- [ ] Verify staging deployment works
- [ ] Merge to main for production

---

**Your CI/CD pipeline is ready! Push to trigger it.** 🚀
