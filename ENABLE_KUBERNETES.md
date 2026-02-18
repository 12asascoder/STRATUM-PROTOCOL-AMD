# 🚨 KUBERNETES NOT ENABLED - ACTION REQUIRED

## ❌ Current Issue

You're seeing this error:
```
The connection to the server localhost:8080 was refused - did you specify the right host or port?
```

**Root Cause:** Kubernetes is not enabled in Docker Desktop.

---

## ✅ Solution: Enable Kubernetes (3 minutes)

### Step-by-Step Instructions:

#### 1. Open Docker Desktop
- Look for the Docker icon in your menu bar (top right of screen)
- Click it and select "Dashboard" or just open the Docker Desktop app

#### 2. Open Settings
- Click the **Settings** icon (⚙️) in the top right corner of Docker Desktop

#### 3. Navigate to Kubernetes
- In the left sidebar, click **"Kubernetes"**

#### 4. Enable Kubernetes
- Check the box: ☑️ **"Enable Kubernetes"**
- Optionally check: ☑️ **"Show system containers (advanced)"**

#### 5. Apply Changes
- Click the **"Apply & Restart"** button at the bottom
- Docker Desktop will restart (this is normal)

#### 6. Wait for Kubernetes to Start
- **Wait 2-3 minutes** for Kubernetes to initialize
- You'll see **"Kubernetes is running"** in green when ready
- The Kubernetes icon in Docker Desktop will turn green

#### 7. Verify Installation
```bash
kubectl cluster-info
```

**Expected output:**
```
Kubernetes control plane is running at https://kubernetes.docker.internal:6443
CoreDNS is running at https://kubernetes.docker.internal:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

---

## 🎯 After Kubernetes is Running

### Once you see "Kubernetes is running", run these commands:

```bash
# 1. Verify Kubernetes is working
kubectl cluster-info
kubectl get nodes

# 2. Create namespace
kubectl create namespace stratum-protocol

# 3. Create secrets (I've already created .env for you!)
kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol

# 4. Deploy all components
kubectl apply -f k8s/config/
kubectl apply -f k8s/databases/
kubectl apply -f k8s/services/
kubectl apply -f k8s/monitoring/
kubectl apply -f k8s/ingress/

# 5. Watch deployment progress
kubectl get pods -n stratum-protocol -w
```

### Or use the automated deployment script:

```bash
./scripts/deploy.sh production
```

---

## 🔍 Troubleshooting

### If Kubernetes fails to start:

1. **Check Docker Desktop has enough resources:**
   - Settings → Resources → Advanced
   - **Memory:** At least 4GB (8GB recommended)
   - **CPUs:** At least 2 (4 recommended)
   - **Disk:** At least 20GB free

2. **Restart Docker Desktop:**
   ```bash
   # Quit Docker Desktop completely
   # Then restart it from Applications
   ```

3. **Reset Kubernetes cluster:**
   - Settings → Kubernetes → Reset Kubernetes Cluster
   - Click "Reset" and wait for reinitialization

4. **Check Docker Desktop logs:**
   - Click the bug icon in Docker Desktop
   - View logs for any errors

---

## 📝 What I've Already Fixed

✅ **Created `.env` file** - Copied from `.env.example`  
✅ **Infrastructure running** - 15/15 services operational  
✅ **Configuration files** - All created and ready  
✅ **Documentation** - Complete guides available  

---

## 🎓 Why Kubernetes is Needed

**STRATUM PROTOCOL uses Kubernetes for:**
- **Orchestration:** Managing 8+ microservices
- **Scaling:** Auto-scaling based on load
- **Resilience:** Automatic recovery from failures
- **Networking:** Service discovery and load balancing
- **Configuration:** Managing secrets and configs
- **Monitoring:** Health checks and metrics collection

---

## 🚀 Alternative: Docker Compose Only (No Kubernetes)

If you want to test locally **without Kubernetes**, you can:

1. **Keep infrastructure running** (already done):
   ```bash
   docker-compose -f infrastructure/docker-compose.yml ps
   ```

2. **Run services manually** (each in a separate terminal):
   ```bash
   # Terminal 1 - Data Ingestion
   cd services/data-ingestion
   pip install -r requirements.txt
   python main.py
   
   # Terminal 2 - Knowledge Graph
   cd services/knowledge-graph
   pip install -r requirements.txt
   python main.py
   
   # ... and so on for all 8 services
   ```

3. **Run frontend**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

But **Kubernetes is much easier** - it handles everything automatically!

---

## 📚 Additional Resources

- **Quick Start Guide:** [QUICKSTART.md](QUICKSTART.md)
- **Troubleshooting Guide:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Infrastructure Status:** [INFRASTRUCTURE_STATUS.md](INFRASTRUCTURE_STATUS.md)
- **Error Resolution:** [ERROR_RESOLUTION_COMPLETE.md](ERROR_RESOLUTION_COMPLETE.md)

---

## ✅ Checklist

- [x] Docker Desktop installed and running
- [x] Infrastructure services running (15/15)
- [x] Configuration files created
- [x] `.env` file created
- [ ] **Kubernetes enabled** ← **YOU ARE HERE**
- [ ] Namespace and secrets created
- [ ] Microservices deployed
- [ ] Frontend accessible

---

**Next Step:** Enable Kubernetes in Docker Desktop Settings → Kubernetes → Enable

**Time Required:** 2-3 minutes for Kubernetes to start

**Help:** See [QUICKSTART.md](QUICKSTART.md) for detailed step-by-step guide with screenshots references.
