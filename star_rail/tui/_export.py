from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Button


class ExportScreen(ModalScreen[str]):
    BINDINGS = [("escape", "handle_cancel", "cancel_export")]

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Button("导出 Execl", id="export_excel")
            yield Button("导出 SRGF", id="export_srgf")
            yield Button("导出 UIGF", id="export_uigf")
            yield Button("取消", id="cancel")

    @on(Button.Pressed, "#export_excel")
    def handle_export_execl(self):
        self.dismiss("execl")

    @on(Button.Pressed, "#export_srgf")
    def handle_export_srgf(self):
        self.dismiss("srgf")

    @on(Button.Pressed, "#export_uigf")
    def handle_export_uigf(self):
        self.dismiss("uigf")

    @on(Button.Pressed, "#cancel")
    def action_handle_cancel(self):
        self.dismiss("cancel")
