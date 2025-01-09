from __future__ import annotations

import typing

from textual import work
from textual.containers import HorizontalGroup
from textual.reactive import reactive
from textual.widgets import Static

from ._account import AccountView
from ._import import ImportScreen
from ._record import RecordView

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult, RenderResult
    from textual.events import Click

    from star_rail.module import HSRClient

__all__ = ["Footer"]


class UserNav(Static):
    uid: str = reactive("", layout=True)

    def render(self) -> RenderResult:
        return "UID: 未登陆" if not self.uid else f"UID: {self.uid}"

    def on_click(self, event: Click):
        event.stop()
        self.app.query_one(AccountView).toggle_account_view()

    def update_uid(self, uid: str):
        self.uid = uid


class RefreshNav(Static):
    def render(self) -> RenderResult:
        return "更新"

    @work
    async def on_click(self, event: Click):
        event.stop()
        opt = await self.app.push_screen_wait("refresh_screen")
        client: HSRClient = self.app.client
        if opt == "cancel":
            return
        if opt == "full_update":
            cnt = await client.refresh_gacha_record(mode="full")
        else:
            cnt = await client.refresh_gacha_record(mode="incremental")
        if cnt > 0:
            await self.app.query_one(RecordView).refresh_analyze_summary()


class ImportNav(Static):
    def render(self) -> RenderResult:
        return "导入"

    def on_click(self, event: Click):
        event.stop()
        self.app.push_screen(ImportScreen())


class ExportNav(Static):
    def render(self) -> RenderResult:
        return "导出"

    @work
    async def on_click(self, event: Click):
        event.stop()
        opt = await self.app.push_screen_wait("export_screen")
        client: HSRClient = self.app.client
        if opt == "execl":
            await client.export_to_execl()
        elif opt == "srgf":
            await client.export_to_srgf()
        elif opt == "uigf":
            await client.export_to_uigf()
        else:
            return


class HelpNav(Static):
    def render(self) -> RenderResult:
        return "帮助"

    def on_click(self, event: Click):
        event.stop()
        self.app.push_screen("help_screen")


class Footer(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield UserNav()
        yield RefreshNav()
        yield ImportNav()
        yield ExportNav()
        yield HelpNav()
