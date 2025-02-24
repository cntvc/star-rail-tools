from __future__ import annotations

import bisect
import os
import typing
from dataclasses import dataclass

import xlsxwriter
from loguru import logger
from pydantic import ValidationError

from star_rail import __version__, constants
from star_rail import exceptions as error
from star_rail.config import config
from star_rail.module.account import Account
from star_rail.module.base import BaseClient
from star_rail.module.metadata import BaseMetadata
from star_rail.utils import Date, load_json, save_json

from .entity import GachaRecordDbClient
from .fetcher import GachaRecordFetcher
from .gacha_url import GachaUrl
from .model import (
    GachaAnalyzeSummary,
    GachaIndexItem,
    GachaPoolAnalyzeResult,
    GachaRecordInfo,
    GachaRecordItem,
)
from .srgf import SRGFData, convert_record_to_srgf, convert_srgf_to_record
from .types import GACHA_TYPE_DICT, GACHA_TYPE_IDS
from .uigf import UIGFData, convert_record_to_uigf

if typing.TYPE_CHECKING:
    from .entity import GachaRecordBatchEntity

__all__ = ["GachaRecordClient", "ExportHelper", "ImportHelper"]


class GachaRecordClient(BaseClient):
    def __init__(self, user: Account, _metadata: BaseMetadata = None):
        super().__init__(user, _metadata)
        self.metadata = _metadata

    async def refresh_gacha_record(self, mode: typing.Literal["incremental", "full"]):
        logger.debug("Refresh gacha record，mode: {}", mode)
        url = GachaUrl(self.user).parse_from_web_cache()
        if url is None:
            raise error.GachaRecordError("未获取到有效链接")

        fetcher = GachaRecordFetcher(url)
        uid, lang, region_time_zone = await fetcher.get_url_info()
        if not uid:
            raise error.GachaRecordError("暂无新跃迁记录")

        logger.debug(f"url info: uid={uid}, lang={lang}, region_time_zone={region_time_zone}")
        if self.user.uid != uid:
            raise error.GachaRecordError(f"当前跃迁记录不属于用户 {self.user.uid}")

        need_insert_record = await self._fetch_record(fetcher, mode)
        logger.debug(f"The number of records to be added: {len(need_insert_record)}")
        if need_insert_record:
            cnt = await self._insert_record(lang, region_time_zone, need_insert_record, mode)
            logger.debug("{} new records added", cnt)
        else:
            cnt = 0
            logger.debug("No new records to be added")
        return cnt

    async def _fetch_record(
        self, fetcher: GachaRecordFetcher, mode: typing.Literal["incremental", "full"]
    ):
        record_db_client = GachaRecordDbClient(self.user)
        latest_gacha_record = await record_db_client.get_latest_gacha_record()
        stop_id = None

        if mode == "full":
            gacha_record_iter = await fetcher.fetch_gacha_record(stop_id=stop_id)
            gacha_record_list = list(await gacha_record_iter.flatten())
            gacha_record_list.reverse()
            return gacha_record_list
        else:
            # 增量模式 只保存新增记录
            if latest_gacha_record:
                stop_id = latest_gacha_record.id
            gacha_record_iter = await fetcher.fetch_gacha_record(stop_id=stop_id)
            gacha_record_list = list(await gacha_record_iter.flatten())
            gacha_record_list.reverse()

            need_insert = gacha_record_list
            if latest_gacha_record:
                index = bisect.bisect_right(gacha_record_list, latest_gacha_record)
                need_insert = gacha_record_list[index:]
            return need_insert

    async def _insert_record(
        self,
        lang,
        region_time_zone,
        gacha_record: list[GachaRecordItem],
        mode: typing.Literal["incremental", "full"],
    ):
        record_db_client = GachaRecordDbClient(self.user)
        target_time_zone = region_time_zone
        if latest_batch_record := await record_db_client.get_latest_batch():
            target_time_zone = latest_batch_record.region_time_zone

        def convert_record_timezone(data: list[GachaRecordItem], source_tz: int, target_tz: int):
            if source_tz == target_tz:
                return
            for item in data:
                item.time = Date.convert_timezone(item.time, source_tz, target_tz)

        convert_record_timezone(gacha_record, region_time_zone, target_time_zone)

        next_batch_id = await record_db_client.get_next_batch_id()
        info = GachaRecordInfo(
            uid=self.user.uid,
            batch_id=next_batch_id,
            lang=lang,
            region_time_zone=target_time_zone,
            source=f"{constants.APP_NAME}_{__version__}",
        )

        insert_mode = "ignore" if mode == "incremental" else "replace"
        return await record_db_client.insert_gacha_record(gacha_record, info, insert_mode)

    async def load_analyze_summary(self) -> GachaAnalyzeSummary:
        analyzer = GachaRecordAnalyzer(self)
        await analyzer.load()
        return analyzer.analyze_summary

    async def refresh_analyze_summary(self):
        logger.debug("Refresh analyze summary")
        analyzer = GachaRecordAnalyzer(self)
        await analyzer.refresh()
        return analyzer.analyze_summary


