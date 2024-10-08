import abc
import typing
from pathlib import Path

MetadataAttr: typing.TypeAlias = typing.Literal["name", "rank_type", "item_type"]

__all__ = ["BaseMetadata"]


class BaseMetadata(abc.ABC):
    path: Path

    @abc.abstractmethod
    def get(self, lang: str, item_id: str, key: MetadataAttr, /, default="-") -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def update(self):
        raise NotImplementedError
