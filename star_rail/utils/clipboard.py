"""clipboard tools"""
from typing import Optional

import win32api
import win32clipboard
import win32con

from star_rail.utils.log import logger

__all__ = ["get_text_or_html"]


def get_text_or_html() -> Optional[str]:
    """get str from clipboad"""
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

        logger.debug(f"GetClipboardData={data}")
        if isinstance(data, bytes):
            data = data.decode(errors="ignore")
        if not isinstance(data, str):
            return None

        return data
    except win32api.error:
        logger.error("剪切板读取出现错误")
        return None
    finally:
        win32clipboard.CloseClipboard()
