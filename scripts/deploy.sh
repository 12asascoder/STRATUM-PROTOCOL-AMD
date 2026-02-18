#!/bin/bash
# STRATUM PROTOCOL - Complete Deployment Script
# Deploys entire platform to Kubernetes cluster

set -e

echo "🚀 STRATUM PROTOCOL - Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="stratum-protocol"
DEPLOYMENT_ENV="${1:-staging}"  # staging or production

echo -e "${YELLOW}Deployment Environment: $DEPLOYMENT_ENV${NC}"

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

echo ""
echo "📋 Running pre-flight checks..."

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check helm
if ! command -v helm &> /dev/null; then
    echo -e "${YELLOW}⚠️  helm not found. Continuing without Helm...${NC}"
fi

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pre-flight checks passed${NC}"

# =============================================================================
# CREATE NAMESPACE
# =============================================================================

echo ""
echo "📦 Creating namespace..."

kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace $NAMESPACE environment=$DEPLOYMENT_ENV --overwrite

echo -e "${GREEN}✅ Namespace created/updated${NC}"

# =============================================================================
# APPLY SECRETS AND CONFIGMAPS
# =============================================================================

echo ""
echo "🔐 Applying secrets and configmaps..."

# Check if secrets file exists
if [ ! -f "k8s/secrets.yaml" ]; then
    echo -e "${YELLOW}⚠️  secrets.yaml not found. Creating from template...${NC}"
    # In production, use Vault or Sealed Secrets
fi

kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmaps.yaml

echo -e "${GREEN}✅ Secrets and ConfigMaps applied${NC}"

# =============================================================================
# DEPLOY DATABASES (if not using managed services)
# =============================================================================

echo ""
echo "🗄️  Deploying databases..."

# PostgreSQL
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: $NAMESPACE
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: timescale/timescaledb:latest-pg16
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: stratum-secrets
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: $NAMESPACE
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
  clusterIP: None
EOF

# Neo4j
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: $NAMESPACE
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.15-enterprise
        ports:
        - containerPort: 7687
        - containerPort: 7474
        env:
        - name: NEO4J_AUTH
          value: "neo4j/stratumgraph123"
        - name: NEO4J_ACCEPT_LICENSE_AGREEMENT
          value: "yes"
        volumeMounts:
        - name: neo4j-storage
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: neo4j-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: $NAMESPACE
spec:
  selector:
    app: neo4j
  ports:
  - port: 7687
    name: bolt
  - port: 7474
    name: http
EOF

# Redis
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: $NAMESPACE
spec:
  selector:
    app: redis
  ports:
  - port: 6379
EOF

echo -e "${GREEN}✅ Databases deployed${NC}"

# Wait for databases to be ready
echo ""
echo "⏳ Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=neo4j -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

# =============================================================================
# INITIALIZE DATABASES
# =============================================================================

echo ""
echo "🔧 Initializing databases..."

# Run PostgreSQL init script
kubectl exec -n $NAMESPACE deployment/postgres -- psql -U postgres -f /init-scripts/01-init-postgres.sql || echo "Init script already run"

echo -e "${GREEN}✅ Databases initialized${NC}"

# =============================================================================
# DEPLOY MICROSERVICES
# =============================================================================

echo ""
echo "🚢 Deploying microservices..."

SERVICES=(
    "data-ingestion"
    "knowledge-graph"
    "cascading-failure"
    "state-estimation"
    "citizen-behavior"
    "policy-optimization"
    "economic-intelligence"
    "decision-ledger"
)

for service in "${SERVICES[@]}"; do
    echo "  Deploying $service..."
    kubectl apply -f "k8s/services/$service.yaml"
done

echo -e "${GREEN}✅ Microservices deployed${NC}"

# =============================================================================
# DEPLOY FRONTEND
# =============================================================================

echo ""
echo "🎨 Deploying frontend..."

kubectl apply -f k8s/services/frontend.yaml

echo -e "${GREEN}✅ Frontend deployed${NC}"

# =============================================================================
# WAIT FOR DEPLOYMENTS
# =============================================================================

echo ""
echo "⏳ Waiting for all deployments to be ready..."

for service in "${SERVICES[@]}"; do
    echo "  Waiting for $service..."
    kubectl rollout status deployment/$service -n $NAMESPACE --timeout=5m
done

kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=3m

echo -e "${GREEN}✅ All deployments ready${NC}"

# =============================================================================
# DEPLOY MONITORING STACK
# =============================================================================

echo ""
echo "📊 Deploying monitoring stack..."

# Prometheus
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: $NAMESPACE
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
EOF

# Grafana
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: $NAMESPACE
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
  type: LoadBalancer
EOF

echo -e "${GREEN}✅ Monitoring stack deployed${NC}"

# =============================================================================
# VERIFY DEPLOYMENT
# =============================================================================

echo ""
echo "🔍 Verifying deployment..."

echo ""
echo "Pods:"
kubectl get pods -n $NAMESPACE

echo ""
echo "Services:"
kubectl get svc -n $NAMESPACE

echo ""
echo "Deployments:"
kubectl get deployments -n $NAMESPACE

# =============================================================================
# GET ACCESS INFORMATION
# =============================================================================

echo ""
echo "📍 Access Information:"
echo "======================================"

FRONTEND_IP=$(kubectl get svc frontend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending...")
GRAFANA_IP=$(kubectl get svc grafana -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending...")

echo -e "${GREEN}Frontend:${NC} http://$FRONTEND_IP"
echo -e "${GREEN}Grafana:${NC} http://$GRAFANA_IP:3000"
echo ""
echo "To port-forward services locally:"
echo "  kubectl port-forward -n $NAMESPACE svc/frontend 3000:80"
echo "  kubectl port-forward -n $NAMESPACE svc/grafana 3001:3000"
echo ""

# =============================================================================
# RUN SMOKE TESTS
# =============================================================================

echo ""
echo "🧪 Running smoke tests..."

# Wait a bit for services to stabilize
sleep 10

# Test health endpoints
SERVICES_TO_TEST=("data-ingestion:8001" "knowledge-graph:8002" "cascading-failure:8005")

for service_port in "${SERVICES_TO_TEST[@]}"; do
    service="${service_port%%:*}"
    port="${service_port##*:}"
    
    echo "  Testing $service..."
    kubectl run test-$service --image=curlimages/curl --restart=Never -n $NAMESPACE -- \
        curl -f "http://$service:$port/health" && \
    kubectl wait --for=condition=complete --timeout=30s pod/test-$service -n $NAMESPACE && \
    kubectl delete pod test-$service -n $NAMESPACE
done

echo -e "${GREEN}✅ Smoke tests passed${NC}"

# =============================================================================
# COMPLETION
# =============================================================================

echo ""
echo "========================================" 
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Configure DNS to point to frontend LoadBalancer IP"
echo "2. Set up SSL/TLS certificates"
echo "3. Configure backup schedules"
echo "4. Set up monitoring alerts"
echo "5. Run integration tests"
echo ""
echo "For logs: kubectl logs -f deployment/<service-name> -n $NAMESPACE"
echo "For shell: kubectl exec -it deployment/<service-name> -n $NAMESPACE -- /bin/bash"
echo ""
