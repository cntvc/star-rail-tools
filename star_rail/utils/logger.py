import os

from loguru import logger

from star_rail import constants

__all__ = ["logger"]

"""
日志格式化文档: https://loguru.readthedocs.io/en/stable/api/logger.html#record
"""

# 移除默认的日志输出
logger.remove()

# 文件输出
logger.add(
    sink=os.path.join(constants.LOG_PATH, "log_{time:YYYY_MM}.log"),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | {file.path}:{line} | {function} | message: {message}",  # noqa
    level="DEBUG",
    rotation="5MB",
    compression="tar.gz",
)
