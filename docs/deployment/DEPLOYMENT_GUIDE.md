# STRATUM PROTOCOL - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Cloud Provider Setup](#cloud-provider-setup)
5. [Configuration Management](#configuration-management)
6. [Monitoring & Observability](#monitoring--observability)
7. [Security Hardening](#security-hardening)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum (Development)**:
- Docker 24.0+
- Kubernetes 1.28+ (minikube/k3s for local)
- Python 3.11+
- Node.js 20+
- 16GB RAM
- 100GB disk space

**Production**:
- Kubernetes cluster (50+ nodes)
- 32 vCPU, 128GB RAM per node
- 10TB+ distributed storage
- Load balancer
- Managed databases (or HA setup)

### Required Tools

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
brew install helm

# Install Docker Desktop (includes Kubernetes)
brew install --cask docker

# Install Python dependencies
pip install kubernetes kubectl-switch
```

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/stratum-protocol.git
cd stratum-protocol
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
vim .env
```

**Critical Environment Variables**:
```bash
ENVIRONMENT=development
POSTGRES_PASSWORD=your_secure_password
NEO4J_PASSWORD=your_secure_password
KAFKA_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_super_secret_key_min_32_chars
DATA_ENCRYPTION_KEY=your_32_byte_encryption_key
```

### Step 3: Start Infrastructure Services

```bash
# Start databases, Kafka, observability stack
docker-compose -f infrastructure/docker-compose.yml up -d

# Verify all services are running
docker-compose -f infrastructure/docker-compose.yml ps

# Check logs
docker-compose -f infrastructure/docker-compose.yml logs -f postgres neo4j kafka
```

### Step 4: Initialize Databases

```bash
# PostgreSQL schema
docker exec -it stratum-postgres psql -U stratum_admin -d stratum_protocol -f /docker-entrypoint-initdb.d/init_schema.sql

# Neo4j constraints (auto-initialized on first connection)

# Kafka topics
docker exec -it stratum-kafka kafka-topics --create --bootstrap-server localhost:9092 --topic stratum.ingestion.iot
docker exec -it stratum-kafka kafka-topics --create --bootstrap-server localhost:9092 --topic stratum.simulation.cascade
```

### Step 5: Run Services Locally

**Option A: Run Individual Services**

```bash
# Data Ingestion Service
cd services/data-ingestion
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Knowledge Graph Service (in new terminal)
cd services/knowledge-graph
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Option B: Run with Docker Compose**

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f data-ingestion knowledge-graph
```

### Step 6: Verify Setup

```bash
# Health checks
curl http://localhost:8001/health  # Data Ingestion
curl http://localhost:8002/health  # Knowledge Graph
curl http://localhost:8004/health  # Cascading Failure

# Check metrics
curl http://localhost:8001/metrics

# View dashboards
open http://localhost:3001  # Grafana (admin/admin)
open http://localhost:16686  # Jaeger tracing
open http://localhost:9090  # Prometheus
```

---

## Kubernetes Deployment

### Step 1: Create Namespace

```bash
kubectl create namespace stratum-protocol
kubectl config set-context --current --namespace=stratum-protocol
```

### Step 2: Create Secrets

```bash
# Create secrets from .env file
kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol

# Verify
kubectl get secrets -n stratum-protocol
```

### Step 3: Deploy Infrastructure Services

```bash
# Deploy databases
kubectl apply -f k8s/config/postgres.yaml
kubectl apply -f k8s/config/neo4j.yaml
kubectl apply -f k8s/config/redis.yaml
kubectl apply -f k8s/config/kafka.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
kubectl wait --for=condition=ready pod -l app=neo4j --timeout=300s
```

### Step 4: Deploy Microservices

```bash
# Deploy all services
kubectl apply -f k8s/services/

# Verify deployments
kubectl get deployments -n stratum-protocol

# Check pods
kubectl get pods -n stratum-protocol

# View logs
kubectl logs -f deployment/data-ingestion -n stratum-protocol
```

### Step 5: Deploy API Gateway

```bash
# Deploy Nginx Ingress Controller
kubectl apply -f k8s/ingress/nginx-controller.yaml

# Deploy Ingress rules
kubectl apply -f k8s/ingress/api-gateway.yaml

# Get external IP
kubectl get ingress -n stratum-protocol
```

### Step 6: Deploy Observability Stack

```bash
# Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace stratum-protocol \
  --values k8s/monitoring/prometheus-values.yaml

# Grafana (included in above)

# Jaeger
kubectl apply -f k8s/monitoring/jaeger.yaml

# ELK Stack
kubectl apply -f k8s/monitoring/elasticsearch.yaml
kubectl apply -f k8s/monitoring/kibana.yaml
kubectl apply -f k8s/monitoring/logstash.yaml
```

---

## Cloud Provider Setup

### AWS Deployment

#### 1. Create EKS Cluster

```bash
# Install eksctl
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl

# Create cluster
eksctl create cluster \
  --name stratum-protocol-prod \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type m5.4xlarge \
  --nodes 50 \
  --nodes-min 20 \
  --nodes-max 100 \
  --managed

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name stratum-protocol-prod
```

#### 2. Provision RDS for PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier stratum-postgres \
  --db-instance-class db.r5.4xlarge \
  --engine postgres \
  --engine-version 16.1 \
  --master-username stratum_admin \
  --master-user-password <secure-password> \
  --allocated-storage 1000 \
  --storage-type gp3 \
  --multi-az \
  --vpc-security-group-ids sg-xxx \
  --db-subnet-group-name stratum-subnet-group
```

#### 3. Deploy MSK (Managed Kafka)

```bash
aws kafka create-cluster \
  --cluster-name stratum-kafka \
  --broker-node-group-info file://kafka-broker-config.json \
  --kafka-version 3.6.0 \
  --number-of-broker-nodes 3
```

#### 4. Configure S3 for Storage

```bash
aws s3 mb s3://stratum-protocol-data --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket stratum-protocol-data \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket stratum-protocol-data \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### Azure Deployment

#### 1. Create AKS Cluster

```bash
# Create resource group
az group create --name stratum-protocol-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group stratum-protocol-rg \
  --name stratum-protocol-aks \
  --node-count 50 \
  --node-vm-size Standard_D16s_v3 \
  --enable-managed-identity \
  --network-plugin azure \
  --enable-addons monitoring

# Get credentials
az aks get-credentials \
  --resource-group stratum-protocol-rg \
  --name stratum-protocol-aks
```

#### 2. Provision Azure Database for PostgreSQL

```bash
az postgres flexible-server create \
  --resource-group stratum-protocol-rg \
  --name stratum-postgres \
  --location eastus \
  --admin-user stratum_admin \
  --admin-password <secure-password> \
  --sku-name Standard_D16s_v3 \
  --tier GeneralPurpose \
  --storage-size 1024 \
  --version 16 \
  --high-availability Enabled
```

#### 3. Deploy Event Hubs (Kafka)

```bash
az eventhubs namespace create \
  --resource-group stratum-protocol-rg \
  --name stratum-kafka \
  --location eastus \
  --sku Standard \
  --enable-kafka true
```

### GCP Deployment

#### 1. Create GKE Cluster

```bash
gcloud container clusters create stratum-protocol-gke \
  --region us-central1 \
  --num-nodes 50 \
  --machine-type n2-standard-16 \
  --enable-autoscaling \
  --min-nodes 20 \
  --max-nodes 100 \
  --enable-stackdriver-kubernetes

# Get credentials
gcloud container clusters get-credentials stratum-protocol-gke --region us-central1
```

#### 2. Provision Cloud SQL

```bash
gcloud sql instances create stratum-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-custom-16-65536 \
  --region=us-central1 \
  --availability-type=REGIONAL \
  --storage-size=1000GB \
  --storage-type=SSD
```

---

## Configuration Management

### ConfigMaps

```bash
# Create ConfigMap for application config
kubectl create configmap stratum-config \
  --from-file=config/application.yaml \
  --namespace=stratum-protocol

# Create ConfigMap for logging
kubectl create configmap logging-config \
  --from-file=config/logging.yaml \
  --namespace=stratum-protocol
```

### Secrets Management

**Option A: Kubernetes Secrets**

```bash
kubectl create secret generic db-credentials \
  --from-literal=postgres-user=stratum_admin \
  --from-literal=postgres-password=<secure-password> \
  --namespace=stratum-protocol
```

**Option B: HashiCorp Vault**

```bash
# Install Vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \
  --namespace stratum-protocol \
  --set "server.ha.enabled=true"

# Initialize and unseal
kubectl exec -it vault-0 -n stratum-protocol -- vault operator init
kubectl exec -it vault-0 -n stratum-protocol -- vault operator unseal

# Store secrets
vault kv put secret/stratum/postgres \
  username=stratum_admin \
  password=<secure-password>
```

### Feature Flags

```bash
# Create ConfigMap for feature flags
kubectl create configmap feature-flags \
  --from-literal=ENABLE_AUTONOMOUS_ACTIONS=false \
  --from-literal=ENABLE_FEDERATED_LEARNING=true \
  --from-literal=ENABLE_CYBER_DEFENSE=true \
  --namespace=stratum-protocol
```

---

## Monitoring & Observability

### Prometheus Metrics

**Access Prometheus**:
```bash
kubectl port-forward -n stratum-protocol svc/prometheus-kube-prometheus-prometheus 9090:9090
open http://localhost:9090
```

**Key Metrics**:
- `data_ingestion_total` - Total data points ingested
- `simulation_duration_seconds` - Simulation execution time
- `api_request_duration_seconds` - API latency
- `kafka_consumer_lag` - Message processing lag

### Grafana Dashboards

```bash
# Get Grafana password
kubectl get secret -n stratum-protocol prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode

# Port forward
kubectl port-forward -n stratum-protocol svc/prometheus-grafana 3000:80

# Access
open http://localhost:3000
```

**Pre-built Dashboards**:
1. Platform Overview
2. Service Health
3. Simulation Performance
4. Infrastructure Status
5. Business Metrics

### Distributed Tracing

```bash
# Access Jaeger UI
kubectl port-forward -n stratum-protocol svc/jaeger-query 16686:16686
open http://localhost:16686
```

### Centralized Logging

```bash
# Access Kibana
kubectl port-forward -n stratum-protocol svc/kibana 5601:5601
open http://localhost:5601
```

**Log Queries**:
- Service errors: `level:ERROR AND service:data-ingestion`
- Slow requests: `duration:>1000`
- Security events: `tags:security`

---

## Security Hardening

### Network Policies

```bash
# Apply network policies
kubectl apply -f k8s/security/network-policies.yaml

# Verify
kubectl get networkpolicies -n stratum-protocol
```

### Pod Security Policies

```bash
# Enable PSP
kubectl apply -f k8s/security/pod-security-policy.yaml

# Verify
kubectl get psp
```

### RBAC Configuration

```bash
# Create service accounts
kubectl apply -f k8s/security/service-accounts.yaml

# Create roles and role bindings
kubectl apply -f k8s/security/rbac.yaml

# Verify
kubectl get roles,rolebindings -n stratum-protocol
```

### TLS/SSL Certificates

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create cluster issuer
kubectl apply -f k8s/security/cluster-issuer.yaml

# Certificates will be auto-provisioned by ingress
```

---

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl get pods -n stratum-protocol

# Describe pod
kubectl describe pod <pod-name> -n stratum-protocol

# Check logs
kubectl logs <pod-name> -n stratum-protocol

# Check events
kubectl get events -n stratum-protocol --sort-by='.lastTimestamp'
```

#### 2. Database Connection Issues

```bash
# Test connectivity
kubectl run -it --rm debug --image=postgres:16 --restart=Never -- psql -h postgres -U stratum_admin -d stratum_protocol

# Check service
kubectl get svc postgres -n stratum-protocol

# Check endpoints
kubectl get endpoints postgres -n stratum-protocol
```

#### 3. High Memory Usage

```bash
# Check resource usage
kubectl top pods -n stratum-protocol

# Increase memory limit
kubectl set resources deployment/<deployment-name> \
  --limits=memory=8Gi \
  --namespace=stratum-protocol
```

#### 4. Kafka Consumer Lag

```bash
# Check consumer groups
kubectl exec -it stratum-kafka-0 -n stratum-protocol -- \
  kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Check lag
kubectl exec -it stratum-kafka-0 -n stratum-protocol -- \
  kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group <group-name> --describe

# Scale consumers
kubectl scale deployment data-ingestion --replicas=10 -n stratum-protocol
```

### Health Check Commands

```bash
# Cluster health
kubectl get componentstatuses

# Node health
kubectl get nodes
kubectl describe node <node-name>

# Service health
for svc in data-ingestion knowledge-graph cascading-failure; do
  curl http://$svc:8001/health
done

# Database health
kubectl exec -it postgres-0 -n stratum-protocol -- pg_isready
```

### Log Analysis

```bash
# Grep for errors across all pods
kubectl logs -n stratum-protocol -l app=data-ingestion --tail=1000 | grep ERROR

# Stream logs from multiple pods
kubectl logs -n stratum-protocol -l tier=backend -f

# Export logs
kubectl logs -n stratum-protocol deployment/data-ingestion --since=1h > logs.txt
```

---

## Backup & Restore

### Database Backup

```bash
# PostgreSQL backup
kubectl exec -it postgres-0 -n stratum-protocol -- \
  pg_dump -U stratum_admin stratum_protocol | \
  gzip > backup-$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql.gz s3://stratum-protocol-backups/
```

### Restore from Backup

```bash
# Download from S3
aws s3 cp s3://stratum-protocol-backups/backup-20260218.sql.gz .

# Restore
gunzip -c backup-20260218.sql.gz | \
  kubectl exec -i postgres-0 -n stratum-protocol -- \
  psql -U stratum_admin stratum_protocol
```

---

## Scaling

### Horizontal Pod Autoscaling

```bash
# Create HPA
kubectl autoscale deployment data-ingestion \
  --cpu-percent=70 \
  --min=3 \
  --max=20 \
  --namespace=stratum-protocol

# Check HPA status
kubectl get hpa -n stratum-protocol
```

### Cluster Autoscaling

**AWS**:
```bash
eksctl create iamserviceaccount \
  --cluster=stratum-protocol-prod \
  --namespace=kube-system \
  --name=cluster-autoscaler \
  --attach-policy-arn=arn:aws:iam::aws:policy/AutoScalingFullAccess \
  --approve

kubectl apply -f k8s/autoscaling/cluster-autoscaler.yaml
```

---

## Production Checklist

- [ ] All secrets rotated from defaults
- [ ] TLS certificates configured
- [ ] Network policies applied
- [ ] RBAC configured
- [ ] Monitoring dashboards verified
- [ ] Alerting configured
- [ ] Backup strategy tested
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation reviewed
- [ ] Runbook created

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-18  
**Maintainer**: Platform Engineering Team
