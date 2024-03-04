from textual.message import Message


class SwitchAccount(Message, bubble=True):
    pass


class ChangeAccountList(Message, bubble=True):
    pass


class ExitAccount(Message, bubble=True):
    pass


class ReverseGachaRecord(Message, bubble=True):
    """修改逆序显示跃迁记录设置"""

    def __init__(self, value) -> None:
        super().__init__()
        self.value = value


class ShowLuckLevel(Message, bubble=True):
    def __init__(self, value) -> None:
        super().__init__()
        self.value = value
