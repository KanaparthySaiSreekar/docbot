#!/usr/bin/env python3
"""
Admin override CLI tool for direct database corrections.

Provides safe administrative operations on the DocBot SQLite database.
All write operations require --confirm flag for safety.
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Import state machine for validation (needs Python path adjustment)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
try:
    from docbot.state_machine import transition, VALID_TRANSITIONS, AppointmentStatus
except ImportError as e:
    print(f"Error: Cannot import state machine module: {e}", file=sys.stderr)
    print("Ensure you run this script from the project root.", file=sys.stderr)
    sys.exit(1)


def format_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Format data as ASCII table."""
    if not rows:
        return "No results."

    # Convert all values to strings
    str_rows = [[str(val) if val is not None else "" for val in row] for row in rows]

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in str_rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    # Build table
    lines = []

    # Header
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # Rows
    for row in str_rows:
        lines.append(" | ".join(val.ljust(w) for val, w in zip(row, col_widths)))

    return "\n".join(lines)


def log_action(action: str, details: str = ""):
    """Log administrative action with timestamp."""
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"[{timestamp}] ADMIN ACTION: {action}")
    if details:
        print(f"  Details: {details}")


def list_appointments(conn: sqlite3.Connection, date: str):
    """List all appointments for a specific date."""
    cursor = conn.execute(
        """
        SELECT id, patient_phone, appointment_date, slot_time, status, created_at
        FROM appointments
        WHERE appointment_date = ?
        ORDER BY slot_time
        """,
        (date,)
    )

    rows = cursor.fetchall()
    headers = ["ID", "Patient Phone", "Appointment Date", "Slot Time", "Status", "Created At"]

    print(f"\nAppointments for {date}:")
    print(format_table(headers, rows))
    print(f"\nTotal: {len(rows)} appointments")


def get_appointment(conn: sqlite3.Connection, appointment_id: str):
    """Show full appointment details."""
    cursor = conn.execute(
        """
        SELECT id, patient_phone, patient_name, patient_age, patient_gender,
               consultation_type, appointment_date, slot_time, status,
               razorpay_payment_id, razorpay_order_id, razorpay_refund_id,
               google_calendar_event_id, google_meet_link, language,
               created_at, updated_at, cancelled_at, refunded_at
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,)
    )

    row = cursor.fetchone()
    if not row:
        print(f"Error: Appointment {appointment_id} not found", file=sys.stderr)
        sys.exit(1)

    # Print as key-value pairs
    print(f"\nAppointment Details:")
    print(f"  ID:                   {row[0]}")
    print(f"  Patient Phone:        {row[1]}")
    print(f"  Patient Name:         {row[2]}")
    print(f"  Patient Age:          {row[3]}")
    print(f"  Patient Gender:       {row[4]}")
    print(f"  Consultation Type:    {row[5]}")
    print(f"  Appointment Date:     {row[6]}")
    print(f"  Slot Time:            {row[7]}")
    print(f"  Status:               {row[8]}")
    print(f"  Razorpay Payment ID:  {row[9]}")
    print(f"  Razorpay Order ID:    {row[10]}")
    print(f"  Razorpay Refund ID:   {row[11]}")
    print(f"  Calendar Event ID:    {row[12]}")
    print(f"  Google Meet Link:     {row[13]}")
    print(f"  Language:             {row[14]}")
    print(f"  Created At:           {row[15]}")
    print(f"  Updated At:           {row[16]}")
    print(f"  Cancelled At:         {row[17]}")
    print(f"  Refunded At:          {row[18]}")


def update_status(conn: sqlite3.Connection, appointment_id: str, status: str, confirm: bool):
    """Update appointment status with state machine validation."""
    if not confirm:
        print("Error: --confirm flag required for write operations", file=sys.stderr)
        sys.exit(1)

    # Get current status
    cursor = conn.execute(
        "SELECT status FROM appointments WHERE id = ?",
        (appointment_id,)
    )
    row = cursor.fetchone()
    if not row:
        print(f"Error: Appointment {appointment_id} not found", file=sys.stderr)
        sys.exit(1)

    current_status = row[0]

    # Validate transition
    try:
        new_status = transition(current_status, status)
    except ValueError as e:
        print(f"Error: Invalid status transition - {e}", file=sys.stderr)
        sys.exit(1)

    # Update status
    cursor = conn.execute(
        """
        UPDATE appointments
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_status, datetime.now(timezone.utc).isoformat(), appointment_id)
    )
    conn.commit()

    log_action(
        f"Update status for appointment {appointment_id}",
        f"{current_status} -> {new_status}"
    )
    print(f"Success: Status updated to {new_status}")


