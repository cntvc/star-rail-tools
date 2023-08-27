from star_rail.database import (
    DataBaseClient,
    DataBaseField,
    DataBaseModel,
    model_convert_item,
    model_convert_list,
)


class GachaRecordInfoMapper(DataBaseModel):
    __table_name__ = "record_info"

    uid: str = DataBaseField(primary_key=True)

    lang: str

    region: str

    region_time_zone: int

    @classmethod
    def query(cls, uid: str):
        sql = """select * from record_info where uid = ?; """
        with DataBaseClient() as db:
            row = db.execute(sql, uid).fetchone()
        return model_convert_item(row, cls)


class GachaItemMapper(DataBaseModel):
    __table_name__ = "record_item"

    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str = DataBaseField(primary_key=True)
    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str

    @classmethod
    def query_all(cls, uid: str):
        """查询按id从小到大排序的结果"""

        sql = """select * from record_item where uid = ? ORDER BY id; """
        with DataBaseClient() as db:
            row = db.execute(sql, uid).fetchall()
        return model_convert_list(row, cls)

    @classmethod
    def query_latest(cls, uid: str):
        """查询id最大的一条记录"""
        sql = """SELECT * FROM record_item where uid = ? ORDER BY id DESC LIMIT 1;"""
        with DataBaseClient() as db:
            row = db.execute(sql, uid).fetchone()
        return model_convert_item(row, cls)
