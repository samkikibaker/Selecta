import os
import logging

from selecta.utils import log_dir

def generate_logger(debug_mode=False):
    # Define a log directory for the app logs
    os.makedirs(log_dir, exist_ok=True)

    # Define the log file path
    log_file = os.path.join(log_dir, "selecta.log")

    # Create handlers
    handlers = [logging.FileHandler(log_file, mode="a", encoding="utf-8")]

    if debug_mode:
        handlers.append(logging.StreamHandler())  # Also log to console if in debug mode

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if debug_mode else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    logger = logging.getLogger()  # Get the root logger
    return logger
