import os
from pathlib import Path

from pydantic import BaseModel

from star_rail import constants
from star_rail.i18n import i18n
from star_rail.utils.functional import color_str, load_json, save_json

__all__ = ["settings", "get_config_status_msg"]

_config_path = Path(constants.CONFIG_PATH, "settings.json")


class Settings(BaseModel):
    FLAG_CHECK_UPDATE: bool = True

    FLAG_GENERATE_XLSX: bool = False

    FLAG_UPATED_COMPLETE: bool = False

    # 旧版本文件名，在更新版本后删除该文件
    OLD_EXE_NAME = ""

    DEFAULT_UID = ""

    LANGUAGE = "zh_cn"

    class Config:
        extra = "forbid"

    def __setattr__(self, k, v):
        if k not in self.__fields__:
            return
        from star_rail.utils.log import logger

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
        save_json(_config_path, self.dict())

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


def get_config_status_msg(key):
    assert hasattr(settings, key)
    return "{}: {}".format(
        i18n.config.settings.current_status,
        color_str(i18n.common.open, "green")
        if settings.get(key)
        else color_str(i18n.common.close, "red"),
    )
