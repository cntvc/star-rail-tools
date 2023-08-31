import os
import typing

from pydantic import BaseModel, ConfigDict, Field

from star_rail import constants
from star_rail.utils.functional import load_json, save_json

__all__ = ["settings"]

_config_path = os.path.join(constants.CONFIG_PATH, "settings.json")


class Settings(BaseModel):
    FLAG_AUTO_UPDATE: bool = True
    """自动更新"""

    FLAG_UPDATED_COMPLETE: bool = False

    UPDATE_SOURCE: typing.Literal["Github", "Coding"] = "Github"
    """更新源"""

    OLD_EXE_NAME: str = ""
    """旧版本程序文件名，用于在更新版本后删除该文件"""

    DEFAULT_UID: str = ""

    LANGUAGE: str = ""

    SALT: str = ""
    """加密 salt"""

    GACHA_RECORD_DESC_MOD: typing.Literal["table", "tree"] = "table"
    """抽卡记录详情的显示模式"""

    model_config = ConfigDict(extra="ignore")

    config_path: str = Field(exclude=True)

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


settings = Settings(config_path=_config_path)
