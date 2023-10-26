import json
import os
from pathlib import Path


def save_json(full_path: str | Path, data):
    path = Path(full_path)
    os.makedirs(path.parent, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, sort_keys=False, indent=4)


def load_json(full_path: str | Path) -> dict:
    with open(full_path, "r", encoding="UTF-8") as file:
        data = json.load(file)
    return data


def input_int(left: int, right: int, error_msg: str):
    """
    input an integer, and the range of integers is in the interval [left, right]
    """
    while True:
        index = input().strip()
        if not index.isdigit():
            print(color_str(error_msg, "yellow"))
            continue

        index = int(index)
        if index > right or index < left:
            print(color_str(error_msg, "yellow"))
            continue

        return index


def input_yes_or_no(prompt: str = "", default="y", error_msg: str = ""):
    """输入 y/N 并校验"""
    while True:
        user_input = input(prompt).strip().lower()
        if not user_input:
            return default
        elif user_input == "y" or user_input == "n":
            return user_input
        else:
            print(error_msg)


def clear_all():
    os.system("cls")


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


def desensitize_url(url: str, param_name: str, desensitized_value: str = "******"):
    """脱敏 URL 中指定参数的值"""
    assert param_name
    start_index = url.find(f"{param_name}=")
    if start_index != -1:
        # 截取参数的值
        start_index += len(f"{param_name}=")
        end_index = url.find("&", start_index)
        if end_index == -1:
            end_index = len(url)
        desensitized_url = url[:start_index] + desensitized_value + url[end_index:]
        return desensitized_url
    return url
