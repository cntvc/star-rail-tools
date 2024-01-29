from .mapper import GachaRecordItemMapper
from .model import GachaRecordItem


def convert_to_record_item_mapper(
    data: GachaRecordItem | list[GachaRecordItem], batch_id: int
) -> list[GachaRecordItemMapper] | GachaRecordItemMapper:
    if isinstance(data, list):
        return [convert_to_record_item_mapper(item, batch_id) for item in data]
    elif isinstance(data, GachaRecordItem):
        return GachaRecordItemMapper(
            gacha_id=data.gacha_id,
            gacha_type=data.gacha_type,
            item_id=data.item_id,
            time=data.time,
            id=data.id,
            count=data.count,
            name=data.name,
            rank_type=data.rank_type,
            uid=data.uid,
            lang=data.lang,
            item_type=data.item_type,
            batch_id=batch_id,
        )
    else:
        assert False, (
            "Param type error. Expected type 'list' or 'GachaRecordItemMapper',"
            f" got [{type(data)}]."
        )


def convert_to_record_item(
    data: GachaRecordItemMapper | list[GachaRecordItemMapper],
) -> list[GachaRecordItem] | GachaRecordItem:
    if isinstance(data, list):
        return [convert_to_record_item(item) for item in data]
    elif isinstance(data, GachaRecordItemMapper):
        return GachaRecordItem(
            gacha_id=data.gacha_id,
            gacha_type=data.gacha_type,
            item_id=data.item_id,
            time=data.time,
            id=data.id,
            count=data.count,
            name=data.name,
            rank_type=data.rank_type,
            uid=data.uid,
            lang=data.lang,
            item_type=data.item_type,
        )
    else:
        assert False, (
            "Param type error. Expected type 'list' or 'GachaRecordItemMapper',"
            f" got [{ type(data)}]."
        )
