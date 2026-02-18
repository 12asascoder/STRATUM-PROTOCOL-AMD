# 🚀 LOCAL DEVELOPMENT GUIDE - STRATUM PROTOCOL

## Quick Status Check ✅

**Your Current System Status:**
```
✅ Docker Desktop: Running
✅ Infrastructure Services: 15/15 Running (Postgres, Neo4j, Kafka, Redis, etc.)
✅ .env Configuration: Present
❌ Kubernetes: NOT ENABLED (required for microservices)
```

## 🎯 Three Ways to Run Locally

### Option 1: Infrastructure Only (Current State) - **FASTEST FOR TESTING**

**What You Have NOW:** All backend infrastructure services running via Docker Compose.

**Access Points:**
```bash
# Databases
PostgreSQL:        localhost:5432  (user: stratum, pass: stratum_dev)
TimescaleDB:       localhost:5433  (user: stratum, pass: stratum_dev)
Neo4j Browser:     http://localhost:7474  (user: neo4j, pass: stratum_dev)
MongoDB:           localhost:27017  (user: stratum, pass: stratum_dev)
Redis:             localhost:6380  (password: stratum_dev)

# Monitoring & Observability
Grafana:           http://localhost:3001  (user: admin, pass: admin)
Prometheus:        http://localhost:9090
Jaeger UI:         http://localhost:16686
Kibana:            http://localhost:5601
Elasticsearch:     http://localhost:9200

# Message Queue
Kafka:             localhost:9092
Zookeeper:         localhost:2181

# ML Infrastructure
Ray Dashboard:     http://localhost:8265
MLflow:            http://localhost:5001

# API Gateway
Nginx:             http://localhost (port 80/443)
```

**How to Use This Setup:**
```bash
# 1. Check all services are healthy
docker ps --filter "name=stratum-" --format "table {{.Names}}\t{{.Status}}"

# 2. Test database connections
# PostgreSQL
docker exec -it stratum-postgres psql -U stratum -d stratum_protocol -c "SELECT version();"

# Neo4j
curl -u neo4j:stratum_dev http://localhost:7474/db/data/

# Redis
docker exec -it stratum-redis redis-cli -a stratum_dev PING

# 3. View logs
docker-compose -f infrastructure/docker-compose.yml logs -f <service-name>

# 4. Restart a service if needed
docker-compose -f infrastructure/docker-compose.yml restart <service-name>

# 5. Stop all infrastructure
docker-compose -f infrastructure/docker-compose.yml down

# 6. Start again
docker-compose -f infrastructure/docker-compose.yml up -d
```

---

### Option 2: Infrastructure + Local Python Services - **BEST FOR DEVELOPMENT**

**Use this when:** You want to develop/test individual microservices without Kubernetes complexity.

**Setup Steps:**

#### Step 1: Ensure Infrastructure is Running
```bash
docker-compose -f infrastructure/docker-compose.yml up -d
```

#### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install shared dependencies
pip install -e shared/auth/
pip install -e shared/messaging/
pip install -e shared/monitoring/
```

#### Step 3: Run Individual Services Locally

**Data Ingestion Service:**
```bash
cd services/data-ingestion
pip install -r requirements.txt
export DATABASE_URL="postgresql://stratum:stratum_dev@localhost:5432/stratum_protocol"
export REDIS_URL="redis://:stratum_dev@localhost:6380/0"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
uvicorn app.main:app --reload --port 8001
```

**Knowledge Graph Service:**
```bash
cd services/knowledge-graph
pip install -r requirements.txt
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="stratum_dev"
uvicorn app.main:app --reload --port 8002
```

**State Estimation Service:**
```bash
cd services/state-estimation
pip install -r requirements.txt
export REDIS_URL="redis://:stratum_dev@localhost:6380/0"
export TIMESCALEDB_URL="postgresql://stratum:stratum_dev@localhost:5433/stratum_timeseries"
uvicorn app.main:app --reload --port 8003
```

**Cascading Failure Service:**
```bash
cd services/cascading-failure
pip install -r requirements.txt
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="stratum_dev"
export RAY_ADDRESS="localhost:8265"
uvicorn app.main:app --reload --port 8004
```

**Test Services:**
```bash
# Data Ingestion
curl http://localhost:8001/health
curl http://localhost:8001/docs  # OpenAPI docs

