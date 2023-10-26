from pydantic import BaseModel


class _DayData(BaseModel):
    """[API] 当日数据"""

    current_hcoin: int
    current_rails_pass: int
    last_hcoin: int
    last_rails_pass: int


class _RewardSource(BaseModel):
    """[API] 开拓月历星穹来源"""

    action: str
    num: int
    percent: int
    action_name: str


class _MonthData(BaseModel):
    """[API] 月历数据"""

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
    group_by: list[_RewardSource]
    """星穹来源"""


class MonthInfoData(BaseModel):
    """[API] 开拓月历接口模型"""

    uid: str
    region: str
    login_flag: bool
    optional_month: list
    """可查询月份"""
    month: str
    """当前月份"""
    data_month: str
    month_data: _MonthData
    day_data: _DayData
    version: str
    start_month: str
    """起始月份"""
    data_text: dict


class MonthInfo(BaseModel):
    """[DB] 开拓月历"""

    uid: str
    """用户id"""

    month: str
    """月份"""

    hcoin: int
    """星穹"""

    rails_pass: int
    """列车票"""
