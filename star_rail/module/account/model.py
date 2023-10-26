from pydantic import BaseModel


class GameRecordCard(BaseModel):
    """[API] mihoyo 账户的游戏角色"""

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
    """[API] mihoyo 账户的游戏角色列表"""

    list: list[GameRecordCard]
