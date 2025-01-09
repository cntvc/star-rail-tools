from __future__ import annotations

import typing

from textual.containers import Grid, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Collapsible, Markdown, Static

from star_rail import __version__

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult, RenderResult

APP_INFO = f"""\
软件版本: [bold green]{__version__}[/]
[@click="app.open_link('https://github.com/cntvc/star-rail-tools')"]项目主页[/]
[@click="app.open_link('https://github.com/cntvc/star-rail-tools/issues')"]Bug 反馈[/]
[@click="app.open_link('https://github.com/cntvc/star-rail-tools/releases')"]下载链接[/]
"""

IMPORT_EXPORT_MANUAL = """\
## 导入数据

导入数据支持 SRGF/UIGF 两种格式的数据
将待导入的数据文件保存到软件所在目录的 UserData/Import 目录下, 该目录会在运行一次后自动创建
可以同时放入多个文件，在打开 "导入" 功能界面后，软件会自动获取该目录下的所有文件并显示可导入的文件列表

- SRGF/UIGF : SRGF/UIGF 为 UIGF 组织制定的数据交换格式, 详情请见 [UIGF 官网](http://uigf.org)
"""

# RECORD_MANUAL = """"""

ADVANCED_SETTINGS = """\
以下为可自定义的软件设置, 修改软件所在目录的 AppData/Config.json 文件即可

如果您不清楚这些是什么，请不要修改

| 设置项 | 设置描述 | 可选值|备注|
|:---|:---|:---|:---|
|CHECK_UPDATE|配置是否开启自动检测更新|true/false||
|DEFAULT_UID|软件启动时默认登陆的账号|Any|不要修改该项|
|USE_METADATA|启用第三方 metadata 以用于补全可能缺失的数据项|true/false||
|METADATA_LANGUAGE|第三方 metadata 的语言|"zh-cn"/"en-us"|仅在 USE_METADATA 设置为 true 时有效|

"""


# class AppChangelog(Collapsible):
#     BINDINGS = [("escape", "exit_help", "exit help screen")]

#     def compose(self) -> ComposeResult:
#         yield Markdown()
#         yield Button("上一页", id="prevpage")
#         yield Button("下一页", id="nextpage")

#     def on_mount(self): ...


class AppInfoView(Grid):
    def compose(self) -> ComposeResult:
        for line in APP_INFO.splitlines():
            yield Static(line)


class BackMain(Static):
    def render(self) -> RenderResult:
        return "返回主界面"

    def on_click(self):
        self.app.pop_screen()


class HelpFooter(Horizontal):
    def compose(self) -> ComposeResult:
        yield BackMain()


class HelpScreen(Screen):
    BINDINGS = [("escape", "exit_help", "exit help screen")]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("Star Rail Tools", id="title")
            with Collapsible(title="导入导出", collapsed=False):
                yield Markdown(IMPORT_EXPORT_MANUAL)
            with Collapsible(title="高级设置"):
                yield Markdown(ADVANCED_SETTINGS)
            yield AppInfoView()
        yield HelpFooter()

    def action_exit_help(self):
        self.app.pop_screen()
