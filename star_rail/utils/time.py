import time
from enum import Enum

__all__ = ["get_format_time", "get_local_timezone", "local_time_to_timezone"]


class TimeFormat(str, Enum):
    YYYY_MM_DD = "%Y-%m-%d"
    YYYY_MM_DD_HHMMSS = "%Y-%m-%d %H:%M:%S"


def get_format_time(std_time: float = None, time_format: str = TimeFormat.YYYY_MM_DD_HHMMSS.value):
    """将时间格式化为字符串"""
    return time.strftime(time_format, time.localtime(std_time))


def get_local_timezone(local_time: time.struct_time):
    """获取本地时间的时区"""
    utc_offset_seconds = local_time.tm_gmtoff
    utc_offset_hours = abs(utc_offset_seconds) // 3600
    timezone = utc_offset_hours if utc_offset_seconds >= 0 else -utc_offset_hours
    return timezone


def local_time_to_timezone(local_time: time.struct_time, target_timezone):
    """将本地时间转换为特定时区时间"""
    local_timezone = get_local_timezone(local_time)
    target_time = time.mktime(local_time) + (target_timezone - local_timezone) * 3600
    return time.localtime(target_time)
