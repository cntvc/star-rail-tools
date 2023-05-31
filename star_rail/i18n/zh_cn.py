# flake8: noqa
zh_cn_lang_pack = {
    # config
    "config.settings.current_status": "当前状态",
    # i18n
    "i18n.update_lang.tips": "重启后使语言更改生效，是否继续？ y/N",
    "i18n.update_lang.invalid_input": "请输入有效的选项，只能输入 'y' 或 'N'。",
    # module/gacha
    "gacha.retry": "请设置账号后重试",
    "gacha.true_user": "游戏已登陆账号与软件设置账号不一致，将导出账号 {} 的数据",
    "gacha.export_finish": "数据导出完成，按任意键查看抽卡报告",
    "gacha.analyze_time": "统计时间:",
    "gacha.tips": "注：平均抽数不包括“保底计数”",
    "gacha.file_not_found": "未找到账号 {} 相关数据文件",
    "gacha.export_xlsx_success": "导出到 Execl 成功",
    "gacha.export_srgf_success": "导出为 SRGF 格式成功",
    "gacha.validation_error.history": "历史数据校验失败，无法合并数据",
    "gacha.validation_error.srgf": "'{}' 文件 SRGF 格式校验失败，已忽略该文件",
    "gacha.validation_error.gacha_data": "'{}' 文件抽卡数据校验失败，已忽略该文件",
    "gacha.import_data.success": "导入抽卡数据成功",
    # module/gacha_data
    "gacha_data.invalid_gacha_data": "无效的抽卡数据",
    # module/gacha/gacha_log
    "gacha_log.link_expires": "链接过期",
    "gacha_log.link_error": "链接错误",
    "gacha_log.error_code": "数据为空，错误代码：",
    "gacha_log.start_fetch": "开始查询抽卡记录",
    "gacha_log.fetch_status": "\033[K正在获取 {} 卡池数据 {}",
    "gacha_log.fetch_finish": "查询 {} 结束, 共 {} 条数据",
    # module/gacha/gacha_url
    "gacha_url.unfind_link": "未获取到抽卡链接",
    # module/account
    "account.account_uid": "当前账号 {}",
    "account.without_account": "当前未设置账号",
    # module/account-menu
    "account.menu.creat_user": "创建新用户",
    "account.menu.input_uid": "请输入用户UID, 输入 0 取消新建用户\n",
    "account.menu.invalid_uid_format": "请输入正确格式的UID",
    # module/game_client
    "game_client.game_log_not_found": "未找到游戏日志文件",
    "game_client.game_path_not_found": "未找到游戏路径",
    "game_client.game_webcache_file_not_found": "未找到游戏网页缓存文件",
    # module/info
    "info.app_name": "软件名: ",
    "info.project_home": "项目主页: ",
    "info.author": "作者: ",
    "info.email": "邮箱: ",
    "info.app_version": "软件版本: {}",
    # module/updater
    "updater.invalid_input": "请输入有效的选项，只能输入 'y' 或 'N'。",
    "updater.download_failed": "下载新版本文件失败, 请检查网络连接状态",
    "updater.download_success": "新版本下载完成：{}",
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
    # utils/clipboard
    "utils.clipboard.read_data_error": "剪切板读取出现错误",
    # utils/menu
    "utils.menu.return_to_pre_menu": "0.返回上级菜单",
    "utils.menu.exit": "0.退出",
    "utils.menu.input_number": "请输入数字选择菜单项:",
    "utils.menu.invalid_input": "无效输入，请重试",
    # main-menu
    "main.menu.todo": "等待开发",
    "main.menu.main_menu": "主菜单",
    # main-menu-account
    "main.menu.account_setting": "账号设置",
    # main-menu-gacha_log
    "main.menu.gacha_log.export": "导出抽卡数据",
    "main.menu.gacha_log.by_webcache": "使用游戏缓存导出",
    "main.menu.gacha_log.by_clipboard": "使用剪切板导出",
    "main.menu.gacha_log.by_appcache": "使用软件缓存导出",
    "main.menu.gacha_log.to_xlsx": "导出到 Execl 表格文件",
    "main.menu.gacha_log.to_srgf": "导出到 SRGF 通用格式",
    "main.menu.merge_gacha_log": "导入或合并数据",
    "main.menu.show_analyze_result": "查看抽卡分析报告",
    # main-menu-setting
    "main.menu.settings.home": "软件设置",
    "main.menu.settings.check_update": "自动更新",
    "main.menu.settings.update_source": "设置更新源",
    "main.menu.settings.update_source_coding": "Coding （国内推荐",
    "main.menu.settings.update_source_github": "Github",
    "main.menu.settings.export.to_xlsx": "自动导出到 Execl 表格",
    "main.menu.settings.export.srgf": "自动导出到 SRGF 通用格式",
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
}
