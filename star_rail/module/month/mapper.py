from star_rail.database import DBModel, Field_Ex


class MonthInfoMapper(DBModel):
    __table_name__ = "month_info"

    uid: str = Field_Ex(primary_key=True)
    """用户id"""

    month: str = Field_Ex(primary_key=True)
    """月份"""

    hcoin: int
    """星穹"""

    rails_pass: int
    """列车票"""


class MonthInfoRewardSourceMapper(DBModel):
    """开拓月历星穹来源"""

    __table_name__ = "month_reward_source"

    uid: str = Field_Ex(primary_key=True)

    month: str = Field_Ex(primary_key=True)

    action: str = Field_Ex(primary_key=True)

    num: int

    percent: int

    action_name: str
