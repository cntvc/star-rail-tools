import argparse
import platform

from star_rail import __version__ as version
from star_rail import about, constant
from star_rail.config import config_status, settings, update_and_save
from star_rail.module import updater
from star_rail.module.gacha import (
    export_to_xlsx,
    export_use_clipboard,
    export_use_user_profile,
    export_use_webcache,
    show_analytical_results,
)
from star_rail.module.menu import Menu, MenuItem
from star_rail.module.updater import get_cur_version_info, parse_changelog
from star_rail.module.user import choose_user_menu, get_account_status
from star_rail.utils.functional import clear_files, clear_screen, color_str, get_format_time, pause
from star_rail.utils.log import logger


def init_menu():
    main_menu = MenuItem(
        title="主菜单",
        options=[
            MenuItem(
                title="账号设置",
                options=choose_user_menu,  # TODO 使用 MenuItem 创建菜单
            ),
            MenuItem(
                title="导出抽卡数据",
                options=[
                    MenuItem(
                        title="使用游戏缓存导出",
                        options=export_use_webcache,
                    ),
                    MenuItem(title="使用剪切板导出", options=export_use_clipboard),
                    MenuItem(
                        title="使用软件缓存导出",
                        options=export_use_user_profile,
                    ),
                    MenuItem(
                        title="导出到Execl表格文件",
                        options=export_to_xlsx,
                    ),
                ],
                tips=lambda: get_account_status(),
            ),
            MenuItem(title="合并抽卡数据", options=lambda: print("等待开发")),
            MenuItem(
                title="查看抽卡分析报告",
                options=lambda: show_analytical_results(),
            ),
            MenuItem(
                title="软件设置",
                options=[
                    MenuItem(
                        title="软件更新检测",
                        options=[
                            MenuItem(
                                title="打开",
                                options=lambda: update_and_save("FLAG_CHECK_UPDATE", True),
                            ),
                            MenuItem(
                                title="关闭",
                                options=lambda: update_and_save("FLAG_CHECK_UPDATE", False),
                            ),
                        ],
                        tips=lambda: config_status("FLAG_CHECK_UPDATE"),
                    ),
                    MenuItem(
                        title="导出到Execl表格",
                        options=[
                            MenuItem(
                                title="打开",
                                options=lambda: update_and_save("FLAG_GENERATE_XLSX", True),
                            ),
                            MenuItem(
                                title="关闭",
                                options=lambda: update_and_save("FLAG_GENERATE_XLSX", False),
                            ),
                        ],
                        tips=lambda: config_status("FLAG_GENERATE_XLSX"),
                    ),
                    MenuItem(title="自动备份", options=lambda: print("等待开发")),
                    MenuItem(title="切换语言", options=lambda: print("等待开发")),
                ],
            ),
            MenuItem(title="关于...", options=about),
        ],
        tips=lambda: get_account_status(),
    )
    return Menu(main_menu)


@logger.catch()
def start():
    logger.debug(" Launch the application ========================================\n")
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
        get_format_time(),
        platform.platform(),
        settings.as_dict(),
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", help="清理文件，文件路径以 `,` 分隔")
    parser.add_argument("--update-info", action="store_true", help="显示更新信息")

    args = parser.parse_args()
    logger.debug("args:{}", args)
    if args.clean:
        file_paths = args.clean.split(",")
        clear_files(file_paths)
    if args.update_info:
        logger.success("软件更新成功\n")
        print(color_str(version, "green") + " 版本更新日志：")
        print("=" * constant.MAX_MENU_LENGTH)
        print(parse_changelog(get_cur_version_info()))
        print("=" * constant.MAX_MENU_LENGTH)
        pause()

    if not args.update_info and settings.FLAG_CHECK_UPDATE:
        if not updater.update():
            pause()
            clear_screen()

    menu = init_menu()
    menu.run()


if __name__ == "__main__":
    start()
