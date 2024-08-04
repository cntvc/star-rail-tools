import json
import os.path

import aiohttp

from star_rail import constants
from star_rail.utils.file import load_json, save_json
from star_rail.utils.logger import logger

from .base import BaseMetadata, MetadataAttr

__all__ = ["HakushMetadata"]


class HakushMetadata(BaseMetadata):
    LIGHTCONE_API = "https://api.hakush.in/hsr/data/lightcone.json"
    CHARACTER_API = "https://api.hakush.in/hsr/data/character.json"
    path = os.path.join(constants.TEMP_PATH, "hakush_metadata.json")

    def __init__(self):
        if os.path.exists(self.path):
            self.data = load_json(self.path)

    def get(self, item_id: str, key: MetadataAttr, /, default="-") -> str:
        if item_id not in self.data:
            return default
        return self.data[item_id][key]

    async def update(self):
        self.data = await self.fetch()
        save_json(self.path, self.data)

    async def fetch(self):
        logger.debug("Fetching Hakush metadata")
        item_dict = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.CHARACTER_API) as resp:
                data = await resp.text()
                data = json.loads(data)
                data = {key: {**value, "item_type": "角色"} for key, value in data.items()}
                item_dict.update(data)

            async with session.get(self.LIGHTCONE_API) as resp:
                data = await resp.text()
                data = json.loads(data)
                data = {key: {**value, "item_type": "光锥"} for key, value in data.items()}
                item_dict.update(data)

        new_item_dict = {}
        for k, v in item_dict.items():
            new_item_dict[k] = {
                "rank_type": v["rank"][-1:],
                "name": v["cn"],
                "item_type": v["item_type"],
            }

        return new_item_dict
