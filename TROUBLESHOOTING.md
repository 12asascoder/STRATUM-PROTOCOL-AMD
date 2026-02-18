# 🔧 STRATUM PROTOCOL - Troubleshooting Guide

## ❌ Common Errors & Solutions

### Error 1: "Cannot connect to the Docker daemon"

**Symptom:**
```
Cannot connect to the Docker daemon at unix:///Users/arnav/.docker/run/docker.sock. 
Is the docker daemon running?
```

**Root Cause:** Docker Desktop is not running

**Solution:**
1. **Start Docker Desktop:**
   - Open **Docker Desktop** application from Applications folder
   - Wait for Docker icon in menu bar to show "Docker Desktop is running"
   - Verify with: `docker ps`

2. **If Docker Desktop is not installed:**
   ```bash
   # Install via Homebrew
   brew install --cask docker
   
   # Or download from: https://www.docker.com/products/docker-desktop
   ```

3. **Verify Docker is running:**
   ```bash
   docker version
   docker ps
   ```

---

### Error 2: "connection refused" to localhost:8080 (Kubernetes)

**Symptom:**
```
dial tcp [::1]:8080: connect: connection refused
```

**Root Cause:** No Kubernetes cluster is running

**Solution - Option A: Use Docker Desktop Kubernetes (Recommended for macOS)**

1. **Enable Kubernetes in Docker Desktop:**
   - Open Docker Desktop
   - Go to **Settings (⚙️)** → **Kubernetes**
   - Check ☑️ **Enable Kubernetes**
   - Click **Apply & Restart**
   - Wait 2-3 minutes for Kubernetes to start

2. **Verify Kubernetes is running:**
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

3. **Set context to docker-desktop:**
   ```bash
   kubectl config use-context docker-desktop
   ```

**Solution - Option B: Use Minikube**

1. **Install Minikube:**
   ```bash
   brew install minikube
   ```

2. **Start Minikube cluster:**
   ```bash
   # Start with recommended resources
   minikube start --cpus=4 --memory=8192 --disk-size=50g
   
   # Enable addons
   minikube addons enable ingress
   minikube addons enable metrics-server
   ```

3. **Verify cluster:**
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

**Solution - Option C: Use Kind (Kubernetes in Docker)**

1. **Install Kind:**
   ```bash
   brew install kind
   ```

2. **Create cluster:**
   ```bash
   kind create cluster --name stratum-protocol
   ```

3. **Verify:**
   ```bash
   kubectl cluster-info --context kind-stratum-protocol
   ```

---

### Error 3: "helm not found"

**Symptom:**
```
⚠️  helm not found. Continuing without Helm...
```

**Solution:**
```bash
# Install Helm
brew install helm

# Verify installation
helm version
```

---

### Error 4: Services not responding on ports 8001-8008

**Symptom:**
```
✗ Data Ingestion (port 8001) - Not responding
✗ Knowledge Graph (port 8002) - Not responding
```

**Root Cause:** Services are not running yet

**Solution:**

1. **First time setup - Start infrastructure only:**
   ```bash
   # Make sure Docker is running first!
   docker ps
   
   # Start databases and infrastructure
   docker-compose -f infrastructure/docker-compose.yml up -d
   
   # Wait 30 seconds for databases to initialize
   sleep 30
   
   # Check infrastructure is running
   docker-compose -f infrastructure/docker-compose.yml ps
   ```

2. **Start microservices individually:**
   ```bash
   # Install dependencies for each service
   cd services/data-ingestion
   pip install -r requirements.txt
   python main.py &
   
   cd ../knowledge-graph
   pip install -r requirements.txt
   python main.py &
   
   # ... repeat for other services
   ```

3. **Or use Kubernetes deployment (after cluster is running):**
   ```bash
   # Apply all manifests
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/config/
   kubectl apply -f k8s/databases/
   kubectl apply -f k8s/services/
   
   # Wait for pods to be ready
   kubectl wait --for=condition=ready pod --all -n stratum-protocol --timeout=300s
   
   # Check status
   kubectl get pods -n stratum-protocol
   ```

---

## 🚀 Complete Fresh Setup (macOS)

### Step 1: Install Prerequisites

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Install kubectl
brew install kubectl

# Install Helm (optional but recommended)
brew install helm

# Install Python 3.11
brew install python@3.11

# Install Node.js
brew install node@20
```

### Step 2: Start Docker Desktop

1. Open **Docker Desktop** from Applications
2. Wait for green indicator in menu bar
3. Go to **Settings** → **Kubernetes** → **Enable Kubernetes**
4. Click **Apply & Restart**
5. Wait 2-3 minutes

### Step 3: Verify Everything

```bash
# Check Docker
docker version
docker ps

