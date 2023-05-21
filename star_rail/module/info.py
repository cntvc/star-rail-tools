from star_rail import __version__ as version
from star_rail.constants import APP_NAME
from star_rail.utils.functional import clear_screen


def show_about():
    _APP_NAME = "软件名: " + APP_NAME
    _HOME_PAGE = "项目主页: https://github.com/cntvc/star-rail-tools"
    _AUTHOR = "作者: cntvc"
    _EMAIL = "邮箱: cntvc@outlook.com"
    _VERSION = "软件版本: {}".format(version)

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