def release_locks(conn: sqlite3.Connection, expired_only: bool, confirm: bool):
    """Release slot locks (expired only or all)."""
    if not confirm:
        print("Error: --confirm flag required for write operations", file=sys.stderr)
        sys.exit(1)

    if expired_only:
        # Delete expired locks (older than 10 minutes)
        cursor = conn.execute(
            """
            DELETE FROM slot_locks
            WHERE datetime(locked_until) < datetime('now')
            """
        )
        deleted = cursor.rowcount
        conn.commit()
        log_action(f"Released {deleted} expired slot locks")
        print(f"Success: Released {deleted} expired locks")
    else:
        # Delete all locks (dangerous!)
        cursor = conn.execute("DELETE FROM slot_locks")
        deleted = cursor.rowcount
        conn.commit()
        log_action(f"Released ALL {deleted} slot locks (CAUTION)")
        print(f"Success: Released ALL {deleted} locks")


def run_sql(conn: sqlite3.Connection, query: str):
    """Execute arbitrary read-only SQL query."""
    # Safety check: only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        print("Error: Only SELECT queries are allowed", file=sys.stderr)
        sys.exit(1)

    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()

        # Get column names
        headers = [desc[0] for desc in cursor.description]

        print("\nQuery Results:")
        print(format_table(headers, rows))
        print(f"\nTotal: {len(rows)} rows")

    except sqlite3.Error as e:
        print(f"Error: SQL query failed - {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DocBot Admin Override Tool - Direct database operations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--db",
        required=True,
        help="Path to SQLite database file"
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm write operations (required for safety)"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-appointments
    list_parser = subparsers.add_parser("list-appointments", help="List appointments for a date")
    list_parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")

    # get-appointment
    get_parser = subparsers.add_parser("get-appointment", help="Show full appointment details")
    get_parser.add_argument("--id", required=True, help="Appointment UUID")

    # update-status
    update_parser = subparsers.add_parser("update-status", help="Update appointment status")
    update_parser.add_argument("--id", required=True, help="Appointment UUID")
    update_parser.add_argument(
        "--status",
        required=True,
        choices=[s.value for s in AppointmentStatus],
        help="New status"
    )

    # release-locks
    locks_parser = subparsers.add_parser("release-locks", help="Release slot locks")
    locks_parser.add_argument(
        "--expired",
        action="store_true",
        help="Only release expired locks (older than 10 minutes)"
    )

    # run-sql
    sql_parser = subparsers.add_parser("run-sql", help="Execute read-only SQL query")
    sql_parser.add_argument("--query", required=True, help="SELECT query to execute")

    args = parser.parse_args()

    # Check database exists
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database file not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    # Connect to database
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        print(f"Error: Cannot connect to database - {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Route to command handler
        if args.command == "list-appointments":
            list_appointments(conn, args.date)
        elif args.command == "get-appointment":
            get_appointment(conn, args.id)
        elif args.command == "update-status":
            update_status(conn, args.id, args.status, args.confirm)
        elif args.command == "release-locks":
            release_locks(conn, args.expired, args.confirm)
        elif args.command == "run-sql":
            run_sql(conn, args.query)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
