import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


class Date:
    class Format:
        YYYY_MM_DD = "%Y-%m-%d"
        YYYY_MM_DD_HHMMSS = "%Y-%m-%d %H:%M:%S"
        YYYYMMDDHHMMSS = "%Y%m%d%H%M%S"

    @staticmethod
    def now():
        return datetime.now()

    @staticmethod
    def local_time_to_timezone(target_tz_offset: int):
        """将当前本地时间转为对应时区的时间"""
        local_time = datetime.now()
        local_tz = datetime.now(timezone.utc).astimezone().tzinfo
        target_tz = timezone(timedelta(hours=target_tz_offset))
        return local_time.replace(tzinfo=local_tz).astimezone(target_tz)

    @staticmethod
    def convert_timezone(time: str, tz_offset: int, target_tz_offset: int):
        """将某个时区的日期字符串，转化为目标时区字符串"""
        dt = datetime.strptime(time, Date.Format.YYYY_MM_DD_HHMMSS)

        source_tz = timezone(timedelta(hours=tz_offset))
        target_tz = timezone(timedelta(hours=target_tz_offset))

        dt_with_tz = dt.replace(tzinfo=source_tz)
        converted_dt = dt_with_tz.astimezone(target_tz)

        return converted_dt.strftime(Date.Format.YYYY_MM_DD_HHMMSS)


def save_json(full_path: str | Path, data):
    path = Path(full_path)
    os.makedirs(path.parent, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, sort_keys=False, indent=4)


def load_json(full_path: str | Path) -> dict:
    with open(full_path, encoding="UTF-8") as file:
        data = json.load(file)
    return data
