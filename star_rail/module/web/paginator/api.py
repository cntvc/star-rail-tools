"""Base paginators made specifically for interaction with the api."""

from __future__ import annotations

import abc
import typing
import warnings

from pydantic import BaseModel

from . import base

__all__ = ["CursorPaginator", "PagedPaginator", "TokenPaginator"]


T = typing.TypeVar("T")
T_co = typing.TypeVar("T_co", covariant=True)
Model = typing.TypeVar("Model", bound=BaseModel)


class GetterCallback(typing.Protocol[T_co]):
    """Callback for returning resources based on a page"""

    async def __call__(self, page: int) -> typing.Sequence[T_co]:
        """Return a sequence of resources."""
        ...


class CursorGetterCallback(typing.Protocol[T_co]):
    """Callback for returning resource based on endid"""

    async def __call__(self, end_id: int) -> typing.Sequence[T_co]:
        """Return a sequence of resources."""
        ...


class TokenGetterCallback(typing.Protocol[T_co]):
    """Callback for returning resources based on a page or cursor."""

    async def __call__(self, token: str) -> tuple[str, typing.Sequence[T_co]]:
        """Return a sequence of resources."""
        ...


class APIPaginator(typing.Generic[T], base.BufferedPaginator[T], abc.ABC):
    """Paginator for interaction with the api."""

    __slots__ = ("getter",)

    getter: typing.Callable[..., typing.Awaitable[object]]
    """Underlying getter that yields the next page."""


class PagedPaginator(typing.Generic[T], APIPaginator[T]):
    """Paginator for resources which only require a page number.

    Due to ratelimits the requests must be sequential.
    """

    __slots__ = ("_page_size", "current_page")

    getter: GetterCallback[T]
    """Underlying getter that yields the next page."""

    _page_size: int | None
    """Expected non-zero page size to be able to tell the end."""

    current_page: int | None
    """Current page counter.."""

    def __init__(
        self,
        getter: GetterCallback[T],
        *,
        limit: int | None = None,
        page_size: int | None = None,
    ) -> None:
        super().__init__(limit=limit)
        self.getter = getter
        self._page_size = page_size

        self.current_page = 1

    async def next_page(self) -> typing.Iterable[T] | None:
        """Get the next page of the paginator."""
        if self.current_page is None:
            return None

        data = await self.getter(self.current_page)

        if self._page_size is None:
            warnings.warn("No page size specified for resource, having to guess.")
            self._page_size = len(data)

        if len(data) < self._page_size:
            self.current_page = None
            return data

        self.current_page += 1
        return data


class TokenPaginator(typing.Generic[T], APIPaginator[T]):
    """Paginator for resources which require a token."""

    __slots__ = ("_page_size", "token")

    getter: TokenGetterCallback[T]
    """Underlying getter that yields the next page."""

    _page_size: int | None
    """Expected non-zero page size to be able to tell the end."""

    token: str | None

    def __init__(
        self,
        getter: TokenGetterCallback[T],
        *,
        limit: int | None = None,
        page_size: int | None = None,
    ) -> None:
        super().__init__(limit=limit)
        self.getter = getter
        self._page_size = page_size

        self.token = ""

    async def next_page(self) -> typing.Iterable[T] | None:
        """Get the next page of the paginator."""
        if self.token is None:
            return None

        self.token, data = await self.getter(self.token)

        if self._page_size is None:
            warnings.warn("No page size specified for resource, having to guess.")
            self._page_size = len(data)

        if len(data) < self._page_size:
            self.token = None
            return data

        return data


class CursorPaginator(typing.Generic[Model], APIPaginator[Model]):
    """Paginator based on end_id cursors."""

    __slots__ = ("_page_size", "end_id", "stop_id")

    getter: CursorGetterCallback[Model]
    """Underlying getter that yields the next page."""

    _page_size: int | None
    """Expected non-zero page size to be able to tell the end."""

    end_id: int | None
    """Current end id. If none then exhausted."""

    stop_id: str | None
    """Stop turn page if end_id is smaller than stop_id."""

    def __init__(
        self,
        getter: CursorGetterCallback[Model],
        *,
        limit: int | None = None,
        end_id: int = 0,
        page_size: int | None = 20,
        stop_id: str | None = None,
    ) -> None:
        super().__init__(limit=limit)
        self.getter = getter
        self.end_id = end_id

        self._page_size = page_size
        self.stop_id = stop_id

    async def next_page(self) -> typing.Iterable[Model] | None:
        """Get the next page of the paginator."""
        if self.end_id is None:
            return None

        data = await self.getter(end_id=self.end_id)

        if self._page_size is None:
            warnings.warn("No page size specified for resource, having to guess.")
            self._page_size = len(data)

        if len(data) < self._page_size:
            self.end_id = None
            return data

        if self.stop_id is not None:
            if data[-1].id < self.stop_id:
                self.end_id = None
                return data

        self.end_id = data[-1].id
        return data
