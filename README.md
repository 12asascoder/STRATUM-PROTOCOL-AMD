# STRATUM PROTOCOL
## The Urban Decision Intelligence & Resilience Infrastructure Layer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)

**STRATUM PROTOCOL** is a production-grade, sovereign-ready AI platform for real-time urban decision intelligence, infrastructure resilience modeling, and cascading failure prediction at national scale.

## 🏗️ System Overview

A multi-layer AI infrastructure platform capable of:
- **Real-time Multi-Source Urban Data Ingestion** - Streaming telemetry from IoT, traffic, weather, social
- **Cross-Domain Infrastructure Dependency Modeling** - Multi-layer graph representation
- **Cascading Failure Prediction** - GNN-based stress propagation simulation
- **Citizen Behavior Simulation** - Agent-based evacuation & mobility modeling
- **Economic Impact Modeling** - GDP, ROI, insurance risk quantification
- **Autonomous Policy Simulation** - Monte Carlo optimization with multi-objective tradeoffs
- **Cryptographically Verifiable Urban Decision Ledger** - Immutable AI decision records
- **Federated Cross-City Learning** - Privacy-preserving global intelligence
- **Sovereign AI Governance & Compliance** - Explainability, bias detection, audit trails
- **Cyber-Physical Defense Modeling** - Adversarial attack cascade simulation
- **Autonomous Infrastructure Orchestration** - Traffic, energy, emergency dispatch optimization
- **Long-Term Urban Evolution Forecasting** - 5-30 year climate & infrastructure stress projection
- **Immersive Digital Twin Visualization** - 3D real-time stress heatmaps & VR-ready interface

## 🎯 Core Architecture

**Microservices Architecture** | **Event-Driven** | **Zero-Trust Security** | **Multi-Cloud Deployable**

### System Modules

| Module | Purpose | Tech Stack |
|--------|---------|------------|
| **Data Ingestion Service** | Real-time streaming, edge ingestion, validation | Kafka, TimescaleDB, FastAPI |
| **Urban Knowledge Graph Service** | Multi-layer infrastructure graph | Neo4j, PyTorch Geometric |
| **State Estimation Engine** | Bayesian inference, stress scoring | PyTorch, Ray |
| **Cascading Failure Simulation** | Multi-hop failure propagation | GNN, RL, Monte Carlo |
| **Citizen Behavior Simulation** | Agent-based modeling | Mesa, Ray RLlib |
| **Policy Simulation & Optimization** | Multi-objective optimization | Optuna, NSGA-II |
| **Economic Intelligence Engine** | GDP impact, ROI, risk scoring | Pandas, NumPy, SciPy |
| **Urban Decision Ledger** | Cryptographic audit trail | PostgreSQL, Merkle Trees |
| **Federated Intelligence Module** | Privacy-preserving learning | Flower, PySyft |
| **Sovereign AI Governance** | Explainability, bias detection | SHAP, Fairlearn |
| **Cyber-Physical Defense** | Adversarial detection | PyTorch, ART |
| **Autonomous Orchestration** | Infrastructure action engine | FastAPI, Redis |
| **Long-Term Evolution Simulator** | 5-30 year forecasting | Prophet, ARIMA, LSTM |
| **Digital Twin Visualization** | 3D city interface | React, Three.js, Deck.gl |
| **Self-Learning Adaptive Engine** | Continuous improvement | MLflow, Ray Tune |

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STRATUM PROTOCOL PLATFORM                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   IoT Data   │───▶│   Ingestion  │───▶│ Knowledge    │          │
│  │   Streams    │    │   Service    │    │    Graph     │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                              │                    │                  │
│                              ▼                    ▼                  │
│  ┌──────────────────────────────────────────────────────┐           │
│  │           State Estimation & Risk Scoring            │           │
│  └──────────────────────────────────────────────────────┘           │
│                              │                                       │
│              ┌───────────────┼───────────────┐                      │
│              ▼               ▼               ▼                      │
│  ┌────────────────┐ ┌────────────┐ ┌─────────────────┐            │
│  │   Cascading    │ │  Citizen   │ │     Policy      │            │
│  │    Failure     │ │  Behavior  │ │   Simulation    │            │
│  │   Simulation   │ │ Simulation │ │  & Optimization │            │
│  └────────────────┘ └────────────┘ └─────────────────┘            │
│              │               │               │                      │
│              └───────────────┼───────────────┘                      │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────┐           │
│  │         Urban Decision Ledger (Immutable)            │           │
│  └──────────────────────────────────────────────────────┘           │
│                              │                                       │
│              ┌───────────────┼───────────────┐                      │
│              ▼               ▼               ▼                      │
│  ┌────────────────┐ ┌────────────┐ ┌─────────────────┐            │
│  │   Federated    │ │ Sovereign  │ │  Cyber-Physical │            │
│  │  Intelligence  │ │    AI      │ │     Defense     │            │
│  │     Module     │ │ Governance │ │     Engine      │            │
│  └────────────────┘ └────────────┘ └─────────────────┘            │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────┐           │
│  │      Autonomous Infrastructure Orchestration         │           │
│  └──────────────────────────────────────────────────────┘           │
│                              │                                       │
│              ┌───────────────┼───────────────┐                      │
│              ▼               ▼               ▼                      │
│  ┌────────────────┐ ┌────────────┐ ┌─────────────────┐            │
│  │   Long-Term    │ │  Digital   │ │  Self-Learning  │            │
│  │   Evolution    │ │    Twin    │ │    Adaptive     │            │
│  │   Simulator    │ │Visualization│ │     Engine      │            │
│  └────────────────┘ └────────────┘ └─────────────────┘            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker 24.0+ (Docker Desktop for macOS)
- Kubernetes 1.28+ (Enable in Docker Desktop Settings)
- Python 3.11+
- Node.js 20+
- 8GB RAM minimum (32GB recommended)
- 20GB free disk space
- NVIDIA GPU (optional, for accelerated training)

