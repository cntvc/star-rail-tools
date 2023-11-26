import bisect
import functools
import os
import typing

import pydantic
import xlsxwriter
import yarl

from star_rail import constants
from star_rail import exceptions as error
from star_rail.core import CursorPaginator, MergedPaginator, Paginator, request
from star_rail.database import AsyncDBClient
from star_rail.module import Account, routes
from star_rail.module.base import BaseClient
from star_rail.utils import functional
from star_rail.utils.time import TimeUtils

from . import srgf, types
from .gacha_url import GachaUrlProvider
from .mapper import GachaRecordBatchMapper, GachaRecordItemMapper
from .model import AnalyzeResult, GachaRecordData, GachaRecordItem, StatisticItem, StatisticResult

__all__ = ["GachaRecordClient"]


class GachaRecordAPIClient(BaseClient):
    def __init__(self, user: Account) -> None:
        self.user = user

    def filter_required_params(self, url: yarl.URL):
        """链接替换请求路径只保留必要的参数"""
        required_params = ("authkey", "lang", "game_biz", "authkey_ver")
        filtered_params = {key: value for key, value in url.query.items() if key in required_params}
        return routes.GACHA_LOG_URL.get_url(self.user.game_biz).with_query(filtered_params)

    async def get_url_info(self, url: yarl.URL):
        """获取URL对应的 UID 和 region 等信息"""
        uid, lang, region_time_zone = "", "", ""
        for gacha_type in types.GACHA_TYPE_IDS:
            data = await self.request_gacha_record_data(url, gacha_type, 1, 0)
            if data.list:
                region_time_zone = data.region_time_zone
                uid = data.list[0].uid
                lang = data.list[0].lang
                break
        return uid, lang, region_time_zone

    async def request_gacha_record_data(
        self, url: yarl.URL, gacha_type: int | str, size: int | str, end_id: int | str
    ) -> GachaRecordData:
        query_params = {
            "size": size,
            "gacha_type": gacha_type,
            "end_id": end_id,
        }
        query_params.update(url.query)
        return GachaRecordData(**await request("GET", url=url, params=query_params))

    async def request_gacha_record_page(
        self, url: yarl.URL, gacha_type: int | str, size: int | str, end_id: int | str
    ) -> typing.Sequence[GachaRecordItem]:
        gacha_data = await self.request_gacha_record_data(url, gacha_type, size, end_id)
        return gacha_data.list

    async def get_gacha_record(
        self,
        url: yarl.URL,
        *,
        gacha_type_list: typing.Optional[typing.Union[str, typing.Sequence[str]]] = None,
        end_id=0,
    ) -> Paginator[GachaRecordItem]:
        """获取跃迁记录

        Args:
            url (yarl.URL): 跃迁记录URL
            gacha_type_list : 需要查询的卡池id列表. 默认为 None 时查询全部卡池.
            end_id (int, optional): 用于翻页的起始查询id. 默认 0 时从第一页开始.

        Returns:
            Paginator[GachaRecordItem]: 从大到小迭代跃迁记录
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
                        self.request_gacha_record_page,
                        url=url,
                        gacha_type=gacha_type,
                        size=max_page_size,
                    ),
                    end_id=end_id,
                    page_size=max_page_size,
                )
            )

        if len(iterators) == 1:
            return iterators[0]
        # 从大到小的迭代器，在小顶堆中按从大到小输出，
        return MergedPaginator(iterators, key=lambda x: -int(x.id))


class GachaRecordRepository(BaseClient):
    def __init__(self, user: Account) -> None:
        self.user = user

    async def get_next_batch_id(self) -> int:
        """从批次表中获取下一个可用的批次ID"""
        return await GachaRecordBatchMapper.query_next_batch_id()

    async def get_all_batch(self):
        """查询所有批次信息"""

    async def get_latest_batch(self) -> GachaRecordBatchMapper | None:
        return await GachaRecordBatchMapper.query_latest_batch(self.user.uid)

    async def get_latest_gacha_record_by_uid(self) -> typing.Optional[GachaRecordItem]:
        """根据UID从数据库查询出最大的一条记录"""
        record_mapper = await GachaRecordItemMapper.query_latest_gacha_record(self.user.uid)
        if not record_mapper:
            return None
        from . import converter

        return converter.convert_to_record_item(record_mapper)

    async def get_all_gacha_record(self) -> list[GachaRecordItem]:
        """查询账户的所有抽卡记录"""
        record_mapper_list = await GachaRecordItemMapper.query_all_gacha_record(self.user.uid)
        from . import converter

        return converter.convert_to_record_item(record_mapper_list)

    async def insert_gacha_record(self, gacha_record_list: list[GachaRecordItem], params: dict):
        """批量插入抽卡记录

        Args:
            gacha_record_list (list[GachaRecordItem]): 抽卡记录
            params (dict): 抽卡记录归档信息
                required: (uid, batch_id, lang, region_time_zone, source)

        Raises:
            error.HsrException: 保存数据出现错误
        """

        from . import converter

        record_item_mapper_list = converter.convert_to_record_item_mapper(
            gacha_record_list, params["batch_id"]
        )

        async with AsyncDBClient() as db:
            await db.start_transaction()
            cnt = await db.insert(record_item_mapper_list, mode="ignore")

            if cnt == 0:
                # 数据库无新增记录
                return 0
            local_time = TimeUtils.get_local_time()
            server_time = TimeUtils.local_time_to_timezone(local_time, params["region_time_zone"])

            record_batch_mapper = GachaRecordBatchMapper(
                **params, count=cnt, timestamp=TimeUtils.convert_to_timestamp(server_time)
            )
            await db.insert(record_batch_mapper, "ignore")

            await db.commit_transaction()
        return cnt


class GachaRecordAnalyzer(BaseClient):
    def __init__(self, user: Account) -> None:
        self.user = user

    def analyze_records(self, gacha_record_list: list[GachaRecordItem]):
        analyze_result = AnalyzeResult(
            uid=self.user.uid,
            update_time=TimeUtils.get_format_time(TimeUtils.get_time()),
        )

        def analyze(gacha_type: str, record_item_list: list[GachaRecordItem]):
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
                    StatisticItem(index=str(rank_5_index), **rank_5_item.model_dump())
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
        functional.save_json(self.user.gacha_record_analyze_path, analyze_result.model_dump())

    async def load_analyze_result(self):
        if self.user.gacha_record_analyze_path.exists():
            try:
                return AnalyzeResult(**functional.load_json(self.user.gacha_record_analyze_path))
            except pydantic.ValidationError:
                await self.refresh_analyze_result()
                return AnalyzeResult(**functional.load_json(self.user.gacha_record_analyze_path))
        else:
            await self.refresh_analyze_result()
            return AnalyzeResult(**functional.load_json(self.user.gacha_record_analyze_path))


class GachaRecordClient(BaseClient):
    def __init__(self, user: Account) -> None:
        self.user = user

    async def refresh_gacha_record(self, source: typing.Literal["webcache", "clipboard"]):
        """刷新跃迁记录

        Return:
            成功更新的数量
        """
        if source == "webcache":
            url = GachaUrlProvider().parse_game_web_cache(self.user)
        elif source == "clipboard":
            url = GachaUrlProvider().parse_clipboard_url()
        else:
            raise error.HsrException(
                f"Param value error. Expected value 'webcache' or 'clipboard', got [{source}]."
            )
        if url is None:
            raise error.GachaRecordError("Not found valid url.")

        api_client = GachaRecordAPIClient(self.user)
        url = api_client.filter_required_params(url)
        uid, lang, region_time_zone = await api_client.get_url_info(url)

        if not uid:
            raise error.GachaRecordError("This url has no gacha record.")

        if self.user.uid != uid:
            raise error.GachaRecordError("The url does not belong to the current account.")

        gacha_record_iter = await api_client.get_gacha_record(url)
        gacha_item_list = list(await gacha_record_iter.flatten())
        # 反转后为从小到大排序
        gacha_item_list.reverse()

        # 新增数据插入到数据库：
        # 首先查询批次表，获取下一个批次ID
        # 根据UID从数据库查询出最大的一条记录
        #     如果无记录，直接全部插入
        #     有记录，比较id后只对数据库插入不存在的条目
        # 根据插入操作返回的数量，生成 时间、数据来源、服务器时区、语言等信息，插入到 批次表

        record_repository = GachaRecordRepository(self.user)
        latest_record = await record_repository.get_latest_gacha_record_by_uid()

        if latest_record:
            index = bisect.bisect_right(gacha_item_list, latest_record)
            need_insert = gacha_item_list[index:]
        else:
            need_insert = gacha_item_list
        cnt = 0
        if need_insert:
            next_batch_id = await record_repository.get_next_batch_id()
            params = dict(
                uid=self.user.uid,
                batch_id=next_batch_id,
                lang=lang,
                region_time_zone=region_time_zone,
                source=source,
            )
            cnt = await record_repository.insert_gacha_record(need_insert, params)

        # 查询所有记录并生成统计结果
        await GachaRecordAnalyzer(self.user).refresh_analyze_result()
        return cnt

    async def export_to_execl(self):
        """导出所有数据到ExecL

        即使账户无数据也会正常导出
        """
        record_repository = GachaRecordRepository(self.user)

        gacha_record_list = await record_repository.get_all_gacha_record()
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

    async def export_to_srgf(self):
        record_repository = GachaRecordRepository(self.user)
        gacha_record_list = await record_repository.get_all_gacha_record()
        if not gacha_record_list:
            return False
        record_batch = await record_repository.get_latest_batch()
        srgf_data = srgf.convert_to_srgf(gacha_record_list, record_batch)
        functional.save_json(self.user.srgf_path, srgf_data.model_dump())
        return True

    async def _import_srgf_data(self, file_data: srgf.SRGFData):
        record_repository = GachaRecordRepository(self.user)
        item_list, info = srgf.convert_to_gacha_record_data(file_data)

        next_batch_id = await record_repository.get_next_batch_id()
        info.update(batch_id=next_batch_id)
        return await record_repository.insert_gacha_record(item_list, info)

    async def import_srgf_json(self):
        """导入SRGF数据

        Return:
            成功导入的数据数量"""
        import_data_path = constants.IMPORT_DATA_PATH
        file_list = [
            name
            for name in os.listdir(import_data_path)
            if os.path.isfile(os.path.join(import_data_path, name)) and name.endswith(".json")
        ]
        invalid_file_list = []
        cnt = 0

        for file_name in file_list:
            file_path = os.path.join(import_data_path, file_name)
            data = functional.load_json(file_path)
            try:
                srgf_data = srgf.SRGFData.model_validate(data)
            except pydantic.ValidationError:
                invalid_file_list.append(file_name)
                continue
            if srgf_data.info.uid != self.user.uid:
                invalid_file_list.append(file_name)
                continue

            cnt += await self._import_srgf_data(srgf_data)

        if cnt:
            await GachaRecordAnalyzer(self.user).refresh_analyze_result()
        return cnt, invalid_file_list

    async def view_analysis_results(self):
        analyzer = GachaRecordAnalyzer(self.user)
        return await analyzer.load_analyze_result()
