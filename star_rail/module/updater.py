import aiohttp
from loguru import logger
from pydantic import BaseModel
from yarl import URL

from star_rail import __version__ as app_version
from star_rail import exceptions
from star_rail.version import Version

__all__ = ["Updater"]


class Changelog(BaseModel):
    html_url: str
    tag_name: str
    name: str
    prerelease: bool
    body: str


class Updater:
    async def check_update(self):
        logger.debug("Check update")
        # 该接口获取最新的 release，包括预览版
        url = URL("https://api.github.com/repos/cntvc/star-rail-tools/releases?page=1&per_page=1")

        async with aiohttp.ClientSession() as session:
            async with session.request(method="GET", url=url) as response:
                data = await response.json()
        if "message" in data:
            raise exceptions.HsrException("检测更新失败\n" + data["message"])

        latest_version = data[0]["tag_name"]
        if Version(app_version) < Version(latest_version):
            return latest_version
        return None

    async def get_changelog(self, page_size: int):
        logger.debug("Get changelog")
        url = URL(
            f"https://api.github.com/repos/cntvc/star-rail-tools/releases?page=1&per_page={page_size}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.request(method="GET", url=url) as response:
                data = await response.json()
        changelog = []
        for asset in data:
            changelog.append(Changelog(**asset))
        return changelog
