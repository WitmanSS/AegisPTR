import logging
from typing import Any


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s %(message)s'
            )
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_event(component: str, message: str, **context: Any) -> None:
    logger = get_logger(component)
    if context:
        logger.info("%s | %s", message, context)
    else:
        logger.info(message)
