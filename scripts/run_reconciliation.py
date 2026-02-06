#!/usr/bin/env python3
"""
Reconciliation script for cron job.

Run nightly: 0 2 * * * cd /app && python scripts/run_reconciliation.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docbot.database import get_db
from docbot.reconciliation import run_reconciliation
import logging

logger = logging.getLogger(__name__)


async def main():
    """Run reconciliation job."""
    logger.info("Starting scheduled reconciliation")

    try:
        async for db in get_db():
            results = await run_reconciliation(db)

        logger.info(f"Reconciliation completed: {results}")

        # Exit with error code if critical issues found
        if results["calendar_retries"]["failed"] > 0:
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        logger.error(f"Reconciliation failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
