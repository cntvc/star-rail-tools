"""Exceptions"""


class StarRailError(Exception):
    def __init__(self, msg: str, *args) -> None:
        self.msg = msg.format(*args)
        super().__init__(self.msg)


class UserInfoError(StarRailError):
    pass


class PathNotExistError(StarRailError):
    pass


class InvalidDataError(StarRailError):
    pass
