import platform

from star_rail import __version__
from star_rail.config import settings
from star_rail.utils.time import TimeUtils


def get_sys_info():
    s_copy = settings.model_copy(deep=True)
    s_copy.ENCRYPT_KEY = "***"
    return (
        f"Software version:{__version__}\n",
        f"System time:{TimeUtils.get_format_time(TimeUtils.get_time())}\n",
        f"System version:{ platform.platform()}\n",
        f"Config: {s_copy.model_dump()}",
    )
