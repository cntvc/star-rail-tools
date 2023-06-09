import time
from typing import List

import xlsxwriter
from prettytable import PrettyTable

from star_rail.i18n import i18n
from star_rail.module.account import Account
from star_rail.module.gacha.gacha_log import GachaData, GachaInfo, GachaType
from star_rail.utils import functional
from star_rail.utils.log import logger
from star_rail.utils.time import get_format_time, get_timezone
from star_rail.utils.version import compare_versions

_lang = i18n.gacha_data


def parse_gacha_info(user: Account, gacha_datas: List[dict]):
    """验证并生成一个 GachaInfo"""
    lang = ""
    region_time_zone = None
    for gacha_data in gacha_datas:
        info = gacha_data["info"]
        if not lang:
            lang = info["lang"]
        elif lang != info["lang"]:
            return False, "lang"
        if region_time_zone is None:
            region_time_zone = info["region_time_zone"]
        elif region_time_zone != info["region_time_zone"]:
            return False, "region_time_zone"
    return True, GachaInfo.gen(user.uid, lang, region_time_zone)


def merge(info: GachaInfo, gacha_data_list: List[dict]):
    gacha_log = {}
    for gacha_type in GachaType.list():
        gacha_log[gacha_type] = []
    for data in gacha_data_list:
        for gacha_type in GachaType.list():
            gacha_log[gacha_type].extend(data["gacha_log"][gacha_type])

    for gacha_type in GachaType.list():
        gacha_log[gacha_type] = list(functional.dedupe(gacha_log[gacha_type], lambda x: x["id"]))
        gacha_log[gacha_type] = sorted(gacha_log[gacha_type], key=lambda item: item["id"])

    gacha_data = {}
    gacha_data["info"] = info.dict()
    gacha_data["gacha_log"] = gacha_log
    gacha_data["gacha_type"] = GachaType.dict()
    return gacha_data


def create_xlsx(user: Account, gacha_data):
    if "gacha_log" not in gacha_data:
        raise ValueError(_lang.invalid_gacha_data)
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

    for gahca_type, gacha_data in gacha_data["gacha_log"].items():
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


def gacha_data_adapter(gacha_data: dict):
    """低版本 gacha_data 转换为最新的版本"""
    if compare_versions(gacha_data["info"]["export_app_version"], "1.1.0") == -1:
        # 1.1.0 版本以下 gacha_log 不包含 region_time_zone 字段，设置默认值为本地时区
        local_time = time.localtime(time.time())
        gacha_data["info"]["region_time_zone"] = get_timezone(local_time)
    return gacha_data


class Analyzer:
    def __init__(self, user: Account, result=None) -> None:
        self.user = user
        self.result = result

    @staticmethod
    def is_analyze_data(data):
        flg = True
        for type in GachaType.list():
            if type not in data:
                flg = False
        return flg and "uid" in data and "time" in data

    @staticmethod
    def parse_file(user, path):
        data = functional.load_json(path)
        if Analyzer.is_analyze_data(data):
            return Analyzer(user, data)
        elif GachaData.is_gacha_data(data):
            return Analyzer._parse_gacha_data(user, data)
        else:
            return None

    @staticmethod
    def _parse_gacha_data(user: Account, gacha_data):
        analyzer = Analyzer(user)
        analyzer.analyze(gacha_data)
        return analyzer

    def analyze(self, gacha_data):
        if "gacha_log" not in gacha_data:
            raise ValueError(_lang.invalid_gacha_data)
        logger.debug("分析抽卡数据")
        # 每个卡池统计信息：总抽数，时间范围，5星的具体抽数，当前未保底次数，平均抽数（不计算未保底）
        analyze_result = {}
        analyze_result["uid"] = self.user.uid
        analyze_result["time"] = get_format_time(time.time())
        for _gahca_type, _gacha_data in gacha_data["gacha_log"].items():
            analyze_result[_gahca_type] = {}

            # 抽卡时间范围
            start_time, end_time = (
                ("~", "~") if not _gacha_data else (_gacha_data[0]["time"], _gacha_data[-1]["time"])
            )
            analyze_result[_gahca_type]["start_time"] = start_time
            analyze_result[_gahca_type]["end_time"] = end_time

            # 5 星列表
            rank_5 = [gacha for gacha in _gacha_data if gacha["rank_type"] == "5"]
            # 5 星原始位置
            rank5_index = [i for i, gacha in enumerate(_gacha_data, 1) if gacha["rank_type"] == "5"]
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
            pity_count = len(rank5_index) if not rank5_index else len(_gacha_data) - rank5_index[-1]

            analyze_result[_gahca_type]["rank5"] = rank5_info
            analyze_result[_gahca_type]["pity_count"] = pity_count
            analyze_result[_gahca_type]["total_count"] = len(_gacha_data)

        functional.save_json(self.user.gacha_log_analyze_path, analyze_result)
        self.result = analyze_result
        return analyze_result

    def get_overview_table(self):
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
            data = self.result[gacha_type]
            total_count = data["total_count"]
            rank5_count = len(data["rank5"])
            pity_count = data["pity_count"]
            rank5_average = "-"
            if rank5_count:
                rank5_average = (total_count - pity_count) / rank5_count
                rank5_average = round(rank5_average, 2)
            overview_table.add_column(
                gacha_name, [total_count, rank5_count, rank5_average, pity_count]
            )
        return overview_table

    def get_star_5_detail_table(self):
        max_rank5_count = max(
            [len(self.result[gacha_type]["rank5"]) for gacha_type in GachaType.list()]
        )
        rank5_detail_table = PrettyTable()
        rank5_detail_table.title = i18n.table.star5.title
        rank5_detail_table.align = "l"
        for gacha_type, gacha_name in GachaType.dict().items():
            rank5_data: list = self.result[gacha_type]["rank5"]
            rank5_detail = [
                item["name"] + " : " + item["number"] + i18n.table.star5.pull_count
                for item in rank5_data
            ]
            rank5_detail += [""] * (max_rank5_count - len(rank5_detail))
            rank5_detail_table.add_column(gacha_name, rank5_detail)
        return rank5_detail_table

    def visualization(self):
        functional.clear_screen()
        print("UID:", functional.color_str("{}".format(self.result["uid"]), "green"))
        print(_lang.analyze_time, self.result["time"])
        print(self.get_overview_table())
        print(functional.color_str(_lang.tips, "yellow"), end="\n\n")
        print(self.get_star_5_detail_table())
