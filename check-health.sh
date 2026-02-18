#!/bin/bash

# STRATUM PROTOCOL - Local System Health Check
# Usage: ./check-health.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     STRATUM PROTOCOL - System Health Check                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
check_docker() {
    if docker info >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Docker is NOT running${NC}"
        echo "   👉 Start Docker Desktop: open /Applications/Docker.app"
        return 1
    fi
}

check_kubernetes() {
    if kubectl cluster-info >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Kubernetes is enabled and running${NC}"
        KUBE_VERSION=$(kubectl version --short 2>/dev/null | grep Server | awk '{print $3}')
        echo "   Version: ${KUBE_VERSION}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Kubernetes is NOT enabled${NC}"
        echo "   👉 See ENABLE_KUBERNETES.md for setup instructions"
        return 1
    fi
}

check_infrastructure() {
    local running=$(docker ps --filter "name=stratum-" --format "{{.Names}}" | wc -l | tr -d ' ')
    local total=15
    
    if [ "$running" -ge "$total" ]; then
        echo -e "${GREEN}✅ Infrastructure services: ${running}/${total} running${NC}"
        return 0
    elif [ "$running" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Infrastructure services: ${running}/${total} running${NC}"
        echo "   Some services are down. Check logs with:"
        echo "   docker-compose -f infrastructure/docker-compose.yml logs"
        return 1
    else
        echo -e "${RED}❌ Infrastructure services: 0/${total} running${NC}"
        echo "   👉 Start services: docker-compose -f infrastructure/docker-compose.yml up -d"
        return 1
    fi
}

check_database() {
    local db_name=$1
    local check_cmd=$2
    
    if eval "$check_cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ ${db_name}${NC}"
    else
        echo -e "${RED}  ❌ ${db_name}${NC}"
    fi
}

check_service_url() {
    local service_name=$1
    local url=$2
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -qE "^(200|301|302)"; then
        echo -e "${GREEN}  ✅ ${service_name}: ${url}${NC}"
    else
        echo -e "${RED}  ❌ ${service_name}: ${url} (not responding)${NC}"
    fi
}

# Start checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 Docker Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_docker
DOCKER_OK=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "☸️  Kubernetes Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_kubernetes
KUBE_OK=$?

if [ $DOCKER_OK -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Infrastructure Services"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    check_infrastructure
    
    echo ""
    echo "🗄️  Database Health:"
    check_database "PostgreSQL" "docker exec stratum-postgres pg_isready -U stratum"
    check_database "TimescaleDB" "docker exec stratum-timescaledb pg_isready -U stratum"
    check_database "Neo4j" "curl -s -u neo4j:stratum_dev http://localhost:7474/db/data/"
    check_database "Redis" "docker exec stratum-redis redis-cli -a stratum_dev PING 2>/dev/null | grep -q PONG"
    check_database "MongoDB" "docker exec stratum-mongodb mongosh --quiet --eval 'db.adminCommand({ping:1})' 2>/dev/null | grep -q ok"
    check_database "Kafka" "docker exec stratum-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null | grep -q ApiVersion"
    
    echo ""
    echo "📊 Monitoring Services:"
    check_service_url "Grafana" "http://localhost:3001"
    check_service_url "Prometheus" "http://localhost:9090"
    check_service_url "Jaeger" "http://localhost:16686"
    check_service_url "Kibana" "http://localhost:5601"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Container Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker ps --filter "name=stratum-" --format "table {{.Names}}\t{{.Status}}" | grep -E "stratum-|NAMES"
fi

if [ $KUBE_OK -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Kubernetes Pods"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if kubectl get namespace stratum-protocol >/dev/null 2>&1; then
        kubectl get pods -n stratum-protocol 2>/dev/null || echo "No pods found"
    else
        echo -e "${YELLOW}⚠️  Namespace 'stratum-protocol' not created yet${NC}"
        echo "   👉 Create: kubectl create namespace stratum-protocol"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Configuration Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
else
    echo -e "${RED}❌ .env file missing${NC}"
    echo "   👉 Create: cp .env.example .env"
fi

if [ -f "infrastructure/docker-compose.yml" ]; then
    echo -e "${GREEN}✅ docker-compose.yml exists${NC}"
else
    echo -e "${RED}❌ docker-compose.yml missing${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Access URLs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Monitoring & Observability:"
echo "   Grafana:        http://localhost:3001     (admin / admin)"
echo "   Prometheus:     http://localhost:9090"
echo "   Jaeger:         http://localhost:16686"
echo "   Kibana:         http://localhost:5601"
echo "   Ray Dashboard:  http://localhost:8265"
echo ""
echo "🗄️  Databases:"
echo "   Neo4j Browser:  http://localhost:7474     (neo4j / stratum_dev)"
echo "   PostgreSQL:     localhost:5432            (stratum / stratum_dev)"
echo "   TimescaleDB:    localhost:5433            (stratum / stratum_dev)"
echo "   Redis:          localhost:6380            (password: stratum_dev)"
echo "   MongoDB:        localhost:27017           (stratum / stratum_dev)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Quick Actions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $DOCKER_OK -ne 0 ]; then
    echo "🔴 Start Docker Desktop:"
    echo "   open /Applications/Docker.app"
    echo ""
fi

if [ $KUBE_OK -ne 0 ]; then
    echo "🟡 Enable Kubernetes:"
    echo "   See ENABLE_KUBERNETES.md for step-by-step guide"
    echo ""
fi

echo "📦 Infrastructure commands:"
echo "   Start:   docker-compose -f infrastructure/docker-compose.yml up -d"
echo "   Stop:    docker-compose -f infrastructure/docker-compose.yml down"
echo "   Logs:    docker-compose -f infrastructure/docker-compose.yml logs -f"
echo "   Restart: docker-compose -f infrastructure/docker-compose.yml restart"
echo ""

if [ $KUBE_OK -eq 0 ]; then
    echo "☸️  Kubernetes commands:"
    echo "   Deploy:  ./scripts/deploy.sh production"
    echo "   Pods:    kubectl get pods -n stratum-protocol"
    echo "   Logs:    kubectl logs -f <pod-name> -n stratum-protocol"
    echo ""
fi

echo "📚 Documentation:"
echo "   Local Dev Guide:    LOCAL_DEVELOPMENT_GUIDE.md"
echo "   Troubleshooting:    TROUBLESHOOTING.md"
echo "   Quick Start:        QUICKSTART.md"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Summary
if [ $DOCKER_OK -eq 0 ] && docker ps --filter "name=stratum-" | grep -q stratum-postgres; then
    echo -e "${GREEN}✅ SYSTEM READY FOR LOCAL DEVELOPMENT${NC}"
    echo ""
    echo "👉 Next steps:"
    echo "   1. Check LOCAL_DEVELOPMENT_GUIDE.md"
    echo "   2. Choose development option (1, 2, or 3)"
    echo "   3. Start coding!"
else
    echo -e "${YELLOW}⚠️  SYSTEM NEEDS SETUP${NC}"
    echo ""
    echo "👉 Follow these steps:"
    echo "   1. Ensure Docker Desktop is running"
    echo "   2. Start infrastructure: docker-compose -f infrastructure/docker-compose.yml up -d"
    echo "   3. Run this script again to verify"
fi

echo ""
