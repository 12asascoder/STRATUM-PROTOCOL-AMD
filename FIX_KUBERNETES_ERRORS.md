# 🔧 FIXING KUBERNETES DEPLOYMENT ERRORS

## 🚨 Problems Identified

Based on `kubectl get pods -n stratum-protocol -w`, you have:

1. **❌ ImagePullBackOff** (Frontend) - Docker images don't exist
2. **❌ CreateContainerConfigError** (MongoDB, Neo4j) - Missing secret keys
3. **❌ Pending** (Multiple services) - Insufficient memory
4. **❌ CrashLoopBackOff** (Frontend) - Container failing to start

## 📊 Error Summary

```
Frontend:        ImagePullBackOff → Image "ghcr.io/stratum-protocol/frontend:latest" not found
MongoDB:         CreateContainerConfigError → Missing MONGO_PASSWORD in secrets
Neo4j:           CreateContainerConfigError → Missing NEO4J_AUTH in secrets
Cascading-Failure: Pending → Insufficient memory
Knowledge-Graph: Pending → Insufficient memory
Postgres:        Pending → Insufficient memory
Kafka:           Pending → Insufficient memory
```

---

## ✅ SOLUTION: Use Infrastructure-Only Mode (RECOMMENDED)

**Why?** Your local Kubernetes cluster doesn't have enough resources to run everything. The infrastructure services (Postgres, Neo4j, Redis, etc.) are already running perfectly in Docker Compose!

### Option A: Use Docker Compose Instead (FASTEST)

You already have everything running! Just clean up the failed K8s deployment:

```bash
# 1. Delete the failed Kubernetes deployment
kubectl delete namespace stratum-protocol

# 2. Verify infrastructure is still running
docker-compose -f infrastructure/docker-compose.yml ps

# 3. All services are accessible:
echo "✅ PostgreSQL:   localhost:5432"
echo "✅ Neo4j:        http://localhost:7474"
echo "✅ Redis:        localhost:6380"
echo "✅ MongoDB:      localhost:27017"
echo "✅ Grafana:      http://localhost:3001"
echo "✅ Prometheus:   http://localhost:9090"

# 4. Access monitoring dashboards
open http://localhost:3001  # Grafana (admin/admin)
open http://localhost:7474  # Neo4j Browser
open http://localhost:9090  # Prometheus
```

**This is the BEST option for local development!** ✨

---

## Option B: Fix K8s Deployment (If You Really Want K8s)

### Step 1: Clean Up Failed Deployment

```bash
# Delete everything
kubectl delete namespace stratum-protocol --force --grace-period=0

# Wait for cleanup
kubectl get pods -n stratum-protocol 2>&1 | grep -q "NotFound" && echo "✅ Cleaned up"
```

### Step 2: Fix .env File

```bash
# Add missing MongoDB password
cat >> .env << 'EOF'

# MongoDB Configuration
MONGODB_PASSWORD=stratum_dev_mongo_pass
MONGO_PASSWORD=stratum_dev_mongo_pass

# Redis Configuration  
REDIS_PASSWORD=stratum_dev

# Kafka Configuration
KAFKA_PASSWORD=stratum_dev
EOF

# Verify
grep -E "MONGODB_PASSWORD|MONGO_PASSWORD" .env
```

### Step 3: Recreate Secrets

```bash
# Delete old secret
kubectl delete secret stratum-secrets -n stratum-protocol 2>/dev/null || true

# Create namespace
kubectl create namespace stratum-protocol

# Create new secret with updated .env
kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol

# Verify secret has all keys
kubectl describe secret stratum-secrets -n stratum-protocol | grep -E "MONGO|MONGODB"
```

### Step 4: Build Docker Images Locally

**This is critical** - The images don't exist yet!

```bash
# Build all service images
cd services

# Build data-ingestion
docker build -t stratum-protocol/data-ingestion:local ./data-ingestion

# Build knowledge-graph
docker build -t stratum-protocol/knowledge-graph:local ./knowledge-graph

# Build cascading-failure
docker build -t stratum-protocol/cascading-failure:local ./cascading-failure

# Build state-estimation
docker build -t stratum-protocol/state-estimation:local ./state-estimation

# Build frontend
cd ../frontend
docker build -t stratum-protocol/frontend:local .

# Verify images
docker images | grep stratum-protocol
```

### Step 5: Update K8s Manifests to Use Local Images

The manifests need `imagePullPolicy: Never` to use local images:

```bash
# Update all deployments to use local images
find k8s/ -name "*.yaml" -type f -exec sed -i '' 's/imagePullPolicy: Always/imagePullPolicy: Never/g' {} \;
find k8s/ -name "*.yaml" -type f -exec sed -i '' 's|image: ghcr.io/.*|image: stratum-protocol/frontend:local|g' {} \;
```

