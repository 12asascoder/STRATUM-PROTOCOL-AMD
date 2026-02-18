#!/bin/bash
# Local development setup script

set -e

echo "🛠️  STRATUM PROTOCOL - Local Development Setup"
echo "=============================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "✅ Docker found"

# Pull images
echo ""
echo "📥 Pulling Docker images..."
docker-compose -f infrastructure/docker-compose.yml pull

# Start infrastructure
echo ""
echo "🚀 Starting infrastructure..."
docker-compose -f infrastructure/docker-compose.yml up -d

# Wait for services
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check health
echo ""
echo "🔍 Checking service health..."
docker-compose -f infrastructure/docker-compose.yml ps

# Initialize databases
echo ""
echo "🗄️  Initializing databases..."

# PostgreSQL
docker exec stratum-postgres psql -U postgres -f /docker-entrypoint-initdb.d/01-init-postgres.sql || echo "Already initialized"

# Neo4j
sleep 5
docker exec stratum-neo4j cypher-shell -u neo4j -p stratumgraph123 "RETURN 1" || echo "Waiting for Neo4j..."

echo ""
echo "✅ Infrastructure ready!"
echo ""
echo "🌐 Access points:"
echo "  PostgreSQL: localhost:5432"
echo "  Neo4j:      localhost:7474 (browser) / localhost:7687 (bolt)"
echo "  Redis:      localhost:6379"
echo "  MongoDB:    localhost:27017"
echo "  Kafka:      localhost:9092"
echo "  Prometheus: localhost:9090"
echo "  Grafana:    localhost:3000"
echo "  MLflow:     localhost:5000"
echo ""
echo "To start microservices:"
echo "  cd services/data-ingestion && python main.py"
echo "  cd services/knowledge-graph && python main.py"
echo "  cd services/cascading-failure && python main.py"
echo ""
echo "To start frontend:"
echo "  cd frontend && npm install && npm start"
echo ""
