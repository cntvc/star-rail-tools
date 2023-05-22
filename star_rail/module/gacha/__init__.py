from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.module.account import Account, account_manager
from star_rail.module.gacha.gacha_log import (
    GachaDataProcessor,
    GachaLogFetcher,
    convert_to_table,
    verify_gacha_log_url,
)
from star_rail.module.gacha.gacha_url import *
from star_rail.utils import functional
from star_rail.utils.log import logger

_lang = i18n.gacha


def export_by_clipboard():
    url = get_provider(ProviderType.CLIPBOARD)().get_url()
    if not url:
        return
    if not verify_gacha_log_url(url):
        return

    gacha_log_fetcher = GachaLogFetcher(url)
    gacha_log_fetcher.query()
    uid = gacha_log_fetcher.uid
    gacha_log = gacha_log_fetcher.gacha_data

    user = Account(uid=uid, gacha_url=url)
    user.save_profile()
    account_manager.login(user)

    save_and_show_result(gacha_log)


def export_by_webcache():
    user = account_manager.account
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    url = get_provider(ProviderType.WEB_CACHE, user)().get_url()
    if not url:
        return
    if not verify_gacha_log_url(url):
        return

    gacha_log_fetcher = _query_gacha_log(url, user)
    save_and_show_result(gacha_log_fetcher.gacha_data)


def export_by_user_profile():
    user = account_manager.account
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    url = get_provider(ProviderType.USER_PROFILE, user)().get_url()
    if not url:
        return
    if not verify_gacha_log_url(url):
        return

    gacha_log_fetcher = _query_gacha_log(url, user)
    save_and_show_result(gacha_log_fetcher.gacha_data)


def _query_gacha_log(url: str, user: Account):
    """查询抽卡记录并根据记录设置账户"""
    gacha_log_fetcher = GachaLogFetcher(url)
    gacha_log_fetcher.query()
    uid = gacha_log_fetcher.uid

    if uid != user.uid:
        logger.warning(_lang.true_user, uid)
        user = Account(uid)

    user.gacha_url = url
    user.save_profile()
    account_manager.login(user)
    return gacha_log_fetcher


def save_and_show_result(gacha_log):
    data_processor = GachaDataProcessor(gacha_log)
    data_processor.merge_history()
    functional.save_json(data_processor.user.gacha_log_json_path, data_processor.gacha_data)
    if settings.FLAG_GENERATE_XLSX:
        data_processor.create_xlsx()

    analyze_data = data_processor.analyze()
    print(functional.color_str(_lang.export_finish, "green"))
    functional.pause()
    _print_analytical_result(analyze_data)


def _print_analytical_result(analyze_data):
    overview, rank5_detail = convert_to_table(analyze_data)
    functional.clear_screen()
    print("UID:", functional.color_str("{}".format(analyze_data["uid"]), "green"))
    print(_lang.analyze_time, analyze_data["time"])
    print(overview)
    print(functional.color_str(_lang.tips, "yellow"), end="\n\n")
    print(rank5_detail)


def show_analytical_result():
    user = account_manager.account
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    if not user.gacha_log_analyze_path.exists() and not user.gacha_log_json_path.exists():
        logger.warning(_lang.file_not_found, user.uid)
        return
    if not user.gacha_log_analyze_path.exists():
        data_processor = GachaDataProcessor(functional.load_json(user.gacha_log_json_path))
        analyze_data = data_processor.analyze()
    else:
        analyze_data = functional.load_json(user.gacha_log_analyze_path)

    _print_analytical_result(analyze_data)


def export_to_xlsx():
    user = account_manager.account
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    if not user.gacha_log_json_path.exists():
        logger.warning(_lang.file_not_found, user.uid)
        return
    gacha_log = functional.load_json(user.gacha_log_json_path)
    GachaDataProcessor(gacha_log).create_xlsx()
    logger.success(_lang.export_xlsx_success)
