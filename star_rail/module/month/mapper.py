import typing

from star_rail.core import DBClient, DBModel, Field_Ex, convert


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

    @classmethod
    def query(
        cls, uid: str, month: typing.Optional[str], limit: typing.Optional[int]
    ) -> typing.Union[typing.List["MonthInfoMapper"], typing.Optional["MonthInfoMapper"]]:
        """查询开拓月历记录"""
        where_month = """and month = "{}" """.format(month) if month else ""
        limit = """ DESC LIMIT {} """.format(limit) if limit else ""
        query_sql = """SELECT * FROM month_info WHERE uid = "{}" {} ORDER BY month {}
        """.format(
            uid, where_month, limit
        )
        with DBClient() as db:
            cursor = db.select(query_sql)
        res = cursor.fetchall()
        return convert(res, MonthInfoMapper)


class MonthInfoRewardSourceMapper(DBModel):
    """开拓月历星穹来源"""

    __table_name__ = "month_reward_source"

    uid: str = Field_Ex(primary_key=True)

    month: str = Field_Ex(primary_key=True)

    action: str = Field_Ex(primary_key=True)

    num: int

    percent: int

    action_name: str
