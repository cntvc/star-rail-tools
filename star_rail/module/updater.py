import abc
import enum
import os
import re
import shutil
import subprocess
import sys
import time
import typing
from pathlib import Path

import requests
from loguru import logger
from pydantic import BaseModel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from star_rail import __version__ as version
from star_rail import constants
from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.utils.console import color_str, pause
from star_rail.utils.functional import input_yes_or_no
from star_rail.utils.version import compare_versions

__all__ = ["UpdateManager", "UpdateSource"]

_lang = i18n.updater


class _UpdateContext(BaseModel):
    version: str = ""
    """版本号"""
    name: str = ""
    """文件名"""
    download_url: str = ""
    """下载链接"""


class BaseUpdater(abc.ABC):
    url: str
    """更新检测链接"""
    name: str
    """更新源名"""

    @abc.abstractmethod
    def check_update(self) -> typing.Tuple[bool, typing.Optional[_UpdateContext]]:
        """
        Returns:
            typing.Tuple[bool, typing.Optional[_UpdateContext]]: [检测更新的操作结果，新版本内容]
        """

    def upgrade(self, update_context: _UpdateContext):
        temp_file = Path(constants.TEMP_PATH, update_context.name)
        temp_file.touch()
        logger.debug("temp file: {}", temp_file)
        try:
            self._download(temp_file, update_context)
        except requests.RequestException as e:
            logger.warning(_lang.download_failed)
            logger.debug(e)
            os.remove(temp_file)
            return
        except KeyboardInterrupt:
            logger.warning(_lang.download_canceled)
            os.remove(temp_file)
            # 显示取消下载的提示信息 1s
            time.sleep(1)
            return

        shutil.move(temp_file, update_context.name)
        logger.info(_lang.download_success, update_context.name)
        time.sleep(1)
        # 保存当前版本文件名
        settings.OLD_EXE_NAME = os.path.basename(sys.argv[0])
        settings.FLAG_UPDATED_COMPLETE = True
        settings.save_config()
        subprocess.Popen(update_context.name, creationflags=subprocess.CREATE_NEW_CONSOLE)
        sys.exit()

    def _download(self, file_path: str, update_context: _UpdateContext):
        """下载新版本文件"""
        default_chunk_size = 1024

        with requests.get(
            update_context.download_url, stream=True, timeout=constants.REQUEST_TIMEOUT
        ) as r:
            file_size = int(r.headers.get("content-length", 0))
            progress = Progress(
                TextColumn("[bold cadet_blue]{task.fields[filename]}", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
            )
            task = progress.add_task(
                description="StarRailTools...", total=file_size, filename=update_context.name
            )

            with open(file_path, "wb") as f, progress:
                for chunk in r.iter_content(chunk_size=default_chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))


class GithubUpdater(BaseUpdater):
    """Github 更新源"""

    def __init__(self) -> None:
        self.url = "https://api.github.com/repos/cntvc/star-rail-tools/releases/latest"
        self.name = "Github"

    def check_update(self):
        """
        Returns:
            Tuple[bool, UpdateContext]:
                True: 需要更新
                False: 更新检测失败或无需更新
        """
        logger.info(_lang.check_update)
        try:
            data = requests.get(self.url, timeout=constants.REQUEST_TIMEOUT).json()
        except requests.RequestException as e:
            logger.warning(_lang.check_update_net_error)
            logger.debug(e)
            return False, None
        if "tag_name" not in data:
            logger.warning(_lang.check_update_has_no_ctx)
            return False, None

        latest_version = data["tag_name"]
        if compare_versions(latest_version, version) != 1:
            logger.success(_lang.is_latest_version)
            return False, None

        download_url = data["assets"][0]["browser_download_url"]
        name = data["assets"][0]["name"]
        return True, _UpdateContext(name=name, version=latest_version, download_url=download_url)


