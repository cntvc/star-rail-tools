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
