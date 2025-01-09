import abc
import typing
from pathlib import Path

MetadataAttr: typing.TypeAlias = typing.Literal["name", "rank_type", "item_type"]


class BaseMetadata(abc.ABC):
    path: Path
    """Cache file path for metadata"""

    @abc.abstractmethod
    def get(self, item_id: str, key: MetadataAttr, /, default="-") -> str: ...

    @abc.abstractmethod
    async def update(self): ...

    @abc.abstractmethod
    async def check_update(self) -> bool: ...
