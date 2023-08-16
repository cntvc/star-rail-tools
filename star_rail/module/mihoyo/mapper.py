import typing

from star_rail.core import DBClient, DBModel, Field_Ex, convert


class CookieMapper(DBModel):
    __table_name__ = "cookie"

    uid: str = Field_Ex(primary_key=True)

    login_ticket: str = ""

    login_uid: str = ""

    account_id: str = ""

    cookie_token: str = ""

    ltoken: str = ""

    ltuid: str = ""

    mid: str = ""

    stoken: str = ""

    stuid: str = ""

    @staticmethod
    def query_cookie(uid: str) -> typing.Optional["CookieMapper"]:
        sql = """select * from cookie where uid = "{}"
        """.format(
            uid
        )
        with DBClient() as db:
            row = db.select(sql).fetchone()
        return convert(row, CookieMapper)


class UserMapper(DBModel):
    __table_name__ = "user"

    uid: str = Field_Ex(primary_key=True)

    gacha_url: str

    region: str

    game_biz: str

    @staticmethod
    def query_user(uid: str) -> typing.Optional["UserMapper"]:
        """根据id查询用户数据"""
        sql = """select * from user where uid = "{}"
        """.format(
            uid
        )
        with DBClient() as db:
            row = db.select(sql).fetchone()
        return convert(row, UserMapper)

    @staticmethod
    def query_all() -> typing.List["UserMapper"]:
        """查询所有用户，按照uid顺序返回"""
        sql = """select * from user order by uid;"""
        with DBClient() as db:
            row = db.select(sql).fetchall()
        return convert(row, UserMapper)
