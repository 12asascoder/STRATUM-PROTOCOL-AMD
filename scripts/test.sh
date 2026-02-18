#!/bin/bash

###############################################################################
# STRATUM PROTOCOL - Integration Test Runner
# Runs comprehensive integration tests across all services
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   STRATUM PROTOCOL - Integration Test Suite              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Configuration
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$WORKSPACE_DIR/tests/integration"
REPORT_DIR="$WORKSPACE_DIR/test-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create report directory
mkdir -p "$REPORT_DIR"

echo -e "${YELLOW}📋 Test Configuration:${NC}"
echo "  Workspace: $WORKSPACE_DIR"
echo "  Test Directory: $TEST_DIR"
echo "  Report Directory: $REPORT_DIR"
echo ""

# Check if services are running
echo -e "${YELLOW}🔍 Checking service availability...${NC}"

check_service() {
    local service_name=$1
    local port=$2
    local url="http://localhost:$port/health"
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $service_name (port $port) - Running"
        return 0
    else
        echo -e "  ${RED}✗${NC} $service_name (port $port) - Not responding"
        return 1
    fi
}

SERVICES_OK=true

check_service "Data Ingestion" 8001 || SERVICES_OK=false
check_service "Knowledge Graph" 8002 || SERVICES_OK=false
check_service "Cascading Failure" 8003 || SERVICES_OK=false
check_service "State Estimation" 8004 || SERVICES_OK=false
check_service "Citizen Behavior" 8005 || SERVICES_OK=false
check_service "Policy Optimization" 8006 || SERVICES_OK=false
check_service "Economic Intelligence" 8007 || SERVICES_OK=false
check_service "Decision Ledger" 8008 || SERVICES_OK=false

echo ""

if [ "$SERVICES_OK" = false ]; then
    echo -e "${RED}❌ Not all services are running!${NC}"
    echo "Please start services first:"
    echo "  ./scripts/dev-setup.sh"
    exit 1
fi

echo -e "${GREEN}✅ All services are running${NC}"
echo ""

# Install test dependencies
echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov httpx

# Run integration tests
echo ""
echo -e "${YELLOW}🧪 Running integration tests...${NC}"
echo ""

cd "$TEST_DIR"

pytest test_end_to_end.py \
    -v \
    --tb=short \
    --cov=../../services \
    --cov-report=html:"$REPORT_DIR/coverage_$TIMESTAMP" \
    --cov-report=term \
    --junit-xml="$REPORT_DIR/junit_$TIMESTAMP.xml" \
    --html="$REPORT_DIR/report_$TIMESTAMP.html" \
    --self-contained-html

TEST_EXIT_CODE=$?

echo ""
echo "═══════════════════════════════════════════════════════════"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
fi

echo ""
echo -e "${YELLOW}📊 Test Reports:${NC}"
echo "  HTML Report: $REPORT_DIR/report_$TIMESTAMP.html"
echo "  Coverage Report: $REPORT_DIR/coverage_$TIMESTAMP/index.html"
echo "  JUnit XML: $REPORT_DIR/junit_$TIMESTAMP.xml"
echo ""

# Open HTML report in browser (macOS)
if command -v open &> /dev/null; then
    echo "Opening HTML report in browser..."
    open "$REPORT_DIR/report_$TIMESTAMP.html"
fi

exit $TEST_EXIT_CODE
