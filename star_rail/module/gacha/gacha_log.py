import json
import time
from operator import itemgetter
from random import random
from typing import List
from urllib import parse

import requests
import xlsxwriter
from prettytable import PrettyTable

from star_rail import APP_NAME
from star_rail import __version__ as version
from star_rail import constant
from star_rail.exceptions import InvalidDataError
from star_rail.module.gacha.metadata import GACHA_TYPE_DICT
from star_rail.module.user import User
from star_rail.utils.functional import dedupe, get_format_time, get_timestamp, load_json, save_json
from star_rail.utils.log import logger


def generate_info(uid, lang):
    sys_time = time.time()
    info = {}
    info["uid"] = uid
    info["lang"] = lang
    info["export_timestamp"] = get_timestamp(sys_time)
    info["export_time"] = get_format_time(sys_time)
    info["export_app"] = APP_NAME
    info["export_app_version"] = version
    return info


def get_uid_and_lang(gacha_log):
    uid = ""
    lang = ""
    for gacha_type in GACHA_TYPE_DICT.keys():
        if not uid and gacha_log["gacha_log"][gacha_type]:
            uid = gacha_log["gacha_log"][gacha_type][-1]["uid"]
        if not lang and gacha_log["gacha_log"][gacha_type]:
            lang = gacha_log["gacha_log"][gacha_type][-1]["lang"]
    return uid, lang


def query_gacha_log(url: str):
    """查询抽卡记录

    Args:
        url (str): URL

    Returns:
        tuple(str, dict): uid, gacha_log
    """
    logger.info("开始查询抽卡记录")
    gacha_log = {}
    gacha_log["gacha_type"] = GACHA_TYPE_DICT
    gacha_log["gacha_log"] = {}

    for gacha_type_id in GACHA_TYPE_DICT.keys():
        gacha_type_log = query_by_type_id(url, gacha_type_id)
        # 抽卡记录以时间顺序排列
        gacha_type_log.reverse()
        gacha_log["gacha_log"][gacha_type_id] = gacha_type_log

    uid, lang = get_uid_and_lang(gacha_log)
    gacha_log["info"] = generate_info(uid, lang)
    return uid, gacha_log


def query_by_type_id(url: str, gacha_type_id: str):
    """
    Query gacha log by type
    """

    max_size = "20"
    gacha_list = []
    end_id = "0"
    type_name = GACHA_TYPE_DICT[gacha_type_id]
    for page in range(1, 9999):
        msg = "\033[K正在获取 {} 卡池数据 {}".format(type_name, ".." * ((page - 1) % 3 + 1))
        print(msg, end="\r")
        url = concatenate_url_parameters(url, gacha_type_id, max_size, page, end_id)
        res = requests.get(url, timeout=constant.TIMEOUT).content.decode("utf-8")
        res_json = json.loads(res)
        gacha = res_json["data"]["list"]
        if not gacha:
            break
        for i in gacha:
            gacha_list.append(i)
        end_id = res_json["data"]["list"][-1]["id"]
        time.sleep(0.2 + random())
    completed_tips = "\033[K查询 {} 结束, 共 {} 条数据".format(type_name, len(gacha_list))
    print(completed_tips)
    logger.debug(completed_tips)
    return gacha_list


def concatenate_url_parameters(url: str, gacha_type_id, size, page, end_id=""):
    parsed = parse.urlparse(url)
    querys = parse.parse_qsl(str(parsed.query))
    param_dict = dict(querys)

    param_dict["size"] = size
    param_dict["gacha_type"] = gacha_type_id
    param_dict["page"] = page
    param_dict["lang"] = "zh-cn"
    param_dict["end_id"] = end_id

    param = parse.urlencode(param_dict)
    spliturl = url.split("?", maxsplit=1)[0]
    api = spliturl + "?" + param
    return api


def merge_data(datas: List[dict]):
    gacha_log = {}

    for gacha_type in GACHA_TYPE_DICT.keys():
        gacha_log[gacha_type] = []

    for data in datas:
        for gacha_type in GACHA_TYPE_DICT.keys():
            gacha_log[gacha_type].extend(data["list"][gacha_type])
    for gacha_type in GACHA_TYPE_DICT.keys():
        gacha_log[gacha_type] = list(dedupe(gacha_log[gacha_type], lambda x: x["id"]))
        gacha_log[gacha_type] = sorted(gacha_log[gacha_type], key=itemgetter("id"))
    gacha_data = {}
    gacha_data["gacha_log"] = gacha_log
    uid, lang = get_uid_and_lang(gacha_data)
    gacha_data["info"] = generate_info(uid, lang)
    return gacha_data


