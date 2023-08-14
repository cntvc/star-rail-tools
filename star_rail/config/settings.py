import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from star_rail import constants
from star_rail.utils.functional import color_str, load_json, save_json
from star_rail.utils.log import logger

__all__ = ["settings", "get_config_status_desc"]

_config_path = Path(constants.CONFIG_PATH, "settings.json")


class Settings(BaseModel):
    FLAG_CHECK_UPDATE: bool = True

    FLAG_UPDATE_SOURCE: str = "Github"
    """更新源 : ["Github", "Coding"] """

    FLAG_GENERATE_XLSX: bool = False

    FLAG_GENERATE_SRGF: bool = False
    """自动生成 SRGF 格式文件"""

    FLAG_UPATED_COMPLETE: bool = False

    OLD_EXE_NAME: str = ""
    """旧版本程序文件名，用于在更新版本后删除该文件"""

    DEFAULT_UID: str = ""

    LANGUAGE: str = ""

    model_config = ConfigDict(extra="ignore")

    def __setattr__(self, k, v):
        if k not in self.__fields__:
            return
        logger.debug("更新设置: {} -> {}", k, v)
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


def get_config_status_desc(key):
    assert hasattr(settings, key)
    from star_rail.i18n import i18n

    return "{}: {}".format(
        i18n.config.settings.current_status,
        color_str(i18n.common.open, "green")
        if settings.get(key)
        else color_str(i18n.common.close, "red"),
    )
