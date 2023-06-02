import enum
import json
import time
from random import random
from typing import Dict, List
from urllib import parse

import requests
from pydantic import BaseModel, ValidationError, validator

from star_rail import __version__ as version
from star_rail import constants
from star_rail.i18n import i18n
from star_rail.module.account import verify_uid_format
from star_rail.utils import functional
from star_rail.utils.log import logger
from star_rail.utils.time import convert_time_to_timezone, get_format_time

_lang = i18n.gacha_log


class GachaType(str, enum.Enum):
    REGULAR_WARP = "1"
    STARTER_WARP = "2"
    CHARACTER_EVENT_WARP = "11"
    LIGHT_CONE_EVENT_WARP = "12"

    @staticmethod
    def dict():
        return {
            GachaType.REGULAR_WARP.value: i18n.regular_warp,
            GachaType.STARTER_WARP.value: i18n.starter_warp,
            GachaType.CHARACTER_EVENT_WARP.value: i18n.character_event_warp,
            GachaType.LIGHT_CONE_EVENT_WARP.value: i18n.light_cone_event_warp,
        }

    @staticmethod
    def list():
        """gacha type id list"""
        return [member.value for member in GachaType]


class GachaInfo(BaseModel):
    uid: str
    lang: str
    region_time_zone: int
    export_timestamp: int
    export_time: str
    export_app: str
    export_app_version: str

    _verify_uid_format = validator("uid", always=True, allow_reuse=True)(verify_uid_format)

    @staticmethod
    def gen(uid: str, lang: str, region_time_zone: int):
        local_std_time = time.localtime(time.time())
        origin_time = convert_time_to_timezone(local_std_time, region_time_zone)

        export_app = constants.APP_NAME
        export_app_version = version
        return GachaInfo(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=int(time.mktime(origin_time)),
            export_time=get_format_time(time.mktime(origin_time)),
            export_app=export_app,
            export_app_version=export_app_version,
        )


class BaseGachaItem(BaseModel):
    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str

    def __eq__(self, __value: "BaseGachaItem") -> bool:
        return self.id == __value.id

    def __ne__(self, __value: "BaseGachaItem") -> bool:
        return self.id != __value.id

    def __gt__(self, __value: "BaseGachaItem") -> bool:
        return self.id > __value.id

    def __lt__(self, __value: "BaseGachaItem") -> bool:
        return self.id < __value.id


class GachaItem(BaseGachaItem):
    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str


class GachaData(BaseModel):
    info: GachaInfo
    gacha_log: Dict[str, List[GachaItem]]
    gacha_type: dict = GachaType.dict()

    @validator("gacha_log")
    def _gacha_log_key_must_in_gacha_type(cls, _value: dict):
        for gacha_type in GachaType.list():
            if gacha_type not in _value:
                raise ValidationError
        return _value

    @staticmethod
    def is_gacha_data(data: dict):
        return (
            "info" in data
            and "gacha_log" in data
            and data["info"]["export_app"] == constants.APP_NAME
            and "uid" in data["info"]
        )


def verify_gacha_log_url(url):
    logger.debug("验证链接有效性: " + functional.desensitize_url(url, "authkey"))

    res = requests.get(url, timeout=constants.REQUEST_TIMEOUT)
    res_json = json.loads(res.content.decode("utf-8"))

    if not res_json["data"]:
        if res_json["message"] == "authkey timeout":
            logger.warning(_lang.link_expires)
        elif res_json["message"] == "authkey error":
            logger.warning(_lang.link_error)
        else:
            logger.warning(_lang.error_code + res_json["message"])
        return False
    logger.debug("链接可用")
    return True


def get_uid_and_lang(gacha_log):
    """gacha_log: Dict[GachaType, List[GachaItem]]"""
    uid = ""
    lang = ""
    for gacha_type in GachaType.list():
        if not uid and gacha_log[gacha_type]:
            uid = gacha_log[gacha_type][-1]["uid"]
        if not lang and gacha_log[gacha_type]:
            lang = gacha_log[gacha_type][-1]["lang"]
    return uid, lang


class GachaLogFetcher:
    def __init__(self, url: str) -> None:
        self.parsed_url = parse.urlparse(url)
        self.gacha_data = None
        self.region = None
        self.region_time_zone = None
        self.uid = None
        self.lang = None

    def query(self):
        logger.info(_lang.start_fetch)
        gacha_log = {}
        for gacha_type_id in GachaType.list():
            gacha_type_log = self._query_by_type_id(gacha_type_id)
            # 抽卡记录以时间顺序排列
            gacha_type_log.reverse()
            gacha_log[gacha_type_id] = gacha_type_log

        self.uid, self.lang = get_uid_and_lang(gacha_log)
        gacha_data = {}
        gacha_data["info"] = GachaInfo.gen(self.uid, self.lang, self.region_time_zone).dict()
        gacha_data["gacha_log"] = gacha_log
        gacha_data["gacha_type"] = GachaType.dict()
        self.gacha_data = gacha_data

    def _query_by_type_id(self, gacha_type_id: str):
        max_size = "20"
        gacha_list = []
        end_id = "0"
        type_name = GachaType.dict()[gacha_type_id]
        for page in range(1, 9999):
            msg = _lang.fetch_status.format(type_name, ".." * ((page - 1) % 3 + 1))
            print(msg, end="\r")
            self._add_page_param(gacha_type_id, max_size, page, end_id)
            url = parse.urlunparse(self.parsed_url)

            res = requests.get(url, timeout=constants.REQUEST_TIMEOUT)
            res_json = json.loads(res.content.decode("utf-8"))

            if not res_json["data"]["list"]:
                break

            if not self.region:
                self.region = res_json["data"]["region"]
                self.region_time_zone = res_json["data"]["region_time_zone"]

            gacha_list += res_json["data"]["list"]
            end_id = res_json["data"]["list"][-1]["id"]
            time.sleep(0.2 + random())

        completed_tips = _lang.fetch_finish.format(type_name, len(gacha_list))
        print("\033[K" + completed_tips)
        logger.debug(completed_tips)
        return gacha_list

    def _add_page_param(self, gacha_type, size, page, end_id):
        query_params = parse.parse_qs(self.parsed_url.query)

        query_params["size"] = [size]
        query_params["gacha_type"] = [gacha_type]
        query_params["page"] = [page]
        query_params["end_id"] = [end_id]
        self.parsed_url = self.parsed_url._replace(query=parse.urlencode(query_params, doseq=True))
