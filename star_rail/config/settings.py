import os
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, ConfigDict

from star_rail import constants
from star_rail.utils.functional import load_json, save_json

__all__ = ["settings"]

_config_path = Path(constants.CONFIG_PATH, "settings.json")


class Settings(BaseModel):
    FLAG_CHECK_UPDATE: bool = True

    FLAG_UPDATE_SOURCE: str = "Github"
    """更新源 : ["Github", "Coding"] """

    FLAG_UPATED_COMPLETE: bool = False

    OLD_EXE_NAME: str = ""
    """旧版本程序文件名，用于在更新版本后删除该文件"""

    DEFAULT_UID: str = ""

    LANGUAGE: str = ""

    model_config = ConfigDict(extra="ignore")

    def __setattr__(self, k, v):
        if k not in self.__fields__:
            return
        logger.debug("update config: {} -> {}", k, v)
        return super().__setattr__(k, v)

    def __init__(self, **data):
        super().__init__(**data)
        self.load()

    def load(self):
        if not os.path.exists(_config_path):
            return
        local_config = load_json(_config_path)
        self.update(local_config)

    def save(self):
        save_json(_config_path, self.model_dump())

    def update(self, config_data: dict):
        for k, v in config_data.items():
            setattr(self, k, v)

    def update_and_save(self, config_data: dict):
        self.update(config_data)
        self.save()

    def get(self, key: str):
        return getattr(self, key)

    def set_and_save(self, k, v):
        """set and save"""
        self.set(k, v)
        self.save()

    def set(self, k, v):
        setattr(self, k, v)


settings = Settings()
