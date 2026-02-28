#!/usr/bin/env zsh
# =============================================================================
# STRATUM PROTOCOL - Full Project Startup Script
# =============================================================================
# Starts the ENTIRE platform: Infrastructure → Databases → Microservices → Frontend
#
# Usage:
#   ./start.sh              # Start everything (interactive)
#   ./start.sh --infra      # Infrastructure only (databases, monitoring, queues)
#   ./start.sh --backend    # Infrastructure + all microservices
#   ./start.sh --frontend   # Infrastructure + frontend only
#   ./start.sh --stop       # Stop everything
#   ./start.sh --status     # Show status of all components
#   ./start.sh --logs       # Tail logs from all microservices
# =============================================================================

set -e

# ─── Configuration ───────────────────────────────────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker-compose.yml"
VENV_DIR="$PROJECT_ROOT/venv"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
SERVICES_DIR="$PROJECT_ROOT/services"
LOG_DIR="$PROJECT_ROOT/.logs"
PID_DIR="$PROJECT_ROOT/.pids"
ENV_FILE="$PROJECT_ROOT/.env"

# Port assignments for all microservices
typeset -A SERVICE_PORTS
SERVICE_PORTS=(
  data-ingestion      8001
  knowledge-graph     8002
  state-estimation    8003
  cascading-failure   8004
  policy-optimization 8005
  economic-intelligence 8006
  decision-ledger     8007
  citizen-behavior    8008
)

# Ordered list for iteration
SERVICE_ORDER=(
  data-ingestion
  knowledge-graph
  state-estimation
  cascading-failure
  policy-optimization
  economic-intelligence
  decision-ledger
  citizen-behavior
)

# Frontend port (3000 may be taken, use 3002)
FRONTEND_PORT=3002

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Helper Functions ────────────────────────────────────────────────────────

print_banner() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}🌐 STRATUM PROTOCOL — Urban Decision Intelligence Platform${NC}  ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

log_step() {
  echo -e "\n${BLUE}━━━ $1 ━━━${NC}"
}

log_ok() {
  echo -e "  ${GREEN}✅ $1${NC}"
}

log_warn() {
  echo -e "  ${YELLOW}⚠️  $1${NC}"
}

log_err() {
  echo -e "  ${RED}❌ $1${NC}"
}

log_info() {
  echo -e "  ${CYAN}ℹ️  $1${NC}"
}

ensure_dirs() {
  mkdir -p "$LOG_DIR" "$PID_DIR"
}

# ─── Pre-flight Checks ──────────────────────────────────────────────────────

preflight() {
  log_step "Pre-flight Checks"

  # Docker
  if ! command -v docker &>/dev/null; then
    log_err "Docker not found. Install Docker Desktop: https://docker.com/products/docker-desktop"
    exit 1
  fi
  if ! docker info &>/dev/null; then
    log_err "Docker daemon not running. Start Docker Desktop first."
    exit 1
  fi
  log_ok "Docker Desktop running"

  # docker-compose (v1 or v2)
  if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
  else
    log_err "docker-compose not found."
    exit 1
  fi
  log_ok "Docker Compose available ($COMPOSE_CMD)"

  # Node.js (for frontend)
  if command -v node &>/dev/null; then
    log_ok "Node.js $(node -v)"
  else
    log_warn "Node.js not found — frontend will be skipped"
  fi

  # Python
  if command -v python3 &>/dev/null; then
    log_ok "Python $(python3 --version 2>&1 | awk '{print $2}')"
  else
    log_warn "Python 3 not found — microservices will be skipped"
  fi

  # .env file
  if [ -f "$ENV_FILE" ]; then
    log_ok ".env file present"
  else
    log_warn ".env not found — creating from .env.example"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
      cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    fi
  fi

  # Compose file
  if [ ! -f "$COMPOSE_FILE" ]; then
    log_err "docker-compose.yml not found at $COMPOSE_FILE"
    exit 1
  fi
  log_ok "docker-compose.yml found"
}

# ─── Infrastructure (Docker Compose) ────────────────────────────────────────