# Check Kubernetes
kubectl cluster-info
kubectl get nodes

# Check Helm
helm version

# Check Python
python3.11 --version

# Check Node
node --version
```

### Step 4: Clone & Setup STRATUM PROTOCOL

```bash
# Clone repository (if not done)
git clone https://github.com/your-org/stratum-protocol.git
cd stratum-protocol

# Copy environment variables
cp .env.example .env

# Edit .env with your settings
nano .env
```

### Step 5: Start Infrastructure

```bash
# Start databases and supporting services
docker-compose -f infrastructure/docker-compose.yml up -d

# Wait 30 seconds for initialization
sleep 30

# Verify infrastructure
docker-compose -f infrastructure/docker-compose.yml ps
```

### Step 6: Deploy to Kubernetes

```bash
# Create namespace and secrets
kubectl apply -f k8s/namespace.yaml

kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol

# Deploy configuration
kubectl apply -f k8s/config/

# Deploy databases
kubectl apply -f k8s/databases/

# Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres -n stratum-protocol --timeout=300s

# Deploy microservices
kubectl apply -f k8s/services/

# Deploy ingress
kubectl apply -f k8s/ingress/

# Deploy monitoring
kubectl apply -f k8s/monitoring/
```

### Step 7: Verify Deployment

```bash
# Check all pods
kubectl get pods -n stratum-protocol

# Check services
kubectl get svc -n stratum-protocol

# Check ingress
kubectl get ingress -n stratum-protocol

# View logs for a service
kubectl logs -f deployment/data-ingestion -n stratum-protocol
```

### Step 8: Access the Platform

```bash
# Port forward frontend
kubectl port-forward svc/frontend 3000:3000 -n stratum-protocol

# Open browser
open http://localhost:3000

# Port forward Grafana
kubectl port-forward svc/grafana 3001:3000 -n stratum-protocol

# Open monitoring
open http://localhost:3001
```

---

## 🐛 Debugging Commands

### Check Docker

```bash
# List running containers
docker ps

# View container logs
docker logs <container-id>

# Inspect container
docker inspect <container-id>

# Restart Docker
killall Docker && open /Applications/Docker.app
```

### Check Kubernetes

```bash
# Get cluster info
kubectl cluster-info
kubectl get nodes
kubectl get namespaces

# Check pods
kubectl get pods -n stratum-protocol
kubectl describe pod <pod-name> -n stratum-protocol
kubectl logs <pod-name> -n stratum-protocol

# Check services
kubectl get svc -n stratum-protocol
kubectl describe svc <service-name> -n stratum-protocol

# Check events
kubectl get events -n stratum-protocol --sort-by='.lastTimestamp'

# Check resource usage
kubectl top nodes
kubectl top pods -n stratum-protocol
```

### Check Networking

```bash
# Test service connectivity
kubectl run curl-test --image=curlimages/curl:latest -n stratum-protocol --rm -it -- sh

# Inside the pod:
curl http://data-ingestion:8001/health
curl http://knowledge-graph:8002/health
exit

# Port forward to test locally
kubectl port-forward svc/data-ingestion 8001:8001 -n stratum-protocol
curl http://localhost:8001/health
```

### Check Resources

```bash
# View resource usage
kubectl top nodes
kubectl top pods -n stratum-protocol

# Check PersistentVolumeClaims
kubectl get pvc -n stratum-protocol

# Check PersistentVolumes
kubectl get pv
```

### Clean Up & Restart

```bash
# Delete all resources in namespace
kubectl delete namespace stratum-protocol

# Recreate namespace
kubectl create namespace stratum-protocol

# Redeploy everything
./scripts/deploy.sh production

# Or delete specific resources
kubectl delete deployment <name> -n stratum-protocol
kubectl delete service <name> -n stratum-protocol
kubectl delete pod <name> -n stratum-protocol
```

---

## 📊 Service Health Checks

### Manual Health Checks

```bash
# Data Ingestion
curl http://localhost:8001/health

# Knowledge Graph
curl http://localhost:8002/health

# Cascading Failure
curl http://localhost:8003/health

# State Estimation
curl http://localhost:8004/health

# Citizen Behavior
curl http://localhost:8005/health

# Policy Optimization
curl http://localhost:8006/health

# Economic Intelligence
curl http://localhost:8007/health

# Decision Ledger
curl http://localhost:8008/health
```

### Automated Health Checks

```bash
# Use the test script
./scripts/test.sh

