# 🚀 STRATUM PROTOCOL - Quick Start Guide

## ⚡ 5-Minute Setup (macOS)

### Prerequisites Check

Before starting, ensure you have:
- ✅ **Docker Desktop** installed and running
- ✅ **Kubernetes** enabled in Docker Desktop
- ✅ **kubectl** installed
- ✅ **Python 3.11+** installed
- ✅ **8GB+ RAM** available

---

## Step 1: Start Docker Desktop (CRITICAL)

### 🔴 This is the MOST COMMON error!

1. **Open Docker Desktop application:**
   ```bash
   open /Applications/Docker.app
   ```

2. **Wait for Docker to start** (green indicator in menu bar)

3. **Verify Docker is running:**
   ```bash
   docker ps
   ```
   
   ✅ **Expected output:** Table of running containers (may be empty)  
   ❌ **If error:** Docker is not running - restart Docker Desktop

---

## Step 2: Enable Kubernetes

1. **Open Docker Desktop Settings (⚙️)**

2. **Go to: Kubernetes tab**

3. **Check:** ☑️ **Enable Kubernetes**

4. **Click:** **Apply & Restart**

5. **Wait 2-3 minutes** for Kubernetes to initialize

6. **Verify Kubernetes is running:**
   ```bash
   kubectl cluster-info
   ```
   
   ✅ **Expected output:** Cluster information with URLs  
   ❌ **If error:** Wait longer or restart Docker Desktop

---

## Step 3: Verify Environment

Run this single command to check everything:

```bash
echo "🔍 Checking prerequisites..." && \
docker version > /dev/null 2>&1 && echo "✅ Docker: OK" || echo "❌ Docker: NOT RUNNING - Start Docker Desktop!" && \
kubectl cluster-info > /dev/null 2>&1 && echo "✅ Kubernetes: OK" || echo "❌ Kubernetes: NOT RUNNING - Enable in Docker Desktop!" && \
python3 --version > /dev/null 2>&1 && echo "✅ Python: OK" || echo "❌ Python: NOT INSTALLED" && \
echo "✅ All checks complete!"
```

---

## Step 4: Setup STRATUM PROTOCOL

### A. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings (optional for local dev)
nano .env
```

### B. Start Infrastructure Services

```bash
# Start databases (PostgreSQL, Neo4j, MongoDB, Redis, Kafka)
docker-compose -f infrastructure/docker-compose.yml up -d

# Wait 30 seconds for databases to initialize
echo "⏳ Waiting 30 seconds for databases to start..."
sleep 30

# Verify infrastructure is running
docker-compose -f infrastructure/docker-compose.yml ps
```

✅ **Expected:** All services showing "Up" status  
❌ **If error:** Check Docker is running, then try again

---

## Step 5: Deploy to Kubernetes

### A. Create Namespace and Secrets

```bash
# Create namespace
kubectl create namespace stratum-protocol

# Create secrets from .env file
kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol

# Verify
kubectl get namespace stratum-protocol
kubectl get secrets -n stratum-protocol
```

### B. Deploy All Components

```bash
# Deploy in correct order
echo "📦 Deploying configuration..."
kubectl apply -f k8s/config/

echo "📦 Deploying databases..."
kubectl apply -f k8s/databases/

echo "⏳ Waiting for databases to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=ready pod -l app=postgres -n stratum-protocol --timeout=300s || echo "⏭️  Continuing..."

echo "📦 Deploying microservices..."
kubectl apply -f k8s/services/

echo "📦 Deploying monitoring..."
kubectl apply -f k8s/monitoring/

echo "📦 Deploying ingress..."
kubectl apply -f k8s/ingress/

echo "✅ Deployment complete!"
```

---

## Step 6: Verify Deployment

```bash
# Check all pods (may take 2-3 minutes to start)
kubectl get pods -n stratum-protocol

# Check services
kubectl get svc -n stratum-protocol

# Watch pods until they're all running (Ctrl+C to exit)
kubectl get pods -n stratum-protocol -w
```

**Wait until most pods show `Running` status**

---

## Step 7: Access the Platform

### A. Access Frontend

```bash
# Port forward frontend service
kubectl port-forward svc/frontend 3000:3000 -n stratum-protocol &

# Open in browser
open http://localhost:3000
```

### B. Access Monitoring (Grafana)

```bash
# Port forward Grafana
kubectl port-forward svc/grafana 3001:3000 -n stratum-protocol &

# Open in browser
open http://localhost:3001

# Default credentials:
# Username: admin
# Password: stratum-admin-123
```

### C. Access Individual Services

```bash
# Port forward any service (example: data-ingestion)
kubectl port-forward svc/data-ingestion 8001:8001 -n stratum-protocol &

# Test health endpoint
curl http://localhost:8001/health

# View API docs
open http://localhost:8001/docs
```

---

## Step 8: Run Tests

```bash
# First, port forward all services
for port in {8001..8008}; do
  kubectl port-forward svc/$(kubectl get svc -n stratum-protocol -o name | grep $port | cut -d/ -f2) $port:$port -n stratum-protocol &