start_infrastructure() {
  log_step "Starting Infrastructure Services (Docker Compose)"
  
  cd "$PROJECT_ROOT"
  $COMPOSE_CMD -f "$COMPOSE_FILE" up -d 2>&1 | while read -r line; do
    echo -e "  ${CYAN}▸${NC} $line"
  done

  log_info "Waiting for services to initialize (20s)..."
  sleep 20

  # Health checks
  log_step "Infrastructure Health Checks"
  
  local all_healthy=true

  # PostgreSQL
  if docker exec stratum-postgres pg_isready -U stratum_admin &>/dev/null; then
    log_ok "PostgreSQL         → localhost:5432"
  else
    log_warn "PostgreSQL still starting..."; all_healthy=false
  fi

  # TimescaleDB
  if docker exec stratum-timescaledb pg_isready -U timescale_admin &>/dev/null; then
    log_ok "TimescaleDB        → localhost:5433"
  else
    log_warn "TimescaleDB still starting..."; all_healthy=false
  fi

  # Neo4j
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 | grep -q "200"; then
    log_ok "Neo4j              → localhost:7474 (browser) / :7687 (bolt)"
  else
    log_warn "Neo4j still starting..."; all_healthy=false
  fi

  # Redis
  if docker exec stratum-redis redis-cli -a dev_password PING 2>/dev/null | grep -q PONG; then
    log_ok "Redis              → localhost:6380 (password: dev_password)"
  else
    log_warn "Redis still starting..."; all_healthy=false
  fi

  # MongoDB
  if docker exec stratum-mongodb mongosh --quiet --eval "db.runCommand({ping:1})" &>/dev/null; then
    log_ok "MongoDB            → localhost:27017"
  else
    log_warn "MongoDB still starting..."; all_healthy=false
  fi

  # Kafka
  if docker exec stratum-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &>/dev/null 2>&1; then
    log_ok "Kafka              → localhost:9092"
  else
    log_warn "Kafka still starting..."; all_healthy=false
  fi

  # Elasticsearch
  if curl -s http://localhost:9200/_cluster/health 2>/dev/null | grep -q '"status"'; then
    log_ok "Elasticsearch      → localhost:9200"
  else
    log_warn "Elasticsearch still starting..."; all_healthy=false
  fi

  # Monitoring
  curl -s http://localhost:9090/-/ready &>/dev/null && log_ok "Prometheus         → http://localhost:9090" || log_warn "Prometheus starting..."
  curl -s http://localhost:3001/api/health &>/dev/null && log_ok "Grafana            → http://localhost:3001 (anonymous access)" || log_warn "Grafana starting..."
  curl -s http://localhost:16686 &>/dev/null && log_ok "Jaeger             → http://localhost:16686" || log_warn "Jaeger starting..."
  curl -s http://localhost:5601/api/status &>/dev/null && log_ok "Kibana             → http://localhost:5601" || log_warn "Kibana starting..."

  # ML
  curl -s http://localhost:5001 &>/dev/null && log_ok "MLflow             → http://localhost:5001" || log_warn "MLflow starting..."
  curl -s http://localhost:8265 &>/dev/null && log_ok "Ray Dashboard      → http://localhost:8265" || log_warn "Ray starting..."

  local running_count=$(docker ps --filter "name=stratum-" --format "{{.Names}}" | wc -l | tr -d ' ')
  echo ""
  log_info "Infrastructure: ${GREEN}${running_count}/16${NC} containers running"
}

# ─── Python Virtual Environment ──────────────────────────────────────────────

setup_python_env() {
  log_step "Setting Up Python Environment"

  if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    log_ok "Virtual environment created at ./venv"
  else
    log_ok "Virtual environment already exists"
  fi

  source "$VENV_DIR/bin/activate"
  log_ok "Virtual environment activated"

  # Upgrade pip silently
  pip install --upgrade pip --quiet 2>/dev/null

  # Install base requirements that ALL services need
  log_info "Installing common dependencies..."
  pip install \
    fastapi==0.109.0 \
    "uvicorn[standard]==0.27.0" \
    pydantic==2.5.3 \
    prometheus-client==0.19.0 \
    httpx==0.26.0 \
    numpy==1.26.3 \
    redis==5.0.1 \
    --quiet 2>/dev/null
  log_ok "Common dependencies installed"

  # Make shared/ importable via PYTHONPATH (no setup.py needed)
  export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/shared:$PYTHONPATH"
  log_ok "PYTHONPATH configured for shared modules"
}

# ─── Microservices ───────────────────────────────────────────────────────────

