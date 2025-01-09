import os

from loguru import logger

from star_rail import constants

__all__ = ["logger", "init_logger"]

"""
loguru wiki: https://loguru.readthedocs.io/en/stable/api.html
"""


def init_logger():
    # 移除默认的日志输出
    logger.remove()

    # 文件输出
    logger.add(
        sink=os.path.join(constants.LOG_PATH, "star_rail_tools_{time:YYYYMMDD_HHmmss}.log"),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | {name}:{line} | {function} | message: {message}",  # noqa
        level="DEBUG",
        retention=30,
    )
