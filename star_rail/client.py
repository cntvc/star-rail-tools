from star_rail.i18n import i18n
from star_rail.module import MonthClient, UserManager
from star_rail.module.month.mapper import MonthInfoMapper
from star_rail.utils import functional

__all__ = ["refresh_month_info", "show_month_info"]

_lang = i18n.client
##############################################################
# 跃迁记录
##############################################################


class HSRClient:
    def __init__(self) -> None:
        pass


def refresh_month_info():
    user = UserManager().user
    if None is user:
        print(functional.color_str(_lang.no_account, "yellow"))
        return
    if not user.cookie.verify_cookie_token():
        print(functional.color_str(_lang.empty_cookie, "yellow"))
        return
    month_client = MonthClient(user)
    month_client.refresh_month_info()
    month_client.visualization(MonthInfoMapper.query(user.uid, None, 6))


def show_month_info():
    user = UserManager().user
    if None is user:
        print(functional.color_str(_lang.no_account, "yellow"))
        return
    month_client = MonthClient(user)
    month_client.visualization(MonthInfoMapper.query(user.uid, None, 6))