start_service() {
  local service_name="$1"
  local port="${SERVICE_PORTS[$service_name]}"
  local service_dir="$SERVICES_DIR/$service_name"
  local log_file="$LOG_DIR/${service_name}.log"
  local pid_file="$PID_DIR/${service_name}.pid"

  if [ ! -d "$service_dir" ]; then
    log_warn "$service_name — directory not found, skipping"
    return
  fi

  # Kill existing process if running
  if [ -f "$pid_file" ]; then
    local old_pid=$(cat "$pid_file")
    if kill -0 "$old_pid" 2>/dev/null; then
      kill "$old_pid" 2>/dev/null
      sleep 1
    fi
    rm -f "$pid_file"
  fi

  # Also check if port is already in use
  if lsof -i ":$port" -sTCP:LISTEN &>/dev/null; then
    log_warn "$service_name — port $port already in use, skipping"
    return
  fi

  # Install service-specific requirements
  if [ -f "$service_dir/requirements.txt" ]; then
    pip install -r "$service_dir/requirements.txt" --quiet 2>/dev/null
  fi

  # Set common environment variables
  export DATABASE_URL="postgresql://stratum_admin:dev_password@localhost:5432/stratum_protocol"
  export TIMESCALEDB_URL="postgresql://timescale_admin:dev_password@localhost:5433/stratum_timeseries"
  export REDIS_URL="redis://:dev_password@localhost:6380/0"
  export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
  export NEO4J_URI="bolt://localhost:7687"
  export NEO4J_USER="neo4j"
  export NEO4J_PASSWORD="stratum_dev"
  export MONGODB_URL="mongodb://stratum_admin:dev_password@localhost:27017/stratum_protocol?authSource=admin"
  export RAY_ADDRESS="localhost:8265"
  export MLFLOW_TRACKING_URI="http://localhost:5001"
  export PROMETHEUS_PUSHGATEWAY="http://localhost:9091"
  export JAEGER_ENDPOINT="http://localhost:14268/api/traces"
  export SERVICE_NAME="$service_name"
  export SERVICE_PORT="$port"

  # Start the service in background
  cd "$service_dir"
  nohup python3 main.py > "$log_file" 2>&1 &
  local pid=$!
  echo "$pid" > "$pid_file"
  cd "$PROJECT_ROOT"

  # Brief wait to check it didn't crash immediately
  sleep 2
  if kill -0 "$pid" 2>/dev/null; then
    log_ok "$service_name → http://localhost:$port  (PID: $pid)"
  else
    log_err "$service_name — failed to start (check $log_file)"
  fi
}

start_all_services() {
  log_step "Starting Microservices (8 services)"

  source "$VENV_DIR/bin/activate"
  export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/shared:$PYTHONPATH"

  for service_name in $SERVICE_ORDER; do
    start_service "$service_name"
  done

  echo ""
  local running=0
  for service_name in $SERVICE_ORDER; do
    local pid_file="$PID_DIR/${service_name}.pid"
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
      ((running++))
    fi
  done
  log_info "Microservices: ${GREEN}${running}/${#SERVICE_ORDER[@]}${NC} running"
}

# ─── Frontend ────────────────────────────────────────────────────────────────

start_frontend() {
  log_step "Starting Frontend (React + Three.js)"

  if [ ! -d "$FRONTEND_DIR" ]; then
    log_err "Frontend directory not found at $FRONTEND_DIR"
    return
  fi

  if ! command -v node &>/dev/null; then
    log_err "Node.js not installed — skipping frontend"
    return
  fi

  local pid_file="$PID_DIR/frontend.pid"
  local log_file="$LOG_DIR/frontend.log"

  # Kill existing
  if [ -f "$pid_file" ]; then
    local old_pid=$(cat "$pid_file")
    if kill -0 "$old_pid" 2>/dev/null; then
      kill "$old_pid" 2>/dev/null
      sleep 2
    fi
    rm -f "$pid_file"
  fi

  if lsof -i ":$FRONTEND_PORT" -sTCP:LISTEN &>/dev/null; then
    log_warn "Port $FRONTEND_PORT already in use — skipping frontend"
    return
  fi

  cd "$FRONTEND_DIR"

  # Install dependencies if node_modules missing or outdated
  if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
    log_info "Installing frontend dependencies..."
    npm install --silent 2>/dev/null
  fi

  # Start React dev server (suppress source map warnings)
  GENERATE_SOURCEMAP=false BROWSER=none PORT=$FRONTEND_PORT \
    nohup npm start > "$log_file" 2>&1 &
  local pid=$!
  echo "$pid" > "$pid_file"

  cd "$PROJECT_ROOT"

  # Wait for the dev server to compile
  log_info "Waiting for frontend to compile..."
  local waited=0
  while [ $waited -lt 45 ]; do
    if curl -s -o /dev/null http://localhost:$FRONTEND_PORT 2>/dev/null; then
      log_ok "Frontend           → http://localhost:$FRONTEND_PORT  (PID: $pid)"
      return
    fi
    sleep 3
    ((waited+=3))
  done

  # Check if process still alive even if curl didn't succeed
  if kill -0 "$pid" 2>/dev/null; then
    log_ok "Frontend starting   → http://localhost:$FRONTEND_PORT  (PID: $pid)"
    log_info "May take a few more seconds to compile..."
  else
    log_err "Frontend failed to start (check $log_file)"
  fi
}

