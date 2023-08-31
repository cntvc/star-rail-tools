import functools
import typing

from star_rail import exceptions as error
from star_rail.i18n import i18n
from star_rail.module import AccountManager, GachaClient, MonthClient, StatisticalResult
from star_rail.utils import console

_lang = i18n.client

__all__ = ["HSRClient"]


class HSRClient:
    def __init__(self) -> None:
        self.account_manager = AccountManager()
        self.account_manager.init_default_user()

        self.user = self.account_manager.user
        self.month_client = MonthClient(self.user)
        self.gacha_client = GachaClient(self.user)

    def check_user(func: typing.Callable):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            self.user = self.account_manager.user
            if self.user is None:
                print(console.color_str(_lang.no_account, "yellow"))
                return

            if (
                self.month_client.user is None
                or self.account_manager.user != self.month_client.user
            ):
                self.user = self.account_manager.user
                self.month_client = MonthClient(self.user)
                self.gacha_client = GachaClient(self.user)

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
            print(console.color_str(_lang.empty_cookie, "yellow"))
            return
        self.month_client.refresh_month_info()
        self.month_client.show_month_info()

    @error.exec_catch()
    @check_user
    def show_month_info(self):
        self.month_client.show_month_info()

    @error.exec_catch()
    @check_user
    def refresh_record_by_user_cache(self):
        self.gacha_client.refresh_record_by_user_cache()

    @error.exec_catch()
    @check_user
    def refresh_record_by_game_cache(self):
        self.gacha_client.refresh_record_by_game_cache()

    @error.exec_catch()
    @check_user
    def refresh_record_by_clipboard(self):
        self.gacha_client.refresh_record_by_clipboard()

    @error.exec_catch()
    @check_user
    def show_analyze_result(self):
        self.gacha_client.show_analyze_result()

    @error.exec_catch()
    @check_user
    def import_gacha_record(self):
        self.gacha_client.import_gacha_record()

    @error.exec_catch()
    @check_user
    def export_record_to_xlsx(self):
        self.gacha_client.export_record_to_xlsx()

    @error.exec_catch()
    @check_user
    def export_record_to_srgf(self):
        self.gacha_client.export_record_to_srgf()

    def gen_account_menu(self):
        return self.account_manager.gen_account_menu()

    def get_account_status_desc(self):
        return self.account_manager.get_account_status_desc()

    def set_gacha_record_display_mode(self, mode: typing.Literal["table", "tree"]):
        StatisticalResult.set_display_mode(mode)

    def get_gacha_record_desc(self):
        return StatisticalResult.get_show_display_desc()