class GachaRecordAnalyzer:
    def __init__(self, client: GachaRecordClient):
        self.client = client
        self.analyze_summary: GachaAnalyzeSummary | None = None
        self.user = client.user
        self.analyze_result_path = self.user.analyze_result_path

    @staticmethod
    def _analyze(uid, gacha_record_list: list[GachaRecordItem]):
        logger.debug("Analyze gacha record")
        analyze_summary = GachaAnalyzeSummary(
            uid=uid, update_time=Date.now().strftime(Date.Format.YYYY_MM_DD_HHMMSS)
        )
        for gacha_type_id in GACHA_TYPE_IDS:
            gacha_data = [item for item in gacha_record_list if item.gacha_type == gacha_type_id]
            analyze_result = GachaRecordAnalyzer._analyze_gacha_pool(gacha_type_id, gacha_data)
            analyze_summary.data.append(analyze_result)
        return analyze_summary

    @staticmethod
    def _analyze_gacha_pool(gacha_type: str, record_item_list: list[GachaRecordItem]):
        """按卡池类型统计数据"""
        total_count = len(record_item_list)
        # 5 星列表
        rank5_list = [item for item in record_item_list if item.rank_type == "5"]
        # 5 星原始位置
        rank5_raw_index = [i for i, item in enumerate(record_item_list, 1) if item.rank_type == "5"]

        rank5_result = []
        pity_count = total_count

        if rank5_list:
            # 计算5星抽数列表
            first_rank5_index = rank5_raw_index[0]
            rank5_count_list = [first_rank5_index] + [
                # 相邻5星的位置差
                current_index - previous_index
                for previous_index, current_index in zip(
                    rank5_raw_index, rank5_raw_index[1:], strict=False
                )
            ]

            # 将5星列表与抽数列表对应
            rank5_result = [
                GachaIndexItem(index=index, **item.model_dump())
                for item, index in zip(rank5_list, rank5_count_list, strict=False)
            ]

            pity_count = total_count - rank5_raw_index[-1]

        return GachaPoolAnalyzeResult(
            gacha_type=gacha_type,
            pity_count=pity_count,
            total_count=total_count,
            rank5=rank5_result,
        )

    async def load(self):
        if self.analyze_result_path.exists():
            self.analyze_summary = GachaAnalyzeSummary(**load_json(self.analyze_result_path))
        else:
            await self.refresh()

    async def refresh(self):
        gacha_record_list = await GachaRecordDbClient(self.user).get_all_gacha_record()

        if config.USE_METADATA:
            _update_gacha_record_metadata(self.client.metadata, gacha_record_list)

        self.analyze_summary = GachaRecordAnalyzer._analyze(self.user.uid, gacha_record_list)
        save_json(self.user.analyze_result_path, self.analyze_summary.model_dump())


