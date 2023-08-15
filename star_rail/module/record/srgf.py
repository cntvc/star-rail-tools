from star_rail.utils.version import get_version

SRGF_VERSION = (1, 0)


def get_srgf_version(srgf_version):
    return "v" + get_version(srgf_version)


class SRGFClient:
    def __init__(self) -> None:
        pass
