use std::path::PathBuf;
use std::sync::LazyLock;

use crate::{APP_PATH, Result, logger};

static DB_PATH: LazyLock<PathBuf> = LazyLock::new(|| APP_PATH.db_dir.join("star-rail-tools.db"));

pub struct DatabaseService;

impl DatabaseService {
    pub fn init() -> Result<()> {
        logger::info!("Initializing database");
        let mut conn = Self::connection()?;
        conn.pragma_update(None, "journal_mode", "WAL")?;
        Self::create_database(&mut conn)?;
        logger::info!("Database initialized successfully");
        Ok(())
    }

    fn create_database(conn: &mut rusqlite::Connection) -> Result<()> {
        let tx = conn.transaction()?;
        for s in SQL_V0 {
            tx.execute(s, [])?;
        }
        tx.commit()?;
        Ok(())
    }

    pub fn connection() -> Result<rusqlite::Connection> {
        let conn = rusqlite::Connection::open(DB_PATH.as_path())?;
        conn.busy_timeout(std::time::Duration::from_secs(2))?;
        Ok(conn)
    }
}

const SQL_V0: [&str; 7] = [
    // account
    "CREATE TABLE IF NOT EXISTS account (uid TEXT PRIMARY KEY);",
    // setting
    "CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT);",
    // app_status
    "CREATE TABLE IF NOT EXISTS app_status (key TEXT PRIMARY KEY, value TEXT);",
    // gacha_record_item
    "CREATE TABLE IF NOT EXISTS gacha_record
    (
        id         INTEGER PRIMARY KEY,
        gacha_id   INTEGER NOT NULL,
        gacha_type INTEGER NOT NULL,
        item_id    INTEGER NOT NULL,
        time       TEXT    NOT NULL,
        rank_type  INTEGER NOT NULL,
        uid        TEXT    NOT NULL,
        batch_id   INTEGER NOT NULL
    );",
    // gacha_update_log
    "CREATE TABLE IF NOT EXISTS gacha_update_log
    (
        batch_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        uid      TEXT                              NOT NULL,
        time     TEXT                              NOT NULL,
        source   TEXT                              NOT NULL
    );",
    // gacha_analysis
    "CREATE TABLE IF NOT EXISTS gacha_analysis
    (
        uid         TEXT    NOT NULL,
        gacha_type  INTEGER NOT NULL,
        pity_count  INTEGER NOT NULL,
        total_count INTEGER NOT NULL,
        rank5       TEXT,
        PRIMARY KEY (uid, gacha_type)
    );",
    // gacha_metadata
    "CREATE TABLE IF NOT EXISTS gacha_metadata
    (
        item_id   INTEGER PRIMARY KEY NOT NULL,
        rarity    INTEGER             NOT NULL,
        item_type TEXT                NOT NULL,
        names     TEXT                NOT NULL
    );",
];
