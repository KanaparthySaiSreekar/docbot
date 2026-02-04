#!/usr/bin/env python3
"""
Backup and verification script for DocBot SQLite database.

Creates timestamped backup with integrity checks and row count validation.
Cross-platform alternative to backup_verify.sh using Python's sqlite3 module.
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def print_error(message: str):
    """Print error message."""
    print(f"ERROR: {message}", file=sys.stderr)


def print_success(message: str):
    """Print success message."""
    print(f"SUCCESS: {message}")


def print_info(message: str):
    """Print info message."""
    print(f"INFO: {message}")


def verify_integrity(db_path: Path) -> bool:
    """Run integrity check on database."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()[0]
        conn.close()
        return result == "ok"
    except sqlite3.Error as e:
        print_error(f"Integrity check failed: {e}")
        return False


def get_table_row_counts(db_path: Path) -> dict[str, int]:
    """Get row counts for all user tables."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cursor.fetchall()]

        row_counts = {}
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table};")
            row_counts[table] = cursor.fetchone()[0]

        conn.close()
        return row_counts
    except sqlite3.Error as e:
        print_error(f"Failed to count rows: {e}")
        return {}


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> int:
    """Delete backups older than retention_days."""
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0

    for backup_file in backup_dir.glob("docbot_*.db"):
        if backup_file.stat().st_mtime < cutoff_time.timestamp():
            backup_file.unlink()
            deleted_count += 1

    return deleted_count


def main():
    """Main backup and verification logic."""
    parser = argparse.ArgumentParser(
        description="DocBot Database Backup & Verification"
    )
    parser.add_argument(
        "db_path",
        nargs="?",
        default="data/docbot.db",
        help="Path to database file (default: data/docbot.db)"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=7,
        help="Delete backups older than this many days (default: 7)"
    )

    args = parser.parse_args()

    db_path = Path(args.db_path)
    backup_dir = Path("data/backups")
    retention_days = args.retention_days

    # Check if database exists
    if not db_path.exists():
        print_error(f"Error: Database file not found: {db_path}")
        sys.exit(1)

    # Create backup directory
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for backup filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"docbot_{timestamp}.db"

    print("=" * 50)
    print("DocBot Database Backup & Verification")
    print("=" * 50)
    print(f"Source:     {db_path}")
    print(f"Backup:     {backup_path}")
    print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # Step 1: Create backup
    print_info("[1/4] Creating backup...")
    try:
        shutil.copy2(db_path, backup_path)
        print_success("Backup created")
    except Exception as e:
        print_error(f"Backup creation failed: {e}")
        sys.exit(1)
    print()

    # Step 2: Run integrity check on backup
    print_info("[2/4] Running integrity check on backup...")
    if verify_integrity(backup_path):
        print_success("Integrity check PASSED")
    else:
        print_error("Integrity check FAILED")
        sys.exit(1)
    print()

    # Step 3: Verify row counts match
    print_info("[3/4] Verifying row counts...")

    source_counts = get_table_row_counts(db_path)
    backup_counts = get_table_row_counts(backup_path)

    all_match = True
    for table in sorted(source_counts.keys()):
        source_count = source_counts[table]
        backup_count = backup_counts.get(table, -1)

        if source_count == backup_count:
            status = "MATCH"
        else:
            status = "MISMATCH"
            all_match = False

        print(f"  {table}: {source_count} rows - {status}")

    print()
    if all_match:
        print_success("Row count verification PASSED")
    else:
        print_error("Row count verification FAILED")
        sys.exit(1)
    print()

    # Step 4: Cleanup old backups
    print_info(f"[4/4] Cleaning up old backups (older than {retention_days} days)...")
    deleted_count = cleanup_old_backups(backup_dir, retention_days)

    if deleted_count > 0:
        print_success(f"Deleted {deleted_count} old backup(s)")
    else:
        print_success("No old backups to delete")
    print()

    # Final summary
    backup_size = backup_path.stat().st_size / 1024  # KB
    print("=" * 50)
    print_success("Backup completed and verified")
    print("=" * 50)
    print(f"Backup file: {backup_path}")
    print(f"Backup size: {backup_size:.1f} KB")
    print(f"Completed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()


if __name__ == "__main__":
    main()
