import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger("tui_log_viewer")
logger.setLevel(logging.INFO)
logger.propagate = False

log_directory = Path.home() / ".logtui" / "logs"
log_directory.mkdir(parents=True, exist_ok=True)

if not logger.handlers:
    handler = RotatingFileHandler(
        log_directory / "logtui.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d - %(name)s.%(funcName)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