# ─── Stop Everything ─────────────────────────────────────────────────────────

stop_all() {
  print_banner
  log_step "Stopping All STRATUM Services"

  # Stop microservices
  if [ -d "$PID_DIR" ]; then
    for pid_file in "$PID_DIR"/*.pid; do
      if [ -f "$pid_file" ]; then
        local name=$(basename "$pid_file" .pid)
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
          kill "$pid" 2>/dev/null
          log_ok "Stopped $name (PID: $pid)"
        fi
        rm -f "$pid_file"
      fi
    done
  fi

  # Stop frontend (kill the whole process group)
  if [ -f "$PID_DIR/frontend.pid" ]; then
    local fpid=$(cat "$PID_DIR/frontend.pid")
    # React scripts spawn child processes, kill the group
    pkill -P "$fpid" 2>/dev/null
    kill "$fpid" 2>/dev/null
    rm -f "$PID_DIR/frontend.pid"
    log_ok "Stopped frontend"
  fi

  # Stop infrastructure
  log_info "Stopping Docker Compose services..."
  cd "$PROJECT_ROOT"
  
  if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  else
    COMPOSE_CMD="docker-compose"
  fi

  $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>&1 | while read -r line; do
    echo -e "  ${CYAN}▸${NC} $line"
  done

  log_ok "All services stopped"
  echo ""
}

# ─── Status ──────────────────────────────────────────────────────────────────

show_status() {
  print_banner
  log_step "System Status"

  echo ""
  echo -e "  ${BOLD}📦 Infrastructure (Docker Compose):${NC}"
  local infra_count=$(docker ps --filter "name=stratum-" --format "{{.Names}}" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$infra_count" -gt 0 ]; then
    docker ps --filter "name=stratum-" --format "    {{.Names}}\t{{.Status}}" | sort
    echo ""
    echo -e "    ${GREEN}$infra_count containers running${NC}"
  else
    echo -e "    ${RED}No infrastructure containers running${NC}"
  fi

  echo ""
  echo -e "  ${BOLD}🔧 Microservices:${NC}"
  local svc_running=0
  for service_name in $SERVICE_ORDER; do
    local port="${SERVICE_PORTS[$service_name]}"
    local pid_file="$PID_DIR/${service_name}.pid"
    local svc_state="${RED}stopped${NC}"
    
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
      local pid=$(cat "$pid_file")
      if curl -s -o /dev/null http://localhost:$port 2>/dev/null; then
        svc_state="${GREEN}running${NC} → http://localhost:$port (PID: $pid)"
      else
        svc_state="${YELLOW}starting${NC} (PID: $pid)"
      fi
      ((svc_running++))
    fi
    echo -e "    $service_name: $svc_state"
  done
  echo -e "    ${CYAN}$svc_running/${#SERVICE_ORDER[@]} services running${NC}"

  echo ""
  echo -e "  ${BOLD}🖥️  Frontend:${NC}"
  local fpid_file="$PID_DIR/frontend.pid"
  if [ -f "$fpid_file" ] && kill -0 "$(cat "$fpid_file")" 2>/dev/null; then
    echo -e "    ${GREEN}running${NC} → http://localhost:$FRONTEND_PORT (PID: $(cat "$fpid_file"))"
  else
    echo -e "    ${RED}stopped${NC}"
  fi

  echo ""
  echo -e "  ${BOLD}🌐 Dashboard URLs:${NC}"
  echo "    Grafana:       http://localhost:3001  (anonymous access)"
  echo "    Prometheus:    http://localhost:9090"
  echo "    Neo4j:         http://localhost:7474  (neo4j / stratum_dev)"
  echo "    Jaeger:        http://localhost:16686"
  echo "    Kibana:        http://localhost:5601"
  echo "    Ray:           http://localhost:8265"
  echo "    MLflow:        http://localhost:5001"
  echo "    Frontend:      http://localhost:$FRONTEND_PORT"
  echo ""
}

# ─── Logs ────────────────────────────────────────────────────────────────────

show_logs() {
  print_banner
  log_step "Tailing All Microservice Logs"
  echo -e "  ${CYAN}Press Ctrl+C to stop${NC}\n"

  if [ ! -d "$LOG_DIR" ] || [ -z "$(ls -A "$LOG_DIR" 2>/dev/null)" ]; then
    log_warn "No log files found. Start services first."
    exit 0
  fi

  tail -f "$LOG_DIR"/*.log 2>/dev/null
}

# ─── Main Startup (Full Stack) ──────────────────────────────────────────────

start_full() {
  print_banner
  ensure_dirs

  # 1. Pre-flight
  preflight

  # 2. Infrastructure
  start_infrastructure

  # 3. Python env + microservices
  if command -v python3 &>/dev/null; then
    setup_python_env
    start_all_services
  else
    log_warn "Python 3 not found — skipping microservices"
  fi

  # 4. Frontend
  if command -v node &>/dev/null; then
    start_frontend
  else
    log_warn "Node.js not found — skipping frontend"
  fi

  # 5. Summary
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}${BOLD}🎉 STRATUM PROTOCOL — All Systems Online!${NC}                    ${CYAN}║${NC}"
  echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}Frontend:${NC}       http://localhost:$FRONTEND_PORT                     ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}API Gateway:${NC}    http://localhost:80                        ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}Microservices:${NC}                                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    data-ingestion          http://localhost:8001              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    knowledge-graph         http://localhost:8002              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    state-estimation        http://localhost:8003              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    cascading-failure       http://localhost:8004              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    policy-optimization     http://localhost:8005              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    economic-intelligence   http://localhost:8006              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    decision-ledger         http://localhost:8007              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    citizen-behavior        http://localhost:8008              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}Dashboards:${NC}                                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Grafana      http://localhost:3001                        ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Prometheus   http://localhost:9090                        ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Neo4j        http://localhost:7474                        ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Jaeger       http://localhost:16686                       ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Kibana       http://localhost:5601                        ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Ray          http://localhost:8265                        ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    MLflow       http://localhost:5001                        ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}Databases:${NC}                                                  ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    PostgreSQL   localhost:5432                               ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    TimescaleDB  localhost:5433                               ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    MongoDB      localhost:27017                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Redis        localhost:6380  (pass: dev_password)         ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Neo4j Bolt   localhost:7687                               ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Kafka        localhost:9092                               ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${YELLOW}Commands:${NC}                                                   ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    ./start.sh --status   Show full system status             ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    ./start.sh --logs     Tail microservice logs              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    ./start.sh --stop     Shutdown everything                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

# ─── CLI Argument Routing ────────────────────────────────────────────────────

case "${1:-}" in
  --stop|-s)
    stop_all
    ;;
  --status|-t)
    show_status
    ;;
  --logs|-l)
    show_logs
    ;;
  --infra|-i)
    print_banner
    ensure_dirs
    preflight
    start_infrastructure
    ;;
  --backend|-b)
    print_banner
    ensure_dirs
    preflight
    start_infrastructure
    setup_python_env
    start_all_services
    ;;
  --frontend|-f)
    print_banner
    ensure_dirs
    preflight
    start_infrastructure
    start_frontend
    ;;
  --help|-h)
    echo "STRATUM PROTOCOL — Full Stack Startup Script"
    echo ""
    echo "Usage: ./start.sh [option]"
    echo ""
    echo "Options:"
    echo "  (no args)     Start everything: infra + backend + frontend"
    echo "  --infra, -i   Infrastructure only (databases, monitoring, queues)"
    echo "  --backend, -b Infrastructure + all 8 microservices"
    echo "  --frontend, -f Infrastructure + frontend only"
    echo "  --stop, -s    Stop all services (infra, backend, frontend)"
    echo "  --status, -t  Show status of all components"
    echo "  --logs, -l    Tail all microservice log files"
    echo "  --help, -h    Show this help message"
    echo ""
    ;;
  "")
    start_full
    ;;
  *)
    echo "Unknown option: $1"
    echo "Run ./start.sh --help for usage"
    exit 1
    ;;
esac
