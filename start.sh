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

# Do NOT use set -e — individual failures are handled per-command

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

# Frontend port (3000 may be taken by other apps)
FRONTEND_PORT=3002

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Compose command flag
USE_COMPOSE_PLUGIN=false

# ─── Helper Functions ────────────────────────────────────────────────────────

print_banner() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}🌐 STRATUM PROTOCOL — Urban Decision Intelligence Platform${NC}  ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

log_step()  { echo -e "\n${BLUE}━━━ $1 ━━━${NC}"; }
log_ok()    { echo -e "  ${GREEN}✅ $1${NC}"; }
log_warn()  { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
log_err()   { echo -e "  ${RED}❌ $1${NC}"; }
log_info()  { echo -e "  ${CYAN}ℹ️  $1${NC}"; }

ensure_dirs() { mkdir -p "$LOG_DIR" "$PID_DIR"; }

# Wrapper: run docker compose correctly (avoids zsh word-splitting "docker compose")
run_compose() {
  if $USE_COMPOSE_PLUGIN; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

# ─── Pre-flight Checks ──────────────────────────────────────────────────────

preflight() {
  log_step "Pre-flight Checks"

  if ! command -v docker &>/dev/null; then
    log_err "Docker not found. Install Docker Desktop."; return 1
  fi
  if ! docker info &>/dev/null 2>&1; then
    log_err "Docker daemon not running. Start Docker Desktop first."; return 1
  fi
  log_ok "Docker Desktop running"

  if docker compose version &>/dev/null 2>&1; then
    USE_COMPOSE_PLUGIN=true
    log_ok "Docker Compose (plugin)"
  elif command -v docker-compose &>/dev/null; then
    USE_COMPOSE_PLUGIN=false
    log_ok "Docker Compose (standalone)"
  else
    log_err "docker-compose not found."; return 1
  fi

  command -v node &>/dev/null && log_ok "Node.js $(node -v)" || log_warn "Node.js not found — frontend skipped"
  command -v python3 &>/dev/null && log_ok "Python $(python3 --version 2>&1 | awk '{print $2}')" || log_warn "Python 3 not found — microservices skipped"

  if [ -f "$ENV_FILE" ]; then
    log_ok ".env file present"
  else
    log_warn ".env not found — creating from .env.example"
    [ -f "$PROJECT_ROOT/.env.example" ] && cp "$PROJECT_ROOT/.env.example" "$ENV_FILE" || touch "$ENV_FILE"
  fi

  [ -f "$COMPOSE_FILE" ] && log_ok "docker-compose.yml found" || { log_err "docker-compose.yml not found"; return 1; }
}

# ─── Infrastructure (Docker Compose) ────────────────────────────────────────

start_infrastructure() {
  log_step "Starting Infrastructure Services (Docker Compose)"

  cd "$PROJECT_ROOT"
  run_compose -f "$COMPOSE_FILE" up -d 2>&1 | while IFS= read -r line; do
    echo -e "  ${CYAN}▸${NC} $line"
  done

  log_info "Waiting for services to initialize (25s)..."
  sleep 25

  log_step "Infrastructure Health Checks"

  docker exec stratum-postgres pg_isready -U stratum_admin &>/dev/null 2>&1 \
    && log_ok "PostgreSQL         → localhost:5432" \
    || log_warn "PostgreSQL still starting..."

  docker exec stratum-timescaledb pg_isready -U timescale_admin &>/dev/null 2>&1 \
    && log_ok "TimescaleDB        → localhost:5433" \
    || log_warn "TimescaleDB still starting..."

  curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 2>/dev/null | grep -q "200" \
    && log_ok "Neo4j              → localhost:7474 / :7687" \
    || log_warn "Neo4j still starting..."

  docker exec stratum-redis redis-cli -a dev_password PING 2>/dev/null | grep -q PONG \
    && log_ok "Redis              → localhost:6380" \
    || log_warn "Redis still starting..."

  docker exec stratum-mongodb mongosh --quiet --eval "db.runCommand({ping:1})" &>/dev/null 2>&1 \
    && log_ok "MongoDB            → localhost:27017" \
    || log_warn "MongoDB still starting..."

  docker exec stratum-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &>/dev/null 2>&1 \
    && log_ok "Kafka              → localhost:9092" \
    || log_warn "Kafka still starting..."

  curl -s http://localhost:9200/_cluster/health 2>/dev/null | grep -q '"status"' \
    && log_ok "Elasticsearch      → localhost:9200" \
    || log_warn "Elasticsearch still starting..."

  curl -s http://localhost:9090/-/ready &>/dev/null \
    && log_ok "Prometheus         → http://localhost:9090" \
    || log_warn "Prometheus starting..."

  curl -s http://localhost:3001/api/health &>/dev/null \
    && log_ok "Grafana            → http://localhost:3001 (no login)" \
    || log_warn "Grafana starting..."

  curl -s -o /dev/null http://localhost:16686 &>/dev/null \
    && log_ok "Jaeger             → http://localhost:16686" \
    || log_warn "Jaeger starting..."

  curl -s -o /dev/null http://localhost:5601/api/status &>/dev/null \
    && log_ok "Kibana             → http://localhost:5601" \
    || log_warn "Kibana starting..."

  curl -s -o /dev/null http://localhost:5001 &>/dev/null \
    && log_ok "MLflow             → http://localhost:5001" \
    || log_warn "MLflow starting..."

  curl -s -o /dev/null http://localhost:8265 &>/dev/null \
    && log_ok "Ray Dashboard      → http://localhost:8265" \
    || log_warn "Ray starting..."

  local running_count
  running_count=$(docker ps --filter "name=stratum-" --format "{{.Names}}" | wc -l | tr -d ' ')
  echo ""
  log_info "Infrastructure: ${GREEN}${running_count}/16${NC} containers running"
}

# ─── Python Virtual Environment ──────────────────────────────────────────────

setup_python_env() {
  log_step "Setting Up Python Environment"

  if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || { log_err "Failed to create venv"; return 1; }
    log_ok "Virtual environment created at ./venv"
  else
    log_ok "Virtual environment already exists"
  fi

  source "$VENV_DIR/bin/activate"
  log_ok "Virtual environment activated"

  pip install --upgrade pip --quiet 2>/dev/null || true

  log_info "Installing common dependencies (first run may take 1-2 min)..."
  pip install \
    "fastapi>=0.109.0,<1.0" \
    "uvicorn[standard]>=0.27.0,<1.0" \
    "pydantic>=2.5.0,<3.0" \
    "prometheus-client>=0.19.0" \
    "httpx>=0.26.0" \
    "numpy>=1.26.0" \
    "redis>=5.0.0" \
    "aiokafka>=0.10.0" \
    "aiohttp>=3.9.0" \
    "python-multipart>=0.0.6" \
    "python-json-logger>=2.0.0" \
    --quiet 2>/dev/null || true
  log_ok "Common dependencies installed"

  export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/shared:$PYTHONPATH"
  log_ok "PYTHONPATH configured for shared modules"
}

# ─── Microservices ───────────────────────────────────────────────────────────

start_service() {
  local svc="$1"
  local port="${SERVICE_PORTS[$svc]}"
  local svc_dir="$SERVICES_DIR/$svc"
  local log_file="$LOG_DIR/${svc}.log"
  local pid_file="$PID_DIR/${svc}.pid"

  [ ! -d "$svc_dir" ] && { log_warn "$svc — not found, skipping"; return 0; }

  # Kill existing
  if [ -f "$pid_file" ]; then
    local old_pid=$(cat "$pid_file" 2>/dev/null)
    kill "$old_pid" 2>/dev/null || true
    sleep 1
    rm -f "$pid_file"
  fi

  # Port check
  lsof -i ":$port" -sTCP:LISTEN &>/dev/null && { log_warn "$svc — port $port busy, skipping"; return 0; }

  # Install service-specific deps (don't fail script)
  [ -f "$svc_dir/requirements.txt" ] && pip install -r "$svc_dir/requirements.txt" --quiet 2>/dev/null || true

  # Environment variables for all services
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
  export JAEGER_ENDPOINT="http://localhost:14268/api/traces"
  export SERVICE_NAME="$svc"
  export SERVICE_PORT="$port"

  # Launch
  cd "$svc_dir"
  nohup "$VENV_DIR/bin/python" main.py > "$log_file" 2>&1 &
  local pid=$!
  echo "$pid" > "$pid_file"
  cd "$PROJECT_ROOT"

  sleep 2
  kill -0 "$pid" 2>/dev/null \
    && log_ok "$svc → http://localhost:$port  (PID: $pid)" \
    || log_err "$svc — failed (check .logs/${svc}.log)"
}

start_all_services() {
  log_step "Starting Microservices (8 services)"

  source "$VENV_DIR/bin/activate"
  export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/shared:$PYTHONPATH"

  for svc in "${SERVICE_ORDER[@]}"; do
    start_service "$svc"
  done

  echo ""
  local running=0
  for svc in "${SERVICE_ORDER[@]}"; do
    [ -f "$PID_DIR/${svc}.pid" ] && kill -0 "$(cat "$PID_DIR/${svc}.pid" 2>/dev/null)" 2>/dev/null && ((running++))
  done
  log_info "Microservices: ${GREEN}${running}/${#SERVICE_ORDER[@]}${NC} running"
}

# ─── Frontend ────────────────────────────────────────────────────────────────

start_frontend() {
  log_step "Starting Frontend (React + Three.js)"

  [ ! -d "$FRONTEND_DIR" ] && { log_err "Frontend dir not found"; return 0; }
  command -v node &>/dev/null || { log_err "Node.js not installed — skipping"; return 0; }

  local pid_file="$PID_DIR/frontend.pid"
  local log_file="$LOG_DIR/frontend.log"

  # Kill existing
  if [ -f "$pid_file" ]; then
    local old_pid=$(cat "$pid_file" 2>/dev/null)
    pkill -P "$old_pid" 2>/dev/null || true
    kill "$old_pid" 2>/dev/null || true
    sleep 2
    rm -f "$pid_file"
  fi

  lsof -i ":$FRONTEND_PORT" -sTCP:LISTEN &>/dev/null && { log_warn "Port $FRONTEND_PORT busy — skipping"; return 0; }

  cd "$FRONTEND_DIR"

  # Install deps if needed
  if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    npm install 2>/dev/null || true
  fi

  # Start React dev server in background
  GENERATE_SOURCEMAP=false BROWSER=none PORT=$FRONTEND_PORT \
    nohup npm start > "$log_file" 2>&1 &
  local pid=$!
  echo "$pid" > "$pid_file"
  cd "$PROJECT_ROOT"

  log_info "Waiting for frontend to compile (30-60s)..."
  local waited=0
  while [ $waited -lt 60 ]; do
    if curl -s -o /dev/null http://localhost:$FRONTEND_PORT 2>/dev/null; then
      log_ok "Frontend           → http://localhost:$FRONTEND_PORT  (PID: $pid)"
      return 0
    fi
    kill -0 "$pid" 2>/dev/null || { log_err "Frontend process died (check .logs/frontend.log)"; return 0; }
    sleep 5
    ((waited+=5))
  done

  kill -0 "$pid" 2>/dev/null \
    && log_ok "Frontend starting  → http://localhost:$FRONTEND_PORT  (PID: $pid)" \
    || log_err "Frontend failed (check .logs/frontend.log)"
}

# ─── Stop Everything ─────────────────────────────────────────────────────────

stop_all() {
  print_banner
  log_step "Stopping All STRATUM Services"

  if [ -d "$PID_DIR" ]; then
    for pid_file in "$PID_DIR"/*.pid(N); do
      local name=$(basename "$pid_file" .pid)
      local pid=$(cat "$pid_file" 2>/dev/null)
      if [ -n "$pid" ]; then
        pkill -P "$pid" 2>/dev/null || true
        kill "$pid" 2>/dev/null || true
        log_ok "Stopped $name (PID: $pid)"
      fi
      rm -f "$pid_file"
    done
  fi

  log_info "Stopping Docker Compose services..."
  cd "$PROJECT_ROOT"
  run_compose -f "$COMPOSE_FILE" down 2>&1 | while IFS= read -r line; do
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
    docker ps --filter "name=stratum-" --format "    {{.Names}}\t{{.Status}}" 2>/dev/null | sort
    echo -e "\n    ${GREEN}$infra_count containers running${NC}"
  else
    echo -e "    ${RED}No infrastructure containers running${NC}"
  fi

  echo ""
  echo -e "  ${BOLD}🔧 Microservices:${NC}"
  local svc_running=0
  for svc in "${SERVICE_ORDER[@]}"; do
    local port="${SERVICE_PORTS[$svc]}"
    local pid_file="$PID_DIR/${svc}.pid"
    local svc_state="${RED}stopped${NC}"
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file" 2>/dev/null)" 2>/dev/null; then
      local pid=$(cat "$pid_file")
      curl -s -o /dev/null http://localhost:$port 2>/dev/null \
        && svc_state="${GREEN}running${NC} → http://localhost:$port (PID: $pid)" \
        || svc_state="${YELLOW}starting${NC} (PID: $pid)"
      ((svc_running++))
    fi
    echo -e "    $svc: $svc_state"
  done
  echo -e "    ${CYAN}$svc_running/${#SERVICE_ORDER[@]} services running${NC}"

  echo ""
  echo -e "  ${BOLD}🖥️  Frontend:${NC}"
  if [ -f "$PID_DIR/frontend.pid" ] && kill -0 "$(cat "$PID_DIR/frontend.pid" 2>/dev/null)" 2>/dev/null; then
    echo -e "    ${GREEN}running${NC} → http://localhost:$FRONTEND_PORT (PID: $(cat "$PID_DIR/frontend.pid"))"
  else
    echo -e "    ${RED}stopped${NC}"
  fi

  echo ""
  echo -e "  ${BOLD}🌐 URLs:${NC}"
  echo "    Frontend:      http://localhost:$FRONTEND_PORT"
  echo "    Grafana:       http://localhost:3001"
  echo "    Prometheus:    http://localhost:9090"
  echo "    Neo4j:         http://localhost:7474"
  echo "    Jaeger:        http://localhost:16686"
  echo "    Kibana:        http://localhost:5601"
  echo "    Ray:           http://localhost:8265"
  echo "    MLflow:        http://localhost:5001"
  echo ""
}

# ─── Logs ────────────────────────────────────────────────────────────────────

show_logs() {
  print_banner
  log_step "Tailing All Logs (Ctrl+C to stop)"
  [ ! -d "$LOG_DIR" ] || [ -z "$(ls -A "$LOG_DIR" 2>/dev/null)" ] && { log_warn "No logs yet."; return 0; }
  tail -f "$LOG_DIR"/*.log 2>/dev/null
}

# ─── Main Full Startup ──────────────────────────────────────────────────────

start_full() {
  print_banner
  ensure_dirs
  preflight || return 1
  start_infrastructure

  if command -v python3 &>/dev/null; then
    setup_python_env
    start_all_services
  else
    log_warn "Python 3 not found — skipping microservices"
  fi

  if command -v node &>/dev/null; then
    start_frontend
  else
    log_warn "Node.js not found — skipping frontend"
  fi

  # Final summary
  echo ""
  echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${GREEN}${BOLD}🎉 STRATUM PROTOCOL — All Systems Online!${NC}                      ${CYAN}║${NC}"
  echo -e "${CYAN}╠════════════════════════════════════════════════════════════════╣${NC}"
  echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}🖥️  Frontend:${NC}        http://localhost:${FRONTEND_PORT}                     ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}🌐 API Gateway:${NC}      http://localhost:80                      ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}🔧 Microservices:${NC}                                              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    data-ingestion          http://localhost:8001              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    knowledge-graph         http://localhost:8002              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    state-estimation        http://localhost:8003              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    cascading-failure       http://localhost:8004              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    policy-optimization     http://localhost:8005              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    economic-intelligence   http://localhost:8006              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    decision-ledger         http://localhost:8007              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    citizen-behavior        http://localhost:8008              ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}📊 Dashboards:${NC}                                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Grafana      http://localhost:3001  (no login needed)      ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Prometheus   http://localhost:9090                          ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Neo4j        http://localhost:7474  (neo4j/stratum_dev)    ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Jaeger       http://localhost:16686                         ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Kibana       http://localhost:5601                          ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Ray          http://localhost:8265                          ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    MLflow       http://localhost:5001                          ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}🗄️  Databases:${NC}                                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    PostgreSQL   localhost:5432                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    TimescaleDB  localhost:5433                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    MongoDB      localhost:27017                                ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Redis        localhost:6380  (pass: dev_password)           ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Neo4j Bolt   localhost:7687                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}    Kafka        localhost:9092                                 ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${YELLOW}./start.sh --status${NC}  │  ${YELLOW}./start.sh --logs${NC}  │  ${YELLOW}./start.sh --stop${NC}  ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}                                                                ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}All services run in background. Terminal is free to use.${NC}     ${CYAN}║${NC}"
  echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

# ─── CLI Routing ─────────────────────────────────────────────────────────────

case "${1:-}" in
  --stop|-s)    stop_all ;;
  --status|-t)  show_status ;;
  --logs|-l)    show_logs ;;
  --infra|-i)   print_banner; ensure_dirs; preflight || exit 1; start_infrastructure ;;
  --backend|-b) print_banner; ensure_dirs; preflight || exit 1; start_infrastructure; setup_python_env; start_all_services ;;
  --frontend|-f) print_banner; ensure_dirs; preflight || exit 1; start_infrastructure; start_frontend ;;
  --help|-h)
    echo "STRATUM PROTOCOL — Full Stack Startup Script"
    echo ""
    echo "Usage: ./start.sh [option]"
    echo ""
    echo "  (no args)      Start everything: infra + backend + frontend"
    echo "  --infra, -i    Infrastructure only (Docker Compose)"
    echo "  --backend, -b  Infrastructure + all 8 microservices"
    echo "  --frontend, -f Infrastructure + frontend only"
    echo "  --stop, -s     Stop all services"
    echo "  --status, -t   Show system status"
    echo "  --logs, -l     Tail microservice logs"
    echo "  --help, -h     This help message"
    echo ""
    ;;
  "") start_full ;;
  *)  echo "Unknown option: $1"; echo "Run ./start.sh --help"; exit 1 ;;
esac
