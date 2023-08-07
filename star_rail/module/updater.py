import abc
import enum
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, Tuple

import requests
from pydantic import BaseModel
from tqdm import tqdm

from star_rail import __version__ as version
from star_rail import constants
from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.utils.functional import color_str, input_yes_or_no, pause
from star_rail.utils.log import logger
from star_rail.utils.version import compare_versions

__all__ = ["upgrade", "select_updater_source"]

_lang = i18n.updater


class UpdateContext(BaseModel):
    version: str = ""
    name: str = ""  # 文件名
    download_url: str = ""


class BaseUpdater(abc.ABC):
    def __init__(self, url="", name="") -> None:
        self._url = url
        self._name = name

    @property
    def name(self):
        return self._name

    @abc.abstractmethod
    def check_update(self) -> Tuple[bool, UpdateContext]:
        """
        Returns:
            Tuple[bool, UpdateContext]: [检测更新的操作结果，新版本内容]
        """

    def upgrade(self, update_context: UpdateContext):
        try:
            temp_file = self._download(update_context)
        except requests.RequestException as e:
            logger.warning(_lang.download_failed)
            logger.debug(e)
            return

        shutil.move(temp_file, update_context.name)
        logger.info(_lang.download_success, update_context.name)
        time.sleep(1)
        # 保存当前版本文件名
        settings.OLD_EXE_NAME = os.path.basename(sys.argv[0])
        settings.FLAG_UPATED_COMPLETE = True
        settings.save()
        subprocess.Popen(update_context.name, creationflags=subprocess.CREATE_NEW_CONSOLE)
        sys.exit()

    def _download(self, update_context: UpdateContext):
        """下载新版本文件到当前目录，名称 StarRailTools_{version}.exe"""
        DEFAULT_CHUNK_SIZE = 1024
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file_path = temp_file.name
        with open(file_path, "wb") as f:
            with requests.get(
                update_context.download_url, stream=True, timeout=constants.REQUEST_TIMEOUT
            ) as r:
                file_size = int(r.headers.get("content-length", 0))
                with tqdm(total=file_size, unit="B", unit_scale=True, desc="StarRailTools") as pbar:
                    for chunk in r.iter_content(chunk_size=DEFAULT_CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            pbar.update(DEFAULT_CHUNK_SIZE)
        return file_path


class GithubUpdater(BaseUpdater):
    """Github 更新源"""

    def __init__(self) -> None:
        self._url = "https://api.github.com/repos/cntvc/star-rail-tools/releases/latest"
        self._name = "Github"

    def check_update(self):
        """
        Returns:
            Tuple[bool, UpdateContext]:
                True: 需要更新
                False: 更新检测失败或无需更新
        """
        logger.info(_lang.check_update)
        try:
            response = requests.get(self._url, timeout=constants.REQUEST_TIMEOUT)
            data = json.loads(response.content.decode())
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
        return True, UpdateContext(name=name, version=latest_version, download_url=download_url)


class CodingUpdater(BaseUpdater):
    """
    国内更新源
    https://cntvc.coding.net/public-artifacts/star-rail-tools/releases/packages
    """

    def __init__(self) -> None:
        self._url = "https://cntvc.coding.net/api/team/cntvc/anonymity/artifacts/?pageSize=10"
        self._name = "Coding"

    def check_update(self) -> Tuple[bool, UpdateContext]:
        logger.info(_lang.check_update)
        try:
            response = requests.get(self._url, timeout=constants.REQUEST_TIMEOUT)
            data = json.loads(response.content.decode())
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
        return True, UpdateContext(
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


_update_source: Dict[str, BaseUpdater] = {
    "Github": UpdateSource.GITHUB.updater,
    "Coding": UpdateSource.CODING.updater,
}

_updater = _update_source[settings.FLAG_UPDATE_SOURCE]


def select_updater_source(source: UpdateSource):
    global _updater
    _updater = _update_source[source.name]
    settings.FLAG_UPDATE_SOURCE = source.name
    settings.save()
    logger.info(_lang.select_update_source, source.name)


def upgrade():
    """根据软件保存的状态，显示更新日志或检测更新"""
    if settings.FLAG_UPATED_COMPLETE is True:
        logger.success(_lang.upgrade_success, version)
        old_exe_path = os.path.join(os.path.dirname(sys.argv[0]), settings.OLD_EXE_NAME)
        try:
            os.remove(old_exe_path)
        except IOError as e:
            logger.warning(_lang.delete_file_failed, old_exe_path)
            logger.debug(e)
        settings.OLD_EXE_NAME = ""
        settings.FLAG_UPATED_COMPLETE = False
        settings.save()
        changelog = get_changelog()
        if changelog:
            print(_lang.changelog)
            print("=" * constants.MENU_BANNER_LENGTH)
            print(changelog)
            print("=" * constants.MENU_BANNER_LENGTH)
        pause()
        return

    check_update_status, update_context = _updater.check_update()
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
    _updater.upgrade(update_context)


def parse_changelog(release_data):
    """移除更新日志中的链接等信息"""
    changelog_raw = release_data["body"]
    link_pattern = r"\[[^\]]+\]\([^)]+\)|https://[^ \n]+|\*\*Full Changelog[^ \n]+"
    change_log = re.sub(link_pattern, "", changelog_raw)
    return change_log.strip()


def get_changelog():
    RELEASE_API = f"https://api.github.com/repos/cntvc/star-rail-tools/releases/tags/{version}"

    try:
        response = requests.get(RELEASE_API, timeout=constants.REQUEST_TIMEOUT).content.decode(
            "utf-8"
        )
    except requests.exceptions as e:
        logger.info(_lang.get_changelog_failed)
        logger.debug(e)
        return ""
    data = json.loads(response)
    return parse_changelog(data)


def get_update_source_status():
    """获取当前更新源状态"""
    global _updater
    return "{}: {}".format(_lang.update_source_status, color_str(_updater.name, "green"))
