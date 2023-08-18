from star_rail.core import DBClient, DBModel, Field_Ex, convert


class GachaRecordInfoMapper(DBModel):
    __table_name__ = "record_info"

    uid: str = Field_Ex(primary_key=True)

    lang: str

    region: str

    region_time_zone: int

    @classmethod
    def query(cls, uid: str):
        sql = """select * from record_info where uid = ?; """
        with DBClient() as db:
            row = db.select(sql, uid).fetchone()
        return convert(row, cls)


class GachaItemMapper(DBModel):
    __table_name__ = "record_item"

    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str = Field_Ex(primary_key=True)
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
        with DBClient() as db:
            row = db.select(sql, uid).fetchall()
        return convert(row, cls)

    @classmethod
    def query_latest(cls, uid: str):
        """查询id最大的一条记录"""
        sql = """SELECT * FROM record_item where uid = ? ORDER BY id DESC LIMIT 1;"""
        with DBClient() as db:
            row = db.select(sql, uid).fetchone()
        return convert(row, cls)
