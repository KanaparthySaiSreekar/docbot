#!/bin/bash
# Backup and verification script for DocBot SQLite database
# Creates timestamped backup with integrity checks and row count validation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DB_PATH="${1:-data/docbot.db}"
BACKUP_DIR="data/backups"
RETENTION_DAYS=7

# Check if database exists
if [[ ! -f "$DB_PATH" ]]; then
    echo -e "${RED}Error: Database file not found: $DB_PATH${NC}" >&2
    exit 1
fi

# Check if sqlite3 is installed
if ! command -v sqlite3 &> /dev/null; then
    echo -e "${RED}Error: sqlite3 command not found. Please install SQLite.${NC}" >&2
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp for backup filename
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
BACKUP_PATH="$BACKUP_DIR/docbot_$TIMESTAMP.db"

echo "========================================="
echo "DocBot Database Backup & Verification"
echo "========================================="
echo "Source:     $DB_PATH"
echo "Backup:     $BACKUP_PATH"
echo "Started at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Step 1: Create backup
echo -e "${YELLOW}[1/4] Creating backup...${NC}"
cp "$DB_PATH" "$BACKUP_PATH"
echo -e "${GREEN}✓ Backup created${NC}"
echo ""

# Step 2: Run integrity check on backup
echo -e "${YELLOW}[2/4] Running integrity check on backup...${NC}"
INTEGRITY_RESULT=$(sqlite3 "$BACKUP_PATH" "PRAGMA integrity_check;")

if [[ "$INTEGRITY_RESULT" == "ok" ]]; then
    echo -e "${GREEN}✓ Integrity check PASSED${NC}"
else
    echo -e "${RED}✗ Integrity check FAILED:${NC}"
    echo "$INTEGRITY_RESULT"
    exit 1
fi
echo ""

# Step 3: Verify row counts match
echo -e "${YELLOW}[3/4] Verifying row counts...${NC}"

# Get list of tables
TABLES=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")

ALL_MATCH=true
VERIFICATION_SUMMARY=""

for TABLE in $TABLES; do
    # Count rows in source
    SOURCE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $TABLE;")

    # Count rows in backup
    BACKUP_COUNT=$(sqlite3 "$BACKUP_PATH" "SELECT COUNT(*) FROM $TABLE;")

    # Check if counts match
    if [[ "$SOURCE_COUNT" == "$BACKUP_COUNT" ]]; then
        STATUS="${GREEN}✓ MATCH${NC}"
        VERIFICATION_SUMMARY+="  $TABLE: $SOURCE_COUNT rows $STATUS\n"
    else
        STATUS="${RED}✗ MISMATCH${NC}"
        VERIFICATION_SUMMARY+="  $TABLE: Source=$SOURCE_COUNT, Backup=$BACKUP_COUNT $STATUS\n"
        ALL_MATCH=false
    fi
done

# Print verification summary
echo -e "$VERIFICATION_SUMMARY"

if [[ "$ALL_MATCH" == "false" ]]; then
    echo -e "${RED}✗ Row count verification FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Row count verification PASSED${NC}"
fi
echo ""

# Step 4: Cleanup old backups
echo -e "${YELLOW}[4/4] Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"

DELETED_COUNT=0
while IFS= read -r OLD_BACKUP; do
    if [[ -n "$OLD_BACKUP" ]]; then
        rm -f "$OLD_BACKUP"
        ((DELETED_COUNT++))
    fi
done < <(find "$BACKUP_DIR" -name "docbot_*.db" -type f -mtime +$RETENTION_DAYS)

if [[ $DELETED_COUNT -gt 0 ]]; then
    echo -e "${GREEN}✓ Deleted $DELETED_COUNT old backup(s)${NC}"
else
    echo -e "${GREEN}✓ No old backups to delete${NC}"
fi
echo ""

# Final summary
BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
echo "========================================="
echo -e "${GREEN}SUCCESS: Backup completed and verified${NC}"
echo "========================================="
echo "Backup file: $BACKUP_PATH"
echo "Backup size: $BACKUP_SIZE"
echo "Completed at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

exit 0
