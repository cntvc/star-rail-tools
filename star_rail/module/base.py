from star_rail.module import Account


class BaseClient:
    __slots__ = ("user",)

    user: Account
