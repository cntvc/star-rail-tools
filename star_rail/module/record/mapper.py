from star_rail.core import DBClient, DBModel, Field_Ex, convert


class GachaRecordInfoMapper(DBModel):
    __table_name__ = "record_info"

    uid: str = Field_Ex(primary_key=True)

    lang: str

    region: str

    region_time_zone: int

    @classmethod
    def query(cls, uid: str):
        sql = """select * from {} where uid = "{}"; """.format(cls.__table_name__, uid)
        with DBClient() as db:
            row = db.select(sql).fetchone()
        return convert(row, GachaRecordInfoMapper)


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
    def query_all(cls, uid: str, gacha_type: str = "", begin_id: str = ""):
        """查询按id从小到大排序的结果"""
        type_sql = """ and gacha_type = "{}" """.format(gacha_type) if gacha_type else ""
        id_sql = """ and id > "{}" """.format(begin_id) if begin_id else ""
        sql = """select * from {} where uid = "{}" {} {} ORDER BY id; """.format(
            cls.__table_name__, uid, type_sql, id_sql
        )
        with DBClient() as db:
            row = db.select(sql).fetchall()
        return convert(row, cls)

    @classmethod
    def query_latest(cls, uid: str):
        """查询id最大的一条记录"""
        sql = """SELECT * FROM record_item where uid = "{}" ORDER BY id DESC LIMIT 1;
        """.format(
            uid
        )
        with DBClient() as db:
            row = db.select(sql).fetchone()
        return convert(row, cls)
