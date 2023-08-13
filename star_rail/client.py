from star_rail.module.mihoyo.account import account_manager
from star_rail.module.month.client import MonthClient
from star_rail.utils import functional

__all__ = ["refresh_month_info", "show_month_info"]


def refresh_month_info():
    user = account_manager.account
    if None is user:
        print(functional.color_str("未设置账户", "yellow"))
        return
    if not user.cookie.verify_cookie_token():
        return
    month_client = MonthClient(user)
    month_client.refresh_month_info()
    month_client.visualization()


def show_month_info():
    user = account_manager.account
    if None is user:
        print(functional.color_str("未设置账户", "yellow"))
        return
    month_client = MonthClient(user)
    month_client.visualization()
