from typing import List

from pydantic import BaseModel

#######################
# WebApi
#######################


class AccountInfo(BaseModel):
    account_id: int
    area_code: str
    create_time: int
    email: str
    iconid: int
    identity_code: str
    is_adult: int
    is_email_verify: int
    mobile: str
    nickname: str
    real_name: str
    safe_area_code: str
    safe_level: int
    safe_mobile: str
    weblogin_token: str  # 同 login_ticket


class Ticket(BaseModel):
    account_info: AccountInfo
    msg: str
    status: str
    ticket: str


class GameRole(BaseModel):
    game_biz: str
    region: str
    game_uid: str
    nickname: str
    level: str
    is_chosen: bool
    region_name: str
    is_official: bool


class UserGameRoles(BaseModel):
    list: List[GameRole]


#######################
# APP
#######################


class GameRecordCard(BaseModel):
    has_role: bool
    game_id: int
    game_role_id: str
    nickname: str
    region: str
    level: int
    background_image: str
    is_public: bool
    data: list
    region_name: str
    url: str
    data_switches: list
    h5_data_switches: list
    background_color: str


class UserGameRecordCards(BaseModel):
    list: List[GameRecordCard]
