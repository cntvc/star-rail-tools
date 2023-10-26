import os
import typing

from pydantic import BaseModel, ConfigDict, Field

from star_rail import constants
from star_rail.utils.functional import load_json, save_json

__all__ = ["settings"]

_default_config_path = os.path.join(constants.CONFIG_PATH, "settings.json")


class Settings(BaseModel):
    FLAG_AUTO_UPDATE: bool = True
    """自动更新"""

    FLAG_UPDATED_COMPLETE: bool = False

    UPDATE_SOURCE: typing.Literal["Github", "Coding"] = "Github"
    """更新源"""

    OLD_EXE_NAME: str = ""
    """旧版本程序文件名，用于在更新版本后删除该文件"""

    DEFAULT_UID: str = ""

    SALT: str = ""
    """加密 salt"""

    LANGUAGE: str = ""

    DISPLAY_STARTER_WARP: bool = False
    """显示新手池"""

    GACHA_RECORD_DESC_MOD: typing.Literal["table", "tree"] = "tree"
    """抽卡记录详情的显示模式"""

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

    def model_dump(self, mode: typing.Literal["log", "default"] = "default", *args, **kwargs):
        if mode == "log":
            """部分参数值会隐藏"""
            config_dict = super().model_dump()
            config_dict["SALT"] = "***"
            return config_dict
        elif mode == "default":
            return super().model_dump()


settings = Settings(config_path=_default_config_path)