done

# Wait a few seconds
sleep 5

# Run integration tests
./scripts/test.sh

# View test report
open test-reports/report_*.html
```

---

## 🎯 One-Command Setup (After Docker is Running)

If Docker Desktop and Kubernetes are already running, use this single command:

```bash
./scripts/deploy.sh production
```

This will:
- ✅ Check prerequisites
- ✅ Create namespace and secrets
- ✅ Deploy all components
- ✅ Wait for services to be ready
- ✅ Display access URLs

---

## 🔧 Troubleshooting

### Error: "Cannot connect to Docker daemon"

**Solution:** Start Docker Desktop application

```bash
open /Applications/Docker.app
# Wait for green indicator, then retry
```

---

### Error: "connection refused localhost:8080"

**Solution:** Enable Kubernetes in Docker Desktop

1. Open Docker Desktop Settings
2. Go to Kubernetes tab
3. Check "Enable Kubernetes"
4. Apply & Restart
5. Wait 2-3 minutes

---

### Error: "Pods in Pending or CrashLoopBackOff"

**Diagnosis:**
```bash
kubectl get pods -n stratum-protocol
kubectl describe pod <pod-name> -n stratum-protocol
kubectl logs <pod-name> -n stratum-protocol
```

**Common fixes:**
```bash
# Delete and recreate pod
kubectl delete pod <pod-name> -n stratum-protocol

# Or restart deployment
kubectl rollout restart deployment/<name> -n stratum-protocol

# Check if secrets exist
kubectl get secrets -n stratum-protocol
```

---

### Error: "Services not responding"

**Check if pods are running:**
```bash
kubectl get pods -n stratum-protocol
```

**Port forward and test:**
```bash
kubectl port-forward svc/data-ingestion 8001:8001 -n stratum-protocol &
curl http://localhost:8001/health
```

---

### Complete Clean Up and Restart

```bash
# Stop all port forwards
killall kubectl

# Delete everything
kubectl delete namespace stratum-protocol

# Stop Docker infrastructure
docker-compose -f infrastructure/docker-compose.yml down -v

# Start fresh
./scripts/deploy.sh production
```

---

## 📚 What's Next?

After successful deployment:

1. **Explore the Dashboard:** http://localhost:3000
2. **View Monitoring:** http://localhost:3001 (Grafana)
3. **Check API Docs:** http://localhost:8001/docs (any service)
4. **Run Simulations:** Use the frontend to trigger cascading failure simulations
5. **View Metrics:** Check Prometheus at http://localhost:9090

---

## 🎓 Common Tasks

### View Logs
```bash
# All logs in namespace
kubectl logs -n stratum-protocol --all-containers=true --tail=100

# Specific service
kubectl logs -f deployment/data-ingestion -n stratum-protocol

# Multiple services
kubectl logs -f -l app=data-ingestion -n stratum-protocol
```

### Scale Services
```bash
# Scale up
kubectl scale deployment data-ingestion --replicas=3 -n stratum-protocol

# Scale down
kubectl scale deployment data-ingestion --replicas=1 -n stratum-protocol

# Check scaling
kubectl get pods -n stratum-protocol -l app=data-ingestion
```

### Update Configuration
```bash
# Edit ConfigMap
kubectl edit configmap stratum-config -n stratum-protocol

# Restart affected services
kubectl rollout restart deployment/data-ingestion -n stratum-protocol
```

### Database Access
```bash
# PostgreSQL
kubectl exec -it <postgres-pod> -n stratum-protocol -- psql -U postgres

# Neo4j
kubectl exec -it <neo4j-pod> -n stratum-protocol -- cypher-shell -u neo4j -p stratum-neo4j-123

# MongoDB
kubectl exec -it <mongodb-pod> -n stratum-protocol -- mongosh

# Redis
kubectl exec -it <redis-pod> -n stratum-protocol -- redis-cli
```

---

## 🆘 Still Having Issues?

1. **Check full troubleshooting guide:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Verify system requirements:** 8GB RAM, 20GB disk space
3. **Restart Docker Desktop:** Sometimes a restart fixes everything
4. **Check logs:** `kubectl get events -n stratum-protocol --sort-by='.lastTimestamp'`

---

## ✅ Success Checklist

- [ ] Docker Desktop running (green indicator)
- [ ] Kubernetes enabled in Docker Desktop
- [ ] `kubectl cluster-info` returns cluster information
- [ ] Infrastructure services running (`docker ps` shows containers)
- [ ] Namespace created (`kubectl get namespace stratum-protocol`)
- [ ] Pods running (`kubectl get pods -n stratum-protocol`)
- [ ] Frontend accessible at http://localhost:3000
- [ ] Tests passing (`./scripts/test.sh`)

---

**Deployment Time:** ~10 minutes  
**First-time Setup:** ~15 minutes (including downloads)  

**Ready to build the future of urban intelligence! 🏙️**
