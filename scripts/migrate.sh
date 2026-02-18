#!/bin/bash

###############################################################################
# STRATUM PROTOCOL - Database Migration Script
# Handles schema migrations for PostgreSQL, Neo4j, and MongoDB
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   STRATUM PROTOCOL - Database Migration Tool             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default values
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-stratum_admin}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-dev_password}

NEO4J_HOST=${NEO4J_HOST:-localhost}
NEO4J_PORT=${NEO4J_PORT:-7687}
NEO4J_USER=${NEO4J_USER:-neo4j}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-dev_password}

MONGO_HOST=${MONGO_HOST:-localhost}
MONGO_PORT=${MONGO_PORT:-27017}
MONGO_USER=${MONGO_USER:-stratum_admin}
MONGO_PASSWORD=${MONGO_PASSWORD:-dev_password}

# Functions
migrate_postgres() {
    echo -e "${YELLOW}🗄️  Migrating PostgreSQL...${NC}"
    
    PGPASSWORD=$POSTGRES_PASSWORD psql \
        -h $POSTGRES_HOST \
        -p $POSTGRES_PORT \
        -U $POSTGRES_USER \
        -d stratum_main \
        -f infrastructure/init-scripts/01-init-postgres.sql
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL migration complete${NC}"
    else
        echo -e "${RED}❌ PostgreSQL migration failed${NC}"
        return 1
    fi
}

migrate_neo4j() {
    echo -e "${YELLOW}🕸️  Migrating Neo4j...${NC}"
    
    # Run Neo4j init script
    bash infrastructure/init-scripts/02-init-neo4j.sh
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Neo4j migration complete${NC}"
    else
        echo -e "${RED}❌ Neo4j migration failed${NC}"
        return 1
    fi
}

migrate_mongodb() {
    echo -e "${YELLOW}📄 Migrating MongoDB...${NC}"
    
    mongosh "mongodb://$MONGO_USER:$MONGO_PASSWORD@$MONGO_HOST:$MONGO_PORT" \
        < infrastructure/init-scripts/03-init-mongodb.js
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ MongoDB migration complete${NC}"
    else
        echo -e "${RED}❌ MongoDB migration failed${NC}"
        return 1
    fi
}

backup_databases() {
    echo -e "${YELLOW}💾 Creating database backups...${NC}"
    
    BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup PostgreSQL
    echo "  Backing up PostgreSQL..."
    PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
        -h $POSTGRES_HOST \
        -p $POSTGRES_PORT \
        -U $POSTGRES_USER \
        stratum_main > "$BACKUP_DIR/postgres_backup.sql"
    
    # Backup MongoDB
    echo "  Backing up MongoDB..."
    mongodump \
        --host $MONGO_HOST \
        --port $MONGO_PORT \
        --username $MONGO_USER \
        --password $MONGO_PASSWORD \
        --out "$BACKUP_DIR/mongodb_backup"
    
    echo -e "${GREEN}✅ Backups saved to: $BACKUP_DIR${NC}"
}

# Main execution
case "${1:-all}" in
    postgres)
        migrate_postgres
        ;;
    neo4j)
        migrate_neo4j
        ;;
    mongodb)
        migrate_mongodb
        ;;
    backup)
        backup_databases
        ;;
    all)
        echo "Migrating all databases..."
        echo ""
        migrate_postgres
        echo ""
        migrate_neo4j
        echo ""
        migrate_mongodb
        echo ""
        echo -e "${GREEN}✅ All database migrations complete!${NC}"
        ;;
    *)
        echo "Usage: $0 {postgres|neo4j|mongodb|backup|all}"
        echo ""
        echo "Options:"
        echo "  postgres  - Migrate PostgreSQL database only"
        echo "  neo4j     - Migrate Neo4j database only"
        echo "  mongodb   - Migrate MongoDB database only"
        echo "  backup    - Create backups of all databases"
        echo "  all       - Migrate all databases (default)"
        exit 1
        ;;
esac

exit 0
