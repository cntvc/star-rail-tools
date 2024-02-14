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
            bool: 需要更新：True
        """
        logger.debug("Check update.")
        url = yarl.URL("https://api.github.com/repos/cntvc/star-rail-tools/releases/latest")

        async with aiohttp.ClientSession() as session:
            async with session.request(method="GET", url=url) as response:
                data = await response.json()

        latest_version = data["tag_name"]
        return compare_versions(app_version, latest_version) == -1
