import os
import sys

from loguru import logger

from star_rail import constant

__all__ = ["logger"]

config = {
    # format DOC：https://loguru.readthedocs.io/en/stable/api/logger.html#record
    "handlers": [
        {
            "sink": sys.stdout,
            "format": "<level>{message}</level>",
            "level": "INFO",
            "colorize": True,
        },
        {
            "sink": os.path.join(constant.APP_LOG_PATH, "log_{time:YYYY-MM}.log"),
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | {file}:{line} | {function}()  | message: {message}",  # noqa
            "level": "DEBUG",
            "rotation": "1 MB",
            "compression": "tar.gz",
        },
    ],
}

logger.configure(**config)
