from textual.message import Message


class TaskStart(Message, bubble=True):
    pass


class TaskStop(Message, bubble=True):
    pass


class TaskComplete(Message, bubble=True):
    pass


class TaskError(Message, bubble=True):
    pass


class LoginAccount(Message, bubble=True):
    pass


class ChangeStarterWarp(Message, bubble=True):
    def __init__(self, value) -> None:
        super().__init__()
        self.value = value
