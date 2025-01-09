from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from star_rail.module.account import Account


class BaseClient:
    __slots__ = ("user",)

    user: Account | None

    def __init__(self, user: Account) -> None:
        self.user = user
