from datetime import datetime, timedelta, timezone


class Date:
    class Format:
        YYYY_MM_DD = "%Y-%m-%d"
        YYYY_MM_DD_HHMMSS = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def format_time(date: datetime = None, format_str: str = Format.YYYY_MM_DD_HHMMSS):
        """格式化时间字符串"""
        date = date or datetime.now()
        return date.strftime(format_str)

    @staticmethod
    def convert_timezone(_timezone: int):
        """本地时间转为对应时区的时间"""
        utc = timezone(timedelta(hours=_timezone))
        return datetime.now().astimezone(utc)

    @staticmethod
    def now():
        """获取当前时间"""
        return datetime.now()
