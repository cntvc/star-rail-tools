"""clipboard tools"""
import html
from typing import Optional

import win32api
import win32clipboard
import win32con

from star_rail.i18n import i18n
from star_rail.utils.functional import desensitize_url
from star_rail.utils.log import logger

__all__ = ["get_text_or_html"]


def get_text_or_html() -> Optional[str]:
    try:
        formats = []
        win32clipboard.OpenClipboard(0)

        # 注册 CF_HTML 格式剪贴板
        # https://learn.microsoft.com/zh-cn/windows/win32/dataxchg/html-clipboard-format
        CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")
        CF_TEXT = win32con.CF_TEXT

        clipboard_format = win32clipboard.EnumClipboardFormats(0)
        while clipboard_format != 0:
            formats.append(clipboard_format)
            clipboard_format = win32clipboard.EnumClipboardFormats(clipboard_format)
        logger.debug(f"CF_HTML={CF_HTML} EnumClipboardFormats={formats}")

        if CF_HTML in formats:
            data = win32clipboard.GetClipboardData(CF_HTML)
        elif CF_TEXT in formats:
            data = win32clipboard.GetClipboardData(CF_TEXT)
        else:
            return None

        if isinstance(data, bytes):
            data = data.decode(errors="ignore")
        if not isinstance(data, str):
            return None
        data = html.unescape(data)
        logger.debug("读取剪切板数据：{}".format(desensitize_url(data, "authkey")))
        return data
    except win32api.error:
        logger.error(i18n.utils.clipboard.read_data_error)
        return None
    finally:
        win32clipboard.CloseClipboard()