### ⚠️ IMPORTANT: Before Running Any Commands

**1. Start Docker Desktop:**
```bash
# Open Docker Desktop application
open /Applications/Docker.app

# Wait for green indicator in menu bar
# Verify Docker is running:
docker ps
```

**2. Enable Kubernetes in Docker Desktop:**
- Open Docker Desktop **Settings (⚙️)**
- Go to **Kubernetes** tab
- Check ☑️ **Enable Kubernetes**
- Click **Apply & Restart**
- Wait 2-3 minutes for Kubernetes to start
- Verify: `kubectl cluster-info`

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/stratum-protocol.git
cd stratum-protocol

# Copy environment configuration
cp .env.example .env

# Start infrastructure services (databases, Kafka, etc.)
docker-compose -f infrastructure/docker-compose.yml up -d

# Wait 30 seconds for databases to initialize
sleep 30

# Create Kubernetes namespace and secrets
kubectl create namespace stratum-protocol
kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol

# Deploy to Kubernetes
kubectl apply -f k8s/config/
kubectl apply -f k8s/databases/
kubectl apply -f k8s/services/
kubectl apply -f k8s/monitoring/
kubectl apply -f k8s/ingress/

# Wait for pods to be ready (2-3 minutes)
kubectl get pods -n stratum-protocol -w

# Port forward frontend (in new terminal)
kubectl port-forward svc/frontend 3000:3000 -n stratum-protocol

# Access platform
open http://localhost:3000
```

### One-Command Deployment (After Docker/K8s are running)

```bash
# Deploy everything automatically
./scripts/deploy.sh production
```

### Troubleshooting

If you see errors like:
- **"Cannot connect to Docker daemon"** → Start Docker Desktop
- **"connection refused localhost:8080"** → Enable Kubernetes in Docker Desktop
- **"Services not responding"** → Wait longer or check pod status

**See detailed troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)  
**See step-by-step guide:** [QUICKSTART.md](QUICKSTART.md)

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Configure secrets
kubectl create secret generic stratum-secrets \
  --from-env-file=.env \
  --namespace=stratum-protocol
```

## 📦 Project Structure

