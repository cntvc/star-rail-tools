import re
from itertools import zip_longest

__all__ = ["get_version", "compare_versions", "get_version_tuple"]


def get_version(version: tuple[int, int, int, str, int] = None):
    """Return a PEP 440-compliant version number from VERSION."""

    version = get_complete_version(version)

    # Build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = [.devN] - for dev releases

    main = get_main_version(version)

    sub = ""
    if version[3] == "dev":
        sub = ".dev" + str(version[4])

    return main + sub


def get_main_version(version: tuple[int, int, int, str, int] = None):
    """Return main version (X.Y[.Z]) from VERSION."""
    version = get_complete_version(version)
    parts = 2 if version[2] == 0 else 3
    return ".".join(str(x) for x in version[:parts])


def get_complete_version(version: tuple[int, int, int, str, int] = None):
    """
    check for correctness of the tuple provided.
    """
    if version is None:
        from star_rail import VERSION as version
    assert len(version) == 5
    assert version[3] in ("dev", "final")

    return version


def compare_versions(version1: str, version2: str):
    """

    Return:
        -1 : version1 < version2
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


version_component_re = re.compile(r"(\d+|[a-z]+|\.)")


def get_version_tuple(version: str) -> tuple[int, ...]:
    """
    Return a tuple of version numbers (e.g. (1, 2, 3)) from the version string (e.g. '1.2.3').
    """
    numbers = []
    for item in version_component_re.split(version):
        if item and item != ".":
            try:
                components = int(item)
            except ValueError:
                break
            else:
                numbers.append(components)
    return tuple(numbers)
