import bisect
import os
import time
import typing

import pydantic
import xlsxwriter
import yarl
from loguru import logger
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.style import Style
from rich.table import Table
from rich.tree import Tree

from star_rail import constants
from star_rail import exceptions as error
from star_rail.config import settings
from star_rail.database import DataBaseClient
from star_rail.i18n import i18n
from star_rail.module import Account
from star_rail.utils import console, functional
from star_rail.utils.time import get_format_time

from ..mihoyo import request
from ..record import api, converter
from .mapper import GachaItemMapper, GachaRecordInfoMapper
from .model import (
    AnalyzeData,
    AnalyzeDataRecordItem,
    AnalyzeResult,
    ApiGachaData,
    ApiGachaItem,
    GachaRecordInfo,
    SRGFData,
)
from .srgf import convert_to_gacha_record, convert_to_srgf
from .types import GACHA_TYPE_DICT, GACHA_TYPE_IDS, GachaType

__all__ = ["GachaClient", "StatisticalResult"]

_lang = i18n.record.client


class GachaRecordClient:
    def __init__(self, url: yarl.URL) -> None:
        self.url = url

    @classmethod
    def get_record_info(cls, url):
        """获取链接对应的跃迁记录信息"""
        data = {}
        for gacha_type_id in GACHA_TYPE_IDS:
            data = request("get", cls._update_url_param(url, gacha_type_id, 1, 1, 0))
            gacha_data = ApiGachaData(**data)
            if gacha_data.list:
                data["region"] = gacha_data.region
                data["region_time_zone"] = gacha_data.region_time_zone
                data["uid"] = gacha_data.list[0].uid
                data["lang"] = gacha_data.list[0].lang
                break
        logger.debug(data)
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
        logger.info(_lang.fetch_record)
        gacha_log: typing.List[ApiGachaItem] = []
        for gacha_type_id in GACHA_TYPE_IDS:
            gacha_log.extend(self._fetch_by_type_id(gacha_type_id))
        return sorted(gacha_log, key=lambda item: item.id)

    def _fetch_by_type_id(self, gacha_type_id: str):
        gacha_list: typing.List[ApiGachaItem] = []
        gacha_name = GACHA_TYPE_DICT[gacha_type_id]
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
                    GachaRecordClient._update_url_param(
                        self.url, gacha_type_id, max_size, page, end_id
                    ),
                )
                gacha_data = ApiGachaData(**data)
                if not gacha_data.list:
                    break
                page = page + 1
                end_id = gacha_data.list[-1].id
                gacha_list.extend(gacha_data.list)
                # 防止请求过快
                time.sleep(0.3)
                cnt = cnt + 1
                progress.update(task, completed=page, page=page)
        finally:
            progress.stop()
        logger.debug("fetch {} finish, total count : {}", gacha_name, len(gacha_list))
        return gacha_list

    @classmethod
    def _update_url_param(cls, url: yarl.URL, gacha_type, size, page, end_id):
        query_params = {"size": size, "gacha_type": gacha_type, "page": page, "end_id": end_id}
        return url.update_query(query_params)

    @classmethod
    def save_record_info(cls, info: GachaRecordInfo):
        with DataBaseClient() as db:
            db.insert(converter.record_info_to_mapper(info), "ignore")

    @classmethod
    def save_record_gacha_item(cls, data: typing.List[ApiGachaItem]):
        with DataBaseClient() as db:
            db.insert_batch(converter.record_gacha_item_to_mapper(data), "ignore")

    @classmethod
    def query_all(cls, uid: str) -> typing.List[ApiGachaItem]:
        data = GachaItemMapper.query_all(uid)
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
    def __init__(
        self, user: Account, info: GachaRecordInfo, data: typing.List[ApiGachaItem]
    ) -> None:
        self.user = user
        self.info = info
        self.data = data
        self.result = self._analyze(info, data)

    def _analyze(self, info: GachaRecordInfo, data: typing.List[ApiGachaItem]):
        """分析全部抽卡数据"""
        # 每个卡池统计信息：总抽数，时间范围，5星的具体抽数，当前未保底次数，平均抽数（不计算未保底）
        analyze_result = AnalyzeResult()
        analyze_result.uid = info.uid
        analyze_result.update_time = get_format_time(time.time())
        analyze_result.lang = info.lang

        for gacha_type in GACHA_TYPE_IDS:
            gacha_data = [item for item in data if item.gacha_type == gacha_type]
            analyze_result.data.append(self._analyze_gacha_type_data(gacha_type, gacha_data))
        return analyze_result

    def _analyze_gacha_type_data(self, gacha_type: str, gacha_data: typing.List[ApiGachaItem]):
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


