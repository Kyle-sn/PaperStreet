import logging

LOG_FORMAT = (
    "%(asctime)s %(levelname)s "
    "[%(filename)s/%(funcName)s.%(lineno)d]: %(message)s"
)


def setup_logger(name: str = None, level=logging.INFO):
    logger = logging.getLogger(name)

    if not logger.handlers:  # Prevent adding handlers multiple times
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            LOG_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        logger.setLevel(level)
        logger.addHandler(handler)

    return logger
