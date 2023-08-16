import typing

from star_rail.exceptions import ParamTypeError
from star_rail.i18n import i18n
from star_rail.module.mihoyo.account import Account

from .mapper import MonthInfoMapper, MonthInfoRewardSourceMapper
from .model import ApiMonthInfo, MonthInfo

__all__ = ["api_info_to_mapper", "reward_source_to_mapper"]


def api_info_to_mapper(user: Account, month_info: ApiMonthInfo):
    """将 ApiMonthInfo 转换为 MonthInfoMapper"""
    return MonthInfoMapper(
        uid=user.uid,
        month=month_info.data_month,
        hcoin=month_info.month_data.current_hcoin,
        rails_pass=month_info.month_data.current_rails_pass,
    )


def reward_source_to_mapper(user: Account, month_info: ApiMonthInfo):
    """将 MonthInfo 转为 MonthInfoRewardSourceMapper"""
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


def mapper_to_month_info(data: typing.Tuple[MonthInfoMapper, typing.List[MonthInfoMapper]]):
    if isinstance(data, typing.List):
        return [MonthInfo(**item.model_dump()) for item in data]
    elif isinstance(data, MonthInfoMapper):
        return MonthInfo(**data.model_dump())
    else:
        raise ParamTypeError(i18n.error.param_type_error, type(data))
