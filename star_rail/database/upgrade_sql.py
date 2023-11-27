# flake8: noqa E501

__all__ = ["UpgradeSQL"]

DATABASE_VERSION = 1
"""软件中数据库版本"""


class UpgradeSQL:
    _register: list["UpgradeSQL"] = []
    target_version: int
    sql_list: list[str]

    def __init__(self, target_version: int, sql_list: list[str]) -> None:
        self.target_version = target_version
        self.sql_list = sql_list
        self._register.append(self)


UpgradeSQL(
    1,
    [
        # 修改user表:删除 gacha_url 字段，删除cookie表，新增 cookie 字段
        "create table if not exists temp_user (uid primary key,  cookie  default '{}', region, game_biz);",
        "insert into temp_user (uid, region, game_biz) select uid, region, game_biz from user;",
        "drop table if exists user;",
        "drop table if exists cookie;",
        "alter table temp_user rename to user;",
        # 修改月历表，聚合为一个表
        """
        CREATE TABLE IF NOT EXISTS month_info_item
        (
            uid         TEXT,
            month       TEXT,
            hcoin       INTEGER,
            rails_pass  INTEGER,
            source      TEXT,
            update_time TEXT,
            PRIMARY KEY (uid, month)
        );
        """,
        """
        INSERT INTO month_info_item (uid, month, hcoin, rails_pass, update_time, source)
        select mi.uid, mi.month, mi.hcoin, mi.rails_pass, mir.update_time,
            json_group_array(
                json_object(
                    'action', mrs.action,
                    'percent', mrs.percent,
                    'action_name', mrs.action_name,
                    'num', mrs.num
                )
            ) AS source
            from month_info mi
            join month_info_record mir on mi.uid = mir.uid
            join month_reward_source mrs on mi.uid = mrs.uid and mi.month = mrs.month
        GROUP BY
            mi.uid, mi.month;
        """,
        "drop table if exists month_info;",
        "drop table if exists month_info_record;",
        "drop table if exists month_reward_source;",
        # 修改record表
        """
        CREATE TABLE if not exists gacha_record_batch
        (
            lang             TEXT,
            count            INTEGER,
            timestamp        INTEGER,
            region_time_zone TEXT,
            batch_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            uid              TEXT,
            source           TEXT default ''
        );
        """,
        """
        create table if not exists gacha_record_item
        (
            rank_type  TEXT,
            name       TEXT,
            lang       TEXT,
            gacha_id   TEXT,
            item_id    TEXT,
            count      TEXT,
            item_type  TEXT,
            id         TEXT primary key,
            time       TEXT,
            gacha_type TEXT,
            batch_id   INTEGER,
            uid        TEXT
        );
        """,
        """
        INSERT INTO gacha_record_batch (lang, count, timestamp, region_time_zone, uid)
        SELECT lang,
            (SELECT COUNT(*) FROM record_item WHERE record_item.uid = ri.uid) AS count,
            strftime('%s', 'now')                                             AS timestamp,
            region_time_zone,
            uid
        FROM record_info as ri;
        """,
        """
        insert into gacha_record_item (rank_type, name, lang, gacha_id, item_id, count, item_type, id, time, gacha_type,batch_id, uid)
        select ri.rank_type,
            ri.name,
            ri.lang,
            ri.gacha_id,
            ri.item_id,
            ri.count,
            ri.item_type,
            ri.id,
            ri.time,
            ri.gacha_type,
            grb.batch_id,
            ri.uid
        from record_item ri join gacha_record_batch grb on ri.uid = grb.uid;
        """,
        "drop table if exists record_item;",
        "drop table if exists record_info;",
    ],
)