# Knowledge Graph
curl http://localhost:8002/health
curl http://localhost:8002/docs

# State Estimation
curl http://localhost:8003/health
curl http://localhost:8003/docs

# Cascading Failure
curl http://localhost:8004/health
curl http://localhost:8004/docs
```

#### Step 4: Run Frontend Locally
```bash
cd frontend
npm install
npm start

# Access at http://localhost:3000
```

**Advantages:**
- ✅ Fast iteration (hot reload)
- ✅ Easy debugging (breakpoints, logs)
- ✅ No Kubernetes complexity
- ✅ Direct database access
- ✅ Real-time code changes

**Disadvantages:**
- ❌ Manual service startup
- ❌ No service mesh/networking
- ❌ Limited to ~4-5 services running simultaneously

---

### Option 3: Full Kubernetes Deployment - **PRODUCTION-LIKE**

**Use this when:** You want to test the complete production environment locally.

**Prerequisites:**
1. ✅ Docker Desktop running
2. ❌ **Kubernetes must be enabled** (see instructions below)

#### Enable Kubernetes in Docker Desktop

**Step-by-Step Instructions:**

1. **Open Docker Desktop**
   ```bash
   open /Applications/Docker.app
   ```

2. **Open Settings**
   - Click the **⚙️ (Settings/Preferences)** icon in Docker Desktop menu bar
   - Or click Docker icon → **Settings**

3. **Navigate to Kubernetes**
   - Click **Kubernetes** in left sidebar

4. **Enable Kubernetes**
   - Check ☑️ **Enable Kubernetes**
   - Check ☑️ **Show system containers (advanced)** (optional, for debugging)
   - Click **Apply & Restart**

5. **Wait for Initialization**
   - Status will show "Kubernetes is starting..."
   - Wait **2-3 minutes** for cluster to initialize
   - Green indicator means ready

6. **Verify Installation**
   ```bash
   kubectl cluster-info
   # Should show: "Kubernetes control plane is running at https://kubernetes.docker.internal:6443"
   
   kubectl get nodes
   # Should show: docker-desktop   Ready    control-plane   ...
   ```

#### Deploy Full System to Kubernetes

Once Kubernetes is enabled:

```bash
# 1. Create namespace
kubectl create namespace stratum-protocol

# 2. Create secrets
kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol

# 3. Deploy infrastructure config
kubectl apply -f k8s/config/ --namespace=stratum-protocol

# 4. Deploy databases
kubectl apply -f k8s/databases/ --namespace=stratum-protocol

# 5. Wait for databases (1-2 minutes)
kubectl get pods -n stratum-protocol -w

# 6. Deploy microservices
kubectl apply -f k8s/services/ --namespace=stratum-protocol

# 7. Deploy monitoring
kubectl apply -f k8s/monitoring/ --namespace=stratum-protocol

# 8. Deploy ingress/gateway
kubectl apply -f k8s/ingress/ --namespace=stratum-protocol

# 9. Wait for all pods to be Running
kubectl get pods -n stratum-protocol

# 10. Port forward frontend
kubectl port-forward svc/frontend 3000:3000 -n stratum-protocol

# 11. Access application
open http://localhost:3000
```

**Or use automated deployment script:**
```bash
./scripts/deploy.sh production
```

**Access Services:**
```bash
# Port forward any service
kubectl port-forward svc/data-ingestion 8001:8000 -n stratum-protocol
kubectl port-forward svc/knowledge-graph 8002:8000 -n stratum-protocol

# View logs
kubectl logs -f deployment/data-ingestion -n stratum-protocol

# View pod status
kubectl get pods -n stratum-protocol

# Describe pod for debugging
kubectl describe pod <pod-name> -n stratum-protocol

