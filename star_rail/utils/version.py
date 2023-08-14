from itertools import zip_longest
from typing import Tuple

__all__ = ["get_version", "compare_versions", "get_version_tuple"]


def get_version(version: Tuple[int]):
    "(1, 0, 0) -> '1.0.0'"
    return ".".join(str(x) for x in version)


def compare_versions(v1: str, v2: str):
    """比较 v1 和 v2 大小

    Return:
        -1: v1 < v2
        1 : v1 > v2
        0 : v1 = v2
    """
    v1_parts = get_version_tuple(v1)
    v2_parts = get_version_tuple(v2)
    for part1, part2 in zip_longest(v1_parts, v2_parts, fillvalue=0):
        if part1 < part2:
            return -1
        elif part1 > part2:
            return 1
    return 0


def get_version_tuple(version: str):
    """
    Return a tuple of version numbers (e.g. (1, 2, 3)) from the version
    string (e.g. '1.2.3').
    """
    return tuple(map(int, version.split(".")))
