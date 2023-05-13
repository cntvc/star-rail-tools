import html
import json
import os
import re
import tempfile
import traceback
from pathlib import Path
from typing import Optional

import requests
import win32api
from win32api import CopyFile

from star_rail import constant
from star_rail.config import app_profile
from star_rail.exceptions import PathNotExistError
from star_rail.module.clipboard import get_clipboad_text_or_html
from star_rail.module.user import User
from star_rail.utils.functional import color_str
from star_rail.utils.log import logger


def get_url_from_user_profile(user: User):
    logger.debug("从配置文件获取抽卡链接")

    return user.gacha_url


def get_url_from_clipboard():
    logger.debug("从剪切板获取抽卡链接")
    try:
        text = get_clipboad_text_or_html()
    except win32api.error as e:
        print(color_str(e.winerror, "red"))
        logger.debug(traceback.format_exc())
        return None
    logger.debug(f"get_clipboad_text_or_html {text}")
    url = get_url_from_string(text)
    if not url:
        return None
    url = concatenate_url(html.unescape(url))
    return url


def get_url_from_webcache(user: User):
    logger.debug("从游戏缓存获取抽卡链接")
    cache_file = get_webcache_path(user)

    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp_file:
        tmp_file_name = tmp_file.name
    try:
        CopyFile(str(cache_file), str(tmp_file_name))
    except win32api.error:
        print(color_str("游戏缓存读取失败", "red"))
        logger.debug(traceback.format_exc())
        return None

    logger.debug("开始读取缓存")
    with open(tmp_file_name, "rb") as file:
        results = file.read().split(b"1/0/")
    os.remove(tmp_file_name)

    url = None
    # reverse order traversal
    for result in results[::-1]:
        result = result.decode(errors="ignore")
        text = get_url_from_string(result)
        if text:
            url = text
            break

    if not url:
        logger.error("从缓存文件中未找到抽卡链接，请到游戏内查看抽卡记录后重试")
        return None
    url = concatenate_url(url)
    return url


def get_webcache_path(user: User):
    # 从 profile 读取路径，不存在则重新获取路径
    cache_path = app_profile.game_path_cn if user.region == "cn" else app_profile.game_path_os
    if os.path.exists(cache_path):
        return cache_path

    game_log_path = "miHoYo/崩坏：星穹铁道/"
    if user.region == "global":
        game_log_path = "Cognosphere/Star Rail/"
    log_path = Path(constant.GAME_RUNTIME_LOG_PATH, game_log_path, "Player.log")
    if not log_path.exists():
        raise PathNotExistError("未找到游戏日志文件")
    try:
        log_text = log_path.read_text(encoding="utf8")
    except UnicodeDecodeError as err:
        logger.debug(f"日志文件编码不是utf8, 尝试默认编码 {err}")
        log_text = log_path.read_text(encoding=None)
    data_path = "StarRail_Data"
    res = re.search("([A-Z]:/.+{})".format(data_path), log_text)
    game_path = res.group() if res else None
    if not game_path:
        raise PathNotExistError("未找到游戏路径")
    data_2_path = os.path.join(game_path, "webCaches/Cache/Cache_Data/data_2")
    if not os.path.isfile(data_2_path):
        raise PathNotExistError("未找到游戏缓存文件")
    if user.region == "cn":
        app_profile.game_path_cn = data_2_path
    else:
        app_profile.game_path_os = data_2_path
    app_profile.save()
    return data_2_path


def concatenate_url(url: str):
    spliturl = url.split("?")
    if "webstatic-sea.hoyoverse.com" in spliturl[0] or "api-os-takumi" in spliturl[0]:
        spliturl[0] = "https://api-os-takumi.mihoyo.com/common/gacha_record/api/getGachaLog"
    else:
        spliturl[0] = "https://api-takumi.mihoyo.com/common/gacha_record/api/getGachaLog"
    url = "?".join(spliturl)
    return url


URL_RE = re.compile("https://.+?&auth_appid=webview_gacha&.+?authkey=.+?&game_biz=hkrpg_.+?")


def get_url_from_string(string: Optional[str]) -> Optional[str]:
    if not string:
        return None
    res = URL_RE.search(string)
    return res.group() if res else None


def verify_gacha_url(url: str):
    logger.debug("验证链接有效性")
    logger.debug(url)

    if not url:
        logger.warning("链接无效")
        return False

    res = requests.get(url, timeout=constant.TIMEOUT).content.decode("utf-8")

    res_json = json.loads(res)
    logger.debug(res_json)
    if not res_json["data"]:
        if res_json["message"] == "authkey timeout":
            logger.warning("链接过期")
        elif res_json["message"] == "authkey error":
            logger.warning("链接错误")
        else:
            logger.warning("数据为空，错误代码：" + res_json["message"])
        return False
    logger.debug("链接可用")
    return True
