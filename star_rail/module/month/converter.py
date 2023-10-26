from star_rail import exceptions as error
from star_rail.module import Account

from .mapper import MonthInfoMapper, MonthInfoRewardSourceMapper
from .model import MonthInfo, MonthInfoData


def month_info_data_to_month_info_mapper(user: Account, month_info: MonthInfoData):
    """将 MonthInfoData 转换为 MonthInfoMapper"""
    return MonthInfoMapper(
        uid=user.uid,
        month=month_info.data_month,
        hcoin=month_info.month_data.current_hcoin,
        rails_pass=month_info.month_data.current_rails_pass,
    )


def month_info_data_to_reward_source_mapper(user: Account, month_info: MonthInfoData):
    """将 MonthInfoData 转为 MonthInfoRewardSourceMapper"""
    return [
        MonthInfoRewardSourceMapper(
            uid=user.uid,
            month=month_info.data_month,
            action=item.action,
            num=item.num,
            percent=item.percent,
            action_name=item.action_name,
        )
        for item in month_info.month_data.group_by
    ]


def mapper_to_month_info(data: MonthInfoMapper | list[MonthInfoMapper]):
    if isinstance(data, list):
        return [MonthInfo(**item.model_dump()) for item in data]
    elif isinstance(data, MonthInfoMapper):
        return MonthInfo(**data.model_dump())
    else:
        raise error.HsrException("Invalid param: {}", type(data))
