import os

import requests
from pydantic import ValidationError

from star_rail import constants
from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.module.mihoyo.account import Account, UserManager
from star_rail.utils import functional
from star_rail.utils.log import logger

from .gacha_data import Analyzer, create_xlsx, gacha_data_adapter, merge, parse_gacha_info
from .gacha_log import GachaData, GachaInfo, GachaLogFetcher, verify_gacha_log_url
from .gacha_url import *  # noqa
from .srgf import SrgfData, convert_to_app, convert_to_srgf, is_srgf_data

__all__ = [
    "export_by_input_url",
    "export_by_webcache",
    "export_by_user_profile",
    "export_to_xlsx",
    "export_to_srgf",
    "merge_or_import_data",
    "create_merge_dir",
]

_lang = i18n.gacha


def export_by_input_url():
    url = get_provider(ProviderType.CLIPBOARD)().get_url()
    if not url:
        return
    if not verify_gacha_log_url(url):
        return

    gacha_log_fetcher = GachaLogFetcher(url)
    try:
        gacha_log_fetcher.query()
    except requests.RequestException:
        logger.error(i18n.common.network.error)
        return
    uid = gacha_log_fetcher.uid
    gacha_log = gacha_log_fetcher.gacha_data

    user = Account(uid=uid, gacha_url=url)
    user.save_profile()
    UserManager().login(user)

    _save_and_show_result(user, gacha_log)


def export_by_webcache():
    user = UserManager().user
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    url = get_provider(ProviderType.WEB_CACHE, user)().get_url()
    if not url:
        return
    if not verify_gacha_log_url(url):
        return

    gacha_log_fetcher = _query_gacha_log(url, user)
    if gacha_log_fetcher is None:
        return
    _save_and_show_result(user, gacha_log_fetcher.gacha_data)


def export_by_user_profile():
    user = UserManager().user
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    url = get_provider(ProviderType.USER_PROFILE, user)().get_url()
    if not url:
        return
    if not verify_gacha_log_url(url):
        return

    gacha_log_fetcher = _query_gacha_log(url, user)
    if gacha_log_fetcher is None:
        return
    _save_and_show_result(user, gacha_log_fetcher.gacha_data)


def _query_gacha_log(url: str, user: Account):
    """查询抽卡记录并根据记录设置账户"""
    gacha_log_fetcher = GachaLogFetcher(url)
    try:
        gacha_log_fetcher.query()
    except requests.RequestException:
        logger.error(i18n.common.network.error)
        return None
    uid = gacha_log_fetcher.uid

    if uid != user.uid:
        logger.warning(_lang.diff_user, uid)
        user = Account(uid)

    user.gacha_url = url
    user.save_profile()
    UserManager().login(user)
    return gacha_log_fetcher


def _merge_history(user: Account, gacha_data):
    logger.debug("合并历史抽卡数据")
    if not user.gacha_log_json_path.exists():
        return True, gacha_data
    try:
        local_gacha_data = functional.load_json(user.gacha_log_json_path)
        local_gacha_data = GachaData(**gacha_data_adapter(local_gacha_data))
    except ValidationError:
        logger.error(_lang.validation_error.history)
        return False, None
    history_gacha_log = local_gacha_data.model_dump()
    if history_gacha_log:
        info = GachaInfo.gen(
            gacha_data["info"]["uid"],
            gacha_data["info"]["lang"],
            gacha_data["info"]["region_time_zone"],
        )
        gacha_data = merge(info, [gacha_data, history_gacha_log])
        logger.debug("合并完成")
    else:
        logger.debug("无需合并")
    return True, gacha_data


def _save_and_show_result(user: Account, gacha_data):
    res, gacha_data = _merge_history(user, gacha_data)
    if res is False:
        return
    functional.save_json(user.gacha_log_json_path, gacha_data)
    if settings.FLAG_GENERATE_XLSX:
        create_xlsx(user, gacha_data)
    if settings.FLAG_GENERATE_SRGF:
        srgf_data = convert_to_srgf(gacha_data)
        functional.save_json(user.srgf_path, srgf_data.model_dump())

    print(functional.color_str(_lang.export_finish, "green"))
    functional.pause()
    Analyzer._parse_gacha_data(user, gacha_data).visualization()


def show_analytical_result():
    user = UserManager().user
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    if not user.gacha_log_analyze_path.exists() and not user.gacha_log_json_path.exists():
        logger.warning(_lang.file_not_found, user.uid)
        return
    if not user.gacha_log_analyze_path.exists():
        analyzer = Analyzer.parse_file(user, user.gacha_log_json_path)
    else:
        analyzer = Analyzer.parse_file(user, user.gacha_log_analyze_path)
    analyzer.visualization()


def export_to_xlsx():
    user = UserManager().user
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
    user = UserManager().user
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    if not user.gacha_log_json_path.exists():
        logger.warning(_lang.file_not_found, user.uid)
        return
    gacha_data = functional.load_json(user.gacha_log_json_path)
    gacha_data = gacha_data_adapter(gacha_data)
    functional.save_json(user.srgf_path, convert_to_srgf(gacha_data).model_dump())
    logger.success(_lang.export_srgf_success)


def merge_or_import_data():
    user = UserManager().user
    if None is user:
        print(functional.color_str(_lang.retry, "yellow"))
        return
    merge_path = create_merge_dir()
    file_list = [
        name
        for name in os.listdir(merge_path)
        if os.path.isfile(os.path.join(merge_path, name)) and name.endswith(".json")
    ]
    if not file_list:
        logger.warning(_lang.import_data.unfind_file)
        return
    gacha_datas = []
    for file_name in file_list:
        file_path = os.path.join(merge_path, file_name)
        data = functional.load_json(file_path)
        if is_srgf_data(data) and user.uid == data["info"]["uid"]:
            try:
                SrgfData(info=data["info"], list=data["list"])
            except ValidationError:
                logger.warning(_lang.validation_error.srgf, file_name)
                continue
            data = convert_to_app(data)
        elif GachaData.is_gacha_data(data) and user.uid == data["info"]["uid"]:
            data = gacha_data_adapter(data)
            try:
                GachaData(**data)
            except ValidationError:
                logger.warning(_lang.validation_error.gacha_data, file_name)
                continue
        else:
            continue
        gacha_datas.append(data)

    if user.gacha_log_json_path.exists():
        try:
            local_gacha_data = functional.load_json(user.gacha_log_json_path)
            history_gacha_data = GachaData(**gacha_data_adapter(local_gacha_data))
        except ValidationError:
            logger.error(_lang.validation_error.history)
            return
        gacha_datas.append(history_gacha_data.model_dump())

    res, info = parse_gacha_info(user, gacha_datas)
    if res is False:
        logger.warning(_lang.import_data.info_inconsistent, info)
        return
    merge_result = merge(info, gacha_datas)
    functional.save_json(user.gacha_log_json_path, merge_result)
    logger.success(_lang.import_data.success)
    _save_and_show_result(user, merge_result)


def create_merge_dir():
    path = os.path.join(constants.ROOT_PATH, "merge")
    os.makedirs(path, exist_ok=True)
    return path
