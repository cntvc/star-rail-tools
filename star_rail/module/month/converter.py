from star_rail.module.mihoyo.account import Account

from .mapper import MonthInfoMapper, MonthInfoRewardSourceMapper
from .model import MonthInfo

__all__ = ["info_to_mapper", "reward_source_to_mapper"]


def info_to_mapper(user: Account, month_info: MonthInfo):
    """将 MonthInfo 转换为 MonthInfoMapper"""
    return MonthInfoMapper(
        uid=user.uid,
        month=month_info.data_month,
        hcoin=month_info.month_data.current_hcoin,
        rails_pass=month_info.month_data.current_rails_pass,
    )


def reward_source_to_mapper(user: Account, month_info: MonthInfo):
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
