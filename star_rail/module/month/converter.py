import json

from .mapper import MonthInfoItemMapper
from .model import MonthInfoData, MonthInfoItem, MonthInfoSource


def convert_to_month_info_mapper(
    data: list[MonthInfoData], update_time: str
) -> list[MonthInfoItemMapper]:
    month_info_mappers = []

    for item in data:
        source = [s.model_dump() for s in item.month_data.group_by]
        month_info_mapper = MonthInfoItemMapper(
            uid=item.uid,
            month=item.data_month,
            hcoin=item.month_data.current_hcoin,
            rails_pass=item.month_data.current_rails_pass,
            source=json.dumps(source, ensure_ascii=False),
            update_time=update_time,
        )

        month_info_mappers.append(month_info_mapper)

    return month_info_mappers


def convert_to_month_info_item(data: list[MonthInfoItemMapper]) -> list[MonthInfoItem]:
    result = []
    for item_mapper in data:
        month_info_item = MonthInfoItem(
            uid=item_mapper.uid,
            month=item_mapper.month,
            hcoin=item_mapper.hcoin,
            rails_pass=item_mapper.rails_pass,
            source=[
                MonthInfoSource.model_validate(s_item) for s_item in json.loads(item_mapper.source)
            ],
            update_time=item_mapper.update_time,
        )
        result.append(month_info_item)
    return result
