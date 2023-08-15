import bisect
import time
import typing

import yarl
from prettytable import PrettyTable

from star_rail import exceptions as error
from star_rail.core.db_client import DBClient
from star_rail.i18n import i18n
from star_rail.module.mihoyo import Account, UserManager
from star_rail.module.record.mapper import GachaItemMapper, GachaRecordInfoMapper
from star_rail.utils import functional
from star_rail.utils.log import logger
from star_rail.utils.time import get_format_time

from ..mihoyo import request
from ..record import api, converter
from .model import (
    AnalyzeData,
    AnalyzeDataRecordItem,
    AnalyzeResult,
    GachaData,
    GachaItem,
    GachaRecordInfo,
)
from .types import GACHA_TYPE_DICT, GACHA_TYPE_IDS, GachaType

__all__ = ["GachaClient"]


class GachaRecordClient:
    def __init__(self, url: yarl.URL) -> None:
        self.url = url

    @classmethod
    def get_record_info(cls, url):
        """获取链接对应的跃迁记录信息"""
        data = {}
        for gacha_type_id in GACHA_TYPE_IDS:
            data = request("get", cls._update_url_param(url, gacha_type_id, 1, 1, 0))
            gacha_data = GachaData(**data)
            if gacha_data.list:
                data["region"] = gacha_data.region
                data["region_time_zone"] = gacha_data.region_time_zone
                data["uid"] = gacha_data.list[0].uid
                data["lang"] = gacha_data.list[0].lang
                break
        return GachaRecordInfo(**data)

    @classmethod
    def verify_url(cls, url):
        if not url:
            return False
        try:
            request("get", cls._update_url_param(url, GachaType.STARTER_WARP.value, 1, 1, 0))
        except error.AuthkeyExceptionError as e:
            logger.debug(e)
            return False
        return True

    def fetch_gacha_record(self):
        logger.info("正在查询记录")
        gacha_log: typing.List[GachaItem] = []
        for gacha_type_id in GACHA_TYPE_IDS:
            gacha_log.extend(self._fetch_by_type_id(gacha_type_id))
        return sorted(gacha_log, key=lambda item: item.id)

    def _fetch_by_type_id(self, gacha_type_id: str):
        gacha_list: typing.List[GachaItem] = []

        page = 1
        max_size = 20
        end_id = 0

        while True:
            data = request(
                "get",
                GachaRecordClient._update_url_param(
                    self.url, gacha_type_id, max_size, page, end_id
                ),
            )
            gacha_data = GachaData(**data)
            if not gacha_data.list:
                break
            page = page + 1
            end_id = gacha_data.list[-1].id
            gacha_list.extend(gacha_data.list)
            # 防止请求过快
            time.sleep(0.3)
        return gacha_list

    @classmethod
    def _update_url_param(cls, url, gacha_type, size, page, end_id):
        query_params = {}
        query_params["size"] = size
        query_params["gacha_type"] = gacha_type
        query_params["page"] = page
        query_params["end_id"] = end_id
        return url.update_query(query_params)

    @classmethod
    def save_record_info(cls, info: GachaRecordInfo):
        with DBClient() as db:
            db.insert(converter.record_info_to_mapper(info), "ignore")

    @classmethod
    def save_record_gacha_item(cls, data: typing.List[GachaItem]):
        with DBClient() as db:
            db.insert_batch(converter.record_gacha_item_to_mapper(data), "ignore")

    @classmethod
    def query_all(
        cls, uid: str, gacha_type: str = "", begin_id: str = ""
    ) -> typing.List[GachaItem]:
        data = GachaItemMapper.query_all(uid, gacha_type, begin_id)
        return converter.mapper_to_gacha_item(data) if data else None

    @classmethod
    def query_gacha_record_info(cls, uid: str):
        data = GachaRecordInfoMapper.query(uid)
        return converter.mapper_to_record_info(data) if data else None

    @classmethod
    def query_latest(cls, uid: str):
        data = GachaItemMapper.query_latest(uid)
        return converter.mapper_to_gacha_item(data) if data else None


