import re

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
    version1_tuple = get_version_tuple(version1)
    version2_tuple = get_version_tuple(version2)

    for part1, part2 in zip(version1_tuple[:3], version2_tuple[:3], strict=False):
        if part1 < part2:
            return -1
        elif part1 > part2:
            return 1

    if len(version1_tuple) > 3 and len(version2_tuple) > 3:
        # 均是 dev
        assert version1_tuple[3] == version2_tuple[3] == "dev"
        if version1_tuple[4] < version2_tuple[4]:
            return -1
        elif version1_tuple[4] > version2_tuple[4]:
            return 1
        else:
            return 0
    elif len(version1_tuple) > 3:
        # v1 是 dev
        return -1
    elif len(version2_tuple) > 3:
        # v2 是 dev
        return 1
    else:
        # 都不是 dev
        return 0


version_component_re = re.compile(r"(\d+|[a-z]+|\.)")


def get_version_tuple(version: str) -> tuple[int, ...]:
    """
    Return a tuple of version (e.g. (1, 2, 3, 'dev', 1)) from the version string (e.g. '1.2.3.dev1').
    """
    version_component = []
    for item in version_component_re.split(version):
        if item and item != ".":
            try:
                component = int(item)
            except ValueError:
                if item != "dev":
                    raise ValueError(f"Invalid version component: {item}") from None
                version_component.append(item)
            else:
                version_component.append(component)
    return tuple(version_component)
