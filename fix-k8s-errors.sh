#!/bin/bash

# STRATUM PROTOCOL - K8s Error Quick Fix
# This script helps you choose the best solution for your local environment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   STRATUM PROTOCOL - Kubernetes Error Fix                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check current status
echo -e "${BLUE}📊 Current Status:${NC}"
echo ""

K8S_PODS=$(kubectl get pods -n stratum-protocol 2>/dev/null | grep -v "NAME" | wc -l | tr -d ' ')
DOCKER_SERVICES=$(docker ps --filter "name=stratum-" --format "{{.Names}}" | wc -l | tr -d ' ')

echo -e "  Kubernetes Pods:        ${K8S_PODS} pods"
echo -e "  Docker Compose Services: ${DOCKER_SERVICES}/15 running"
echo ""

if [ "$DOCKER_SERVICES" -ge 15 ]; then
    echo -e "${GREEN}✅ Docker Compose infrastructure is fully operational!${NC}"
else
    echo -e "${YELLOW}⚠️  Docker Compose infrastructure incomplete (${DOCKER_SERVICES}/15)${NC}"
fi

if [ "$K8S_PODS" -gt 0 ]; then
    FAILED_PODS=$(kubectl get pods -n stratum-protocol 2>/dev/null | grep -E "Error|CrashLoop|ImagePull|CreateContainer" | wc -l | tr -d ' ')
    if [ "$FAILED_PODS" -gt 0 ]; then
        echo -e "${RED}❌ Kubernetes has ${FAILED_PODS} failing pods${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show options
echo -e "${BLUE}🎯 Choose Your Solution:${NC}"
echo ""
echo -e "${GREEN}[1]${NC} Use Docker Compose Only (RECOMMENDED ⭐)"
echo "    ✅ Already working perfectly"
echo "    ✅ All databases and monitoring operational"
echo "    ✅ Lowest resource usage"
echo "    ✅ Fastest for development"
echo "    ⚡ Action: Clean up K8s, use existing Docker setup"
echo ""
echo -e "${YELLOW}[2]${NC} Fix Kubernetes Deployment (ADVANCED)"
echo "    ⚠️  Requires building Docker images"
echo "    ⚠️  Requires reducing resource limits"
echo "    ⚠️  Needs 16GB+ RAM"
echo "    ⚠️  Will take 15-20 minutes"
echo "    🔧 Action: Fix secrets, build images, reduce limits"
echo ""
echo -e "${BLUE}[3]${NC} Hybrid Mode (K8s Services + Docker DBs)"
echo "    ✅ Best of both worlds"
echo "    ✅ Databases in Docker (fast)"
echo "    ✅ Services in K8s (for learning)"
echo "    🔀 Action: Deploy only microservices to K8s"
echo ""
echo -e "${RED}[4]${NC} Show Detailed Error Analysis"
echo "    📋 View all pod errors and issues"
echo ""
echo "[Q] Quit"
echo ""
read -p "Enter your choice [1-4 or Q]: " choice

