from textual.message import Message


class SwitchAccount(Message, bubble=True):
    pass


class ChangeAccountList(Message, bubble=True):
    pass


class ExitAccount(Message, bubble=True):
    pass