# Execute command in pod
kubectl exec -it <pod-name> -n stratum-protocol -- /bin/bash
```

**Advantages:**
- ✅ Production-like environment
- ✅ Service mesh networking
- ✅ Auto-scaling
- ✅ Health checks
- ✅ Complete monitoring stack

**Disadvantages:**
- ❌ Slower iteration (rebuild + redeploy)
- ❌ More complex debugging
- ❌ Higher resource usage
- ❌ Requires Kubernetes knowledge

---

## 🔍 Common Development Workflows

### Workflow 1: Database Schema Testing
```bash
# Use infrastructure only (Option 1)
docker-compose -f infrastructure/docker-compose.yml up -d postgres

# Connect and test
docker exec -it stratum-postgres psql -U stratum -d stratum_protocol

# Run migrations
python scripts/migrate.sh
```

### Workflow 2: API Development
```bash
# Use Option 2 (local Python services)
# Start infrastructure
docker-compose -f infrastructure/docker-compose.yml up -d

# Run one service
cd services/data-ingestion
source ../../venv/bin/activate
uvicorn app.main:app --reload --port 8001

# Test with curl/Postman
curl http://localhost:8001/docs
```

### Workflow 3: Integration Testing
```bash
# Use Option 2 or 3
# Run test suite
./scripts/test.sh

# Or specific tests
pytest services/data-ingestion/tests/
pytest tests/integration/
```

### Workflow 4: Frontend Development
```bash
# Infrastructure only
docker-compose -f infrastructure/docker-compose.yml up -d

# Run frontend with mock data
cd frontend
npm start

# Or with real backend (Option 2)
# Start backend services first, then frontend
```

---

## 🛠️ Development Tools & Tips

### VS Code Setup
```bash
# Recommended extensions
code --install-extension ms-python.python
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-kubernetes-tools.vscode-kubernetes-tools
code --install-extension esbenp.prettier-vscode
```

### Debug Configuration (.vscode/launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8001"],
      "cwd": "${workspaceFolder}/services/data-ingestion",
      "env": {
        "DATABASE_URL": "postgresql://stratum:stratum_dev@localhost:5432/stratum_protocol"
      }
    }
  ]
}
```

### Useful Aliases (add to ~/.zshrc)
```bash
# Docker shortcuts
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dlogs='docker-compose -f infrastructure/docker-compose.yml logs -f'
alias dup='docker-compose -f infrastructure/docker-compose.yml up -d'
alias ddown='docker-compose -f infrastructure/docker-compose.yml down'

# Kubernetes shortcuts
alias k='kubectl'
alias kgp='kubectl get pods -n stratum-protocol'
alias klogs='kubectl logs -f -n stratum-protocol'
alias kexec='kubectl exec -it -n stratum-protocol'
```

---

## 🐛 Troubleshooting

### Infrastructure Not Starting
```bash
# Check Docker
docker ps
docker-compose -f infrastructure/docker-compose.yml ps

# View logs
docker-compose -f infrastructure/docker-compose.yml logs <service-name>

# Restart specific service
docker-compose -f infrastructure/docker-compose.yml restart postgres

# Nuclear option: full restart
docker-compose -f infrastructure/docker-compose.yml down -v
docker-compose -f infrastructure/docker-compose.yml up -d
```

### Python Service Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Verify virtual environment
which python
pip list

# Check environment variables
env | grep DATABASE_URL

# Test database connection
python -c "import psycopg2; conn = psycopg2.connect('postgresql://stratum:stratum_dev@localhost:5432/stratum_protocol'); print('Connected!')"
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>

# Or change port
uvicorn app.main:app --reload --port 8099
```

### Kubernetes Pods Not Starting
```bash
# Check pod status
kubectl get pods -n stratum-protocol

# Describe pod
kubectl describe pod <pod-name> -n stratum-protocol

# View events
kubectl get events -n stratum-protocol --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n stratum-protocol

# Delete and recreate
kubectl delete pod <pod-name> -n stratum-protocol
```

---

## 📊 Monitoring Your Local Environment

### Health Check Script
```bash
#!/bin/bash
# Save as check-health.sh

echo "🔍 STRATUM PROTOCOL - System Health Check"
echo "=========================================="

echo ""
echo "📦 Docker Services:"
docker ps --filter "name=stratum-" --format "{{.Names}}: {{.Status}}" | sort

echo ""
echo "🗄️ Database Connectivity:"
echo -n "PostgreSQL: "
docker exec stratum-postgres pg_isready -U stratum && echo "✅" || echo "❌"

