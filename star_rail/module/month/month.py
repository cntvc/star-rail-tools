from datetime import datetime

import requests

from ..mihoyo.account import Account
from ..mihoyo.cookie import Cookie
from ..mihoyo.header import ClientType, Header, Origin, Referer, Salt, UserAgent
from ..mihoyo.routes import MONTH_INFO_URL


def get_month_detail(user: Account, cookie: Cookie):
    now_time = datetime.now()

    param = {"uid": user.uid, "region": user.region, "month": now_time.strftime("%Y%m")}

    header = (
        Header()
        .x_rpc_app_version()
        .user_agent(UserAgent.ANDROID)
        .x_rpc_client_type(ClientType.PC)
        .referer(Referer.WEB_STATIC_MIHOYO)
        .origin(Origin.WEB_STATIC_MIHOYO)
        .ds(Salt.LK2, param)
        .build()
    )

    response = requests.get(
        url=MONTH_INFO_URL.get_url(),
        headers=header,
        params=param,
        cookies=cookie.model_dump("all"),
    ).json()
    return response["data"]
