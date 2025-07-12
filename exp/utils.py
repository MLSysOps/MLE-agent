#!/usr/bin/env python3
"""
Author: Li Yuanming
Email: yuanmingleee@gmail.com
Date: Jul 12, 2025
"""
import logging


def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger with the specified name and level.

    Args:
        name (str): The name of the logger.
        level (int): The logging level (default is INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    formatter = logging.Formatter('[%(asctime)s] [%(name)s:%(lineno)d] - %(levelname)s - %(message)s')

    # Remove all handlers (avoids duplicates from earlier logging setup)
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    ch = logging.StreamHandler()
    ch.setLevel(level)

    ch.setFormatter(formatter)

    logger.addHandler(ch)

    logger.propagate = False

    return logger
