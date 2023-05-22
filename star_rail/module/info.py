from star_rail import __version__ as version
from star_rail.constants import APP_NAME
from star_rail.i18n import i18n
from star_rail.utils.functional import clear_screen

_lang = i18n.info


def show_about():
    _APP_NAME = _lang.app_name + APP_NAME
    _HOME_PAGE = _lang.project_home + "https://github.com/cntvc/star-rail-tools"
    _AUTHOR = _lang.author + "cntvc"
    _EMAIL = _lang.email + "cntvc@outlook.com"
    _VERSION = _lang.app_version.format(version)

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
