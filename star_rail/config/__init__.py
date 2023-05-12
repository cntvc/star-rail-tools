"""
Configuration center.
Use https://www.dynaconf.com/
""" ""
import os
import sys
from pathlib import Path

from dynaconf import Dynaconf, loaders

from star_rail import constant
from star_rail.utils.functional import color_str, load_json, save_json
from star_rail.utils.log import logger

# Load default settings.
_settings_files = [Path(__file__).parent / "default_settings.toml"]

# Load user config, will cover default settings
_user_config_path = Path(constant.APP_CONFIG_PATH, "settings.toml")

# custom configuration. It will be cover default settings
_external_files = [_user_config_path]


settings = Dynaconf(
    core_loaders=["TOML"],
    # Loaded at the first
    preload=[],
    # Loaded second (the main file)
    settings_files=_settings_files,
    # Loaded at the end
    includes=_external_files,
    # If False, can't use `settings.foo`, but can only use `settings.FOO`
    lowercase_read=False,
    # Always reloaded from source without the need to reload the application
    # eg: fresh_vars=["password"]
    fresh_vars=[],
)


def reload_config(key):
    """
    this setting is being freshly reloaded from source
    """
    return settings.get_fresh(key)


def update_and_save(key: str, value, path=_user_config_path):
    """
    update and save user setting to file
    """
    logger.debug("变更设置 {} -> {}", key, value)
    settings.update({key: value})
    save_config(path)


def save_config(path=_user_config_path, environment=None):
    """
    save user setting
    """
    if not path.parent.exists():
        os.makedirs(path.parent)
    if not path.exists():
        path.touch()
    data = settings.as_dict(env=environment)
    loaders.write(path.as_posix(), data, env=environment)
    logger.debug("保存设置文件")


def config_status(key):
    return "当前状态: {}".format(
        color_str("打开", "green") if settings.get(key) else color_str("关闭", "red")
    )


_profile_path = Path(constant.APP_CONFIG_PATH, "profile.json")


class Profile:
    game_path_os: str
    game_path_cn: str
    default_uid: str
    is_updated: bool
    exe_path: str

    def __init__(self, profile_path):
        if not os.path.exists(profile_path):
            self._init_default_value()
            return
        data = load_json(_profile_path)
        self.game_path_os = data.get("game_path_os", "")
        self.game_path_cn = data.get("game_path_cn", "")
        self.default_uid = data.get("default_uid", "")
        self.is_updated = data.get("is_updated", False)
        self.exe_path = data.get("exe_path", sys.executable)

    def _init_default_value(self):
        self.game_path_os = ""
        self.game_path_cn = ""
        self.default_uid = ""
        self.is_updated = False
        self.exe_path = sys.executable

    def to_dict(self):
        return {
            "game_path_os": self.game_path_os,
            "game_path_cn": self.game_path_cn,
            "default_uid": self.default_uid,
            "is_updated": self.is_updated,
            "exe_path": self.exe_path,
        }

    def save(self):
        self.exe_path = sys.executable
        save_json(_profile_path, self.to_dict())


app_profile = Profile(_profile_path)