class StatisticalResult:
    title_style = Style(color="cadet_blue", bold=True)
    header_style = Style(color="cadet_blue")

    def __init__(self, data: AnalyzeResult) -> None:
        self.analyze_result = data
        self.analyze_result.data = sorted(
            self.analyze_result.data, key=lambda item: item.gacha_type
        )

    def create_overview_table(self):
        table = Table(
            title=i18n.table.total.title,
            box=box.ASCII2,
            header_style=self.header_style,
            title_style=self.title_style,
        )
        table.add_column(i18n.table.total.gacha)
        table.add_column(i18n.table.total.total_cnt)
        table.add_column(i18n.table.total.star5_cnt)
        table.add_column(i18n.table.total.star5_avg_cnt)
        table.add_column(i18n.table.total.pity_cnt)

        for item in self.analyze_result.data:
            total_count = item.total_count
            rank5_count = len(item.list)
            pity_count = item.pity_count
            rank5_average = "-"
            if rank5_count:
                rank5_average = (total_count - pity_count) / rank5_count
                rank5_average = round(rank5_average, 2)
            table.add_row(
                GACHA_TYPE_DICT[item.gacha_type],
                str(total_count),
                str(rank5_count),
                str(rank5_average),
                str(pity_count),
            )
        return table

    def create_detail_table(self):
        """以表格形式竖列显示"""
        max_rank5_len = max([len(item.list) for item in self.analyze_result.data])
        table = Table(
            title=i18n.table.star5.title,
            box=box.ASCII2,
            header_style=self.header_style,
            title_style=self.title_style,
        )
        for gacha_name in GACHA_TYPE_DICT.values():
            table.add_column(gacha_name, justify="left", overflow="ellipsis")

        rank5_data = {}
        for item in self.analyze_result.data:
            rank5_detail = [
                item.name + " : " + item.number + i18n.table.star5.pull_count for item in item.list
            ]
            # 表格不支持可变长度，因此在末尾追加空字符串使列表长度一致
            rank5_detail += [""] * (max_rank5_len - len(rank5_detail))
            rank5_data[item.gacha_type] = rank5_detail

        for i in range(max_rank5_len):
            data = [rank5_data[gacha_type][i] for gacha_type in GACHA_TYPE_DICT.keys()]

            table.add_row(*data)
        return table

    def create_detail_tree(self):
        """以单元素形式平铺"""
        tree = Tree("[bold cadet_blue]" + i18n.table.star5.title)
        for item in self.analyze_result.data:
            rank5_detail = [
                Panel(item.name + " : " + item.number + i18n.table.star5.pull_count, expand=True)
                for item in item.list
            ]
            tree.add("[cadet_blue]" + GACHA_TYPE_DICT[item.gacha_type]).add(Columns(rank5_detail))
        return tree

    def display(self):
        console.clear_all()
        print("UID:", console.color_str("{}".format(self.analyze_result.uid), "green"))
        print(_lang.analyze_update_time, self.analyze_result.update_time, end="\n\n")
        _console = Console()
        _console.print(self.create_overview_table())
        print("", end="\n\n")
        if settings.GACHA_RECORD_DESC_MOD == "tree":
            _console.print(self.create_detail_tree())
        elif settings.GACHA_RECORD_DESC_MOD == "table":
            _console.print(self.create_detail_table())
        else:
            raise error.ParamValueError(
                i18n.error.param_value_error, settings.GACHA_RECORD_DESC_MOD
            )

    @staticmethod
    def set_display_mode(mode: typing.Literal["table", "tree"]):
        settings.GACHA_RECORD_DESC_MOD = mode
        settings.save_config()
        logger.success(i18n.config.settings.update_success)

    @staticmethod
    def get_show_display_desc():
        """获取当前显示模式描述"""
        if settings.GACHA_RECORD_DESC_MOD == "table":
            return _lang.show_mode_table
        elif settings.GACHA_RECORD_DESC_MOD == "tree":
            return _lang.show_mode_tree
        else:
            raise error.ParamValueError(
                i18n.error.param_value_error, settings.GACHA_RECORD_DESC_MOD
            )


