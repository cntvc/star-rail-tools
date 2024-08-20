import json
import os.path

import aiohttp

from star_rail import constants
from star_rail import exceptions as error
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
            self._load_cache()

    def get(self, lang: str, item_id: str, key: MetadataAttr, /, default="-") -> str:
        if item_id not in self.data[lang]:
            return default
        return self.data[lang][item_id][key]

    async def update(self):
        try:
            self.data = await self._fetch()
            self._save_cache()
        except Exception as err:
            raise error.MetadataError("Failed to update Hakush metadata.") from err

    async def _fetch(self):
        logger.debug("Fetching Hakush metadata")
        row_item = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.CHARACTER_API) as resp:
                data = await resp.text()
                data = json.loads(data)
                data = {
                    key: {**value, "item_type_cn": "角色", "item_type_en": "Character"}
                    for key, value in data.items()
                }
                row_item.update(data)

            async with session.get(self.LIGHTCONE_API) as resp:
                data = await resp.text()
                data = json.loads(data)
                data = {
                    key: {**value, "item_type_cn": "光锥", "item_type_en": "Light Cone"}
                    for key, value in data.items()
                }
                row_item.update(data)

        new_item = {
            "version": self.version,
            "zh-cn": {},
            "en-us": {},
        }

        for k, v in row_item.items():
            new_item["zh-cn"][k] = {
                "rank_type": v["rank"][-1:],
                "name": v["cn"],
                "item_type": v["item_type_cn"],
            }
            new_item["en-us"][k] = {
                "rank_type": v["rank"][-1:],
                "name": v["en"],
                "item_type": v["item_type_en"],
            }

        return new_item

    def _load_cache(self):
        self.data = load_json(self.path)

    def _save_cache(self) -> None:
        save_json(self.path, self.data)
