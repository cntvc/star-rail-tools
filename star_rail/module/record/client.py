import bisect
import os
import time
import typing
from pathlib import Path

import pydantic
import xlsxwriter
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.tree import Tree

from star_rail import constants
from star_rail import exceptions as error
from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.module import Account
from star_rail.utils import functional
from star_rail.utils.log import logger
from star_rail.utils.time import get_format_time

from . import api
from .gacha_record import GachaRecord
from .model import AnalyzeResult, GachaItem, GachaRecordInfo, _AnalyzeRecordItem, _RecordTypeResult
from .srgf import SrgfData, convert_to_gacha_record, convert_to_srgf
from .types import GACHA_TYPE_DICT, GACHA_TYPE_IDS, GachaRecordType

__all__ = ["GachaRecordClient"]

_lang = i18n.record.client


class RecordAnalyzer:
    @staticmethod
    def analyze_data(info: GachaRecordInfo, data: list[GachaItem]):
        """分析全部抽卡数据"""
        # 每个卡池统计信息：总抽数，时间范围，5星的具体抽数，未保底计数，平均抽数（不计算未保底）
        analyze_result = AnalyzeResult(
            uid=info.uid, update_time=get_format_time(time.time()), lang=info.lang
        )

        def analyze_for_type(gacha_type: str, record_item_list: list[GachaItem]):
            """分析单一跃迁类型数据"""
            # 5 星列表
            rank_5_row_list = [item for item in record_item_list if item.rank_type == "5"]
            # 5 星原始位置
            rank_5_row_index = [
                i for i, item in enumerate(record_item_list, 1) if item.rank_type == "5"
            ]
            if rank_5_row_index:
                # 5 星相对位置（抽数
                rank_5_index = [rank_5_row_index[0]] + [
                    j - i for i, j in zip(rank_5_row_index, rank_5_row_index[1:])
                ]
                # 将 5 星与抽数对应起来，用 rank_5_index 表示抽数
                rank_5_item_list = [
                    _AnalyzeRecordItem(index=str(rank_5_index), **rank_5_item.model_dump())
                    for rank_5_item, rank_5_index in zip(rank_5_row_list, rank_5_index)
                ]
            else:
                rank_5_item_list = []
            # 未保底计数
            pity_count = (
                len(rank_5_row_index)
                if not rank_5_row_index
                else len(record_item_list) - rank_5_row_index[-1]
            )
            return _RecordTypeResult(
                gacha_type=gacha_type,
                pity_count=pity_count,
                total_count=len(record_item_list),
                rank_5=rank_5_item_list,
            )

        for gacha_type_id in GACHA_TYPE_IDS:
            gacha_data = [item for item in data if item.gacha_type == gacha_type_id]
            analyze_result.data.append(analyze_for_type(gacha_type_id, gacha_data))
        return analyze_result

    @staticmethod
    def load_data(path: str | Path) -> AnalyzeResult | None:
        """从文件加载已分析的数据"""
        if not os.path.exists(path):
            return None

        try:
            analyze_result = AnalyzeResult.model_validate(functional.load_json(path))
        except pydantic.ValidationError:
            os.remove(path)
            return None
        return analyze_result

    @staticmethod
    def refresh(user: Account):
        """刷新分析结果文件"""
        record_info, record_item_list = GachaRecord.query_record_archive(user.uid)
        record_info = GachaRecord.query_record_info(user.uid)
        if record_info is None:
            return False
        record_item_list = GachaRecord.query_all_record_item(user.uid)
        analyze_result = RecordAnalyzer.analyze_data(record_info, record_item_list)
        functional.save_json(user.gacha_record_analyze_path, analyze_result.model_dump())
        return True


