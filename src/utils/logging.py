import logging
import os
from logging.handlers import RotatingFileHandler


def configure_root_logger(log_level: int, log_file: str = None) -> None:
    """
    Configures the root logger, applying the configuration to all loggers.

    :param log_level: Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
    :param log_file: Optional log file to write logs to.
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Log format
    formatter = logging.Formatter(
        '%(levelname)s:\t%(asctime)s\t[%(name)s] %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (if log_file is specified)
    if log_file:
        # Ensure the log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Rotating file handler
        fh = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Avoid log duplication by setting propagate to False
    logger.propagate = False
