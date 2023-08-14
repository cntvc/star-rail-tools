from .account import Account
from .cookie import Cookie
from .mapper import CookieMapper, UserMapper


def user_to_mapper(user: Account):
    return UserMapper(
        uid=user.uid, gacha_url=user.gacha_url, region=user.region, game_biz=user.game_biz
    )


def user_to_cookie_mapper(user: Account):
    return CookieMapper(uid=user.uid, **user.cookie.model_dump("all"))


def cookie_mapper_to_cookie(cookie_mapper: CookieMapper):
    return Cookie(**cookie_mapper.model_dump())


def user_mapper_to_user(user_mapper: UserMapper):
    return Account(**user_mapper.model_dump())
