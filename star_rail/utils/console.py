import os


def clear_all():
    os.system("cls")


def clear_line():
    print("\033[K")


def pause():
    os.system("pause")


def color_str(string: str, color: str = "none"):
    """generate color str

    Args:
        string (str): string
        color (str, optional): converted target color. Defaults to "none".
            support color:[red, green, yellow, blue]

    Returns:
        str: colored characters in the command line
    """
    color_list = {
        "red": "\033[1;31;40m",
        "green": "\033[1;32;40m",
        "yellow": "\033[1;33;40m",
        "blue": "\033[1;34;40m",
        "none": "\033[0m",
    }
    color_code = color_list.get(color, None)
    if color_code:
        return "{}{}\033[0m".format(color_code, string)
    else:
        return string
