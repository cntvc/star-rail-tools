import typing

from star_rail import exceptions as error

from .mapper import GachaItemMapper, GachaRecordInfoMapper
from .model import GachaItem, GachaRecordInfo


def record_info_to_mapper(data: GachaRecordInfo):
    return GachaRecordInfoMapper(**data.model_dump())


def mapper_to_record_info(data: GachaRecordInfoMapper):
    return GachaRecordInfo(**data.model_dump())


def record_gacha_item_to_mapper(data: typing.List[GachaItem]):
    return [GachaItemMapper(**item.model_dump()) for item in data]


def mapper_to_gacha_item(data: typing.Union[GachaItemMapper, typing.List[GachaItemMapper]]):
    if isinstance(data, typing.List):
        return [GachaItem(**item.model_dump()) for item in data]
    elif isinstance(data, GachaItemMapper):
        return GachaItem(**data.model_dump())
    else:
        raise error.ParamTypeError("参数类型错误, type: {}", type(data))
