from pathlib import Path

from loguru import logger


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


logger.remove()


logger.add(
    LOG_DIR
    / "job_monitor_{time:YYYY-MM-DD}.log",

    rotation="00:00",

    retention="3 days",

    compression=None,

    level="INFO",

    enqueue=False,

    format=(
        "{time:YYYY-MM-DD HH:mm:ss} "
        "| {level:<8} "
        "| {message}"
    ),
)


__all__ = [
    "logger",
]