def _update_gacha_record_metadata(metadata: BaseMetadata, gacha_records: list[GachaRecordItem]):
    attrs = ["name", "rank_type", "item_type"]
    for record in gacha_records:
        for attr in attrs:
            setattr(record, attr, metadata.get(record.item_id, attr))


class ExportHelper(BaseClient):
    def __init__(self, user: Account, _metadata: BaseMetadata) -> None:
        super().__init__(user)
        self.metadata = _metadata

    async def _prepare_data(
        self,
    ) -> tuple[None, None] | tuple[list[GachaRecordItem], GachaRecordBatchEntity]:
        record_db_client = GachaRecordDbClient(self.user)
        gacha_record_list = await record_db_client.get_all_gacha_record()

        if not gacha_record_list:
            return None, None
        record_batch = await record_db_client.get_latest_batch()

        if config.USE_METADATA:
            _update_gacha_record_metadata(self.metadata, gacha_record_list)
            record_batch.lang = config.METADATA_LANGUAGE
        return gacha_record_list, record_batch

    async def export_to_execl(self):
        logger.debug("Export gacha record to Execl")
        gacha_record_list, _ = await self._prepare_data()
        if not gacha_record_list:
            return False
        os.makedirs(self.user.gacha_record_xlsx_path.parent.as_posix(), exist_ok=True)
        workbook = xlsxwriter.Workbook(self.user.gacha_record_xlsx_path.as_posix())

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
                "font_color": "#757575",
                "border_color": "#c4c2bf",
                "border": 1,
                "bold": True,
            }
        )

        star_5 = workbook.add_format({"font_color": "#bd6932", "bold": True})
        star_4 = workbook.add_format({"font_color": "#a256e1", "bold": True})
        star_3 = workbook.add_format({"font_color": "#8e8e8e"})

        for gacha_type in GACHA_TYPE_IDS:
            gacha_record_type_list = [
                item for item in gacha_record_list if item.gacha_type == gacha_type
            ]
            gacha_type_name = GACHA_TYPE_DICT[gacha_type]

            worksheet = workbook.add_worksheet(gacha_type_name)
            excel_header = [
                "时间",
                "名称",
                "类别",
                "星级",
                "跃迁类型",
                "总次数",
                "保底计数",
            ]
            worksheet.set_column("A:A", 22)
            worksheet.set_column("B:B", 14)
            worksheet.set_column("E:E", 14)
            worksheet.write_row(0, 0, excel_header, title_css)
            worksheet.freeze_panes(1, 0)  # 固定标题行
            counter = 0
            pity_counter = 0
            for item in gacha_record_type_list:
                counter += 1
                pity_counter += 1
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
        workbook.close()
        return True

    async def export_to_srgf(self):
        logger.debug("Export gacha record to SRGF")
        gacha_record_list, record_batch = await self._prepare_data()
        if not gacha_record_list:
            return False

        srgf_data = convert_record_to_srgf(gacha_record_list, record_batch)
        save_json(self.user.srgf_path, srgf_data.model_dump())
        return True

    async def export_to_uigf(self):
        logger.debug("Export gacha record to UIGF")
        gacha_record_list, record_batch = await self._prepare_data()
        if not gacha_record_list:
            return False

        uigf_data = convert_record_to_uigf(gacha_record_list, record_batch)
        save_json(self.user.uigf_path, uigf_data.model_dump())
        return True


@dataclass
class FileInfo:
    name: str
    path: str
    data_type: typing.Literal["SRGF", "UIGF"]
    data: UIGFData | SRGFData


