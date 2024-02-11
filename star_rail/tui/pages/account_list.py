from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView

from star_rail.module import HSRClient
from star_rail.tui import events
from star_rail.tui.widgets import SimpleButton

__all__ = ["AccountList"]


class AccountList(ModalScreen):
    user_list = reactive([])

    def compose(self) -> ComposeResult:
        with ListView():
            for user_id in self.user_list:
                yield ListItem(Label(user_id), id=f"uid_{user_id}")
        with Horizontal():
            yield SimpleButton("确认", id="confirm")
            yield SimpleButton("取消", id="cancel")

    def watch_user_list(self, new_list: list[str]):
        list_view = self.query(ListView)
        if not list_view:
            return
        list_view = list_view.first()
        with self.app.batch_update():
            list_view.clear()
            for uid in new_list:
                list_view.append(ListItem(Label(uid), id=f"uid_{uid}"))

    @on(SimpleButton.Pressed, "#confirm")
    async def action_confirm(self):
        client: HSRClient = self.app.client
        index = self.query_one(ListView).index
        uid = self.user_list[index]
        if uid != client.user.uid:
            await client.login(uid)
            self.post_message(events.SwitchUser())
        self.app.pop_screen()

    @on(SimpleButton.Pressed, "#cancel")
    def action_cancel(self):
        self.app.pop_screen()
