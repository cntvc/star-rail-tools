import json
import os.path

import aiohttp
from loguru import logger
from pydantic import BaseModel, ConfigDict

from star_rail import constants
from star_rail.config import config
from star_rail.utils import load_json, save_json

from .base import BaseMetadata, MetadataAttr

__all__ = ["HakushMetadata"]


class HakushData(BaseModel):
    version: str = "-"
    zh_cn: dict = {}
    en_us: dict = {}

    model_config = ConfigDict(extra="ignore")


class HakushMetadata(BaseMetadata):
    LIGHT_CONE_API = "https://api.hakush.in/hsr/data/lightcone.json"
    CHARACTER_API = "https://api.hakush.in/hsr/data/character.json"
    NEW_API = "https://api.hakush.in/hsr/new.json"
    path = os.path.join(constants.TEMP_PATH, "hakush_metadata.json")

    def __init__(self):
        self.data = self._load_cache()
        self.version = self.data.version
        self.current_lang_data = (
            self.data.zh_cn if config.METADATA_LANGUAGE == "zh-cn" else self.data.en_us
        )

    def get(self, item_id: str, key: MetadataAttr, /, default="-") -> str:
        if item_id not in self.current_lang_data:
            return default
        return self.current_lang_data[item_id][key]

    async def update(self):
        self.data = await self._fetch()
        self.current_lang_data = (
            self.data.zh_cn if config.METADATA_LANGUAGE == "zh-cn" else self.data.en_us
        )
        self.version = self.data.version
        self._save()
        logger.debug("Hakush metadata updated completed")

    async def check_update(self):
        logger.debug("Checking Hakush new version")
        async with aiohttp.ClientSession() as session:
            data = await self._request(session, self.NEW_API)
            new_version = data["version"]

            if new_version != self.version:
                logger.debug(f"New Hakush version : {new_version}")
                return True

            logger.debug(f"Hakush is latest version : {new_version}")
            return False

    async def _fetch(self):
        logger.debug("Fetching Hakush metadata")
        raw_data = {}
        async with aiohttp.ClientSession() as session:
            version_data = await self._request(session, self.NEW_API)

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

        new_data = HakushData(version=version_data["version"])

        for k, v in raw_data.items():
            new_data.zh_cn[k] = {
                "rank_type": v["rank"][-1:],
                "name": v["cn"],
                "item_type": v["item_type_cn"],
            }
            new_data.en_us[k] = {
                "rank_type": v["rank"][-1:],
                "name": v["en"],
                "item_type": v["item_type_en"],
            }

        return new_data

    def _load_cache(self):
        if os.path.exists(self.path):
            return HakushData.model_validate(load_json(self.path))
        return HakushData()

    def _save(self) -> None:
        save_json(self.path, self.data.model_dump())

    @staticmethod
    async def _request(session: aiohttp.ClientSession, url) -> dict:
        async with session.get(url) as resp:
            data = await resp.text()
            return json.loads(data)
