from star_rail.module import Account


class BaseClient:
    __slots__ = ("user",)

    user: Account

    def __init__(self, user:Account) -> None:
        self.user = user
