from .mapper import MonthInfoItemMapper
from .model import MonthInfoData


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
            source=str(source),
            update_time=update_time,
        )

        month_info_mappers.append(month_info_mapper)

    return month_info_mappers