class GachaClient:
    def __init__(self, user: Account) -> None:
        self.user = user

    def refresh_record_by_user_cache(self):
        url = api.get_from_user_cache(self.user)
        if url is None:
            logger.warning(_lang.invalid_gacha_url)
            return

        if not GachaRecordClient.verify_url(url):
            logger.warning(_lang.invalid_gacha_url)
            return

        logger.debug(functional.desensitize_url(str(url), "authkey"))
        record_info = GachaRecordClient.get_record_info(url)
        if record_info.uid != self.user.uid:
            raise error.DataError(_lang.record_info_data_error, record_info.uid)

        self._refresh_gacha_record(url, record_info)
        self.show_analyze_result()

    def refresh_record_by_game_cache(self):
        url = api.get_from_game_cache(self.user)
        if url is None:
            logger.warning(_lang.invalid_gacha_url)
            return
        if not GachaRecordClient.verify_url(url):
            logger.warning(_lang.invalid_gacha_url)
            return
        logger.debug(functional.desensitize_url(str(url), "authkey"))
        record_info = GachaRecordClient.get_record_info(url)
        if self.user.uid != record_info.uid:
            logger.warning(_lang.diff_account)
            return

        self.user.gacha_url = str(url)
        self.user.save_profile()

        self._refresh_gacha_record(url, record_info)
        self.show_analyze_result()

    def refresh_record_by_clipboard(self):
        url = api.get_from_clipboard()
        if url is None:
            logger.warning(_lang.invalid_gacha_url)
            return

        if not GachaRecordClient.verify_url(url):
            logger.warning(_lang.invalid_gacha_url)
            return

        logger.debug(functional.desensitize_url(str(url), "authkey"))
        record_info = GachaRecordClient.get_record_info(url)
        if self.user.uid != record_info.uid:
            logger.warning(_lang.diff_account)
            return

        self.user.gacha_url = str(url)
        self.user.save_profile()

        self._refresh_gacha_record(url, record_info)
        self.show_analyze_result()

    def _refresh_gacha_record(self, url: yarl.URL, record_info: GachaRecordInfo):
        """刷新抽卡记录和分析结果"""
        record_client = GachaRecordClient(url)

        gacha_data = record_client.fetch_gacha_record()

        # 数据库增量更
        latest_gacha_item = record_client.query_latest(self.user.uid)
        if not latest_gacha_item:
            # 数据库无记录，直接保存全部数据
            record_client.save_record_info(record_info)
            record_client.save_record_gacha_item(gacha_data)
        else:
            index = bisect.bisect_right(gacha_data, latest_gacha_item)
            new_gacha_data = gacha_data[index:]
            record_client.save_record_gacha_item(new_gacha_data)
        analyzer = Analyzer(self.user, record_info, GachaRecordClient.query_all(self.user.uid))
        analyzer.save_result()

    def show_analyze_result(self):
        if self.user.gacha_log_analyze_path.exists():
            result = AnalyzeResult(**functional.load_json(self.user.gacha_log_analyze_path))
            StatisticalResult(result).display()
        else:
            record_info_mapper = GachaRecordInfoMapper.query(self.user.uid)
            if not record_info_mapper:
                logger.warning(_lang.account_no_record_data)
                return
            record_info = converter.mapper_to_record_info(record_info_mapper)
            analyzer = Analyzer(self.user, record_info, GachaRecordClient.query_all(self.user.uid))
            analyzer.save_result()
            StatisticalResult(analyzer.result).display()

    def import_gacha_record(self):
        logger.debug("import gacha record")
        import_data_path = constants.IMPORT_DATA_PATH
        file_list = [
            name
            for name in os.listdir(import_data_path)
            if os.path.isfile(os.path.join(import_data_path, name)) and name.endswith(".json")
        ]
        record_info = None

        for file_name in file_list:
            file_path = os.path.join(import_data_path, file_name)
            data = functional.load_json(file_path)
            try:
                srgf_data = SRGFData(**data)
            except pydantic.ValidationError:
                logger.info(_lang.invalid_srgf_data, file_path)
                continue
            if srgf_data.info.uid != self.user.uid:
                logger.info(_lang.diff_account_srgf_data, file_path)
                continue
            record_info, item_list = convert_to_gacha_record(srgf_data)
            GachaRecordClient.save_record_info(record_info)
            GachaRecordClient.save_record_gacha_item(item_list)
            logger.success(_lang.import_file_success, file_path)

        if record_info is None:
            logger.warning(_lang.no_file_import)
            return

        analyzer = Analyzer(self.user, record_info, GachaRecordClient.query_all(self.user.uid))
        analyzer.save_result()

    def export_record_to_xlsx(self):
        record_info = GachaRecordClient.query_gacha_record_info(self.user.uid)
        if not record_info:
            logger.warning(_lang.account_no_record_data)
            return
        gacha_data = GachaRecordClient.query_all(self.user.uid)
        self._create_xlsx(gacha_data)
        logger.success(_lang.export_file_success, self.user.gacha_log_xlsx_path.as_posix())

    def export_record_to_srgf(self):
        record_info = GachaRecordClient.query_gacha_record_info(self.user.uid)
        if not record_info:
            logger.warning(_lang.account_no_record_data)
            return
        gacha_data = GachaRecordClient.query_all(self.user.uid)
        srgf_data = convert_to_srgf(record_info, gacha_data)
        functional.save_json(self.user.srgf_path, srgf_data.model_dump())
        logger.success(_lang.export_file_success, self.user.srgf_path.as_posix())

    def _create_xlsx(self, data: typing.List[ApiGachaItem]):
        logger.debug("create sheet: " + self.user.gacha_log_xlsx_path.as_posix())
        os.makedirs(self.user.gacha_log_xlsx_path.parent.as_posix(), exist_ok=True)
        workbook = xlsxwriter.Workbook(self.user.gacha_log_xlsx_path.as_posix())

        # 初始化单元格样式
        content_css = workbook.add_format(
            {
                "align": "left",
                "font_name": "微软雅黑",
                "border_color": "#c4c2bf",
                "border": 1,
            }
        )
        title_css = workbook.add_format(
            {
                "align": "left",
                "font_name": "微软雅黑",
                "color": "#757575",
                "border_color": "#c4c2bf",
                "border": 1,
                "bold": True,
            }
        )

        star_5 = workbook.add_format({"color": "#bd6932", "bold": True})
        star_4 = workbook.add_format({"color": "#a256e1", "bold": True})
        star_3 = workbook.add_format({"color": "#8e8e8e"})

        for gacha_type in GACHA_TYPE_IDS:
            gacha_data = [item for item in data if item.gacha_type == gacha_type]
            gacha_type_name = GACHA_TYPE_DICT[gacha_type]

            worksheet = workbook.add_worksheet(gacha_type_name)
            excel_header = [
                i18n.execl.header.time,
                i18n.execl.header.name,
                i18n.execl.header.type,
                i18n.execl.header.level,
                i18n.execl.header.gacha_type,
                i18n.execl.header.total_count,
                i18n.execl.header.pity_count,
            ]
            worksheet.set_column("A:A", 22)
            worksheet.set_column("B:B", 14)
            worksheet.set_column("E:E", 14)
            worksheet.write_row(0, 0, excel_header, title_css)
            worksheet.freeze_panes(1, 0)  # 固定标题行
            counter = 0
            pity_counter = 0
            for item in gacha_data:
                counter = counter + 1
                pity_counter = pity_counter + 1
                excel_data = [
                    item.time,
                    item.name,
                    item.item_type,
                    item.rank_type,
                    gacha_type_name,
                    counter,
                    pity_counter,
                ]
                # 这里转换为int类型，在后面修改单元格样式时使用
                excel_data[3] = int(excel_data[3])
                worksheet.write_row(counter, 0, excel_data, content_css)
                if excel_data[3] == 5:
                    pity_counter = 0

            first_row = 1  # 不包含表头第一行 (zero indexed)
            first_col = 0  # 第一列
            last_row = len(gacha_data)  # 最后一行
            last_col = len(excel_header) - 1  # 最后一列，zero indexed 所以要减 1
            worksheet.conditional_format(
                first_row,
                first_col,
                last_row,
                last_col,
                {"type": "formula", "criteria": "=$D2=5", "format": star_5},
            )
            worksheet.conditional_format(
                first_row,
                first_col,
                last_row,
                last_col,
                {"type": "formula", "criteria": "=$D2=4", "format": star_4},
            )
            worksheet.conditional_format(
                first_row,
                first_col,
                last_row,
                last_col,
                {"type": "formula", "criteria": "=$D2=3", "format": star_3},
            )
            logger.debug("create sheet {}，total count: {} ", gacha_type_name, len(gacha_data))

        workbook.close()
        logger.debug("create xlsx file success")