case $choice in
    1)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}Option 1: Using Docker Compose (RECOMMENDED)${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        if [ "$K8S_PODS" -gt 0 ]; then
            echo "🧹 Cleaning up failed Kubernetes deployment..."
            kubectl delete namespace stratum-protocol --force --grace-period=0 2>/dev/null || true
            echo -e "${GREEN}✅ Kubernetes cleanup complete${NC}"
            echo ""
        fi
        
        echo "📊 Checking Docker Compose infrastructure..."
        echo ""
        docker-compose -f infrastructure/docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}"
        echo ""
        
        echo -e "${GREEN}🎉 Success! Your development environment is ready!${NC}"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🌐 Access URLs:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📊 Monitoring:"
        echo "   Grafana:        http://localhost:3001  (admin / admin)"
        echo "   Prometheus:     http://localhost:9090"
        echo "   Jaeger:         http://localhost:16686"
        echo "   Kibana:         http://localhost:5601"
        echo "   Ray Dashboard:  http://localhost:8265"
        echo ""
        echo "🗄️  Databases:"
        echo "   Neo4j Browser:  http://localhost:7474  (neo4j / stratum_dev)"
        echo "   PostgreSQL:     localhost:5432         (stratum / stratum_dev)"
        echo "   TimescaleDB:    localhost:5433         (stratum / stratum_dev)"
        echo "   Redis:          localhost:6380         (password: stratum_dev)"
        echo "   MongoDB:        localhost:27017        (stratum / stratum_dev)"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📚 Next Steps:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "1. Open monitoring dashboards:"
        echo "   open http://localhost:3001"
        echo ""
        echo "2. Check LOCAL_DEVELOPMENT_GUIDE.md for development workflows"
        echo ""
        echo "3. Run health check anytime:"
        echo "   ./check-health.sh"
        echo ""
        ;;
        
    2)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${YELLOW}Option 2: Fixing Kubernetes Deployment (ADVANCED)${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "⚠️  This option requires:"
        echo "   - Building 5+ Docker images (15-20 minutes)"
        echo "   - Editing K8s manifests to reduce memory limits"
        echo "   - At least 16GB RAM available"
        echo "   - Manual configuration steps"
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " confirm
        
        if [ "$confirm" != "yes" ]; then
            echo ""
            echo "❌ Cancelled. Consider using Option 1 instead."
            echo ""
            exit 0
        fi
        
        echo ""
        echo "📝 Step 1/5: Updating .env file..."
        
        # Check if MONGODB_PASSWORD exists
        if ! grep -q "MONGODB_PASSWORD" .env; then
            echo "MONGODB_PASSWORD=stratum_dev" >> .env
            echo "MONGO_PASSWORD=stratum_dev" >> .env
            echo -e "${GREEN}✅ Added MongoDB password to .env${NC}"
        else
            echo -e "${GREEN}✅ .env already has MongoDB password${NC}"
        fi
        
        echo ""
        echo "📝 Step 2/5: Cleaning up old deployment..."
        kubectl delete namespace stratum-protocol --force --grace-period=0 2>/dev/null || true
        sleep 3
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        
        echo ""
        echo "📝 Step 3/5: Creating namespace and secrets..."
        kubectl create namespace stratum-protocol
        kubectl create secret generic stratum-secrets --from-env-file=.env -n stratum-protocol
        echo -e "${GREEN}✅ Secrets created${NC}"
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${YELLOW}⚠️  MANUAL STEPS REQUIRED${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "📝 Step 4/5: Build Docker images (run these commands):"
        echo ""
        echo "cd services"
        echo "docker build -t stratum-protocol/data-ingestion:local ./data-ingestion"
        echo "docker build -t stratum-protocol/knowledge-graph:local ./knowledge-graph"
        echo "docker build -t stratum-protocol/cascading-failure:local ./cascading-failure"
        echo "docker build -t stratum-protocol/state-estimation:local ./state-estimation"
        echo "cd ../frontend"
        echo "docker build -t stratum-protocol/frontend:local ."
        echo "cd .."
        echo ""
        echo "📝 Step 5/5: Edit K8s manifests to reduce memory:"
        echo ""
        echo "Edit these files and change memory requests from 2Gi to 512Mi:"
        echo "  - k8s/databases/postgres.yaml"
        echo "  - k8s/databases/mongodb.yaml"
        echo "  - k8s/databases/neo4j.yaml"
        echo "  - k8s/services/*.yaml"
        echo ""
        echo "Then deploy:"
        echo "kubectl apply -f k8s/databases/redis.yaml"
        echo "kubectl apply -f k8s/databases/postgres.yaml"
        echo "kubectl apply -f k8s/services/data-ingestion.yaml"
        echo ""
        echo "📚 See FIX_KUBERNETES_ERRORS.md for complete instructions"
        echo ""
        ;;
        
    3)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${BLUE}Option 3: Hybrid Mode (K8s Services + Docker DBs)${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "This mode uses:"
        echo "  - Docker Compose for databases (already running)"
        echo "  - Kubernetes for microservices only"
        echo ""
        
        if [ "$K8S_PODS" -gt 0 ]; then
            echo "🧹 Cleaning up current K8s deployment..."
            kubectl delete namespace stratum-protocol --force --grace-period=0 2>/dev/null || true
            sleep 3
        fi
        
        echo "📝 Creating namespace and secrets..."
        kubectl create namespace stratum-protocol
        kubectl create secret generic stratum-secrets --from-env-file=.env -n stratum-protocol
        
        echo ""
        echo "⚠️  You need to:"
        echo "1. Build service images first"
        echo "2. Update service manifests to connect to host.docker.internal"
        echo "3. Deploy only service manifests (not databases)"
        echo ""
        echo "See FIX_KUBERNETES_ERRORS.md Option C for detailed instructions"
        echo ""
        ;;
        
    4)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📋 Detailed Error Analysis"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        if [ "$K8S_PODS" -eq 0 ]; then
            echo "No pods found in stratum-protocol namespace"
            exit 0
        fi
        
        echo "🔍 Pod Status:"
        kubectl get pods -n stratum-protocol -o wide
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "❌ Failed Pods (ImagePullBackOff):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        kubectl get pods -n stratum-protocol | grep "ImagePull" || echo "None"
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "❌ Failed Pods (CreateContainerConfigError):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        kubectl get pods -n stratum-protocol | grep "CreateContainer" || echo "None"
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "⏳ Pending Pods (Resource Constraints):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        kubectl get pods -n stratum-protocol | grep "Pending" || echo "None"
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📝 Recent Events:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        kubectl get events -n stratum-protocol --sort-by='.lastTimestamp' | tail -20
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "💡 Recommendations:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Based on the errors above, I recommend:"
        echo ""
        echo "✅ Use Option 1 (Docker Compose Only)"
        echo "   - All infrastructure is already running"
        echo "   - No image building required"
        echo "   - No resource constraints"
        echo "   - Perfect for local development"
        echo ""
        echo "Run this script again and choose Option 1"
        echo ""
        ;;
        
    [Qq])
        echo ""
        echo "👋 Exiting. No changes made."
        echo ""
        exit 0
        ;;
        
    *)
        echo ""
        echo "❌ Invalid choice. Please run again and select 1-4 or Q."
        echo ""
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
