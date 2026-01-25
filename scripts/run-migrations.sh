#!/bin/bash
# Run database migrations for Todo Chatbot
# Usage: ./scripts/run-migrations.sh [DATABASE_URL]

set -e

echo "=========================================="
echo "Todo Chatbot - Database Migrations"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get database URL from argument or environment
DB_URL="${1:-$DATABASE_URL}"

if [ -z "$DB_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL not provided${NC}"
    echo "Usage: $0 <database-url>"
    echo "Or set DATABASE_URL environment variable"
    exit 1
fi

# Parse DATABASE_URL for psql
# Format: postgresql+asyncpg://user:pass@host:port/dbname
# Convert to: postgresql://user:pass@host:port/dbname
PSQL_URL=$(echo "$DB_URL" | sed 's/postgresql+asyncpg/postgresql/')

MIGRATIONS_DIR="$(dirname "$0")/../backend/migrations"

if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo -e "${RED}ERROR: Migrations directory not found: $MIGRATIONS_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}Running migrations from: $MIGRATIONS_DIR${NC}"
echo ""

# Get list of migration files sorted by name
MIGRATION_FILES=$(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort)

if [ -z "$MIGRATION_FILES" ]; then
    echo -e "${YELLOW}No migration files found${NC}"
    exit 0
fi

# Run each migration
for file in $MIGRATION_FILES; do
    filename=$(basename "$file")
    echo -e "${YELLOW}Running migration: $filename${NC}"

    if psql "$PSQL_URL" -f "$file" 2>&1; then
        echo -e "${GREEN}✓ $filename completed${NC}"
    else
        echo -e "${RED}✗ $filename failed${NC}"
        exit 1
    fi
    echo ""
done

echo -e "${GREEN}=========================================="
echo "All migrations completed successfully!"
echo "==========================================${NC}"

# Verify schema
echo -e "\n${YELLOW}Verifying schema...${NC}"
echo "Tables:"
psql "$PSQL_URL" -c "\dt" 2>/dev/null || true

echo -e "\n${YELLOW}Tasks table columns:${NC}"
psql "$PSQL_URL" -c "\d tasks" 2>/dev/null || true
