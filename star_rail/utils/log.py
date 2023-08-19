import os
import sys

from loguru import logger

from star_rail import constants

__all__ = ["init_logger"]


def init_logger():
    # 移除默认的日志输出
    logger.remove()

    # format DOC：https://loguru.readthedocs.io/en/stable/api/logger.html#record
    logger.add(sink=sys.stdout, format="<level>{message}</level>", level="INFO", colorize=True)

    logger.add(
        sink=os.path.join(constants.LOG_PATH, "log_{time:YYYY_MM}.log"),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | {file}:{line} | {function} | message: {message}",  # noqa
        level="DEBUG",
        rotation="5MB",
        compression="tar.gz",
    )