# Or check manually
for port in {8001..8008}; do
  echo -n "Checking port $port: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health || echo "Failed"
done
```

---

## 🔍 Common Issues & Fixes

### Issue: Pods stuck in "Pending" state

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n stratum-protocol
```

**Common causes:**
- Insufficient resources (CPU/Memory)
- PersistentVolumeClaim not bound
- Image pull errors

**Fix:**
```bash
# Check node resources
kubectl top nodes

# Check PVC
kubectl get pvc -n stratum-protocol

# Scale down replicas temporarily
kubectl scale deployment <name> --replicas=1 -n stratum-protocol
```

### Issue: Pods in "CrashLoopBackOff"

**Diagnosis:**
```bash
kubectl logs <pod-name> -n stratum-protocol
kubectl describe pod <pod-name> -n stratum-protocol
```

**Common causes:**
- Application errors
- Missing environment variables
- Database connection failures

**Fix:**
```bash
# Check logs for errors
kubectl logs <pod-name> -n stratum-protocol --previous

# Verify secrets
kubectl get secrets -n stratum-protocol
kubectl describe secret stratum-secrets -n stratum-protocol

# Restart pod
kubectl delete pod <pod-name> -n stratum-protocol
```

### Issue: Services not accessible

**Diagnosis:**
```bash
kubectl get svc -n stratum-protocol
kubectl describe svc <service-name> -n stratum-protocol
```

**Fix:**
```bash
# Check if pods are running
kubectl get pods -l app=<service-name> -n stratum-protocol

# Port forward to test
kubectl port-forward svc/<service-name> <local-port>:<service-port> -n stratum-protocol

# Test connectivity
curl http://localhost:<local-port>/health
```

### Issue: Database connection errors

**Check databases are running:**
```bash
# PostgreSQL
kubectl exec -it <postgres-pod> -n stratum-protocol -- psql -U postgres -c "\l"

# Neo4j
kubectl exec -it <neo4j-pod> -n stratum-protocol -- cypher-shell -u neo4j -p <password> "MATCH (n) RETURN count(n);"

# MongoDB
kubectl exec -it <mongodb-pod> -n stratum-protocol -- mongosh --eval "db.adminCommand('ping')"

# Redis
kubectl exec -it <redis-pod> -n stratum-protocol -- redis-cli ping
```

---

## 📞 Getting Help

### Check logs
```bash
# Application logs
kubectl logs -f deployment/<service-name> -n stratum-protocol

# All logs in namespace
kubectl logs -n stratum-protocol --all-containers=true --tail=100

# Events
kubectl get events -n stratum-protocol --sort-by='.lastTimestamp'
```

### Export cluster state
```bash
# Export all resources for debugging
kubectl get all -n stratum-protocol -o yaml > cluster-state.yaml

# Export specific resource
kubectl get deployment <name> -n stratum-protocol -o yaml > deployment.yaml
```

### System information
```bash
# Kubernetes version
kubectl version

# Docker version
docker version

# OS information
uname -a
sw_vers  # macOS specific

# System resources
sysctl hw.memsize
sysctl hw.ncpu
```

---

## 🎯 Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| Start Docker | Open Docker Desktop app |
| Check Docker | `docker ps` |
| Start K8s | Enable in Docker Desktop Settings |
| Check K8s | `kubectl cluster-info` |
| Deploy all | `./scripts/deploy.sh production` |
| View pods | `kubectl get pods -n stratum-protocol` |
| View logs | `kubectl logs -f <pod-name> -n stratum-protocol` |
| Port forward | `kubectl port-forward svc/<name> <port>:<port> -n stratum-protocol` |
| Delete all | `kubectl delete namespace stratum-protocol` |
| Run tests | `./scripts/test.sh` |

### Port Reference

| Service | Port |
|---------|------|
| Data Ingestion | 8001 |
| Knowledge Graph | 8002 |
| Cascading Failure | 8003 |
| State Estimation | 8004 |
| Citizen Behavior | 8005 |
| Policy Optimization | 8006 |
| Economic Intelligence | 8007 |
| Decision Ledger | 8008 |
| Frontend | 3000 |
| PostgreSQL | 5432 |
| Neo4j HTTP | 7474 |
| Neo4j Bolt | 7687 |
| MongoDB | 27017 |
| Redis | 6379 |
| Kafka | 9092 |
| Prometheus | 9090 |
| Grafana | 3000 |

---

**Last Updated:** February 18, 2026  
**For more help:** See [README.md](README.md) or contact support
