import asyncio
import bisect
import functools
import os
import typing

import pydantic
import xlsxwriter
import yarl

from star_rail import __version__ as version
from star_rail import constants
from star_rail import exceptions as error
from star_rail.constants import APP_NAME
from star_rail.module import BaseMetadata, HakushMetadata, routes
from star_rail.module.account.account import Account
from star_rail.module.types import GameBiz
from star_rail.utils import file
from star_rail.utils.date import Date
from star_rail.utils.logger import logger

from ..base import BaseClient
from ..web import CursorPaginator, MergedPaginator, Paginator, request
from . import srgf, types, uigf
from .gacha_url import GachaUrlProvider
from .model import (
    AnalyzeResult,
    GachaRecordArchiveInfo,
    GachaRecordData,
    GachaRecordItem,
    StatisticItem,
    StatisticResult,
)
from .repository import GachaRecordRepository

if typing.TYPE_CHECKING:
    from star_rail.module import Account


__all__ = ["GachaRecordClient"]


class GachaRecordAPIClient:
    def __init__(self, url: yarl.URL, game_biz: GameBiz) -> None:
        self.game_biz = game_biz
        self.url = self._build_url(url)

    def _build_url(self, url: yarl.URL):
        """过滤并替换URL的请求路径，只保留必要的参数"""
        required_params = ("authkey", "lang", "game_biz", "authkey_ver")
        filtered_params = {key: value for key, value in url.query.items() if key in required_params}
        return routes.GACHA_LOG_URL.get_url(self.game_biz).with_query(filtered_params)

    async def fetch_url_info(self):
        """获取URL对应的 UID、lang和region"""
        uid, lang, region_time_zone = "", "", ""
        for gacha_type in types.GACHA_TYPE_IDS:
            data = await self._fetch_gacha_record_data(gacha_type, 1, 0)
            if data.list:
                region_time_zone = data.region_time_zone
                uid = data.list[0].uid
                lang = data.list[0].lang
                break
        return uid, lang, region_time_zone

    async def _fetch_gacha_record_data(
        self, gacha_type: int | str, size: int | str, end_id: int | str
    ) -> GachaRecordData:
        query_params = {
            "size": size,
            "gacha_type": gacha_type,
            "end_id": end_id,
        }
        query_params.update(self.url.query)
        return GachaRecordData(**await request("GET", url=self.url, params=query_params))

    async def _fetch_gacha_record_page(
        self, gacha_type: int | str, size: int | str, end_id: int | str
    ) -> typing.Sequence[GachaRecordItem]:
        gacha_data = await self._fetch_gacha_record_data(gacha_type, size, end_id)
        return gacha_data.list

    async def fetch_gacha_record(
        self,
        *,
        gacha_type_list: typing.Optional[typing.Union[str, typing.Sequence[str]]] = None,
        stop_id: typing.Optional[str] = None,
    ) -> Paginator[GachaRecordItem]:
        """获取跃迁记录

        Args:
            gacha_type_list: 需要查询的卡池id列表. 默认为 None 时查询全部卡池.
            stop_id: 停止查询的ID. 默认为 None 时查询全部记录

        Returns:
            Paginator[GachaRecordItem]: 按ID从大到小排列的跃迁记录迭代器
        """
        gacha_type_list = gacha_type_list or types.GACHA_TYPE_IDS

        if not isinstance(gacha_type_list, typing.Sequence):
            gacha_type_list = [gacha_type_list]

        max_page_size = 20
        iterators: list[Paginator[GachaRecordItem]] = []

        for gacha_type in gacha_type_list:
            iterators.append(
                CursorPaginator(
                    functools.partial(
                        self._fetch_gacha_record_page,
                        gacha_type=gacha_type,
                        size=max_page_size,
                    ),
                    stop_id=stop_id,
                )
            )

        if len(iterators) == 1:
            return iterators[0]

        # 合并迭代器时使用小顶堆排序，每个迭代器数据按ID从大到小排列
        # 使用 `-int(x.id)` 比较，确保按ID从大到小排序
        return MergedPaginator(iterators, key=lambda x: -int(x.id))


