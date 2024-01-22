import platform

from star_rail import __version__
from star_rail.config import settings
from star_rail.utils.date import Date


def get_sys_info():
    s_copy = settings.model_copy(deep=True)
    s_copy.ENCRYPT_KEY = "***"
    return (
        "\n"
        f"Software version:{__version__}\n"
        f"System time:{Date.format_time()}\n"
        f"System version:{ platform.platform()}\n"
        f"Config: {s_copy.model_dump()}"
    )
