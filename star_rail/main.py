# flake8: noqa:  F405
import platform
import time

from star_rail import __version__ as version
from star_rail.client import *
from star_rail.config import get_config_status_desc, settings
from star_rail.core import init_all_table
from star_rail.core.db_client import DBClient
from star_rail.i18n import LanguageType, i18n, set_locales
from star_rail.module import GachaClient
from star_rail.module.info import show_about
from star_rail.module.mihoyo.account import UserManager
from star_rail.module.updater import (
    UpdateSource,
    get_update_source_status,
    select_updater_source,
    upgrade,
)
from star_rail.utils.log import logger
from star_rail.utils.menu import Menu, MenuItem
from star_rail.utils.time import get_format_time

_lang_menu = i18n.main.menu


def init_menu(client: GachaClient):
    main_menu = MenuItem(
        title=_lang_menu.main_menu,
        options=[
            MenuItem(
                title=_lang_menu.account_setting,
                gen_menu=lambda: UserManager().gen_account_menu(),
                tips=lambda: UserManager().get_status_desc(),
            ),
            MenuItem(
                title=_lang_menu.gacha_log.home,
                options=[
                    MenuItem(
                        title=_lang_menu.gacha_log.fetch_by_webcache,
                        options=client.refresh_record_by_game_cache,
                    ),
                    MenuItem(
                        title=_lang_menu.gacha_log.fetch_by_clipboard,
                        options=client.refresh_record_by_clipboard,
                    ),
                    MenuItem(
                        title=_lang_menu.gacha_log.fetch_by_appcache,
                        options=client.refresh_record_by_user_cache,
                    ),
                    MenuItem(
                        title=_lang_menu.gacha_log.to_xlsx,
                        options=client.export_record_to_xlsx,
                    ),
                    MenuItem(
                        title=_lang_menu.gacha_log.to_srgf,
                        options=client.export_record_to_srgf,
                    ),
                    MenuItem(title=_lang_menu.merge_gacha_log, options=client.import_gacha_record),
                    MenuItem(
                        title=_lang_menu.show_analyze_result,
                        options=client.show_analyze_result,
                    ),
                ],
                tips=lambda: UserManager().get_status_desc(),
            ),
            MenuItem(
                title=_lang_menu.trailblaze_calendar.home,
                options=[
                    MenuItem(
                        title=_lang_menu.trailblaze_calendar.fetch, options=refresh_month_info
                    ),
                    MenuItem(
                        title=_lang_menu.trailblaze_calendar.show_history,
                        options=show_month_info,
                    ),
                ],
            ),
            MenuItem(
                title=_lang_menu.settings.home,
                options=[
                    MenuItem(
                        title=_lang_menu.settings.check_update,
                        options=[
                            MenuItem(
                                title=i18n.common.open,
                                options=lambda: settings.set_and_save("FLAG_CHECK_UPDATE", True),
                            ),
                            MenuItem(
                                title=i18n.common.close,
                                options=lambda: settings.set_and_save("FLAG_CHECK_UPDATE", False),
                            ),
                        ],
                        tips=lambda: get_config_status_desc("FLAG_CHECK_UPDATE"),
                    ),
                    MenuItem(
                        title=_lang_menu.settings.update_source,
                        options=[
                            MenuItem(
                                title=_lang_menu.settings.update_source_coding,
                                options=lambda: select_updater_source(UpdateSource.CODING),
                            ),
                            MenuItem(
                                title=_lang_menu.settings.update_source_github,
                                options=lambda: select_updater_source(UpdateSource.GITHUB),
                            ),
                        ],
                        tips=lambda: get_update_source_status(),
                    ),
                    MenuItem(
                        title=_lang_menu.settings.language,
                        options=[
                            MenuItem(
                                title="简体中文",
                                options=lambda: set_locales(LanguageType.ZH_CN),
                            ),
                            MenuItem(
                                title="English",
                                options=lambda: set_locales(LanguageType.EN_US),
                            ),
                        ],
                    ),
                ],
            ),
            MenuItem(title=_lang_menu.about, options=show_about),
        ],
        tips=lambda: UserManager().get_status_desc(),
    )
    return Menu(main_menu)


@logger.catch()
def run():
    logger.debug(" Launch the application ========================================")
    logger.debug(
        (
            "\n"
            "Software version:{}\n"
            "System time:{}\n"
            "System version:{}\n"
            "--------------------\n"
            "Config: {}\n"
            "===================="
        ),
        version,
        get_format_time(time.time()),
        platform.platform(),
        settings.model_dump(),
    )
    # create_merge_dir()
    if settings.FLAG_CHECK_UPDATE:
        upgrade()
    init_all_table(DBClient())
    client = GachaClient()
    menu = init_menu(client)
    menu.run()


if __name__ == "__main__":
    run()
