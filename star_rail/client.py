import functools

from star_rail import exceptions as error
from star_rail.i18n import i18n
from star_rail.module import AccountManager, GachaClient, MonthClient
from star_rail.utils import functional

_lang = i18n.client

__all__ = ["HSRClient"]


class HSRClient(GachaClient, MonthClient):
    def __init__(self) -> None:
        self.user = AccountManager().user

    def check_user(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            self.user = AccountManager().user
            if self.user is None:
                print(functional.color_str(_lang.no_account, "yellow"))
                return
            return func(self, *args, **kwargs)

        return wrapper

    @error.exec_catch()
    @check_user
    def refresh_month_info(self):
        # TODO 支持国际服
        from star_rail.module.mihoyo import GameBiz

        if GameBiz.get_by_uid(self.user.uid) == GameBiz.GLOBAL:
            raise error.HsrException("该功能尚未支持国际服账号")
        if not self.user.cookie.verify_cookie_token():
            print(functional.color_str(_lang.empty_cookie, "yellow"))
            return
        super().refresh_month_info()
        super().show_month_info()

    @error.exec_catch()
    @check_user
    def show_month_info(self):
        super().show_month_info()

    @error.exec_catch()
    @check_user
    def refresh_record_by_user_cache(self):
        super().refresh_record_by_user_cache()

    @error.exec_catch()
    @check_user
    def refresh_record_by_game_cache(self):
        super().refresh_record_by_game_cache()

    @error.exec_catch()
    def refresh_record_by_clipboard(self):
        super().refresh_record_by_clipboard()

    @error.exec_catch()
    @check_user
    def show_analyze_result(self):
        super().show_analyze_result()

    @error.exec_catch()
    @check_user
    def import_gacha_record(self):
        super().import_gacha_record()

    @error.exec_catch()
    @check_user
    def export_record_to_xlsx(self):
        super().export_record_to_xlsx()

    @error.exec_catch()
    @check_user
    def export_record_to_srgf(self):
        super().export_record_to_srgf()
