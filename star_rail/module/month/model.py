import typing

from pydantic import BaseModel


class MonthInfoDayData(BaseModel):
    """当日数据"""

    current_hcoin: int
    current_rails_pass: int
    last_hcoin: int
    last_rails_pass: int


class MonthInfoRewardSource(BaseModel):
    """开拓月历星穹来源"""

    action: str
    num: int
    percent: int
    action_name: str


class ApiMonthInfoMonthData(BaseModel):
    """月历数据"""

    current_hcoin: int
    """当月获取总数"""
    current_rails_pass: int
    """通票和专票总数"""
    last_hcoin: int
    """上月获取星穹总数"""
    last_rails_pass: int
    """上月获取通票和专票总数"""
    hcoin_rate: int
    """星穹增长率"""
    rails_rate: int
    """票数增长率"""
    group_by: typing.List[MonthInfoRewardSource]
    """星穹来源"""


class ApiMonthInfo(BaseModel):
    uid: str
    region: str
    login_flag: bool
    optional_month: typing.List
    """可查询月份"""
    month: str
    """当前月份"""
    data_month: str  # 202306
    month_data: ApiMonthInfoMonthData
    day_data: MonthInfoDayData
    version: str  # 1.2
    start_month: str
    """起始月份"""
    data_text: typing.Dict


class ApiMonthDetailData(BaseModel):
    action: str
    action_name: str
    num: int
    time: str  # ? 2023-09-02 09:02:23


class ApiMonthDetail(BaseModel):
    current_page: int
    data_month: str  # 202306
    list: typing.List[ApiMonthDetailData]
    region: str
    total: int
    uid: str


class MonthInfo(BaseModel):
    uid: str
    """用户id"""

    month: str
    """月份"""

    hcoin: int
    """星穹"""

    rails_pass: int
    """列车票"""
