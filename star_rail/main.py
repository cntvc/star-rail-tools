import platform

from star_rail import __version__ as version
from star_rail.config import get_config_status_msg, settings
from star_rail.module.account import account_manager, gen_account_manu
from star_rail.module.gacha import (
    export_by_clipboard,
    export_by_user_profile,
    export_by_webcache,
    export_to_xlsx,
    show_analytical_result,
)
from star_rail.module.info import show_about
from star_rail.module.updater import upgrade
from star_rail.utils.functional import get_format_time
from star_rail.utils.log import logger
from star_rail.utils.menu import Menu, MenuItem


def init_menu():
    main_menu = MenuItem(
        title="主菜单",
        options=[
            MenuItem(
                title="账号设置",
                gen_menu=lambda: gen_account_manu(create_option=True),
                tips=lambda: account_manager.get_status_msg(),
            ),
            MenuItem(
                title="导出抽卡数据",
                options=[
                    MenuItem(
                        title="使用游戏缓存导出",
                        options=export_by_webcache,
                    ),
                    MenuItem(title="使用剪切板导出", options=export_by_clipboard),
                    MenuItem(
                        title="使用软件缓存导出",
                        options=export_by_user_profile,
                    ),
                    MenuItem(
                        title="导出到 Execl 表格文件",
                        options=export_to_xlsx,
                    ),
                    MenuItem(
                        title="导出到 SRGF 通用格式",
                        options=lambda: print("等待开发"),
                    ),
                ],
                tips=lambda: account_manager.get_status_msg(),
            ),
            MenuItem(title="合并抽卡数据", options=lambda: print("等待开发")),
            MenuItem(
                title="查看抽卡分析报告",
                options=lambda: show_analytical_result(),
            ),
            MenuItem(
                title="软件设置",
                options=[
                    MenuItem(
                        title="软件更新检测",
                        options=[
                            MenuItem(
                                title="打开",
                                options=lambda: settings.set("FLAG_CHECK_UPDATE", True),
                            ),
                            MenuItem(
                                title="关闭",
                                options=lambda: settings.set("FLAG_CHECK_UPDATE", False),
                            ),
                        ],
                        tips=lambda: get_config_status_msg("FLAG_CHECK_UPDATE"),
                    ),
                    MenuItem(
                        title="自动导出到 Execl 表格",
                        options=[
                            MenuItem(
                                title="打开",
                                options=lambda: settings.set("FLAG_GENERATE_XLSX", True),
                            ),
                            MenuItem(
                                title="关闭",
                                options=lambda: settings.set("FLAG_GENERATE_XLSX", False),
                            ),
                        ],
                        tips=lambda: get_config_status_msg("FLAG_GENERATE_XLSX"),
                    ),
                    MenuItem(title="自动导出到 SRGF 通用格式", options=lambda: print("等待开发")),
                    MenuItem(title="切换语言", options=lambda: print("等待开发")),
                ],
            ),
            MenuItem(title="关于...", options=show_about),
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
