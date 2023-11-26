import time
from enum import Enum

__all__ = ["TimeUtils"]


class TimeUtils:
    class TimeFormat(str, Enum):
        YYYY_MM_DD = "%Y-%m-%d"
        YYYY_MM_DD_HHMMSS = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def get_time():
        return time.time()

    @staticmethod
    def get_local_time():
        """获取本地时间"""
        return time.localtime(time.time())

    @staticmethod
    def convert_to_timestamp(std_time: time.struct_time):
        """转换为时间戳"""
        return int(time.mktime(std_time))

    @staticmethod
    def convert_to_time(std_time: time.struct_time):
        return time.mktime(std_time)

    @staticmethod
    def get_format_time(
        std_time: float = None, time_format: str = TimeFormat.YYYY_MM_DD_HHMMSS.value
    ):
        """格式化为字符串"""
        return time.strftime(time_format, time.localtime(std_time))

    @staticmethod
    def get_local_timezone(local_time: time.struct_time):
        """获取时区"""
        utc_offset_seconds = local_time.tm_gmtoff
        utc_offset_hours = abs(utc_offset_seconds) // 3600
        timezone = utc_offset_hours if utc_offset_seconds >= 0 else -utc_offset_hours
        return timezone

    @staticmethod
    def local_time_to_timezone(local_time: time.struct_time, target_timezone):
        """将时间转换为特定时区时间"""
        local_timezone = TimeUtils.get_local_timezone(local_time)
        target_time = time.mktime(local_time) + (target_timezone - local_timezone) * 3600
        return time.localtime(target_time)