class DataVisualization:
    title_style = Style(color="cadet_blue", bold=True)
    header_style = Style(color="cadet_blue")

    def __init__(self, data: AnalyzeResult) -> None:
        self.analyze_result = data
        self.analyze_result.data = sorted(
            self.analyze_result.data, key=lambda item: item.gacha_type
        )
        self.gacha_type_dict = GACHA_TYPE_DICT.copy()
        if settings.DISPLAY_STARTER_WARP is False:
            del self.gacha_type_dict[GachaRecordType.STARTER_WARP.value]

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
            rank5_count = len(item.rank_5)
            pity_count = item.pity_count
            rank5_average = "-"
            if rank5_count:
                rank5_average = (total_count - pity_count) / rank5_count
                rank5_average = round(rank5_average, 2)
            if item.gacha_type not in self.gacha_type_dict:
                # 跳过新手池显示
                continue
            table.add_row(
                self.gacha_type_dict[item.gacha_type],
                str(total_count),
                str(rank5_count),
                str(rank5_average),
                str(pity_count),
            )
        return table

    def create_detail_table(self):
        """以表格形式竖列显示"""
        max_rank5_len = max([len(item.rank_5) for item in self.analyze_result.data])
        table = Table(
            title=i18n.table.star5.title,
            box=box.ASCII2,
            header_style=self.header_style,
            title_style=self.title_style,
        )
        for gacha_name in self.gacha_type_dict.values():
            table.add_column(gacha_name, justify="left", overflow="ellipsis")

        rank5_data = {}
        for item in self.analyze_result.data:
            rank5_detail = [
                item.name + " : " + item.index + i18n.table.star5.pull_count for item in item.rank_5
            ]
            # 表格不支持可变长度，因此在末尾追加空字符串使列表长度一致
            rank5_detail += [""] * (max_rank5_len - len(rank5_detail))
            rank5_data[item.gacha_type] = rank5_detail

        for i in range(max_rank5_len):
            data = [rank5_data[gacha_type][i] for gacha_type in self.gacha_type_dict.keys()]

            table.add_row(*data)
        return table

    def create_detail_tree(self):
        """以单元素形式平铺"""
        tree = Tree("[bold cadet_blue]" + i18n.table.star5.title)
        for item in self.analyze_result.data:
            rank5_detail = [
                Panel(item.name + " : " + item.index + i18n.table.star5.pull_count, expand=True)
                for item in item.rank_5
            ]
            if item.gacha_type not in self.gacha_type_dict:
                # 跳过新手池显示
                continue
            tree.add("[cadet_blue]" + self.gacha_type_dict[item.gacha_type]).add(
                Columns(rank5_detail)
            )
        return tree

    def display(self):
        functional.clear_all()
        print("UID:", functional.color_str("{}".format(self.analyze_result.uid), "green"))
        print(_lang.analyze_update_time, self.analyze_result.update_time, end="\n\n")
        _console = Console()
        _console.print(self.create_overview_table())
        print("", end="\n\n")
        if settings.GACHA_RECORD_DESC_MOD == "tree":
            _console.print(self.create_detail_tree())
        elif settings.GACHA_RECORD_DESC_MOD == "table":
            _console.print(self.create_detail_table())
        else:
            raise error.HsrException(i18n.error.param_value_error, settings.GACHA_RECORD_DESC_MOD)

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
            raise error.HsrException(i18n.error.param_value_error, settings.GACHA_RECORD_DESC_MOD)

    @staticmethod
    def set_display_starter_warp(status: bool):
        settings.DISPLAY_STARTER_WARP = status
        settings.save_config()
        logger.success(i18n.config.settings.update_success)

    @staticmethod
    def get_display_starter_warp_desc():
        return "{}: {}".format(
            i18n.config.settings.current_status,
            functional.color_str(i18n.common.open, "green")
            if settings.DISPLAY_STARTER_WARP
            else functional.color_str(i18n.common.close, "red"),
        )


