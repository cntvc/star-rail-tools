from star_rail.config import settings
from star_rail.module.gacha.gacha_log import (
    analyze_gacha_log,
    analyze_result,
    create_xlsx,
    merge_history,
    query_gacha_log,
)
from star_rail.module.gacha.gacha_url import (
    get_url_from_clipboard,
    get_url_from_user_profile,
    get_url_from_webcache,
    verify_gacha_url,
)
from star_rail.module.user import Account, User
from star_rail.utils.functional import clear_screen, color_str, load_json, pause, save_json
from star_rail.utils.log import logger


def export_use_clipboard():
    url = get_url_from_clipboard()
    if not url:
        logger.warning("从剪切板未读取到抽卡链接")
        return
    if not verify_gacha_url(url):
        return
    uid, gacha_log = query_gacha_log(url)
    gacha_log = merge_history(uid, gacha_log)
    user = User(uid)
    user.gacha_url = url
    user.save_profile()
    save_gacha_log(user, gacha_log)


def export_use_webcache():
    user = Account().login_user
    if None is user:
        logger.warning("请设置账号后重试")
        return
    url = get_url_from_webcache(user)
    if not verify_gacha_url(url):
        return
    uid, gacha_log = query_gacha_log(url)
    if uid != user.uid:
        logger.warning("游戏已登陆账号与软件设置账号不一致，将导出账号 {} 的数据", uid)
        user = User(uid)
    user.gacha_url = url
    user.save_profile()
    save_gacha_log(user, gacha_log)


def export_use_user_profile():
    user = Account().login_user
    if None is user:
        logger.warning("请设置账号后重试")
        return
    url = get_url_from_user_profile(user)
    if not verify_gacha_url(url):
        return
    uid, gacha_log = query_gacha_log(url)
    if uid != user.uid:
        logger.warning("游戏已登陆账号与软件设置账号不一致，将导出账号 {} 的数据", uid)
        user = User(uid)
    user.gacha_url = url
    user.save_profile()
    save_gacha_log(user, gacha_log)


def save_gacha_log(user: User, gacha_log):
    save_json(user.gacha_log_json_path, gacha_log)
    if settings.FLAG_GENERATE_XLSX:
        create_xlsx(user, gacha_log)
    analyze_data = analyze_gacha_log(user, gacha_log)
    overview, rank5_detail = analyze_result(analyze_data)
    print("数据导出完成，按任意键查看抽卡报告")
    pause()
    clear_screen()
    print("UID:", color_str("{}".format(analyze_data["uid"]), "green"), end="\n")
    print("统计时间:", analyze_data["time"])
    print(overview, end="\n")
    print(color_str("注：平均抽数不包括“保底内抽数”", "yellow"), end="\n\n")
    print(rank5_detail)


def show_analytical_results():
    user = Account().login_user
    if None is user:
        logger.warning("请设置账号后重试")
        return
    if not user.gacha_log_analyze_path.exists():
        logger.warning("未找到{}的分析报告文件", user.uid)
        return
    analyze_data = load_json(user.gacha_log_analyze_path)
    overview, rank5_detail = analyze_result(analyze_data)
    clear_screen()
    print("UID:", color_str("{}".format(analyze_data["uid"]), "green"), end="\n")
    print("统计时间:", analyze_data["time"])
    print(overview, end="\n")
    print(color_str("注：平均抽数不包括“保底内抽数”", "yellow"), end="\n\n")
    print(rank5_detail)