echo -n "Neo4j: "
curl -s -u neo4j:stratum_dev http://localhost:7474/db/data/ > /dev/null && echo "✅" || echo "❌"

echo -n "Redis: "
docker exec stratum-redis redis-cli -a stratum_dev PING 2>/dev/null | grep -q PONG && echo "✅" || echo "❌"

echo ""
echo "☸️  Kubernetes Status:"
kubectl cluster-info 2>/dev/null && echo "✅ Enabled" || echo "❌ Not Enabled"

if kubectl cluster-info 2>/dev/null; then
    echo ""
    echo "🚀 Kubernetes Pods:"
    kubectl get pods -n stratum-protocol 2>/dev/null || echo "Namespace not created yet"
fi

echo ""
echo "🌐 Access URLs:"
echo "Grafana:    http://localhost:3001"
echo "Prometheus: http://localhost:9090"
echo "Neo4j:      http://localhost:7474"
echo "Jaeger:     http://localhost:16686"
echo "Kibana:     http://localhost:5601"
```

```bash
# Make executable and run
chmod +x check-health.sh
./check-health.sh
```

---

## ⚡ Quick Reference

### Start/Stop Commands
```bash
# Start infrastructure only
docker-compose -f infrastructure/docker-compose.yml up -d

# Stop infrastructure
docker-compose -f infrastructure/docker-compose.yml down

# Start with logs
docker-compose -f infrastructure/docker-compose.yml up

# Restart everything
docker-compose -f infrastructure/docker-compose.yml restart

# Remove volumes (fresh start)
docker-compose -f infrastructure/docker-compose.yml down -v
```

### Service URLs (Current Running)
| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Neo4j Browser | http://localhost:7474 | neo4j / stratum_dev |
| Jaeger UI | http://localhost:16686 | - |
| Kibana | http://localhost:5601 | - |
| Ray Dashboard | http://localhost:8265 | - |

### Database Connections
| Database | Connection String |
|----------|-------------------|
| PostgreSQL | `postgresql://stratum:stratum_dev@localhost:5432/stratum_protocol` |
| TimescaleDB | `postgresql://stratum:stratum_dev@localhost:5433/stratum_timeseries` |
| Neo4j | `bolt://localhost:7687` (user: neo4j, pass: stratum_dev) |
| Redis | `redis://:stratum_dev@localhost:6380/0` |
| MongoDB | `mongodb://stratum:stratum_dev@localhost:27017/stratum_protocol` |

---

## 🎓 Learning Path

**New to the project?** Follow this order:

1. **Day 1:** Infrastructure only (Option 1)
   - Start Docker services
   - Explore Grafana dashboards
   - Connect to databases
   - Understand architecture

2. **Day 2-3:** Single service (Option 2)
   - Run data-ingestion service
   - Test API endpoints
   - Modify code and see changes
   - Write unit tests

3. **Day 4-5:** Multiple services (Option 2)
   - Run 2-3 interconnected services
   - Test service-to-service communication
   - Add new endpoints
   - Integration tests

4. **Week 2:** Full deployment (Option 3)
   - Enable Kubernetes
   - Deploy full system
   - End-to-end testing
   - Performance testing

---

## 📚 Additional Resources

- **Full Documentation:** [docs/](docs/)
- **API Specs:** [docs/api/](docs/api/)
- **Architecture:** [docs/architecture/](docs/architecture/)
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)
- **Kubernetes Setup:** [ENABLE_KUBERNETES.md](ENABLE_KUBERNETES.md)

---

## 🆘 Getting Help

**Priority Levels:**

🔴 **Critical:** Services won't start → Check TROUBLESHOOTING.md  
🟡 **Medium:** API errors → Check service logs  
🟢 **Low:** Configuration questions → Check .env.example  

**Debug Checklist:**
- [ ] Docker Desktop is running
- [ ] All infrastructure containers are healthy
- [ ] .env file exists with correct values
- [ ] Python virtual environment is activated
- [ ] Database connections work
- [ ] No port conflicts

---

**Choose your option and start developing! 🚀**

**Recommended for you right now:** **Option 1** or **Option 2** (since Kubernetes isn't enabled yet)
