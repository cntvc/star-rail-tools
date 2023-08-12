import platform
import time

from star_rail import __version__ as version
from star_rail.config import get_config_status_desc, settings
from star_rail.i18n import LanguageType, i18n, set_locales
from star_rail.module.gacha import (
    create_merge_dir,
    export_by_input_url,
    export_by_user_profile,
    export_by_webcache,
    export_to_srgf,
    export_to_xlsx,
    merge_or_import_data,
    show_analytical_result,
)
from star_rail.module.info import show_about
from star_rail.module.mihoyo.account import AccountMenu, account_manager
from star_rail.module.month import export_month_info
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


def init_menu():
    main_menu = MenuItem(
        title=_lang_menu.main_menu,
        options=[
            MenuItem(
                title=_lang_menu.account_setting,
                gen_menu=lambda: AccountMenu().create(),
                tips=lambda: account_manager.get_status_desc(),
            ),
            MenuItem(
                title=_lang_menu.gacha_log.home,
                options=[
                    MenuItem(
                        title=_lang_menu.gacha_log.fetch_by_webcache,
                        options=export_by_webcache,
                    ),
                    MenuItem(
                        # TODO 修改函数名称
                        title=_lang_menu.gacha_log.fetch_by_clipboard,
                        options=export_by_input_url,
                    ),
                    MenuItem(
                        title=_lang_menu.gacha_log.fetch_by_appcache,
                        options=export_by_user_profile,
                    ),
                    MenuItem(
                        title=_lang_menu.gacha_log.to_xlsx,
                        options=export_to_xlsx,
                    ),
                    MenuItem(
                        title=_lang_menu.gacha_log.to_srgf,
                        options=export_to_srgf,
                    ),
                    MenuItem(title=_lang_menu.merge_gacha_log, options=merge_or_import_data),
                    MenuItem(
                        title=_lang_menu.show_analyze_result,
                        options=lambda: show_analytical_result(),
                    ),
                ],
                tips=lambda: account_manager.get_status_desc(),
            ),
            MenuItem(
                title="开拓月历",
                options=[
                    MenuItem(title="获取开拓月历", options=export_month_info),
                    MenuItem(
                        title="查看记录",
                        options=lambda: print("待实现"),
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
                    MenuItem(
                        title=_lang_menu.settings.export.to_xlsx,
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
                        tips=lambda: get_config_status_desc("FLAG_GENERATE_XLSX"),
                    ),
                    MenuItem(
                        title=_lang_menu.settings.export.srgf,
                        options=[
                            MenuItem(
                                title=i18n.common.open,
                                options=lambda: settings.set_and_save("FLAG_GENERATE_SRGF", True),
                            ),
                            MenuItem(
                                title=i18n.common.close,
                                options=lambda: settings.set_and_save("FLAG_GENERATE_SRGF", False),
                            ),
                        ],
                        tips=lambda: get_config_status_desc("FLAG_GENERATE_SRGF"),
                    ),
                    # TODO
                    MenuItem(
                        title="统计显示新手跃迁卡池",
                        options=lambda: print("待实现"),
                    ),
                ],
            ),
            MenuItem(title=_lang_menu.about, options=show_about),
        ],
        tips=lambda: account_manager.get_status_desc(),
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
    create_merge_dir()
    if settings.FLAG_CHECK_UPDATE:
        upgrade()
    menu = init_menu()
    menu.run()


if __name__ == "__main__":
    run()
