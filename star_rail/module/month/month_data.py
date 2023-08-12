import typing

from pydantic import BaseModel

from star_rail.module.month.model import MonthInfoRewardSource


class MonthInfoData(BaseModel):
    """开拓月历数据"""

    month: str
    """日期"""
    current_hcoin: int
    """当月获取总数"""
    current_rails_pass: int
    """通票和专票总数"""
    group_by: typing.List[MonthInfoRewardSource]
    """星穹来源"""
