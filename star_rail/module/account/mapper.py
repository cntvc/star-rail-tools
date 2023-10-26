import typing

from star_rail.database import (
    DataBaseClient,
    DataBaseField,
    DataBaseModel,
    model_convert_item,
    model_convert_list,
)


class CookieMapper(DataBaseModel):
    __table_name__ = "cookie"

    uid: str = DataBaseField(primary_key=True)

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
        sql = """select * from cookie where uid = ? ;"""
        with DataBaseClient() as db:
            row = db.execute(sql, uid).fetchone()
        return model_convert_item(row, CookieMapper)


class UserMapper(DataBaseModel):
    __table_name__ = "user"

    uid: str = DataBaseField(primary_key=True)

    gacha_url: str

    region: str

    game_biz: str

    @staticmethod
    def query_user(uid: str) -> typing.Optional["UserMapper"]:
        """根据id查询用户数据"""
        sql = """select * from user where uid = ? ;"""
        with DataBaseClient() as db:
            row = db.execute(sql, uid).fetchone()
        return model_convert_item(row, UserMapper)

    @staticmethod
    def query_all() -> list["UserMapper"]:
        """查询所有用户，按照uid顺序返回"""
        sql = """select * from user order by uid ;"""
        with DataBaseClient() as db:
            row = db.execute(sql).fetchall()
        return model_convert_list(row, UserMapper)
