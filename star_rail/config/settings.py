import os
import typing

from pydantic import BaseModel, ConfigDict, Field

from star_rail import constants
from star_rail.utils.file import load_json, save_json

__all__ = ["settings"]

_default_config_path = os.path.join(constants.CONFIG_PATH, "settings.json")


class BaseSetting(BaseModel):
    config_path: str = Field(exclude=True)

    model_config = ConfigDict(extra="ignore")

    def __init__(self, config_path: str, **data):
        super().__init__(config_path=config_path, **data)
        self.refresh_config()

    def save_config(self):
        save_json(self.config_path, self.model_dump())

    def update_config(self, config_data: dict):
        for k in self.model_fields.keys():
            if k in config_data:
                setattr(self, k, config_data[k])

    def refresh_config(self):
        if not os.path.exists(self.config_path):
            return
        self.update_config(load_json(self.config_path))


class Settings(BaseSetting):
    CHECK_UPDATE: bool = True

    DEFAULT_UID: str = ""

    ENCRYPT_KEY: str = ""

    REVERSE_GACHA_RECORD: bool = True
    """按ID大小倒序显示跃迁记录"""

    SHOW_LUCK_LEVEL: bool = True
    """显示欧非程度"""

    METADATA_LANG: typing.Literal["zh-cn", "en-us"] = "zh-cn"
    """metadata 默认 lang"""

    RECORD_UPDATE_MODE: typing.Literal["incremental", "full"] = "incremental"

    def __init__(self, config_path: str):
        super().__init__(config_path=config_path)


settings = Settings(config_path=_default_config_path)