class Analyzer:
    def __init__(self, user: Account, info: GachaRecordInfo, data: typing.List[GachaItem]) -> None:
        self.user = user
        self.info = info
        self.data = data
        self.result = self._analyze(info, data)

    def _analyze(self, info: GachaRecordInfo, data: typing.List[GachaItem]):
        """分析全部抽卡数据"""
        logger.debug("分析抽卡数据")
        # 每个卡池统计信息：总抽数，时间范围，5星的具体抽数，当前未保底次数，平均抽数（不计算未保底）
        analyze_result = AnalyzeResult()
        analyze_result.uid = info.uid
        analyze_result.update_time = get_format_time(time.time())
        analyze_result.lang = info.lang

        for gacha_type in GACHA_TYPE_IDS:
            gacha_data = [item for item in data if item.gacha_type == gacha_type]
            analyze_result.data.append(self._analyze_gacha_type_data(gacha_type, gacha_data))
        return analyze_result

    def _analyze_gacha_type_data(self, gacha_type: str, gacha_data: typing.List[GachaItem]):
        """分析单一跃迁类型数据"""
        # 5 星列表
        rank_5 = [item for item in gacha_data if item.rank_type == "5"]
        # 5 星原始位置
        rank5_index = [i for i, item in enumerate(gacha_data, 1) if item.rank_type == "5"]
        if rank5_index:
            # 5 星相对位置（抽数
            rank5_number = [rank5_index[0]] + [j - i for i, j in zip(rank5_index, rank5_index[1:])]
            # 将 5 星与抽数对应起来，用 number 表示抽数
            rank5_item = [
                AnalyzeDataRecordItem(number=str(number), **ran5_item.model_dump())
                for ran5_item, number in zip(rank_5, rank5_number)
            ]
        else:
            rank5_item = []
        # 未保底次数
        pity_count = len(rank5_index) if not rank5_index else len(gacha_data) - rank5_index[-1]
        return AnalyzeData(
            gacha_type=gacha_type,
            pity_count=pity_count,
            total_count=len(gacha_data),
            list=rank5_item,
        )

    def save_result(self):
        """保存分析结果"""
        functional.save_json(self.user.gacha_log_analyze_path, self.result.model_dump())


class StatisticalTable:
    def __init__(self, data: AnalyzeResult) -> None:
        self.analyze_result = data
        self.analyze_result.data = sorted(
            self.analyze_result.data, key=lambda item: item.gacha_type
        )

    def gen_overview_table(self):
        overview_table = PrettyTable()
        overview_table.align = "l"
        overview_table.title = i18n.table.total.title
        overview_table.add_column(
            i18n.table.total.project,
            [
                i18n.table.total.total_cnt,
                i18n.table.total.star5_cnt,
                i18n.table.total.star5_avg_cnt,
                i18n.table.total.pity_cnt,
            ],
        )

        for item in self.analyze_result.data:
            total_count = item.total_count
            rank5_count = len(item.list)
            pity_count = item.pity_count
            rank5_average = "-"
            if rank5_count:
                rank5_average = (total_count - pity_count) / rank5_count
                rank5_average = round(rank5_average, 2)
            overview_table.add_column(
                GACHA_TYPE_DICT[item.gacha_type],
                [total_count, rank5_count, rank5_average, pity_count],
            )
        return overview_table

    def gen_detail_table(self):
        max_rank5_len = max([len(item.list) for item in self.analyze_result.data])
        rank5_detail_table = PrettyTable()
        rank5_detail_table.title = i18n.table.star5.title
        rank5_detail_table.align = "l"
        for item in self.analyze_result.data:
            rank5_detail = [
                item.name + " : " + item.number + i18n.table.star5.pull_count for item in item.list
            ]
            # 表格不支持可变长度，因此在末尾追加空字符串使列表长度一致
            rank5_detail += [""] * (max_rank5_len - len(rank5_detail))
            rank5_detail_table.add_column(GACHA_TYPE_DICT[item.gacha_type], rank5_detail)
        return rank5_detail_table

    def show(self):
        functional.clear_screen()
        print("UID:", functional.color_str("{}".format(self.analyze_result.uid), "green"))
        print("更新时间", self.analyze_result.update_time)
        print(self.gen_overview_table())
        print(functional.color_str("注：XXX", "yellow"), end="\n\n")
        print(self.gen_detail_table())


