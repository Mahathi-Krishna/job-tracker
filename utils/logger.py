from pathlib import Path

from loguru import logger

LOG_DIR = Path("logs")

LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    LOG_DIR / "job_monitor.log",
    rotation="1 day",
    retention="7 days",
    compression=None,
    level="INFO",
    enqueue=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

__all__ = ["logger"]