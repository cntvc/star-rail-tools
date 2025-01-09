import os
import typing

from pydantic import BaseModel, ConfigDict, Field

from star_rail import constants
from star_rail.utils import load_json, save_json

__all__ = ["config"]

_DEFAULT_CONFIG_PATH = os.path.join(constants.APPDATA_PATH, "config.json")


class BaseConfig(BaseModel):
    config_path: str = Field(exclude=True)

    model_config = ConfigDict(extra="ignore")

    def __init__(self, config_path: str, **data):
        super().__init__(config_path=config_path, **data)
        self.load()

    def save(self):
        save_json(self.config_path, self.model_dump())

    def update(self, config_data: dict):
        for k in self.model_fields.keys():
            if k in config_data:
                setattr(self, k, config_data[k])

    def load(self):
        if not os.path.exists(self.config_path):
            return
        self.update(load_json(self.config_path))


class Config(BaseConfig):
    CHECK_UPDATE: bool = True

    DEFAULT_UID: str = ""

    USE_METADATA: bool = True

    METADATA_LANGUAGE: typing.Literal["zh-cn", "en-us"] = "zh-cn"


config = Config(config_path=_DEFAULT_CONFIG_PATH)
