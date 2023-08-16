import platform
import time

from star_rail import __version__ as version
from star_rail.client import HSRClient
from star_rail.config import settings
from star_rail.core import DBClient, init_all_table
from star_rail.i18n import LanguageType, i18n, set_locales
from star_rail.module import AccountManager, updater
from star_rail.module.info import show_about
from star_rail.utils.log import logger
from star_rail.utils.menu import Menu, MenuItem
from star_rail.utils.time import get_format_time

_lang_menu = i18n.main.menu


def init_menu(client: HSRClient):
    main_menu = MenuItem(
        title=_lang_menu.main_menu.home,
        options=[
            MenuItem(
                title=_lang_menu.account_setting,
                gen_menu=lambda: AccountManager().gen_account_menu(),
                tips=lambda: AccountManager().get_status_desc(),
            ),
            MenuItem(
                title=_lang_menu.gacha_record.home,
                options=[
                    MenuItem(
                        title=_lang_menu.refresh_record_by_game_cache,
                        options=client.refresh_record_by_game_cache,
                    ),
                    MenuItem(
                        title=_lang_menu.refresh_record_by_clipboard,
                        options=client.refresh_record_by_clipboard,
                    ),
                    MenuItem(
                        title=_lang_menu.refresh_record_by_user_cache,
                        options=client.refresh_record_by_user_cache,
                    ),
                    MenuItem(
                        title=_lang_menu.export_record_to_xlsx,
                        options=client.export_record_to_xlsx,
                    ),
                    MenuItem(
                        title=_lang_menu.export_record_to_srgf,
                        options=client.export_record_to_srgf,
                    ),
                    MenuItem(
                        title=_lang_menu.import_gacha_record, options=client.import_gacha_record
                    ),
                    MenuItem(
                        title=_lang_menu.show_analyze_result,
                        options=client.show_analyze_result,
                    ),
                ],
                tips=lambda: AccountManager().get_status_desc(),
            ),
            MenuItem(
                title=_lang_menu.trailblaze_calendar.home,
                options=[
                    MenuItem(
                        title=_lang_menu.trailblaze_calendar.fetch,
                        options=client.refresh_month_info,
                    ),
                    MenuItem(
                        title=_lang_menu.trailblaze_calendar.show_history,
                        options=client.show_month_info,
                    ),
                ],
            ),
            MenuItem(
                title=_lang_menu.settings.home,
                options=[
                    MenuItem(
                        title=_lang_menu.settings.auto_update,
                        options=[
                            MenuItem(
                                title=i18n.common.open,
                                options=lambda: client.open_setting("FLAG_CHECK_UPDATE"),
                            ),
                            MenuItem(
                                title=i18n.common.close,
                                options=lambda: client.close_setting("FLAG_CHECK_UPDATE"),
                            ),
                        ],
                        tips=lambda: client.get_config_status("FLAG_CHECK_UPDATE"),
                    ),
                    MenuItem(
                        title=_lang_menu.settings.update_source,
                        options=[
                            MenuItem(
                                title=_lang_menu.settings.update_source_coding,
                                options=lambda: updater.select_updater_source(
                                    updater.UpdateSource.CODING
                                ),
                            ),
                            MenuItem(
                                title=_lang_menu.settings.update_source_github,
                                options=lambda: updater.select_updater_source(
                                    updater.UpdateSource.GITHUB
                                ),
                            ),
                        ],
                        tips=lambda: updater.get_update_source_status(),
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
        tips=lambda: AccountManager().get_status_desc(),
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
    if settings.FLAG_CHECK_UPDATE:
        updater.upgrade()
    init_all_table(DBClient())
    client = HSRClient()
    menu = init_menu(client)
    menu.run()


if __name__ == "__main__":
    run()
