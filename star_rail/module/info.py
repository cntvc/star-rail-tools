from star_rail import __version__ as version
from star_rail.constants import APP_NAME
from star_rail.i18n import i18n
from star_rail.utils.functional import clear_screen


def show_about():
    _APP_NAME = i18n.info.app_name + APP_NAME
    _HOME_PAGE = i18n.info.project_home + "https://github.com/cntvc/star-rail-tools"
    _AUTHOR = i18n.info.author + "cntvc"
    _EMAIL = i18n.info.email + "cntvc@outlook.com"
    _VERSION = i18n.info.app_version.format(version)

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
