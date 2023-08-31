# flake8: noqa
zh_cn_lang_pack = {
    # config
    "config.settings.current_status": "当前状态",
    "config.settings.open_success": "开启成功",
    "config.settings.close_success": "关闭成功",
    # i18n
    "i18n.update_lang.tips": "重启后使语言更改生效，是否继续？ y/N",
    "i18n.update_lang.invalid_input": "请输入有效的选项，只能输入 'y' 或 'N'。",
    # module/mihoyo/account
    "account.login_account_success": "成功设置账户：{}",
    "account.invalid_cookie": "未识别到有效的 Cookie 数据",
    "account.add_account_success": "添加账户成功, UID: {}",
    "account.update_cookie_success": "更新账户 Cookie 成功, UID: {}",
    "account.current_account": "当前账号 {}",
    "account.without_account": "当前未设置账号",
    "account.menu.select_account": "选择账户: {}",
    "account.menu.add_by_game_uid": "输入游戏 UID 添加账号",
    "account.menu.add_by_cookie": "通过 Cookie 添加账号",
    "account.menu.input_uid": "请输入用户UID, 输入 0 取消新建用户\n",
    "account.menu.invalid_uid_format": "请输入正确格式的UID",
    # module/record/client
    "record.client.fetch_record": "正在查询记录",
    "record.client.fetch_msg": "第 {task.fields[page]} 页",
    "record.client.analyze_update_time": "统计更新时间: ",
    "record.client.invalid_gacha_url": "未获取到有效抽卡链接",
    "record.client.record_info_data_error": "账户存储数据出现错误, record_info_uid: {}",
    "record.client.diff_account": "游戏当前账户与软件不一致，无法继续导出",
    "record.client.account_no_record_data": "账户无抽卡记录",
    "record.client.invalid_srgf_data": "文件 {} 不是标准的 SRGF 格式，本次导入将忽略该文件",
    "record.client.diff_account_srgf_data": "文件 {} 中数据不属于当前账户，本次导入将忽略该文件",
    "record.client.import_file_success": "成功导入文件 {}",
    "record.client.no_file_import": "未识别到有效数据文件",
    "record.client.export_file_success": "导出成功，文件位于 {} ",
    # module/game_client
    "game_client.unfind_game_log_file": "未找到游戏日志文件",
    "game_client.unfind_game_path": "未找到游戏路径",
    "game_client.unfind_game_cache_file": "未找到游戏网页缓存文件",
    # module/info
    "info.app_name": "软件名: ",
    "info.project_home": "项目主页: ",
    "info.author": "作者: ",
    "info.email": "邮箱: ",
    "info.app_version": "软件版本: {}",
    # module/updater
    "updater.invalid_input": "请输入有效的选项，只能输入 'y' 或 'N'。",
    "updater.download_failed": "下载新版本文件失败, 请检查网络连接状态",
    "updater.download_success": "新版本下载完成：{}，即将自动重启软件",
    "updater.download_canceled": "下载被取消",
    "updater.check_update": "正在检测软件更新...",
    "updater.check_update_net_error": "检测更新失败, 请检查网络连接状态",
    "updater.check_update_has_no_ctx": "检测更新失败，未获取到版本信息",
    "updater.is_latest_version": "当前已是最新版本",
    "updater.upgrade_success": "软件更新成功，当前版本: {}\n",
    "updater.delete_file_failed": "删除旧版本文件失败，请手动操作以删除文件: {}",
    "updater.changelog": "更新日志：",
    "updater.update_option": "检测到新版本 {}, 是否更新 y/N ? ",
    "updater.get_changelog_failed": "更新日志获取失败",
    "updater.select_update_source": "更新源已变更为 {}",
    "updater.update_source_status": "当前更新源为",
    # utils/menu
    "utils.menu.return_to_pre_menu": "0.返回上级菜单",
    "utils.menu.exit": "0.退出",
    "utils.menu.input_number": "请输入数字选择菜单项:",
    "utils.menu.invalid_input": "无效输入，请重试",
    # client
    "client.no_account": "请设置账户后重试",
    "client.empty_cookie": "未找到 cookie，请设置 cookie 后重试",
    # main-menu
    "main.menu.main_menu.home": "主菜单",
    # main-menu-account
    "main.menu.account_setting": "账号设置",
    # main-menu-gacha_record
    "main.menu.gacha_record.home": "跃迁记录",
    "main.menu.refresh_record_by_game_cache": "通过游戏缓存获取",
    "main.menu.refresh_record_by_clipboard": "通过剪切板获取",
    "main.menu.refresh_record_by_user_cache": "通过软件缓存获取",
    "main.menu.export_record_to_xlsx": "导出到 Execl 表格文件",
    "main.menu.export_record_to_srgf": "导出为 SRGF 通用格式文件",
    "main.menu.import_gacha_record": "导入跃迁记录",
    "main.menu.show_analyze_result": "查看分析结果",
    # main-menu-trailblaze_calendar
    "main.menu.trailblaze_calendar.home": "开拓月历",
    "main.menu.trailblaze_calendar.fetch": "获取开拓月历",
    "main.menu.trailblaze_calendar.show_history": "查看历史记录",
    # main-menu-setting
    "main.menu.settings.home": "软件设置",
    "main.menu.settings.auto_update": "自动更新",
    "main.menu.settings.update_source": "设置更新源",
    "main.menu.settings.update_source_coding": "Coding （国内推荐",
    "main.menu.settings.update_source_github": "Github",
    "main.menu.settings.language": "切换语言",
    "main.menu.about": "关于...",
    # 分析结果总览表
    "table.total.title": "统计结果",
    "table.total.project": "项目",
    "table.total.total_cnt": "抽卡总数",
    "table.total.star5_cnt": "5星总次数",
    "table.total.star5_avg_cnt": "5星平均抽数",
    "table.total.pity_cnt": "保底计数",
    # 5 星详情表
    "table.star5.title": "5星详情",
    "table.star5.pull_count": "抽",
    # 开拓月历
    "table.trailblaze_calendar.title": "开拓月历",
    "table.trailblaze_calendar.month": "日期",
    "table.trailblaze_calendar.hcoin": "星穹",
    "table.trailblaze_calendar.rails_pass": "票数",
    # Execl
    "execl.header.time": "时间",
    "execl.header.name": "名称",
    "execl.header.type": "类别",
    "execl.header.level": "星级",
    "execl.header.gacha_type": "跃迁类型",
    "execl.header.total_count": "总次数",
    "execl.header.pity_count": "保底计数",
    # common
    "common.open": "打开",
    "common.close": "关闭",
    # 卡池
    "regular_warp": "常驻跃迁",
    "starter_warp": "新手跃迁",
    "character_event_warp": "角色活动跃迁",
    "light_cone_event_warp": "光锥活动跃迁",
    # 异常
    "error.param_type_error": "参数类型错误，type: {}",
    "error.db_conn_error": "数据库连接错误",
    "error.request_error": "网络连接异常",
    "error.invalid_cookie_error": "Cookie 无效",
    "error.authkey_error": "链接错误",
    "error.invalid_authkey_error": "链接无效",
}
