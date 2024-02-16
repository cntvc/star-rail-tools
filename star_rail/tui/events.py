from textual.message import Message


class SwitchAccount(Message, bubble=True):
    pass


class ChangeAccountList(Message, bubble=True):
    pass


class ExitAccount(Message, bubble=True):
    pass


class ChangeStarterWarp(Message, bubble=True):
    """是否显示新手池"""

    def __init__(self, value) -> None:
        super().__init__()
        self.value = value
