import os
import sys
from typing import TypedDict

from loguru import logger

from star_rail import constants

__all__ = ["logger"]

"""
日志格式化文档: https://loguru.readthedocs.io/en/stable/api/logger.html#record
"""


def database_filter_for_default(record: TypedDict):
    """数据库模块过滤器：只保留error级别及以上的记录"""
    if record["module"] == "database":
        return record["level"].no >= logger.level("ERROR").no
    return True


def database_filter_for_db(record: TypedDict):
    """数据库模块中，只保留低于error级别的记录"""
    return record["module"] == "database" and record["level"].no < logger.level("ERROR").no


# 移除默认的日志输出
logger.remove()

# 控制台输出
logger.add(sink=sys.stdout, format="<level>{message}</level>", level="INFO", colorize=True)

# 默认的文件输出
logger.add(
    sink=os.path.join(constants.LOG_PATH, "log_{time:YYYY_MM}.log"),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | {file}:{line} | {function} | message: {message}",  # noqa
    level="DEBUG",
    rotation="5MB",
    compression="tar.gz",
    filter=database_filter_for_default,
)

# SQL语句输出
logger.add(
    sink=os.path.join(constants.LOG_PATH, "sql_{time:YYYY_MM}.log"),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | {file}:{line} | {function} | message: {message}",  # noqa
    level="DEBUG",
    rotation="5MB",
    compression="tar.gz",
    filter=database_filter_for_db,
)
