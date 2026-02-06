#!/usr/bin/env python
"""
Cron script to send appointment reminders.

Usage:
    python scripts/run_reminders.py 24h  # Send 24-hour reminders
    python scripts/run_reminders.py 1h   # Send 1-hour reminders

Cron examples:
    0 * * * * cd /app && uv run python scripts/run_reminders.py 24h
    */15 * * * * cd /app && uv run python scripts/run_reminders.py 1h
"""
import asyncio
import logging
import sys

from docbot.logging_config import setup_logging
from docbot.reminder_service import run_reminder_job

setup_logging("INFO")
logger = logging.getLogger(__name__)


async def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("24h", "1h"):
        print("Usage: python scripts/run_reminders.py [24h|1h]")
        sys.exit(1)

    reminder_type = sys.argv[1]
    logger.info(f"Starting {reminder_type} reminder job")

    result = await run_reminder_job(reminder_type)

    logger.info(f"Reminder job complete: {result}")
    print(f"Sent: {result['sent']}, Failed: {result['failed']}, Skipped: {result['skipped']}")


if __name__ == "__main__":
    asyncio.run(main())