```
stratum-protocol/
├── services/                      # Microservices
│   ├── data-ingestion/           # Real-time data streaming
│   ├── knowledge-graph/          # Urban graph database
│   ├── state-estimation/         # Bayesian inference
│   ├── cascading-failure/        # Failure simulation
│   ├── citizen-behavior/         # Agent-based modeling
│   ├── policy-simulation/        # Optimization engine
│   ├── economic-intelligence/    # GDP & ROI modeling
│   ├── decision-ledger/          # Cryptographic audit trail
│   ├── federated-intelligence/   # Privacy-preserving learning
│   ├── sovereign-governance/     # AI compliance & explainability
│   ├── cyber-defense/            # Adversarial detection
│   ├── autonomous-orchestration/ # Infrastructure control
│   ├── evolution-simulator/      # Long-term forecasting
│   ├── digital-twin/             # 3D visualization
│   └── adaptive-engine/          # Self-learning loop
├── shared/                        # Shared libraries
│   ├── auth/                     # Authentication & authorization
│   ├── messaging/                # Event bus abstraction
│   ├── monitoring/               # Observability
│   └── models/                   # Shared data models
├── infrastructure/                # Infrastructure as code
│   ├── docker-compose.yml        # Local development
│   ├── terraform/                # Cloud provisioning
│   └── helm/                     # Kubernetes charts
├── k8s/                          # Kubernetes manifests
│   ├── services/                 # Service deployments
│   ├── config/                   # ConfigMaps & Secrets
│   └── ingress/                  # API Gateway
├── frontend/                     # React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── visualizations/       # Three.js 3D views
│   │   └── dashboard/
│   └── public/
├── docs/                         # Documentation
│   ├── architecture/             # System design
│   ├── api/                      # API specifications
│   ├── deployment/               # Deployment guides
│   └── security/                 # Security architecture
├── scripts/                      # Automation scripts
│   ├── deploy.sh                 # Deployment automation
│   ├── test.sh                   # Integration tests
│   └── migrate.sh                # Database migrations
├── tests/                        # Integration tests
│   ├── e2e/                      # End-to-end tests
│   └── load/                     # Load testing
└── .github/                      # CI/CD workflows
    └── workflows/
```

## 🔐 Security Architecture

- **Zero-Trust Network**: All inter-service communication encrypted (mTLS)
- **RBAC**: Role-based access control with fine-grained permissions
- **OAuth2 + JWT**: Secure authentication and authorization
- **Data Encryption**: At-rest (AES-256) and in-transit (TLS 1.3)
- **Audit Logging**: Comprehensive audit trails in Decision Ledger
- **Vulnerability Scanning**: Automated container scanning in CI/CD
- **Secrets Management**: Kubernetes secrets + HashiCorp Vault integration

## 📡 API Architecture

All services expose REST + gRPC APIs with OpenAPI 3.0 specifications.

**Core Endpoints:**
- `POST /api/v1/ingest/stream` - Real-time data ingestion
- `GET /api/v1/graph/infrastructure` - Query knowledge graph
- `POST /api/v1/simulate/cascade` - Run failure simulation
- `POST /api/v1/policy/optimize` - Policy optimization
- `GET /api/v1/ledger/decisions` - Query decision history
- `POST /api/v1/orchestrate/action` - Execute infrastructure action
- `GET /api/v1/twin/visualization` - Digital twin state

## 🧪 Testing

```bash
# Unit tests
pytest services/*/tests/

# Integration tests
pytest tests/integration/

# Load testing
locust -f tests/load/locustfile.py

# End-to-end tests
npm run test:e2e
```

## 📈 Monitoring & Observability

- **Metrics**: Prometheus + Grafana dashboards
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger distributed tracing
- **Alerting**: PagerDuty integration
- **Health Checks**: Kubernetes liveness/readiness probes

## 🌍 Multi-Cloud Deployment

Supports deployment on:
- **AWS**: EKS, RDS, S3, CloudWatch
- **Azure**: AKS, Cosmos DB, Blob Storage
- **GCP**: GKE, Cloud SQL, Cloud Storage
- **On-Premises**: OpenStack, VMware

## 🛣️ Roadmap

### MVP (Months 0-6)
- ✅ Core data ingestion pipeline
- ✅ Knowledge graph infrastructure
- ✅ Basic cascading failure simulation
- ✅ Decision ledger implementation
- ✅ Initial digital twin visualization

### Phase 1 (Months 6-12)
- 🔄 Advanced citizen behavior modeling
- 🔄 Multi-objective policy optimization
- 🔄 Federated learning infrastructure
- 🔄 Cyber-physical defense engine
- 🔄 Autonomous orchestration v1

### Phase 2 (Months 12-18)
- 📋 Long-term evolution forecasting
- 📋 Advanced economic impact modeling
- 📋 VR/AR digital twin interface
- 📋 Multi-city federated deployment
- 📋 Full sovereign AI governance

### Phase 3 (Months 18-24)
- 📋 National-scale deployment
- 📋 Real-time crisis response system
- 📋 Advanced self-learning capabilities
- 📋 International standards compliance
- 📋 Commercial SaaS offering

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📞 Contact

- **Project Lead**: [Your Organization]
- **Email**: contact@stratum-protocol.io
- **Documentation**: https://docs.stratum-protocol.io
- **Status**: https://status.stratum-protocol.io

## 🔗 Links

- [Architecture Documentation](docs/architecture/)
- [API Reference](docs/api/)
- [Deployment Guide](docs/deployment/)
- [Security Model](docs/security/)
- [Research Papers](docs/research/)

---

**Built for sovereign nations, resilient cities, and the future of urban intelligence.**
