from textual.message import Message


class SwitchUser(Message, bubble=True):
    pass


class ChangeStarterWarp(Message, bubble=True):
    """是否显示新手池"""

    def __init__(self, value) -> None:
        super().__init__()
        self.value = value