class GachaRecordAnalyzer(BaseClient):
    def analyze_records(self, gacha_record_list: list[GachaRecordItem]):
        analyze_result = AnalyzeResult(
            uid=self.user.uid,
            update_time=Date.format_time(),
        )

        def analyze(gacha_type: str, record_item_list: list[GachaRecordItem]):
            """分析单一跃迁类型数据"""
            # 5 星列表
            rank_5_list = [item for item in record_item_list if item.rank_type == "5"]
            # 5 星原始位置
            rank_5_raw_index = [
                i for i, item in enumerate(record_item_list, 1) if item.rank_type == "5"
            ]

            rank_5_item_list = []
            if rank_5_raw_index:
                # 计算5星抽数列表（相邻5星的位置差
                rank_5_count_list = [rank_5_raw_index[0]] + [
                    _next_index - _index
                    for _index, _next_index in zip(
                        rank_5_raw_index, rank_5_raw_index[1:], strict=False
                    )
                ]

                # 将5星列表与抽数列表对应
                rank_5_item_list = [
                    StatisticItem(index=rank_5_index, **rank_5_item.model_dump())
                    for rank_5_item, rank_5_index in zip(
                        rank_5_list, rank_5_count_list, strict=False
                    )
                ]

            # 保底计数
            pity_count = len(record_item_list) - rank_5_raw_index[-1] if rank_5_raw_index else 0

            return StatisticResult(
                gacha_type=gacha_type,
                pity_count=pity_count,
                total_count=len(record_item_list),
                rank_5=rank_5_item_list,
            )

        for gacha_type_id in types.GACHA_TYPE_IDS:
            gacha_data = [item for item in gacha_record_list if item.gacha_type == gacha_type_id]
            analyze_result.data.append(analyze(gacha_type_id, gacha_data))
        return analyze_result

    async def refresh_analyze_result(self):
        record_repository = GachaRecordRepository(self.user)
        gacha_record_list = await record_repository.get_all_gacha_record()
        analyze_result = self.analyze_records(gacha_record_list)
        file.save_json(self.user.gacha_record_analyze_path, analyze_result.model_dump())

    async def load_analyze_result(self):
        if self.user.gacha_record_analyze_path.exists():
            try:
                # 捕获异常用于在代码更新后无法加载旧版本数据时，自动刷新数据
                return AnalyzeResult(**file.load_json(self.user.gacha_record_analyze_path))
            except pydantic.ValidationError:
                await self.refresh_analyze_result()
                return AnalyzeResult(**file.load_json(self.user.gacha_record_analyze_path))
        else:
            await self.refresh_analyze_result()
            return AnalyzeResult(**file.load_json(self.user.gacha_record_analyze_path))


