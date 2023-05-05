import math
from typing import Callable, List, Union

from pydantic import BaseModel

from star_rail.utils.functional import clear_screen, input_int, pause


class MenuItem(BaseModel):
    title: str
    options: Union[Callable, List["MenuItem"]] = None
    tips: Union[str, Callable] = None  # Callable -> str


class Menu:
    MAX_MENU_LENGTH = 40

    def __init__(self, menu: MenuItem) -> None:
        self.menu = menu
        self.stack: List[MenuItem] = []
        self.stack.append(menu)

    def display(self):
        clear_screen()
        # 让标题打印在中间
        title = self.menu.title
        space_len = math.floor((Menu.MAX_MENU_LENGTH - len(title)) / 2)
        print(" " * space_len + title)
        print("=" * Menu.MAX_MENU_LENGTH)
        options: List[MenuItem] = self.menu.options
        for index, option in enumerate(options):
            print("{}.{}".format(index + 1, option.title))
        print("")
        if len(self.stack) > 1:
            print("0.返回上级菜单")
        else:
            print("0.退出")
        print("=" * Menu.MAX_MENU_LENGTH)

        self._display_tips()

    def _display_tips(self):
        tips = self.menu.tips
        if tips is None:
            return
        if isinstance(tips, Callable):
            print(tips())
        elif isinstance(tips, str):
            print(tips)
        print("=" * Menu.MAX_MENU_LENGTH)

    def run(self):
        while self.stack:
            # 获取当前菜单
            self.menu = self.stack[-1]
            self.display()
            options: list = self.menu.options
            print("请输入数字选择菜单项:")
            choice = input_int(0, len(options))

            # 根据当前菜单的内容的类型进行相应的处理
            if choice == 0:
                self.stack.pop()
                continue

            option = options[choice - 1].options

            if isinstance(option, list):
                self.stack.append(options[choice - 1])
                self.display()
                self.run()
            elif isinstance(option, Callable):
                option()
                pause()
                self.display()
