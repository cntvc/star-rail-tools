import os
import time

from pydantic import ValidationError

from star_rail import constants
from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.module.account import Account, account_manager
from star_rail.module.gacha.gacha_data import (
    analyze,
    convert_analyze_to_table,
    create_xlsx,
    is_app_gacha_data,
    merge,
)
from star_rail.module.gacha.gacha_log import GachaData, GachaLogFetcher, verify_gacha_log_url
from star_rail.module.gacha.gacha_url import *
from star_rail.module.gacha.srgf import SrgfData, convert_to_app, convert_to_srgf, is_srgf_data
from star_rail.utils import functional
from star_rail.utils.log import logger
from star_rail.utils.time import get_timezone
from star_rail.utils.version import compare_versions

__all__ = [
    "export_by_clipboard",
    "export_by_webcache",
    "export_by_user_profile",
    "export_to_xlsx",
    "export_to_srgf",
    "import_and_merge_data",
    "create_merge_dir",
]

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

    _save_and_show_result(user, gacha_log)


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
    _save_and_show_result(user, gacha_log_fetcher.gacha_data)


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
    _save_and_show_result(user, gacha_log_fetcher.gacha_data)


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


def _merge_history(user: Account, gacha_data):
    logger.debug("合并历史抽卡数据")
    if not user.gacha_log_json_path.exists():
        return
    try:
        local_gacha_data = GachaData.parse_file(user.gacha_log_json_path)
    except ValidationError:
        logger.error("历史数据校验失败，无法合并数据")
        return
    history_gacha_log = local_gacha_data.dict()
    if history_gacha_log:
        gacha_data = merge([gacha_data, history_gacha_log])
        logger.debug("合并完成")
    else:
        logger.debug("无需合并")


def _save_and_show_result(user: Account, gacha_data):
    _merge_history(user, gacha_data)
    functional.save_json(user.gacha_log_json_path, gacha_data)
    if settings.FLAG_GENERATE_XLSX:
        create_xlsx(user, gacha_data)

    analyze_data = analyze(user, gacha_data)
    print(functional.color_str(_lang.export_finish, "green"))
    functional.pause()
    _print_analytical_result(analyze_data)


def _print_analytical_result(analyze_data):
    overview, rank5_detail = convert_analyze_to_table(analyze_data)
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
        analyze_data = analyze(user, functional.load_json(user.gacha_log_json_path))
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
    create_xlsx(user, gacha_log)
    logger.success(_lang.export_xlsx_success)


def export_to_srgf():
    user = account_manager.account
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    if not user.gacha_log_json_path.exists():
        logger.warning(_lang.file_not_found, user.uid)
        return
    gacha_data = functional.load_json(user.gacha_log_json_path)
    if compare_versions(gacha_data["info"]["export_app_version"], "1.1.0") == -1:
        # 1.1.0 版本以下 gacha_log 不包含 region_time_zone 字段，设置为本地时区
        local_time = time.localtime(time.time())
        gacha_data["info"]["region_time_zone"] = get_timezone(local_time)
    functional.save_json(user.srgf_path, convert_to_srgf(gacha_data).dict())
    logger.success(_lang.export_srgf_success)


def import_and_merge_data():
    user = account_manager.account
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    merge_path = create_merge_dir()
    file_list = [
        name
        for name in os.listdir(merge_path)
        if os.path.isfile(os.path.join(merge_path, name)) and name.endswith(".json")
    ]
    gacha_datas = []
    for file_name in file_list:
        file_path = os.path.join(merge_path, file_name)
        data = functional.load_json(file_path)
        if is_srgf_data(data):
            try:
                SrgfData(data["info"], data["list"])
            except ValidationError:
                logger.warning("{} 文件 SRGF 格式校验失败，已忽略该文件", file_name)
                continue
            data = convert_to_app(data)
        elif is_app_gacha_data(data):
            try:
                GachaData(**data)
            except ValidationError:
                logger.warning("{} 文件抽卡数据校验失败，已忽略该文件", file_name)
                continue
        else:
            continue
        gacha_datas.append(data)
    if user.gacha_log_json_path.exists():
        try:
            history_gacha_data = GachaData.parse_file(user.gacha_log_json_path)
        except ValidationError:
            logger.error("历史数据校验失败，无法合并数据")
            return
        history_data = history_gacha_data.dict()
        gacha_datas.append(history_data)
    merge_result = merge(gacha_datas)
    functional.save_json(user.gacha_log_json_path, merge_result)
    logger.success("导入抽卡数据成功")
    _save_and_show_result(merge_result)


def create_merge_dir():
    path = os.path.join(constants.ROOT_PATH, "merge")
    os.makedirs(path, exist_ok=True)
    return path
