"""Small shared helpers for safe file publication and application logging."""
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def configure_logging(project_root):
    logger = logging.getLogger("option_analyzer")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    path = Path(project_root) / "Logs" / "application.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not any(getattr(h, "baseFilename", None) == str(path.resolve()) for h in logger.handlers):
        for previous in logger.handlers[:]:
            logger.removeHandler(previous)
            previous.close()
        handler = RotatingFileHandler(path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


def log_event(event, **fields):
    # Callers supply counts, filenames and controlled status messages, never credentials.
    logging.getLogger("option_analyzer").info(json.dumps({"time": utc_now(), "event": event, **fields}))


def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".result-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_workbook(path, workbook):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".workbook-", suffix=".xlsx", dir=path.parent)
    os.close(fd)
    try:
        workbook.save(temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
