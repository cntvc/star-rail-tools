import math
from typing import Callable, List, Union

from pydantic import BaseModel

from star_rail import constants
from star_rail.utils.functional import clear_screen, input_int, pause


class MenuItem(BaseModel):
    title: str
    gen_menu: Callable = None
    """ 仅用于动态生成菜单选项列表的函数 -> List[MenuItem]"""
    options: Union[Callable, List["MenuItem"]] = None
    """菜单列表或功能函数"""
    tips: Union[str, Callable] = None  # Callable -> str
    """需要显示的额外信息"""


class Menu:
    def __init__(self, menu: MenuItem) -> None:
        self.menu = menu
        self.stack: List[MenuItem] = []
        self.stack.append(menu)

    def display(self):
        clear_screen()
        # 让标题打印在中间
        title = self.menu.title
        space_len = math.floor((constants.MENU_BANNER_LENGTH - len(title)) / 2)
        print(" " * space_len + title)
        print("=" * constants.MENU_BANNER_LENGTH)
        options: List[MenuItem] = self.menu.options
        for index, option in enumerate(options):
            print("{}.{}".format(index + 1, option.title))
        print("")
        if len(self.stack) > 1:
            print("0.返回上级菜单")
        else:
            print("0.退出")
        print("=" * constants.MENU_BANNER_LENGTH)

        self._display_tips()

    def _display_tips(self):
        tips = self.menu.tips
        if tips is None:
            return
        if isinstance(tips, Callable):
            print(tips())
        elif isinstance(tips, str):
            print(tips)
        print("=" * constants.MENU_BANNER_LENGTH)

    def run(self):
        while self.stack:
            # 获取当前菜单
            self.menu = self.stack[-1]

            if self.menu.gen_menu:
                self.menu.options = self.menu.gen_menu()

            self.display()
            cur_options: List[MenuItem] = self.menu.options
            print("请输入数字选择菜单项:")
            menu_index = input_int(0, len(cur_options))

            if menu_index == 0:
                self.stack.pop()
                continue

            next_menu = cur_options[menu_index - 1]
            if next_menu.gen_menu:
                # 如果菜单表需要动态生成，进入下一级再生成
                self.stack.append(next_menu)
                continue

            next_menu_options = next_menu.options
            if isinstance(next_menu_options, list):
                self.stack.append(next_menu)
                self.run()
            elif isinstance(next_menu_options, Callable):
                next_menu_options()
                pause()
                self.display()