class GachaClient:
    def __init__(self) -> None:
        self.user_manager = UserManager()

    @error.exec_catch(error.HsrException)
    def refresh_record_by_user_cache(self):
        user = self.user_manager.user
        if user is None:
            logger.warning("设置账户后重试")
            return
        url = api.get_from_user_cache(user)
        if url is None:
            logger.warning("未获取到链接")
            return

        if not GachaRecordClient.verify_url(url):
            logger.warning("链接无效")
            return

        record_info = GachaRecordClient.get_record_info(url)
        if record_info.uid != user.uid:
            raise error.DataError("账户存储数据出现错误, record_info_uid: {}", record_info.uid)

        self._refresh_gacha_record(url, record_info)
        self.show_analyze_result()

    @error.exec_catch(error.HsrException)
    def refresh_record_by_game_cache(self):
        user = self.user_manager.user
        if user is None:
            logger.warning("设置账户后重试")
            return

        url = api.get_from_game_cache(user)
        if url is None:
            logger.warning("游戏缓存未获取到有效链接")
            return

        if not GachaRecordClient.verify_url(url):
            logger.warning("链接无效")
            return

        record_info = GachaRecordClient.get_record_info(url)
        if user.uid != record_info.uid:
            logger.warning("游戏链接账户与设置不一致，无法导出")
            return

        user.gacha_url = str(url)
        user.save_profile()

        self._refresh_gacha_record(url, record_info)
        self.show_analyze_result()

    @error.exec_catch(error.HsrException)
    def refresh_record_by_clipboard(self):
        url = api.get_from_clipboard()
        if url is None:
            logger.warning("从剪切板未读取到有效链接")
            return

        if not GachaRecordClient.verify_url(url):
            logger.warning("链接无效")
            return

        record_info = GachaRecordClient.get_record_info(url)

        user = Account(uid=record_info.uid, gacha_url=url)
        user.save_profile()
        UserManager().login(user)

        self._refresh_gacha_record(url, record_info)
        self.show_analyze_result()

    def _refresh_gacha_record(self, url: yarl.URL, record_info: GachaRecordInfo):
        """刷新抽卡记录和分析结果"""
        user = self.user_manager.user
        record_client = GachaRecordClient(url)

        gacha_data = record_client.fetch_gacha_record()

        # 数据库增量更
        latest_gacha_item = record_client.query_latest(user.uid)
        if not latest_gacha_item:
            # 数据库无记录，直接保存全部数据
            record_client.save_record_info(record_info)
            record_client.save_record_gacha_item(gacha_data)
        else:
            index = bisect.bisect_right(gacha_data, latest_gacha_item)
            new_gacha_data = gacha_data[index:]
            record_client.save_record_gacha_item(new_gacha_data)
        analyzer = Analyzer(user, record_info, GachaRecordClient.query_all(user.uid))
        analyzer.save_result()

    def show_analyze_result(self):
        user = self.user_manager.user
        if user is None:
            logger.warning("设置账户后重试")
            return
        if user.gacha_log_analyze_path.exists():
            result = AnalyzeResult(**functional.load_json(user.gacha_log_analyze_path))
            StatisticalTable(result).show()
        else:
            record_info_mapper = GachaRecordInfoMapper.query(user.uid)
            if not record_info_mapper:
                logger.warning("账户无抽卡记录")
                return
            record_info = converter.mapper_to_record_info(record_info_mapper)
            analyzer = Analyzer(user, record_info, GachaRecordClient.query_all(user.uid))
            analyzer.save_result()
            StatisticalTable(analyzer.result).show()

    def import_gacha_record(self):
        """
        导入SRGF格式
        """

    def export_record_to_srgf(self):
        pass

    def export_record_to_execl(self):
        pass
