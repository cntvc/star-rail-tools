import typing

from prettytable import PrettyTable

from star_rail.utils import functional

from ..mihoyo.account import Account, account_manager
from ..mihoyo.client import request
from ..mihoyo.routes import MONTH_INFO_URL
from .model import MonthInfo


def fetch_month_info(user: Account, month: str = ""):
    """获取开拓月历

    cookie: cookie_token 为必须包含
    param:
        month 查询月份，为空则查询当月，格式: yyyymm"""

    param = {"uid": user.uid, "region": user.region, "month": month}

    data = request(
        method="get",
        url=MONTH_INFO_URL.get_url(),
        params=param,
        cookies=user.cookie.model_dump("all"),
    )
    return MonthInfo(**data)


def gen_month_info_tables(month_infos: typing.List[MonthInfo]):
    month_info_table = PrettyTable()

    month_info_table.align = "l"
    month_info_table.title = "开拓月历"
    month_info_table.add_column(
        "日期",  # month
        ["星穹", "票数"],  # star_coin  # rails_pass
    )
    for item in month_infos:
        month_info_table.add_column(
            item.data_month, [item.month_data.current_hcoin, item.month_data.current_rails_pass]
        )
    return month_info_table


def export_month_info():
    user = account_manager.account
    if None is user:
        print(functional.color_str("设置账户后重试", "yellow"))
        return
    if not user.cookie.verify_cookie_token():
        return
    cur_month_data = fetch_month_info(user)

    datas = []
    datas.append(cur_month_data)
    for month in cur_month_data.optional_month[1:]:
        datas.append(fetch_month_info(user, month))
    table = gen_month_info_tables(datas)
    print(table)
