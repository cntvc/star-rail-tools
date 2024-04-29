from textual.message import Message
from textual.worker import Worker


class LoginAccount(Message, bubble=True):
    def __init__(self, uid: str) -> None:
        super().__init__()
        self.uid = uid


class UpdateAccountList(Message, bubble=True):
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


class TaskStatus(Message, bubble=True):
    def __init__(self, worker: Worker) -> None:
        super().__init__()
        self.worker = worker


class TaskRunning(TaskStatus):
    pass


class TaskCancel(TaskStatus):
    pass


class TaskComplete(TaskStatus):
    pass


class TaskError(TaskStatus):
    pass
