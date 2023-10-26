from star_rail import exceptions as error

from .mapper import GachaRecordInfoMapper, RecordItemMapper
from .model import GachaItem, GachaRecordInfo


def record_info_to_mapper(data: GachaRecordInfo):
    return GachaRecordInfoMapper(**data.model_dump())


def mapper_to_record_info(data: GachaRecordInfoMapper):
    return GachaRecordInfo(**data.model_dump())


def record_item_to_mapper(data: list[GachaItem]):
    return [RecordItemMapper(**item.model_dump()) for item in data]


def mapper_to_record_item(data: RecordItemMapper | list[RecordItemMapper]):
    if isinstance(data, list):
        return [GachaItem(**item.model_dump()) for item in data]
    elif isinstance(data, RecordItemMapper):
        return GachaItem(**data.model_dump())
    else:
        raise error.HsrException("Parameter type error, type: {}", type(data))
