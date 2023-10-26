import time

import yarl
from rich.progress import BarColumn, Progress, TextColumn

from star_rail import exceptions as error
from star_rail.database import DataBaseClient
from star_rail.i18n import i18n
from star_rail.module.api_helper import request
from star_rail.utils.log import logger

from . import converter, types
from .mapper import GachaRecordInfoMapper, RecordItemMapper
from .model import GachaItem, GachaRecordData, GachaRecordInfo

__all__ = ["GachaRecord"]

_lang = i18n.record.client


class GachaRecord:
    """跃迁记录"""

    def __init__(self, url: yarl.URL) -> None:
        self.url = url

    def get_record_url_info(self, url):
        """获取跃迁记录信息"""
        data = {}
        """查询一条记录，只获取 UID 和 region 等信息"""
        for gacha_type_id in types.GACHA_TYPE_IDS:
            data = request("get", self._update_url_param(url, gacha_type_id, 1, 1, 0))
            gacha_data = GachaRecordData(**data)
            if gacha_data.list:
                data["region"] = gacha_data.region
                data["region_time_zone"] = gacha_data.region_time_zone
                data["uid"] = gacha_data.list[0].uid
                data["lang"] = gacha_data.list[0].lang
                break
        logger.debug(data)
        return GachaRecordInfo(**data)

    def verify_url(self):
        if not self.url:
            return False
        try:
            request(
                "get",
                self._update_url_param(self.url, types.GachaRecordType.STARTER_WARP.value, 1, 1, 0),
            )
        except error.AuthkeyExceptionError as e:
            logger.debug(e)
            return False
        return True

    def fetch_record_item_list(self):
        logger.info(_lang.fetch_record)
        gacha_item_list: list[GachaItem] = []
        for gacha_type_id in types.GACHA_TYPE_IDS:
            gacha_item_list.extend(self._fetch_by_type_id(gacha_type_id))
        return sorted(gacha_item_list, key=lambda item: item.id)

    def _fetch_by_type_id(self, gacha_type_id: str):
        gacha_item_list: list[GachaItem] = []
        gacha_name = types.GACHA_TYPE_DICT[gacha_type_id]
        page = 1
        max_size = 20
        end_id = 0
        cnt = 1
        progress = Progress(
            TextColumn("[bold]{task.fields[gacha_name]}", justify="right"),
            BarColumn(bar_width=30),
            _lang.fetch_msg,
            transient=True,
        )
        task = progress.add_task("Fetching...", gacha_name=gacha_name, page=page, total=None)
        progress.start()
        try:
            while True:
                data = request(
                    "get",
                    self._update_url_param(self.url, gacha_type_id, max_size, page, end_id),
                )
                gacha_data = GachaRecordData(**data)
                if not gacha_data.list:
                    break
                page = page + 1
                end_id = gacha_data.list[-1].id
                gacha_item_list.extend(gacha_data.list)
                # 防止请求过快
                time.sleep(0.3)
                cnt = cnt + 1
                progress.update(task, completed=page, page=page)
        finally:
            progress.stop()
        logger.debug("fetch {} finish, total count : {}", gacha_name, len(gacha_item_list))
        return gacha_item_list

    def _update_url_param(self, url: yarl.URL, gacha_type, size, page, end_id):
        query_params = {"size": size, "gacha_type": gacha_type, "page": page, "end_id": end_id}
        return url.update_query(query_params)

    @classmethod
    def save_record(cls, record_info: GachaRecordInfo, record_list: list[GachaItem]):
        """保存跃迁记录的存档和跃迁记录内容"""
        with DataBaseClient() as db:
            db.insert(converter.record_info_to_mapper(record_info), "ignore")
            db.insert_batch(converter.record_item_to_mapper(record_list), "ignore")

    @classmethod
    def save_record_item_list(cls, data: list[GachaItem]):
        """保存跃迁记录"""
        with DataBaseClient() as db:
            db.insert_batch(converter.record_item_to_mapper(data), "ignore")

    @classmethod
    def save_record_info(cls, info: GachaRecordInfo):
        """保存跃迁记录的存档"""
        with DataBaseClient() as db:
            db.insert(converter.record_info_to_mapper(info), "ignore")

    @classmethod
    def query_all_record_item(cls, uid: str) -> list[GachaItem]:
        """查询所有跃迁记录项"""
        data = RecordItemMapper.query_all(uid)
        return converter.mapper_to_record_item(data)

    @classmethod
    def query_latest_record_item(cls, uid: str) -> GachaItem | None:
        """查询最新的跃迁记录项"""
        data = RecordItemMapper.query_latest(uid)
        return converter.mapper_to_record_item(data) if data else None

    @classmethod
    def query_record_info(cls, uid: str) -> GachaRecordInfo | None:
        data = GachaRecordInfoMapper.query(uid)
        return converter.mapper_to_record_info(data) if data else None

    @classmethod
    def query_record_archive(
        cls, uid: str
    ) -> tuple[GachaRecordInfo | None, list[GachaItem] | None]:
        record_info_mapper = GachaRecordInfoMapper.query(uid)
        if record_info_mapper is None:
            return None, None
        record_info = converter.mapper_to_record_info(record_info_mapper)
        gacha_item_list = converter.mapper_to_record_item(RecordItemMapper.query_all(uid))
        return record_info, gacha_item_list
