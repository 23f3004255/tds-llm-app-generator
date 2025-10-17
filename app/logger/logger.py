import logging
import os
from logging.handlers import RotatingFileHandler

# --- Ensure logs directory exists ---
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# --- Define log file paths ---
app_log_file = os.path.join(LOG_DIR, "app.log")
error_log_file = os.path.join(LOG_DIR, "error.log")

# --- Define log format ---
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Create file handlers ---
app_handler = RotatingFileHandler(app_log_file, maxBytes=5_000_000, backupCount=3)
app_handler.setFormatter(formatter)
app_handler.setLevel(logging.INFO)

error_handler = RotatingFileHandler(error_log_file, maxBytes=5_000_000, backupCount=3)
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)

# --- Configure root logger ---
logging.basicConfig(level=logging.INFO, handlers=[app_handler, error_handler])

# --- Silence uvicorn internal spam, keep request logs visible ---
logging.getLogger("uvicorn.error").propagate = False
logging.getLogger("uvicorn.access").addHandler(logging.StreamHandler())

def get_logger(name: str):
    """Return a logger for a specific module."""
    return logging.getLogger(name)

# --- Force log files to be created immediately ---
_ = get_logger(__name__)
logging.info("Log system initialized and files ensured.")
