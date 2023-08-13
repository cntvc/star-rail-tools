from star_rail.database.base_model import DBModel, Field_Ex


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


class AccountMapper(DBModel):
    __table_name__ = "user"

    uid: str = Field_Ex(primary_key=True)

    gacha_url: str = ""