class ImportHelper(BaseClient):
    def get_import_file_list(self):
        logger.debug("Scanning files")
        import_data_path = constants.IMPORT_DATA_PATH

        return [
            os.path.join(import_data_path, name)
            for name in os.listdir(import_data_path)
            if os.path.isfile(os.path.join(import_data_path, name)) and name.endswith(".json")
        ]

    def parse_import_file(self, file_path: str):
        data = load_json(file_path)
        logger.debug("Parse file: {}", file_path)
        file_name = os.path.basename(file_path)

        if not self._is_valid_data(data):
            return None

        if "srgf_version" in data["info"]:
            if srgf_data := self._verify_srgf_data(data):
                return FileInfo(name=file_name, path=file_path, data_type="SRGF", data=srgf_data)
            else:
                return None
        else:
            if uigf_data := self._verify_uigf_data(data):
                return FileInfo(name=file_name, path=file_path, data_type="UIGF", data=uigf_data)
            else:
                return None

    async def import_srgf(self, data: SRGFData):
        logger.debug("SRGF info:{}", data.info.model_dump_json())
        if not data.list:
            return 0

        record_db_client = GachaRecordDbClient(self.user)
        latest_batch_record = await record_db_client.get_latest_batch()
        next_batch_id = 1
        if latest_batch_record:
            next_batch_id = latest_batch_record.batch_id + 1
            self._convert_srgf_timezone(data, latest_batch_record.region_time_zone)

        item_list, srgf_info = convert_srgf_to_record(data)
        info = GachaRecordInfo(
            uid=srgf_info.uid,
            batch_id=next_batch_id,
            lang=srgf_info.lang,
            region_time_zone=srgf_info.region_time_zone,
            source=f"{srgf_info.export_app}_{srgf_info.export_app_version}",
        )
        return await record_db_client.insert_gacha_record(item_list, info, "ignore")

    async def import_uigf(self, data: UIGFData):
        record = data.hkrpg[0]
        if not record.list:
            return 0
        logger.debug(
            "UIGF info: uid:{}, timezone:{}, export_app:{}, export_app_version:{}, uigf_version:{}",
            record.uid,
            record.timezone,
            data.info.export_app,
            data.info.export_app_version,
            data.info.version,
        )

        record_db_client = GachaRecordDbClient(self.user)
        latest_batch_record = await record_db_client.get_latest_batch()
        next_batch_id = 1

        if latest_batch_record:
            # 时区与第一个记录保持一致
            target_region_time_zone = latest_batch_record.region_time_zone
            next_batch_id = latest_batch_record.batch_id + 1
            self._convert_uigf_timezone(data, target_region_time_zone)

        info = GachaRecordInfo(
            uid=record.uid,
            batch_id=next_batch_id,
            lang=record.lang or "",
            region_time_zone=record.timezone,
            source=f"{data.info.export_app}_{data.info.export_app_version}",
        )

        item_list = [
            GachaRecordItem(uid=record.uid, lang=record.lang, **item.model_dump())
            for item in record.list
        ]
        return await record_db_client.insert_gacha_record(item_list, info, "ignore")

    def _is_valid_data(self, data: dict) -> bool:
        return "info" in data and ("srgf_version" in data["info"] or "version" in data["info"])

    def _verify_srgf_data(self, srgf_data: dict):
        logger.debug("validate srgf data")
        try:
            srgf_data: SRGFData = SRGFData.model_validate(srgf_data)
            if srgf_data.info.uid == self.user.uid:
                return srgf_data
        except ValidationError:
            pass

        return None

    def _verify_uigf_data(self, uigf_data: dict):
        logger.debug("validate uigf data")
        try:
            uigf_data: UIGFData = UIGFData.model_validate(uigf_data)
            uigf_data.hkrpg = [record for record in uigf_data.hkrpg if record.uid == self.user.uid]
            if uigf_data.hkrpg:
                return uigf_data
        except ValidationError:
            pass
        return None

    @staticmethod
    def _convert_srgf_timezone(data: SRGFData, target_tz: int):
        if data.info.region_time_zone == target_tz:
            return
        from_tz = data.info.region_time_zone
        for item in data.list:
            item.time = Date.convert_timezone(item.time, from_tz, target_tz)
        data.info.region_time_zone = target_tz

    @staticmethod
    def _convert_uigf_timezone(data: UIGFData, target_tz: int):
        _record = data.hkrpg[0]
        if _record.timezone == target_tz:
            return

        from_tz = _record.timezone
        for item in _record.list:
            item.time = Date.convert_timezone(item.time, from_tz, target_tz)
        _record.timezone = target_tz
