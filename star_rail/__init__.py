"""Genshin-Impact-Tools"""

__version__ = "0.1.0"

from star_rail.utils.functional import clear_screen

APP_NAME = "star rail tools"


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