### Step 6: Reduce Resource Requirements

Your Mac doesn't have enough RAM for everything. Edit resource limits:

```bash
# Backup original files
cp -r k8s k8s-backup

# Reduce memory requests (edit these files manually)
# k8s/databases/postgres.yaml
# k8s/databases/mongodb.yaml
# k8s/databases/neo4j.yaml
# k8s/services/knowledge-graph.yaml
# k8s/services/cascading-failure.yaml

# Change from:
#   resources:
#     requests:
#       memory: "2Gi"
#       cpu: "1000m"
# To:
#   resources:
#     requests:
#       memory: "512Mi"
#       cpu: "250m"
```

### Step 7: Deploy Only Essential Services

Don't deploy everything - just core services:

```bash
# Create namespace and secrets
kubectl create namespace stratum-protocol
kubectl create secret generic stratum-secrets --from-env-file=.env -n stratum-protocol

# Deploy ONLY these (one at a time)
kubectl apply -f k8s/databases/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n stratum-protocol --timeout=120s

kubectl apply -f k8s/databases/redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n stratum-protocol --timeout=120s

kubectl apply -f k8s/services/data-ingestion.yaml
kubectl wait --for=condition=ready pod -l app=data-ingestion -n stratum-protocol --timeout=120s

# Check status
kubectl get pods -n stratum-protocol
```

---

## Option C: Minimal K8s + Docker Compose Hybrid (COMPROMISE)

Use Docker Compose for databases, Kubernetes only for services:

### Step 1: Keep Infrastructure in Docker Compose

```bash
# Infrastructure stays in Docker Compose (already running!)
docker-compose -f infrastructure/docker-compose.yml ps
```

### Step 2: Deploy Only Microservices to K8s

```bash
# Create namespace
kubectl create namespace stratum-protocol

# Create secrets
kubectl create secret generic stratum-secrets --from-env-file=.env -n stratum-protocol

# Deploy ONLY services (not databases)
kubectl apply -f k8s/services/data-ingestion.yaml
kubectl apply -f k8s/services/knowledge-graph.yaml

# Check status
kubectl get pods -n stratum-protocol
```

### Step 3: Update Services to Use Host Network

Services need to connect to Docker Compose databases on `host.docker.internal`:

```bash
# Update service manifests to use host.docker.internal for DB connections
# This connects K8s pods to Docker Compose databases

# Example for data-ingestion:
kubectl set env deployment/data-ingestion \
  -n stratum-protocol \
  DATABASE_URL="postgresql://stratum:stratum_dev@host.docker.internal:5432/stratum_protocol"
```

---

## 🎯 RECOMMENDED SOLUTION (Choose One)

### For Learning & Testing → **Option A** (Docker Compose Only)
✅ Already working  
✅ Full monitoring stack  
✅ All databases accessible  
✅ Zero configuration needed  
✅ Lowest resource usage  

**Action:** `kubectl delete namespace stratum-protocol` and use what you have!

### For K8s Experience → **Option B** (Full K8s Fix)
⚠️ Requires building all images  
⚠️ Requires reducing resource limits  
⚠️ Will be slow on local machine  
⚠️ 32GB RAM recommended  

**Action:** Follow Step 1-7 above

### For Real Development → **Option C** (Hybrid)
✅ Best of both worlds  
✅ Fast databases (Docker)  
✅ K8s for services only  
✅ Easier debugging  

**Action:** Follow Option C steps

---

## 🔍 Debugging Commands

### Check Pod Status
```bash
kubectl get pods -n stratum-protocol -o wide
```

### Check Pod Logs
```bash
kubectl logs -n stratum-protocol <pod-name>
kubectl logs -n stratum-protocol <pod-name> --previous  # Previous crash
```

### Describe Pod (Get Events)
```bash
kubectl describe pod -n stratum-protocol <pod-name>
```

### Check Secrets
```bash
kubectl get secret stratum-secrets -n stratum-protocol -o yaml
```

### Check Node Resources
```bash
kubectl top nodes
kubectl describe node docker-desktop
```

### Force Delete Stuck Pods
```bash
kubectl delete pod <pod-name> -n stratum-protocol --force --grace-period=0
```

---

