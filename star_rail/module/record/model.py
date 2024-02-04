from pydantic import BaseModel


class BaseGachaRecordItem(BaseModel):
    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str

    def __eq__(self, __value: "BaseGachaRecordItem") -> bool:
        return self.id == __value.id

    def __ne__(self, __value: "BaseGachaRecordItem") -> bool:
        return self.id != __value.id

    def __gt__(self, __value: "BaseGachaRecordItem") -> bool:
        return self.id > __value.id

    def __lt__(self, __value: "BaseGachaRecordItem") -> bool:
        return self.id < __value.id


########################################################################
# Mihoyo API Model
########################################################################


class GachaRecordItem(BaseGachaRecordItem):
    """抽卡项"""

    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str


class GachaRecordData(BaseModel):
    """跃迁记录 API 结构"""

    page: int
    size: int
    list: list[GachaRecordItem]
    region: str
    region_time_zone: int


########################################################################
# Analyzer
########################################################################


class StatisticItem(GachaRecordItem):
    index: str
    """物品抽数"""


class StatisticResult(BaseModel):
    """分卡池的统计结果"""

    gacha_type: str = ""
    """抽卡类型"""
    pity_count: int = 0
    """保底计数"""
    total_count: int = 0
    """本类型的抽卡总数"""
    rank_5: list[StatisticItem] = []
    """5星物品详情"""


class AnalyzeResult(BaseModel):
    uid: str = ""
    update_time: str = ""
    data: list[StatisticResult] = []

    def empty(self):
        for i in self.data:
            if len(i.rank_5):
                return False
        return True
