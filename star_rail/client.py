from star_rail.module.mihoyo.account import UserManager
from star_rail.module.month.client import MonthClient
from star_rail.module.month.mapper import MonthInfoMapper
from star_rail.utils import functional

__all__ = ["refresh_month_info", "show_month_info"]


##############################################################
# 跃迁记录
##############################################################


def refresh_month_info():
    user = UserManager().user
    if None is user:
        print(functional.color_str("未设置账户", "yellow"))
        return
    if not user.cookie.verify_cookie_token():
        print(functional.color_str("未找到 cookie，请设置 cookie 后重试", "yellow"))
        return
    month_client = MonthClient(user)
    month_client.refresh_month_info()
    month_client.visualization(MonthInfoMapper.query(user.uid, None, 6))


def show_month_info():
    user = UserManager().user
    if None is user:
        print(functional.color_str("未设置账户", "yellow"))
        return
    month_client = MonthClient(user)
    month_client.visualization(MonthInfoMapper.query(user.uid, None, 6))
