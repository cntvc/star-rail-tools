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
    LIGHT_CONE_API = "https://api.hakush.in/hsr/data/lightcone.json"
    CHARACTER_API = "https://api.hakush.in/hsr/data/character.json"
    NEW_API = "https://api.hakush.in/hsr/new.json"
    path = os.path.join(constants.TEMP_PATH, "hakush_metadata.json")

    def __init__(self):
        self.data = self._load_cache()

    def get(self, lang: str, item_id: str, key: MetadataAttr, /, default="-") -> str:
        if item_id not in self.data[lang]:
            return default
        return self.data[lang][item_id][key]

    async def update(self):
        try:
            if not await self._need_update():
                return
        except Exception as err:
            raise error.GachaRecordError("检测 Hakush metadata 更新失败") from err

        try:
            self.data = await self._fetch()
            self._save_cache()
        except Exception as err:
            raise error.GachaRecordError("更新 Hakush metadata 失败") from err

    async def _need_update(self) -> bool:
        async with aiohttp.ClientSession() as session:
            data = await self._request(session, self.NEW_API)
            new_version = data["version"]
            if "version" not in self.data or new_version != self.data["version"]:
                logger.debug(f"New version of Hakush: {new_version}")
                return True
            logger.debug(f"Now is latest version of Hakush: {new_version}")
            return False

    async def _fetch(self) -> dict:
        logger.debug("Fetching Hakush metadata")
        raw_data = {}
        async with aiohttp.ClientSession() as session:
            version_data = await self._request(session, self.NEW_API)
            version = version_data["version"]

            character_data = await self._request(session, self.CHARACTER_API)
            character_data = {
                key: {**value, "item_type_cn": "角色", "item_type_en": "Character"}
                for key, value in character_data.items()
            }
            raw_data.update(character_data)

            light_cone_data = await self._request(session, self.LIGHT_CONE_API)
            light_cone_data = {
                key: {**value, "item_type_cn": "光锥", "item_type_en": "Light Cone"}
                for key, value in light_cone_data.items()
            }
            raw_data.update(light_cone_data)

        new_data = {
            "version": version,
            "zh-cn": {},
            "en-us": {},
        }

        for k, v in raw_data.items():
            new_data["zh-cn"][k] = {
                "rank_type": v["rank"][-1:],
                "name": v["cn"],
                "item_type": v["item_type_cn"],
            }
            new_data["en-us"][k] = {
                "rank_type": v["rank"][-1:],
                "name": v["en"],
                "item_type": v["item_type_en"],
            }

        return new_data

    def _load_cache(self):
        if os.path.exists(self.path):
            return load_json(self.path)
        return {}

    def _save_cache(self) -> None:
        save_json(self.path, self.data)

    @staticmethod
    async def _request(session: aiohttp.ClientSession, url) -> dict:
        async with session.get(url) as resp:
            data = await resp.text()
            return json.loads(data)
