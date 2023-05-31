import time


def get_format_time(std_time: float = None, time_format: str = "%Y-%m-%d %H:%M:%S"):
    return time.strftime(time_format, time.localtime(std_time))


def get_timezone(local_time: time.struct_time):
    utc_offset_seconds = local_time.tm_gmtoff
    utc_offset_hours = abs(utc_offset_seconds) // 3600
    timezone = utc_offset_hours if utc_offset_seconds >= 0 else -utc_offset_hours
    return timezone


def convert_time_to_timezone(local_time: time.struct_time, timezone):
    local_timezone = get_timezone(local_time)
    converted_time = time.mktime(local_time) + (timezone - local_timezone) * 3600
    return time.localtime(converted_time)