def merge_history(user: User, gacha_log):
    logger.debug("合并历史抽卡数据")
    history_gacha_log = load_json(user.gacha_log_json_path)
    if history_gacha_log:
        data = merge_data([gacha_log, history_gacha_log])
        logger.debug("合并完成")
    else:
        logger.debug("无需合并")
    return data


def analyze_gacha_log(user: User, gacha_log):
    """统计数据并生成统计结果"""
    if "gacha_log" not in gacha_log:
        raise InvalidDataError("用于统计分析的抽卡数据无效")
    logger.debug("分析抽卡数据")
    # 每个卡池统计信息：总抽数，时间范围，5星的具体抽数，当前未保底次数，平均抽数（不计算未保底）
    analyze_data = {}
    analyze_data["uid"] = user.uid
    analyze_data["time"] = get_format_time()
    for gahca_type, gacha_data in gacha_log["gacha_log"].items():
        analyze_data[gahca_type] = {}

        # 抽卡时间范围
        start_time, end_time = ("~", "~") if not gacha_data else gacha_data[0]["time"], gacha_data[
            -1
        ]["time"]
        analyze_data[gahca_type]["time_range"] = "{} ~ {}".format(start_time, end_time)

        # 5 星列表
        rank_5 = [gacha for gacha in gacha_data if gacha["rank_type"] == "5"]
        # 5 星原始位置
        rank5_index = [i for i, gacha in enumerate(gacha_data, 1) if gacha["rank_type"] == "5"]
        if rank5_index:
            # 5 星相对位置（抽数
            rank5_number = [rank5_index[0]] + [j - i for i, j in zip(rank5_index, rank5_index[1:])]
            # 将 5 星与抽数对应起来，用 number 表示抽数
            rank5_info = [
                dict(ran5_item, number=str(number))
                for ran5_item, number in zip(rank_5, rank5_number)
            ]
        else:
            rank5_info = []
        # 未保底次数
        pity_count = len(rank5_index) if not rank5_index else len(gacha_data) - rank5_index[-1]

        analyze_data[gahca_type]["rank5"] = rank5_info
        analyze_data[gahca_type]["pity_count"] = pity_count
        analyze_data[gahca_type]["total_count"] = len(gacha_data)

    save_json(user.gacha_log_analyze_path, analyze_data)
    return analyze_data


def create_xlsx(user: User, gacha_log):
    if "gacha_log" not in gacha_log:
        raise InvalidDataError("用于导出 XLSX 文件的抽卡数据无效")
    logger.debug("创建工作簿: " + user.gacha_log_xlsx_path.as_posix())
    workbook = xlsxwriter.Workbook(user.gacha_log_xlsx_path.as_posix())

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

    for gahca_type, gacha_data in gacha_log["gacha_log"].items():
        gacha_type_name = GACHA_TYPE_DICT[gahca_type]
        logger.debug("写入 {}，共 {} 条数据", gacha_type_name, len(gacha_data))
        worksheet = workbook.add_worksheet(gacha_type_name)
        excel_header = ["时间", "名称", "类别", "星级", "跃迁类型", "总次数", "保底内"]
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


def analyze_result(analyze_data):
    max_rank5_count = 0
    # 结果总览
    overview_table = PrettyTable()
    overview_table.align = "l"
    overview_table.title = "统计结果"
    overview_table.add_column("项目", ["抽卡总数", "5星总次数", "5星平均抽数", "保底内抽数"])
    for gacha_type, gacha_name in GACHA_TYPE_DICT.items():
        data = analyze_data[gacha_type]
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
    rank5_detail_table.title = "5星详情"
    rank5_detail_table.align = "l"
    for gacha_type, gacha_name in GACHA_TYPE_DICT.items():
        rank5_data: list = analyze_data[gacha_type]["rank5"]
        rank5_detail = [item["name"] + " : " + item["number"] + "抽" for item in rank5_data]
        rank5_detail += [""] * (max_rank5_count - len(rank5_detail))
        rank5_detail_table.add_column(gacha_name, rank5_detail)
    return overview_table, rank5_detail_table
