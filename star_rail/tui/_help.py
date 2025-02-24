from __future__ import annotations

import typing

from textual.containers import Grid, VerticalScroll
from textual.screen import Screen
from textual.widgets import Collapsible, Markdown, Static

from star_rail import __version__

from ._footer import Footer

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult, RenderResult

APP_INFO = f"""\
软件版本: [bold green]{__version__}[/]
[@click="app.open_link('https://github.com/cntvc/star-rail-tools')"]项目主页[/]
[@click="app.open_link('https://github.com/cntvc/star-rail-tools/issues')"]Bug 反馈[/]
[@click="app.open_link('https://github.com/cntvc/star-rail-tools/releases')"]下载链接[/]
"""

IMPORT_EXPORT_MANUAL = """\
导入数据支持 SRGF/UIGF 两种格式的数据

将待导入的数据文件存放到软件所在目录的 Import 目录下, 该目录会在运行一次后自动创建

您可以同时放入多个文件，在打开 "导入" 功能界面后，软件会自动获取该目录下的所有文件并显示可导入的文件信息

- SRGF/UIGF 为 UIGF 组织制定的数据交换格式, 详情请见 [UIGF 官网](http://uigf.org)
"""


CUSTOM_SETTINGS = """\
以下为可自定义的软件设置, 修改软件所在目录的 AppData/config.json 文件对应配置条目即可

!!! 如果您不清楚这些是什么，请不要修改

| 设置项 | 设置描述 | 默认值 | 可选值 | 备注 |
|:---|:---|:---|:---|:---|
|CHECK_UPDATE|自动检测更新|true|true/false||
|USE_METADATA|启用第三方 metadata|true|true/false|部分软件导出记录时仅包含必要数据, 导致软件无法进行统计分析, 启用该选项后可自动补全所需数据|
|METADATA_LANGUAGE|第三方 metadata 的语言|"zh-cn"|"zh-cn"/"en-us"|仅在 USE_METADATA 设置为 true 时有效|
"""


ERROR_MSG = """\
下面是一些常见的错误消息及对应解决方案

| 错误消息 | 解决方案 |
|:---|:---|
|当前跃迁记录不属于用户xxx|请切换软件账号或游戏账号使二者 UID 保持一致|
|未获取到有效链接|链接已过期，请打开游戏浏览抽卡历史记录后重试|
|Invalid Authkey |链接已过期，请打开游戏浏览抽卡历史记录后重试|
|出现未知错误|请点击下方的 Bug 反馈, 创建对应的 Issue 条目并附上日志文件|
"""


OTHERS = """\
- 切换主题: 按下组合键 Ctrl + P 会出现命令行, 选择 "Change theme"
- 退出程序: 按下组合键 Ctrl + Q 会退出程序
"""


class AppInfoView(Grid):
    def compose(self) -> ComposeResult:
        for line in APP_INFO.splitlines():
            yield Static(line)


class ReturnBtn(Static):
    def render(self) -> RenderResult:
        return "返回主界面"

    def on_click(self):
        self.app.switch_mode("home")


class HelpScreen(Screen):
    BINDINGS = [("escape", "exit_help", "exit help screen")]
    FOOTER_KEY = [ReturnBtn]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("Star Rail Tools", id="title")
            with Collapsible(title="导入数据", collapsed=False):
                yield Markdown(IMPORT_EXPORT_MANUAL)
            with Collapsible(title="常见错误"):
                yield Markdown(ERROR_MSG)
            with Collapsible(title="自定义设置"):
                yield Markdown(CUSTOM_SETTINGS)
            with Collapsible(title="其他"):
                yield Markdown(OTHERS)
            yield AppInfoView()
        yield Footer()

    def action_exit_help(self):
        self.app.switch_mode("home")
