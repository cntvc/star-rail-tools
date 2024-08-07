import typing
from pathlib import Path

MetadataAttr: typing.TypeAlias = typing.Literal["name", "rank_type", "item_type"]


class BaseMetadata:
    data: dict = {}
    path: Path

    def get(self, item_id: str, key: MetadataAttr, /, default="-") -> str:
        raise NotImplementedError

    async def update(self):
        raise NotImplementedError

    async def fetch(self):
        raise NotImplementedError
