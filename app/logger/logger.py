# logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

app_log_file = os.path.join(LOG_DIR, "app.log")
error_log_file = os.path.join(LOG_DIR, "error.log")

# Define format
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File handler for normal app logs
app_handler = RotatingFileHandler(app_log_file, maxBytes=5_000_000, backupCount=3)
app_handler.setFormatter(formatter)
app_handler.setLevel(logging.INFO)

# File handler for errors
error_handler = RotatingFileHandler(error_log_file, maxBytes=5_000_000, backupCount=3)
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)

# Root logger
logging.basicConfig(level=logging.INFO, handlers=[app_handler, error_handler])

# Remove uvicorn’s default handlers to prevent console spam
logging.getLogger("uvicorn.access").addHandler(logging.StreamHandler())  # show only requests
logging.getLogger("uvicorn.error").propagate = False  # silence uvicorn internal logs

def get_logger(name: str):
    """Return a logger for a specific module."""
    return logging.getLogger(name)
