import pyperclip
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, VerticalScroll
from textual.events import Click
from textual.widgets import Static

from star_rail import __version__
from star_rail.tui.widgets import apply_text_color

MANUAL_PART_1 = [
    r"""[B]如何获取 Cookie[/B]""",
    (
        r"""[G]● 1.[/G] 登陆[@click="app.open_link('https://user.mihoyo.com/')"]米哈游通行证[/]"""
        r"""(国际服用户登陆 [@click="app.open_link('https://account.hoyoverse.com/')"]HoYoLAB[/]) 页面"""
    ),
    r"""[G]● 2.[/G] 点击F12按键，选择控制台，粘贴以下代码，在弹出的对话框复制 Cookie""",
]

JS_CODE = "\njavascript:(function(){prompt(document.domain,document.cookie)})();\n"


MANUAL_PART_3 = [
    r"""[G]● 3.[/G] 按照上面步骤切换为对应账号""",
    r"""[G]● 4.[/G] 点击左下角 "UID: xx" > "更新 Cookie" """,
    r"""[G]● 5.[/G] 等待 Cookie 解析完成""",
    r"",
]

UIGF_LINK = [
    r"""[M]● [/M]有关 UIGF/SRGF 格式信息，请访问 UIGF-org [@click="app.open_link('https://uigf.org/zh/')"]官网[/]了解详情"""
]

LINK_REPO = """[@click="app.open_link('https://github.com/cntvc/star-rail-tools')"]项目主页[/]"""
LINK_ISSUE = (
    """[@click="app.open_link('https://github.com/cntvc/star-rail-tools/issues')"]Bug 反馈[/]"""
)
LINK_RELEASE = (
    """[@click="app.open_link('https://github.com/cntvc/star-rail-tools/releases')"]下载链接[/]"""
)


class JSCode(Static):
    def on_click(self, event: Click):
        event.stop()
        pyperclip.copy(JS_CODE)
        self.notify("已复制到剪贴板")


class HelpManual(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Static("Star Rail Tools", id="title")
        with Container(id="content"):
            yield Static(apply_text_color(MANUAL_PART_1), id="part_1")
            with Horizontal(id="part_2"):
                js_code = JSCode(
                    Syntax(
                        JS_CODE,
                        "javascript",
                        theme="material",
                        line_numbers=True,
                    ),
                    id="part_2_code",
                )
                js_code.tooltip = "点击复制代码到剪贴板"
                yield js_code
            yield Static(apply_text_color(MANUAL_PART_3), id="part_3")
            yield Static(apply_text_color(UIGF_LINK), id="part_4")
        with Grid(id="footer"):
            yield Static(apply_text_color([f"软件版本: [G]{__version__}[/G]"]))
            yield Static(LINK_REPO)
            yield Static(LINK_ISSUE)
            yield Static(LINK_RELEASE)
