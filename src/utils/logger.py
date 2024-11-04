import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name, log_file, level=logging.INFO):
    """Function to set up a logger with file and console handlers"""
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger


# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Set up loggers for different components
api_logger = setup_logger("api", "logs/api.log")
model_logger = setup_logger("model", "logs/model.log")
data_logger = setup_logger("data", "logs/data.log")
