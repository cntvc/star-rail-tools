"""update"""
import json
import os
import shutil
import tempfile
import traceback

import requests
import tqdm
from requests import RequestException, Timeout

from star_rail import __version__ as version
from star_rail import constant, get_exe_name
from star_rail.utils.functional import color_str
from star_rail.utils.log import logger

GITHUB_RELEASE_URL = "https://github.com/cntvc/star-rail-wish-tools/releases/latest"
DEFAULT_CHUNK_SIZE = 1024


def input_yes_or_no(prompt: str = "", default="y"):
    """输入 y/N 并校验"""
    while True:
        user_input = input(prompt).strip().lower()
        if not user_input:
            return default
        elif user_input == "y" or user_input == "n":
            return user_input
        else:
            print(color_str("请输入有效的选项，只能输入 'y' 或 'N'。", "red"))


def download(url: str, file_path: str = ""):
    if not file_path:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file_path = temp_file.name
    print(file_path)
    with open(file_path, "wb") as f:
        with requests.get(url, stream=True, timeout=constant.TIMEOUT) as r:
            file_size = int(r.headers.get("content-length", 0))
            with tqdm(total=file_size, unit="B", unit_scale=True, color="green") as pbar:
                for chunk in r.iter_content(chunk_size=DEFAULT_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        pbar.update(DEFAULT_CHUNK_SIZE)
    return file_path


def update():
    # 更新失败，打印官网下载链接，然后进入主菜单
    # 替换成功，新建进程，关闭旧程序，打印更新成功选项并跳过更新检测。
    # 打印更新日志

    print("正在检测软件更新...")
    try:
        GITHUB_RELEASE_API = "https://api.github.com/repos/cntvc/star-rail-tools/releases/latest"
        response = requests.get(GITHUB_RELEASE_API, timeout=constant.TIMEOUT).content.decode(
            "utf-8"
        )
        data = json.loads(response)
    except (Timeout, RequestException):
        print(color_str("检测更新失败, 请检查网络连接状态", "red"))
        logger.debug(traceback.format_exc())
        return False
    if "tag_name" not in data:
        logger.error("检测更新失败，未获取到版本信息")
        return False

    tag_name = data["tag_name"]
    if tag_name == version:
        logger.success("当前已是最新版本\n")
        return True

    logger.warning("检测到新版本 v{} -> v{}", version, tag_name)
    user_input = input_yes_or_no("请输入（y/N）以选择是否进行更新（默认 y）")
    if user_input == "n":
        return True

    origin_url = data["assets"][0]["browser_download_url"]
    new_version_exe_name = data["assets"][0]["name"]
    try:
        temp_file = download(origin_url)
    except (Timeout, RequestException):
        print(color_str("下载新版本文件失败, 请检查网络连接状态", "red"))
        logger.debug(traceback.format_exc())
        return False

    new_version_exe_path = os.path.join(os.getcwd(), new_version_exe_name)
    shutil.move(temp_file, new_version_exe_path)
    os.unlink(temp_file)
    try:
        os.unlink(os.path.join(os.getcwd(), get_exe_name()))
    except Exception:
        print(color_str("旧版本文件删除失败", "red"))
        logger.debug(traceback.format_exc())
        return False
    print("软件更新成功，请重启应用程序")
    return True
