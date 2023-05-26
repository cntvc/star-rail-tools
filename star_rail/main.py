import platform

from star_rail import __version__ as version
from star_rail.config import get_config_status_msg, settings
from star_rail.i18n import LanguageType, i18n, set_locales
from star_rail.module.account import account_manager, gen_account_manu
from star_rail.module.gacha import (
    export_by_clipboard,
    export_by_user_profile,
    export_by_webcache,
    export_to_xlsx,
    show_analytical_result,
)
from star_rail.module.info import show_about
from star_rail.module.updater import (
    UpdateSource,
    get_update_source_status,
    select_updater_source,
    upgrade,
)
from star_rail.utils.functional import get_format_time
from star_rail.utils.log import logger
from star_rail.utils.menu import Menu, MenuItem

_lang = i18n.main.menu


def init_menu():
    main_menu = MenuItem(
        title=_lang.main_menu,
        options=[
            MenuItem(
                title=_lang.account_setting,
                gen_menu=lambda: gen_account_manu(create_option=True),
                tips=lambda: account_manager.get_status_msg(),
            ),
            MenuItem(
                title=_lang.gacha_log.export,
                options=[
                    MenuItem(
                        title=_lang.gacha_log.by_webcache,
                        options=export_by_webcache,
                    ),
                    MenuItem(title=_lang.gacha_log.by_clipboard, options=export_by_clipboard),
                    MenuItem(
                        title=_lang.gacha_log.by_appcache,
                        options=export_by_user_profile,
                    ),
                    MenuItem(
                        title=_lang.gacha_log.to_xlsx,
                        options=export_to_xlsx,
                    ),
                    MenuItem(
                        title=_lang.gacha_log.to_srgf,
                        options=lambda: print(_lang.todo),
                    ),
                ],
                tips=lambda: account_manager.get_status_msg(),
            ),
            MenuItem(title=_lang.merge_gacha_log, options=lambda: print(_lang.todo)),
            MenuItem(
                title=_lang.show_analyze_result,
                options=lambda: show_analytical_result(),
            ),
            MenuItem(
                title=_lang.settings.home,
                options=[
                    MenuItem(
                        title=_lang.settings.check_update,
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
                        tips=lambda: get_config_status_msg("FLAG_CHECK_UPDATE"),
                    ),
                    MenuItem(
                        title=_lang.settings.update_source,
                        options=[
                            MenuItem(
                                title=_lang.settings.update_source_coding,
                                options=lambda: select_updater_source(UpdateSource.CODING),
                            ),
                            MenuItem(
                                title=_lang.settings.update_source_github,
                                options=lambda: select_updater_source(UpdateSource.GITHUB),
                            ),
                        ],
                        tips=lambda: get_update_source_status(),
                    ),
                    MenuItem(
                        title=_lang.settings.export.to_xlsx,
                        options=[
                            MenuItem(
                                title=i18n.common.open,
                                options=lambda: settings.set_and_save("FLAG_GENERATE_XLSX", True),
                            ),
                            MenuItem(
                                title=i18n.common.close,
                                options=lambda: settings.set_and_save("FLAG_GENERATE_XLSX", False),
                            ),
                        ],
                        tips=lambda: get_config_status_msg("FLAG_GENERATE_XLSX"),
                    ),
                    MenuItem(
                        title=_lang.settings.export.srgf,
                        options=lambda: print(_lang.todo),
                    ),
                    MenuItem(
                        title=_lang.settings.language,
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
            MenuItem(title=_lang.about, options=show_about),
        ],
        tips=lambda: account_manager.get_status_msg(),
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
        ).format(version, get_format_time(), platform.platform(), settings.dict())
    )
    if settings.FLAG_CHECK_UPDATE:
        upgrade()
    menu = init_menu()
    menu.run()


if __name__ == "__main__":
    run()