class GachaRecordClient(BaseClient):
    metadata: BaseMetadata
    metadata_is_updated: bool = False

    def __init__(self, user: Account, _metadata: BaseMetadata = None) -> None:
        super().__init__(user)
        self.metadata = _metadata or HakushMetadata()

    def _parse_url(self, source: typing.Literal["webcache", "clipboard"]):
        if source == "webcache":
            return GachaUrlProvider().parse_game_web_cache(self.user)
        elif source == "clipboard":
            return GachaUrlProvider().parse_clipboard_url()
        else:
            raise AssertionError(
                f"Param value error. Expected value 'webcache' or 'clipboard', got [{source}]."
            )

    async def refresh_gacha_record(self, source: typing.Literal["webcache", "clipboard"]):
        """刷新跃迁记录

        Return:
            成功更新的数量
        """
        url = self._parse_url(source)
        if url is None:
            raise error.GachaRecordError("Not found valid url.")

        api_client = GachaRecordAPIClient(url, self.user.game_biz)
        uid, lang, region_time_zone = await api_client.fetch_url_info()

        if not uid:
            raise error.GachaRecordError("This url has no gacha record.")
        logger.debug(f"url info: uid={uid}, lang={lang}, region_time_zone={region_time_zone}")
        if self.user.uid != uid:
            raise error.GachaRecordError(f"The url does not belong to {self.user.uid}.")

        record_repository = GachaRecordRepository(self.user)
        latest_record_item = await record_repository.get_latest_gacha_record_by_uid()

        stop_id = None
        if latest_record_item:
            stop_id = latest_record_item.id
        gacha_record_iter = await api_client.fetch_gacha_record(stop_id=stop_id)
        gacha_item_list = list(await gacha_record_iter.flatten())
        # 反转后为从小到大排序
        gacha_item_list.reverse()

        if latest_record_item:
            index = bisect.bisect_right(gacha_item_list, latest_record_item)
            need_insert = gacha_item_list[index:]
        else:
            need_insert = gacha_item_list

        cnt = 0
        if not need_insert:
            return cnt

        next_batch_id = await record_repository.get_next_batch_id()
        latest_batch_record = await record_repository.get_latest_batch()
        timezone = latest_batch_record.region_time_zone

        def convert_timezone(data: list[GachaRecordItem], from_tz: int, target_tz: int):
            if from_tz == target_tz:
                return
            for item in data:
                item.time = Date.convert_timezone(item.time, from_tz, target_tz)

        convert_timezone(need_insert, region_time_zone, timezone)

        info = GachaRecordArchiveInfo(
            uid=self.user.uid,
            batch_id=next_batch_id,
            lang=lang,
            region_time_zone=timezone,
            source=f"{APP_NAME}_{version}",
        )
        cnt = await record_repository.insert_gacha_record(need_insert, info)

        # 查询所有记录并生成统计结果
        await GachaRecordAnalyzer(self.user).refresh_analyze_result()
        logger.debug("{} new records added.", cnt)
        return cnt

    async def export_to_execl(self):
        """导出所有数据到ExecL"""
        logger.debug("Export gacha record to Execl.")
        record_repository = GachaRecordRepository(self.user)

        gacha_record_list = await record_repository.get_all_gacha_record()
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
                "color": "#757575",
                "border_color": "#c4c2bf",
                "border": 1,
                "bold": True,
            }
        )

        star_5 = workbook.add_format({"color": "#bd6932", "bold": True})
        star_4 = workbook.add_format({"color": "#a256e1", "bold": True})
        star_3 = workbook.add_format({"color": "#8e8e8e"})

        for gacha_type in types.GACHA_TYPE_IDS:
            gacha_record_type_list = [
                item for item in gacha_record_list if item.gacha_type == gacha_type
            ]
            gacha_type_name = types.GACHA_TYPE_DICT[gacha_type]

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
                try:
                    excel_data[3] = int(excel_data[3])
                except ValueError:
                    # 由于SRGF标准未强制包含该字段，若不存在则忽略
                    pass
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

    async def export_to_srgf(self):
        logger.debug("Export gacha record to SRGF.")
        record_repository = GachaRecordRepository(self.user)
        gacha_record_list = await record_repository.get_all_gacha_record()
        if not gacha_record_list:
            return False
        record_batch = await record_repository.get_latest_batch()
        srgf_data = srgf.convert_to_srgf(gacha_record_list, record_batch)
        file.save_json(self.user.srgf_path, srgf_data.model_dump())
        return True

    async def export_to_uigf(self):
        logger.debug("Export gacha record to UIGF")
        record_repository = GachaRecordRepository(self.user)
        gacha_record_list = await record_repository.get_all_gacha_record()
        if not gacha_record_list:
            return False
        record_batch = await record_repository.get_latest_batch()
        uigf_data = uigf.convert_to_uigf(gacha_record_list, record_batch)
        file.save_json(self.user.uigf_path, uigf_data.model_dump())
        return True

    def _update_records_from_metadata(self, lang, records: list[GachaRecordItem]):
        attrs = ["name", "rank_type", "item_type"]
        for record in records:
            for attr in attrs:
                if getattr(record, attr) != "-":
                    continue

                setattr(record, attr, self.metadata.get(lang, record.item_id, attr))

    async def _handle_srgf_data(self, srgf_data: srgf.SRGFData, timezone: int):
        logger.debug("SRGF info:{}", srgf_data.info.model_dump_json())
        if not srgf_data.list:
            return 0
        record_repository = GachaRecordRepository(self.user)
        next_batch_id = await record_repository.get_next_batch_id()

        def convert_timezone(data: srgf.SRGFData, target_tz: int):
            if data.info.region_time_zone == target_tz:
                return
            from_tz = data.info.region_time_zone
            for item in data.list:
                item.time = Date.convert_timezone(item.time, from_tz, target_tz)
            data.info.region_time_zone = target_tz
            return

        target_region_timezone = timezone
        if next_batch_id > 1:
            # 时区与第一个记录保持一致
            latest_batch_record = await record_repository.get_latest_batch()
            target_region_timezone = latest_batch_record.region_time_zone

        convert_timezone(srgf_data, target_region_timezone)

        item_list, srgf_info = srgf.convert_to_gacha_record_data(srgf_data)
        if srgf_info.lang not in ["zh-cn", "en-us"]:
            srgf_info.lang = "en-us"

        info = GachaRecordArchiveInfo(
            uid=srgf_info.uid,
            batch_id=next_batch_id,
            lang=srgf_info.lang,
            region_time_zone=target_region_timezone,
            source=f"{srgf_info.export_app}_{srgf_info.export_app_version}",
        )

        self._update_records_from_metadata(srgf_info.lang, item_list)

        return await record_repository.insert_gacha_record(item_list, info)

    async def _handle_uigf_data(self, uigf_data: uigf.UIGFModel, timezone: int):
        record = uigf_data.hkrpg[0]
        if not record.list:
            return 0

        logger.debug(
            "UIGF info: uid:{}, timezone:{}, export_app:{}, export_app_version:{}, uigf_version:{}",
            record.uid,
            record.timezone,
            uigf_data.info.export_app,
            uigf_data.info.export_app_version,
            uigf_data.info.version,
        )
        record_repository = GachaRecordRepository(self.user)
        next_batch_id = await record_repository.get_next_batch_id()

        def convert_timezone(data: uigf.UIGFModel, target_tz: int):
            _record = data.hkrpg[0]
            if _record.timezone == target_tz:
                return

            from_tz = _record.timezone
            for item in _record.list:
                item.time = Date.convert_timezone(item.time, from_tz, target_tz)
            _record.timezone = target_tz
            return

        target_region_timezone = timezone
        if next_batch_id > 1:
            # 时区与第一个记录保持一致
            latest_batch_record = await record_repository.get_latest_batch()
            target_region_timezone = latest_batch_record.region_time_zone
        convert_timezone(uigf_data, target_region_timezone)

        if record not in ["zh-cn", "en-us"]:
            record.lang = "en-us"

        info = GachaRecordArchiveInfo(
            uid=record.uid,
            batch_id=next_batch_id,
            lang=record.lang,
            region_time_zone=target_region_timezone,
            source=f"{uigf_data.info.export_app}_{uigf_data.info.export_app_version}",
        )

        item_list = [
            GachaRecordItem(uid=record.uid, lang=record.lang, **item.model_dump())
            for item in record.list
        ]
        self._update_records_from_metadata(record.lang, item_list)
        return await record_repository.insert_gacha_record(item_list, info)

    def _validate_srgf_data(self, srgf_data: dict):
        logger.debug("validate srgf data")
        try:
            srgf_data = srgf.SRGFData.model_validate(srgf_data)
        except pydantic.ValidationError:
            return False
        else:
            if srgf_data.info.uid != self.user.uid:
                return False
        return srgf_data

    def _validate_uigf_data(self, uigf_data: dict):
        logger.debug("validate uigf data")
        try:
            uigf_data = uigf.UIGFModel.model_validate(uigf_data)
        except pydantic.ValidationError:
            return False
        else:
            uigf_data.hkrpg = [record for record in uigf_data.hkrpg if record.uid == self.user.uid]
            if not uigf_data.hkrpg:
                return False
        return uigf_data

    async def import_gacha_record(self):
        logger.debug("Import gacha record.")

        if not self.metadata_is_updated:
            await self.metadata.update()
            self.metadata_is_updated = True

        import_data_path = constants.IMPORT_DATA_PATH

        file_list = [
            name
            for name in os.listdir(import_data_path)
            if os.path.isfile(os.path.join(import_data_path, name)) and name.endswith(".json")
        ]
        invalid_file_list = []
        tasks = []
        cnt = 0

        region_timezone = None
        for file_name in file_list:
            file_path = os.path.join(import_data_path, file_name)
            data = file.load_json(file_path)
            if "info" not in data or (
                "srgf_version" not in data["info"] and "version" not in data["info"]
            ):
                invalid_file_list.append(file_name)
                continue

            if "srgf_version" in data["info"]:
                if srgf_data := self._validate_srgf_data(data):
                    region_timezone = region_timezone or srgf_data.info.region_time_zone
                    tasks.append(self._handle_srgf_data(srgf_data, region_timezone))
                else:
                    invalid_file_list.append(file_name)
                continue

            if "version" in data["info"]:
                if uigf_data := self._validate_uigf_data(data):
                    region_timezone = region_timezone or uigf_data.hkrpg[0].timezone
                    tasks.append(self._handle_uigf_data(uigf_data, region_timezone))
                else:
                    invalid_file_list.append(file_name)
                continue

        if tasks:
            results = await asyncio.gather(*tasks)
            cnt = sum(results)

        if cnt:
            await GachaRecordAnalyzer(self.user).refresh_analyze_result()
        logger.debug("{} new records added.", cnt)
        return cnt, invalid_file_list

    async def display_analysis_results(self):
        analyzer = GachaRecordAnalyzer(self.user)
        return await analyzer.load_analyze_result()
