import os

from pydantic import BaseModel, ConfigDict, Field

from star_rail import constants
from star_rail.utils.functional import load_json, save_json

__all__ = ["settings"]

_default_config_path = os.path.join(constants.CONFIG_PATH, "settings.json")


class BaseSetting(BaseModel):
    config_path: str = Field(exclude=True)

    model_config = ConfigDict(extra="ignore")

    def __init__(self, config_path: str, **data):
        super().__init__(config_path=config_path, **data)
        self.refresh_config(config_path)

    def save_config(self):
        save_json(self.config_path, self.model_dump())

    def update_config(self, config_data: dict):
        for k in self.model_fields.keys():
            if k in config_data:
                setattr(self, k, config_data[k])

    def refresh_config(self, path: str):
        if not os.path.exists(path):
            return
        self.update_config(load_json(path))


class Settings(BaseSetting):
    CHECK_UPDATE: bool = True

    DEFAULT_UID: str = ""

    ENCRYPT_KEY: str = ""
    """加密 key"""

    LANGUAGE: str = ""

    DISPLAY_STARTER_WARP: bool = True
    """显示新手池"""


settings = Settings(config_path=_default_config_path)