class CodingUpdater(BaseUpdater):
    """
    国内更新源
    https://cntvc.coding.net/public-artifacts/star-rail-tools/releases/packages
    """

    def __init__(self) -> None:
        self.url = "https://cntvc.coding.net/api/team/cntvc/anonymity/artifacts/?pageSize=10"
        self.name = "Coding"

    def check_update(self) -> typing.Tuple[bool, typing.Optional[_UpdateContext]]:
        logger.info(_lang.check_update)
        try:
            data = requests.get(self.url, timeout=constants.REQUEST_TIMEOUT).json()
        except requests.RequestException as e:
            logger.warning(_lang.check_update_net_error)
            logger.debug(e)
            return False, None

        artifact = data["data"]["list"][0]
        latest_version = artifact["latestVersionName"]
        if compare_versions(latest_version, version) != 1:
            logger.success(_lang.is_latest_version)
            return False, None

        name: str = artifact["name"]
        latest_version_name = "{}_{}.exe".format(name.split(".")[0], latest_version)
        registry_url = artifact["registryUrl"]
        project_name = artifact["projectName"]
        repo_name = artifact["repoName"]
        download_url = "{}/{}/{}/{}?version={}".format(
            registry_url, project_name, repo_name, name, latest_version
        )
        return True, _UpdateContext(
            name=latest_version_name, version=latest_version, download_url=download_url
        )


class UpdateSource(enum.Enum):
    GITHUB = "Github", GithubUpdater()
    CODING = "Coding", CodingUpdater()

    @property
    def name(self) -> str:
        return self.value[0]

    @property
    def updater(self) -> BaseUpdater:
        return self.value[1]


class UpdateManager:
    def __init__(self) -> None:
        self._update_source: typing.Dict[str, BaseUpdater] = {
            "Github": UpdateSource.GITHUB.updater,
            "Coding": UpdateSource.CODING.updater,
        }
        self._updater = self._update_source[settings.UPDATE_SOURCE]

    @staticmethod
    def select_updater_source(source: UpdateSource):
        settings.UPDATE_SOURCE = source.name
        settings.save_config()
        logger.success(_lang.select_update_source, source.name)

    def upgrade(self):
        """根据软件保存的状态，显示更新日志或检测更新"""
        if settings.FLAG_UPDATED_COMPLETE is True:
            logger.success(_lang.upgrade_success, version)
            old_exe_path = os.path.join(os.path.dirname(sys.argv[0]), settings.OLD_EXE_NAME)
            try:
                os.remove(old_exe_path)
            except IOError as e:
                logger.warning(_lang.delete_file_failed, old_exe_path)
                logger.debug(e)
            settings.OLD_EXE_NAME = ""
            settings.FLAG_UPDATED_COMPLETE = False
            settings.save_config()
            changelog = self.get_changelog()
            if changelog:
                print(_lang.changelog)
                print("=" * constants.MENU_BANNER_LENGTH)
                print(changelog)
                print("=" * constants.MENU_BANNER_LENGTH)
            pause()
            return

        check_update_status, update_context = self._updater.check_update()
        if not check_update_status:
            time.sleep(1)
            return
        user_input = input_yes_or_no(
            prompt=_lang.update_option.format(update_context.version),
            default="y",
            error_msg=_lang.invalid_input,
        )
        if user_input == "n":
            return
        self._updater.upgrade(update_context)

    def parse_changelog(self, release_data):
        """移除更新日志中的链接等信息"""
        changelog_raw = release_data["body"]
        link_pattern = r"\[[^\]]+\]\([^)]+\)|https://[^ \n]+|\*\*Full Changelog[^ \n]+"
        change_log = re.sub(link_pattern, "", changelog_raw)
        return change_log.strip()

    def get_changelog(self):
        release_api = f"https://api.github.com/repos/cntvc/star-rail-tools/releases/tags/{version}"

        try:
            data = requests.get(release_api, timeout=constants.REQUEST_TIMEOUT).json()
        except requests.exceptions as e:
            logger.info(_lang.get_changelog_failed)
            logger.debug(e)
            return ""

        return self.parse_changelog(data)

    @staticmethod
    def get_update_source_status():
        """获取当前更新源名称"""
        return "{}: {}".format(
            _lang.update_source_status, color_str(settings.UPDATE_SOURCE, "green")
        )

    @staticmethod
    def open_auto_update():
        settings.FLAG_AUTO_UPDATE = True
        settings.save_config()
        logger.success(i18n.config.settings.open_success)

    @staticmethod
    def close_auto_update():
        settings.FLAG_AUTO_UPDATE = False
        settings.save_config()
        logger.success(i18n.config.settings.close_success)

    @staticmethod
    def get_auto_update_status():
        return "{}: {}".format(
            i18n.config.settings.current_status,
            color_str(i18n.common.open, "green")
            if settings.FLAG_AUTO_UPDATE
            else color_str(i18n.common.close, "red"),
        )
