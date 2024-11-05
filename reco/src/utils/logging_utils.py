# src/utils/logging_utils.py

import logging
import os

def setup_logger(name, log_file, level=logging.INFO):
    """
    Set up a logger with the given name and log file.

    Args:
        name (str): Name of the logger.
        log_file (str): File to write logs to.
        level (int): Logging level.

    Returns:
        logging.Logger: Configured logger.
    """
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # Create a handler for writing to the log file
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    # Create a logger and set its level
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