class GachaRecordClient:
    def __init__(self, user: Account) -> None:
        self.user = user

    def refresh_gacha_record(self, source: typing.Literal["web_cache", "clipboard"] = "web_cache"):
        if source == "clipboard":
            url = api.get_clipboard_url()
        else:
            url = api.get_game_cache_url(self.user)

        if url is None:
            logger.warning(_lang.invalid_gacha_url)
            return

        gacha_record = GachaRecord(url)
        if not gacha_record.verify_url():
            logger.warning(_lang.invalid_gacha_url)
            return
        logger.debug(functional.desensitize_url(str(url), "authkey"))
        record_info = gacha_record.get_record_url_info(url)
        if self.user.uid != record_info.uid:
            logger.warning(_lang.diff_account)
            return

        self.user.gacha_url = str(url)
        self.user.save_profile()

        record_item_list = gacha_record.fetch_record_item_list()

        # 数据库增量更新
        latest_gacha_item = gacha_record.query_latest_record_item(self.user.uid)
        if not latest_gacha_item:
            # 数据库无记录，直接保存全部数据
            GachaRecord.save_record_info(record_info)
            GachaRecord.save_record_item_list(record_item_list)
        else:
            # 查找到最新的跃迁记录位置索引
            index = bisect.bisect_right(record_item_list, latest_gacha_item)
            new_record_data = record_item_list[index:]
            GachaRecord.save_record_item_list(new_record_data)

        RecordAnalyzer.refresh(self.user)
        self.show_analyze_result()

    def show_analyze_result(self):
        if not self.user.gacha_record_analyze_path.exists():
            if RecordAnalyzer.refresh(self.user) is False:
                logger.warning(_lang.account_no_record_data)
                return

        analyze_result = RecordAnalyzer.load_data(self.user.gacha_record_analyze_path)
        if analyze_result:
            DataVisualization(analyze_result).display()
        else:
            RecordAnalyzer.refresh(self.user)
            analyze_result = RecordAnalyzer.load_data(self.user.gacha_record_analyze_path)
            DataVisualization(analyze_result).display()

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
                srgf_data = SrgfData(**data)
            except pydantic.ValidationError:
                logger.info(_lang.invalid_srgf_data, file_path)
                continue
            if srgf_data.info.uid != self.user.uid:
                logger.info(_lang.diff_account_srgf_data, file_path)
                continue
            # FIXME 当 recode_item_list 为空时报错
            record_info, item_list = convert_to_gacha_record(srgf_data)
            GachaRecord.save_record_info(record_info)
            GachaRecord.save_record_item_list(item_list)
            logger.success(_lang.import_file_success, file_path)

        if record_info is None:
            logger.warning(_lang.no_file_import)
            return
        RecordAnalyzer.refresh(self.user)
        self.show_analyze_result()

    def export_record_to_xlsx(self):
        record_info = GachaRecord.query_record_info(self.user.uid)
        if not record_info:
            logger.warning(_lang.account_no_record_data)
            return
        gacha_record_list = GachaRecord.query_all_record_item(self.user.uid)
        logger.debug("create sheet: " + self.user.gacha_record_xlsx_path.as_posix())
        os.makedirs(self.user.gacha_record_xlsx_path.parent.as_posix(), exist_ok=True)
        workbook = xlsxwriter.Workbook(self.user.gacha_record_xlsx_path.as_posix())

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
            gacha_record_type_list = [
                item for item in gacha_record_list if item.gacha_type == gacha_type
            ]
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
            for item in gacha_record_type_list:
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
            last_row = len(gacha_record_type_list)  # 最后一行
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
            logger.debug(
                "create sheet {}，total count: {} ", gacha_type_name, len(gacha_record_type_list)
            )

        workbook.close()
        logger.debug("create xlsx file success")
        logger.success(_lang.export_file_success, self.user.gacha_record_xlsx_path.as_posix())

    def export_record_to_srgf(self):
        record_info = GachaRecord.query_record_info(self.user.uid)
        if not record_info:
            logger.warning(_lang.account_no_record_data)
            return
        gacha_record_list = GachaRecord.query_all_record_item(self.user.uid)
        srgf_data = convert_to_srgf(record_info, gacha_record_list)
        functional.save_json(self.user.srgf_path, srgf_data.model_dump())
        logger.success(_lang.export_file_success, self.user.srgf_path.as_posix())

    def set_gacha_record_display_mode(self, mode: typing.Literal["table", "tree"]):
        DataVisualization.set_display_mode(mode)

    def get_gacha_record_visualization_desc(self):
        """获取当前显示模式描述"""
        return DataVisualization.get_show_display_desc()

    def set_display_starter_warp(self, status: bool):
        DataVisualization.set_display_starter_warp(status)

    def get_display_starter_warp_desc(self):
        return DataVisualization.get_display_starter_warp_desc()
