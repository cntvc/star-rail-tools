from star_rail.utils import functional
from star_rail.utils.log import logger

from .settings import Settings, settings

__all__ = ["ConfigClient"]


class ConfigClient:
    def __init__(self, setting: Settings = settings) -> None:
        self.setting = setting

    def get_config_status(self, key):
        if not hasattr(self.setting, key):
            return
        from star_rail.i18n import i18n

        return "{}: {}".format(
            i18n.config.settings.current_status,
            functional.color_str(i18n.common.open, "green")
            if settings.get(key)
            else functional.color_str(i18n.common.close, "red"),
        )

    def open_setting(self, key: str):
        if not hasattr(self.setting, key):
            return
        self.setting.set_and_save(key, True)
        logger.success("开启成功")

    def close_setting(self, key: str):
        if not hasattr(self.setting, key):
            return
        self.setting.set_and_save(key, False)
        logger.success("关闭成功")
