import json
import time
from operator import itemgetter
from random import random
from typing import List
from urllib import parse

import requests
import xlsxwriter
from prettytable import PrettyTable

from star_rail import constants
from star_rail.i18n import i18n
from star_rail.module.account import Account
from star_rail.module.gacha.model import GachaInfo, GachaType
from star_rail.utils import functional
from star_rail.utils.log import logger

_lang = i18n.gacha_log


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
        gacha_data["info"] = GachaInfo(self.uid, self.lang, self.region_time_zone).dict()
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


class GachaDataProcessor:
    def __init__(self, gacha_data) -> None:
        self.gacha_data = gacha_data
        self.user = Account(gacha_data["info"]["uid"])
        self.analyze_result = None

    def analyze(self):
        """统计5星数据并生成统计结果"""
        if "gacha_log" not in self.gacha_data:
            raise ValueError("用于统计分析的抽卡数据无效")
        logger.debug("分析抽卡数据")
        # 每个卡池统计信息：总抽数，时间范围，5星的具体抽数，当前未保底次数，平均抽数（不计算未保底）
        analyze_result = {}
        analyze_result["uid"] = self.user.uid
        analyze_result["time"] = functional.get_format_time(time.time())
        for gahca_type, gacha_data in self.gacha_data["gacha_log"].items():
            analyze_result[gahca_type] = {}

            # 抽卡时间范围
            start_time, end_time = (
                ("~", "~") if not gacha_data else (gacha_data[0]["time"], gacha_data[-1]["time"])
            )
            analyze_result[gahca_type]["start_time"] = start_time
            analyze_result[gahca_type]["end_time"] = end_time

            # 5 星列表
            rank_5 = [gacha for gacha in gacha_data if gacha["rank_type"] == "5"]
            # 5 星原始位置
            rank5_index = [i for i, gacha in enumerate(gacha_data, 1) if gacha["rank_type"] == "5"]
            if rank5_index:
                # 5 星相对位置（抽数
                rank5_number = [rank5_index[0]] + [
                    j - i for i, j in zip(rank5_index, rank5_index[1:])
                ]
                # 将 5 星与抽数对应起来，用 number 表示抽数
                rank5_info = [
                    dict(ran5_item, number=str(number))
                    for ran5_item, number in zip(rank_5, rank5_number)
                ]
            else:
                rank5_info = []
            # 未保底次数
            pity_count = len(rank5_index) if not rank5_index else len(gacha_data) - rank5_index[-1]

            analyze_result[gahca_type]["rank5"] = rank5_info
            analyze_result[gahca_type]["pity_count"] = pity_count
            analyze_result[gahca_type]["total_count"] = len(gacha_data)

        functional.save_json(self.user.gacha_log_analyze_path, analyze_result)
        return analyze_result

    @staticmethod
    def merge_data(gacha_data_list: List[dict]):
        gacha_log = {}
        for gacha_type in GachaType.list():
            gacha_log[gacha_type] = []
        region_time_zone = None
        for data in gacha_data_list:
            for gacha_type in GachaType.list():
                gacha_log[gacha_type].extend(data["gacha_log"][gacha_type])
                if region_time_zone is None:
                    region_time_zone = data["info"].get("region_time_zone", None)
        for gacha_type in GachaType.list():
            gacha_log[gacha_type] = list(
                functional.dedupe(gacha_log[gacha_type], lambda x: x["id"])
            )
            gacha_log[gacha_type] = sorted(gacha_log[gacha_type], key=itemgetter("id"))

        gacha_data = {}
        uid, lang = get_uid_and_lang(gacha_log)
        gacha_data["info"] = GachaInfo(uid, lang, region_time_zone).dict()
        gacha_data["gacha_log"] = gacha_log
        gacha_data["gacha_type"] = GachaType.dict()
        return gacha_data

    def merge_history(self):
        logger.debug("合并历史抽卡数据")
        if not self.user.gacha_log_json_path.exists():
            return
        history_gacha_log = functional.load_json(self.user.gacha_log_json_path)
        if history_gacha_log:
            self.gacha_data = GachaDataProcessor.merge_data([self.gacha_data, history_gacha_log])
            logger.debug("合并完成")
        else:
            logger.debug("无需合并")

    def create_xlsx(self):
        if "gacha_log" not in self.gacha_data:
            raise ValueError(_lang.invalid_gacha_data)
        logger.debug("创建工作簿: " + self.user.gacha_log_xlsx_path.as_posix())
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

        for gahca_type, gacha_data in self.gacha_data["gacha_log"].items():
            gacha_type_name = GachaType.dict()[gahca_type]
            logger.debug("写入 {}，共 {} 条数据", gacha_type_name, len(gacha_data))
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
            for gacha in gacha_data:
                counter = counter + 1
                pity_counter = pity_counter + 1
                excel_data = [
                    gacha["time"],
                    gacha["name"],
                    gacha["item_type"],
                    gacha["rank_type"],
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

        workbook.close()
        logger.debug("工作簿写入完成")


def convert_to_table(analyze_result):
    """处理分析结果并转换为 PrettyTable"""
    max_rank5_count = 0
    # 结果总览
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
    for gacha_type, gacha_name in GachaType.dict().items():
        data = analyze_result[gacha_type]
        total_count = data["total_count"]
        rank5_count = len(data["rank5"])
        pity_count = data["pity_count"]
        rank5_average = "-"
        if rank5_count:
            rank5_average = (total_count - pity_count) / rank5_count
            rank5_average = round(rank5_average, 2)
        overview_table.add_column(gacha_name, [total_count, rank5_count, rank5_average, pity_count])
        # 记录5星最大的个数，用于在5星详情表格中对齐
        max_rank5_count = max(max_rank5_count, rank5_count)

    # 5 星详情
    rank5_detail_table = PrettyTable()
    rank5_detail_table.title = i18n.table.star5.title
    rank5_detail_table.align = "l"
    for gacha_type, gacha_name in GachaType.dict().items():
        rank5_data: list = analyze_result[gacha_type]["rank5"]
        rank5_detail = [
            item["name"] + " : " + item["number"] + i18n.table.star5.pull_count
            for item in rank5_data
        ]
        rank5_detail += [""] * (max_rank5_count - len(rank5_detail))
        rank5_detail_table.add_column(gacha_name, rank5_detail)
    return overview_table, rank5_detail_table
