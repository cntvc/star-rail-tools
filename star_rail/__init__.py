"""Genshin-Impact-Tools"""

__version__ = "0.1.1"

from star_rail.utils.functional import clear_screen

APP_NAME = "StarRailTools"


def about():
    _APP_NAME = "软件名: " + APP_NAME
    _HOME_PAGE = "项目主页: https://github.com/cntvc/star-rail-tools"
    _AUTHOR = "作者: cntvc"
    _EMAIL = "邮箱: cntvc@outlook.com"
    _VERSION = "软件版本: {}".format(__version__)

    description = [
        _APP_NAME,
        _VERSION,
        _HOME_PAGE,
        _AUTHOR,
        _EMAIL,
    ]
    clear_screen()
    for item in description:
        print(item)
    print()


def get_exe_name():
    return APP_NAME + "_{}.exe".format(__version__)