## 📊 Current System Status

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT STATUS                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ Docker Compose Infrastructure:                          │
│     - PostgreSQL      → localhost:5432  ✅ RUNNING         │
│     - TimescaleDB     → localhost:5433  ✅ RUNNING         │
│     - Neo4j           → localhost:7474  ✅ RUNNING         │
│     - Redis           → localhost:6380  ✅ RUNNING         │
│     - MongoDB         → localhost:27017 ✅ RUNNING         │
│     - Kafka           → localhost:9092  ✅ RUNNING         │
│     - Prometheus      → localhost:9090  ✅ RUNNING         │
│     - Grafana         → localhost:3001  ✅ RUNNING         │
│     - Jaeger          → localhost:16686 ✅ RUNNING         │
│     - Kibana          → localhost:5601  ✅ RUNNING         │
│                                                              │
│  ❌ Kubernetes Services:                                    │
│     - Frontend        → ImagePullBackOff                    │
│     - MongoDB         → CreateContainerConfigError          │
│     - Neo4j           → CreateContainerConfigError          │
│     - Postgres        → Pending (insufficient memory)       │
│     - Knowledge-Graph → Pending (insufficient memory)       │
│     - Cascading-Fail  → Pending (insufficient memory)       │
│                                                              │
│  ✅ Redis             → Running in K8s                      │
│  ✅ Zookeeper         → Running in K8s                      │
│  ✅ Grafana           → Running in K8s                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 💡 Quick Fix Script

Save this as `fix-k8s.sh`:

```bash
#!/bin/bash

echo "🔧 STRATUM PROTOCOL - K8s Error Fix"
echo "===================================="
echo ""

# Option 1: Clean K8s and use Docker Compose
echo "Option 1: Use Docker Compose (RECOMMENDED)"
echo "   kubectl delete namespace stratum-protocol"
echo "   docker-compose -f infrastructure/docker-compose.yml ps"
echo ""

# Option 2: Fix K8s
echo "Option 2: Fix Kubernetes deployment"
echo "   1. Add MONGODB_PASSWORD to .env"
echo "   2. Recreate secrets"
echo "   3. Build Docker images locally"
echo "   4. Reduce resource limits"
echo "   5. Deploy incrementally"
echo ""

read -p "Choose option (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo "✅ Cleaning up Kubernetes..."
    kubectl delete namespace stratum-protocol --force --grace-period=0
    
    echo ""
    echo "✅ Checking Docker Compose infrastructure..."
    docker-compose -f infrastructure/docker-compose.yml ps
    
    echo ""
    echo "🎉 Done! All services running in Docker Compose:"
    echo "   Grafana:    http://localhost:3001"
    echo "   Prometheus: http://localhost:9090"
    echo "   Neo4j:      http://localhost:7474"
    echo "   Jaeger:     http://localhost:16686"
    
elif [ "$choice" = "2" ]; then
    echo "⚠️  This will take 10-15 minutes and require:"
    echo "   - Building 5+ Docker images"
    echo "   - 16GB+ RAM available"
    echo "   - Manual file editing"
    echo ""
    read -p "Continue? (y/n): " confirm
    
    if [ "$confirm" = "y" ]; then
        echo "📝 Step 1: Update .env file..."
        echo "MONGODB_PASSWORD=stratum_dev" >> .env
        echo "MONGO_PASSWORD=stratum_dev" >> .env
        
        echo "📝 Step 2: Cleanup..."
        kubectl delete namespace stratum-protocol --force --grace-period=0 2>/dev/null || true
        sleep 5
        
        echo "📝 Step 3: Recreate namespace and secrets..."
        kubectl create namespace stratum-protocol
        kubectl create secret generic stratum-secrets --from-env-file=.env -n stratum-protocol
        
        echo ""
        echo "⚠️  Manual steps required:"
        echo "   1. Build images: cd services && docker build -t stratum-protocol/data-ingestion:local ./data-ingestion"
        echo "   2. Edit k8s manifests to reduce memory requests"
        echo "   3. Deploy incrementally: kubectl apply -f k8s/databases/postgres.yaml"
        echo ""
        echo "See FIX_KUBERNETES_ERRORS.md for complete instructions"
    fi
fi
```

```bash
chmod +x fix-k8s.sh
./fix-k8s.sh
```

---

## 🎯 MY RECOMMENDATION

**Delete the K8s deployment and stick with Docker Compose:**

```bash
# Clean up failed K8s deployment
kubectl delete namespace stratum-protocol

# Check your working infrastructure
./check-health.sh

# Access your services
open http://localhost:3001  # Grafana
open http://localhost:7474  # Neo4j
open http://localhost:9090  # Prometheus
```

**Why?**
- ✅ Everything already works in Docker Compose
- ✅ Full monitoring stack operational
- ✅ All databases healthy and accessible
- ✅ Lower resource usage
- ✅ Easier development workflow
- ✅ Faster iteration

**You can develop and test everything without Kubernetes!**

When you need K8s later (for production deployment), you'll deploy to a real cloud cluster (AWS EKS, Azure AKS) with proper resources, not your local Mac.

---

## 📚 Related Documentation

- `LOCAL_DEVELOPMENT_GUIDE.md` - Full local setup options
- `TROUBLESHOOTING.md` - Common errors and solutions
- `check-health.sh` - System health checker

---

**Choose Option A (Docker Compose Only) unless you specifically need Kubernetes experience.**
