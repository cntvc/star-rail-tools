from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


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


class GachaRecordItem(BaseGachaRecordItem):
    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str


class GachaRecordPage(BaseModel):
    page: int
    size: int
    list: list[GachaRecordItem]
    region: str
    region_time_zone: int


########################################################################
# Analyzer
########################################################################


class GachaIndexItem(GachaRecordItem):
    index: int
    """物品抽数"""


class GachaPoolAnalyzeResult(BaseModel):
    """分卡池的统计结果"""

    gacha_type: str = ""
    """抽卡类型"""
    pity_count: int = 0
    """保底计数"""
    total_count: int = 0
    """本类型的抽卡总数"""
    rank5: list[GachaIndexItem] = []
    """5星物品详情"""


class GachaAnalyzeSummary(BaseModel):
    uid: str = ""
    update_time: str = ""
    data: list[GachaPoolAnalyzeResult] = []
    version: str = "v1.0"

    model_config = ConfigDict(extra="ignore")

    def is_empty(self) -> bool:
        return all(item.total_count == 0 for item in self.data)

    def get_pool_data(self, gacha_type: str) -> GachaPoolAnalyzeResult:
        return next((x for x in self.data if x.gacha_type == gacha_type), None)


@dataclass
class GachaRecordInfo:
    uid: str
    batch_id: int
    lang: str
    region_time_zone: int
    source: str
