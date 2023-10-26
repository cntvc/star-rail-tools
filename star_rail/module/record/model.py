from pydantic import BaseModel


class BaseGachaItem(BaseModel):
    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str

    def __eq__(self, __value: "BaseGachaItem") -> bool:
        return self.id == __value.id

    def __ne__(self, __value: "BaseGachaItem") -> bool:
        return self.id != __value.id

    def __gt__(self, __value: "BaseGachaItem") -> bool:
        return self.id > __value.id

    def __lt__(self, __value: "BaseGachaItem") -> bool:
        return self.id < __value.id


class GachaItem(BaseGachaItem):
    """[API, DB] 抽卡项"""

    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str


class GachaRecordData(BaseModel):
    """[API] 跃迁记录 API 结构"""

    page: int
    size: int
    list: list[GachaItem]
    region: str
    region_time_zone: int


class GachaRecordInfo(BaseModel):
    """[DB] 跃迁记录存档"""

    uid: str

    lang: str

    region: str

    region_time_zone: int


########################################################################
# SRGF
########################################################################


########################################################################
# Analyzer
########################################################################


class _AnalyzeRecordItem(GachaItem):
    # 添加索引表示抽数
    index: str


class _RecordTypeResult(BaseModel):
    """分卡池的分析结果类"""

    gacha_type: str = ""
    """抽卡类型"""
    pity_count: int = 0
    """保底计数"""
    total_count: int = 0
    """本类型的抽卡总数"""
    rank_5: list[_AnalyzeRecordItem] = []
    """5星物品详情"""


class AnalyzeResult(BaseModel):
    uid: str = ""
    lang: str = ""
    update_time: str = ""
    data: list[_RecordTypeResult] = []
