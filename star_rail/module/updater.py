import aiohttp
import yarl

from star_rail import __version__ as app_version
from star_rail.utils.logger import logger
from star_rail.utils.version import compare_versions

__all__ = ["Updater"]


class Updater:
    async def check_update(self):
        """检测是否需要更新

        Returns:
            tuple[bool, str | None]: 需要更新：True, latest_version
        """
        page = 1
        page_size = 1
        logger.debug("Check update.")
        url = yarl.URL(
            f"https://api.github.com/repos/cntvc/star-rail-tools/releases?page={page}&per_page={page_size}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.request(method="GET", url=url) as response:
                data = await response.json()

        latest_version = data[0]["tag_name"]
        if compare_versions(app_version, latest_version) == -1:
            return True, latest_version
        return False, None
