"""
copy form :https://github.com/kraanzu/dooit/blob/main/dooit/utils/default_config.py
"""

from rich.text import Text

__all__ = ["Color", "apply_text_color"]


class Color:
    DARK_BLACK = "#252a34"
    BLACK = "#2e3440"
    WHITE = "#e5e9f0"
    GREY = "#d8dee9"
    RED = "#bf616a"
    FROST_GREEN = "#8fbcbb"
    CYAN = "#88c0d0"
    GREEN = "#4ebf71"
    YELLOW = "#ebcb8b"
    BLUE = "#81a1c1"
    MAGENTA = "#b48ead"
    ORANGE = "#d08770"


color_legend = {"B": Color.BLUE, "O": Color.ORANGE, "G": Color.GREEN, "M": Color.MAGENTA}
color_legend = {i + "]": j + "]" for i, j in color_legend.items()}


def apply_text_color(art):
    def change(s: str):
        for i, j in color_legend.items():
            s = s.replace(i, j)

        return s

    art = "\n".join([change(i) for i in art])

    return Text.from_markup(art)
