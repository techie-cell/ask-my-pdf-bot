# ============================================================
# Logger Utility
# Centralized logging using loguru
# Writes to logs/ directory and console
# ============================================================

import sys
import os
from pathlib import Path
from loguru import logger


def setup_logger() -> None:
    """
    Configure loguru logger for the application.
    Creates separate log files for general logs and errors.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(os.getenv("LOGS_DIR", "logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Remove default loguru handler
    logger.remove()

    # Console handler - INFO and above
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File handler - All logs (DEBUG and above)
    logger.add(
        logs_dir / "app.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
        rotation="10 MB",    # Rotate when file hits 10MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",   # Compress rotated logs
    )

    # Error-only log file
    logger.add(
        logs_dir / "errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
        rotation="5 MB",
        retention="30 days",
    )

    logger.info("Logger initialized successfully")


# Initialize logger when module is imported
setup_logger()

# Export logger for use in other modules
__all__ = ["logger"]
