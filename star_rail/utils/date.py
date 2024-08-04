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
    def local_to_timezone(target_tz_offset: int):
        """本地时间转为对应时区的时间"""
        local_time = datetime.now()
        local_tz = datetime.now(timezone.utc).astimezone().tzinfo
        target_tz = timezone(timedelta(hours=target_tz_offset))
        return local_time.replace(tzinfo=local_tz).astimezone(target_tz)

    @staticmethod
    def convert_timezone(time: str, tz_offset: int, target_tz_offset: int):
        dt = datetime.strptime(time, Date.Format.YYYY_MM_DD_HHMMSS)

        from_tz = timezone(timedelta(hours=tz_offset))
        target_tz = timezone(timedelta(hours=target_tz_offset))

        dt_with_tz = dt.replace(tzinfo=from_tz)

        converted_dt = dt_with_tz.astimezone(target_tz)

        return converted_dt.strftime(Date.Format.YYYY_MM_DD_HHMMSS)
