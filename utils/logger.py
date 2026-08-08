import logging
import sys
from config.settings import LOG_FILE

def setup_logger():
    """Setup and configure the application logger."""
    logger = logging.getLogger("KDynamics")
    logger.setLevel(logging.DEBUG)

    # File handler for all logs
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)

    # Console handler for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Create a global logger instance
logger = setup_logger()
