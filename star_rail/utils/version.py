from itertools import zip_longest

__all__ = ["get_version", "compare_versions", "get_version_tuple"]


def get_version(version: tuple[int, ...]):
    """(1, 0, 0) -> '1.0.0'"""
    return ".".join(str(x) for x in version)


def compare_versions(version1: str, version2: str):
    """

    Return:
        -1: version1 < version2
        1 : version1 > version2
        0 : version1 = version2
    """
    version1_parts = get_version_tuple(version1)
    version2_parts = get_version_tuple(version2)
    for part1, part2 in zip_longest(version1_parts, version2_parts, fillvalue=0):
        if part1 < part2:
            return -1
        elif part1 > part2:
            return 1
    return 0


def get_version_tuple(version: str) -> tuple[int, ...]:
    """
    Return a tuple of version numbers (e.g. (1, 2, 3)) from the version string (e.g. '1.2.3').
    """
    return tuple(map(int, version.split(".")))
