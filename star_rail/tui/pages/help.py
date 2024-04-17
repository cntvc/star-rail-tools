import pyperclip
from rich.syntax import Syntax
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, VerticalScroll
from textual.widgets import Static

from star_rail import __version__
from star_rail.tui.widgets import SimpleButton, apply_text_color

MENUAL_PART_1 = [
    r"""[B]创建账号[/B]""",
    r"""点击左下角 "+" 按钮, 根据弹窗提示, 添加账号""",
    r"",
    r"""[B]切换账号[/B]""",
    r"""点击左下角 "UID: xx", 选择需要切换的账号, 点击 "切换账号" 按钮""",
    r"",
    r"""[B]如何获取 Cookie[/B]""",
    (
        r"""[G]● 1.[/G] 登陆[@click="app.open_link('https://user.mihoyo.com/')"]米哈游通行证[/]"""
        r"""(国际服用户登陆[@click="app.open_link('https://account.hoyoverse.com/')"]HoYoLAB[/]) 页面"""
    ),
    r"""[G]● 2.[/G] 点击F12按键，选择控制台，粘贴以下代码，在弹出的对话框复制 Cookie""",
]

JS_CODE = "\njavascript:(function(){prompt(document.domain,document.cookie)})();\n"


MENUAL_PART_3 = [
    r"""[G]● 3.[/G] 按照上面步骤切换为对应账号""",
    r"""[G]● 4.[/G] 点击左下角 "UID: xx" > "更新 Cookie" """,
    r"""[G]● 5.[/G] 等待 Cookie 解析完成""",
]


LINK_REPO = """[@click="app.open_link('https://github.com/cntvc/star-rail-tools')"]项目主页[/]"""
LINK_ISSUE = (
    """[@click="app.open_link('https://github.com/cntvc/star-rail-tools/issues')"]Bug 反馈[/]"""
)
LINK_RELEASE = (
    """[@click="app.open_link('https://github.com/cntvc/star-rail-tools/releases')"]下载链接[/]"""
)


class HelpMenual(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Static("Star Rail Tools", id="title")
        with Container(id="content"):
            yield Static(apply_text_color(MENUAL_PART_1), id="part_1")
            with Horizontal(id="part_2"):
                yield Static(
                    Syntax(
                        JS_CODE,
                        "javascript",
                        theme="material",
                        line_numbers=True,
                    ),
                    id="part_2_code",
                )
                yield SimpleButton("复制", id="copy")
            yield Static(apply_text_color(MENUAL_PART_3), id="part_3")
        with Grid(id="footer"):
            yield Static(apply_text_color([f"软件版本: [G]{__version__}[/G]"]))
            yield Static(LINK_REPO)
            yield Static(LINK_ISSUE)
            yield Static(LINK_RELEASE)

    @on(SimpleButton.Pressed)
    def copy_code(self, event: SimpleButton.Pressed) -> None:
        event.stop()
        pyperclip.copy(JS_CODE)
        self.notify("已复制到剪贴板")
