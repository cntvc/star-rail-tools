from star_rail.module.types import GameBiz, Region

from .account import Account
from .cookie import Cookie
from .mapper import AccountMapper


def account_to_mapper(user: Account):
    return AccountMapper(
        uid=user.uid,
        cookie=user.cookie.model_dump_json(exclude_defaults=True),
        region=user.region,
        game_biz=user.game_biz,
    )


def mapper_to_account(user_mapper: AccountMapper):
    cookie = Cookie.model_validate_json(user_mapper.cookie)
    return Account(
        uid=user_mapper.uid,
        cookie=cookie,
        region=Region.get_by_str(user_mapper.region),
        game_biz=GameBiz.get_by_str(user_mapper.game_biz),
    )
