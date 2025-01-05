import logging

logging.basicConfig(
    level=logging.INFO,  # Set the minimum level of severity to capture
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Format of log messages
    handlers=[logging.StreamHandler()],  # Output to console by default
)

logger = logging.getLogger(name="LOGGER")
