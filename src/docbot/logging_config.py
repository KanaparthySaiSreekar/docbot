"""Pretty console logging with loguru + stdlib intercept."""

import logging
import sys
from contextvars import ContextVar

from loguru import logger

# Context variable for request correlation
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class InterceptHandler(logging.Handler):
    """Route all stdlib logging through loguru, preserving caller info and extras."""

    def emit(self, record: logging.LogRecord) -> None:
        # Find loguru level matching the stdlib level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Pass stdlib extras through to loguru
        # Filter out standard LogRecord attributes to get only user extras
        standard_attrs = {
            "name", "msg", "args", "created", "relativeCreated", "exc_info",
            "exc_text", "stack_info", "lineno", "funcName", "filename",
            "module", "pathname", "levelname", "levelno", "msecs", "message",
            "taskName", "process", "processName", "thread", "threadName",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_")
        }

        # Use the stdlib record's own caller info for accurate source location
        extras["_stdlib_name"] = record.name
        extras["_stdlib_func"] = record.funcName
        extras["_stdlib_line"] = record.lineno

        # Use depth=1 and patch to override the caller info from the record
        logger.bind(**extras).opt(exception=record.exc_info).log(
            level, record.getMessage()
        )


def _escape(text: str) -> str:
    """Escape angle brackets so loguru doesn't treat them as color tags."""
    return str(text).replace("<", r"\<").replace(">", r"\>")


def _format(record: dict) -> str:
    """Build a pretty log format string with optional extras."""
    extra = record["extra"]

    # Use stdlib caller info if intercepted, otherwise use loguru's
    name = _escape(extra.get("_stdlib_name", record["name"]))
    func = _escape(extra.get("_stdlib_func", record["function"]))
    line = extra.get("_stdlib_line", record["line"])

    # Base format with color-coded level and module
    fmt = (
        f"<green>{{time:HH:mm:ss}}</green> | "
        f"<level>{{level: <8}}</level> | "
        f"<cyan>{name}</cyan>:<cyan>{func}</cyan>:<cyan>{line}</cyan> - "
        f"<level>{{message}}</level>"
    )

    # Append request_id if present in extra
    req_id = extra.get("request_id")
    if req_id:
        fmt += f"  <dim>[{_escape(req_id):.8}]</dim>"

    # Append any other structured extras (skip internal keys)
    skip_keys = {"request_id", "_stdlib_name", "_stdlib_func", "_stdlib_line"}
    visible_extras = {
        k: v for k, v in extra.items()
        if k not in skip_keys and not k.startswith("_")
    }
    if visible_extras:
        parts = " ".join(
            f"<dim>{_escape(k)}</dim>=<yellow>{_escape(v)}</yellow>"
            for k, v in visible_extras.items()
        )
        fmt += "  " + parts

    fmt += "\n"

    if record["exception"]:
        fmt += "{exception}\n"

    return fmt


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure loguru for pretty console output and intercept stdlib logging.

    All existing code using `logging.getLogger(__name__)` will automatically
    route through loguru with zero changes needed.
    """
    # Remove default loguru handler
    logger.remove()

    # Add pretty console handler
    logger.add(
        sys.stdout,
        format=_format,
        level=log_level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Intercept all stdlib logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Suppress noisy loggers
    for noisy in ("uvicorn.access", "aiosqlite", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
