use std::path::PathBuf;
use std::sync::LazyLock;

use rusqlite::Connection;

use crate::APP_PATH;
use crate::Result;

static DB_PATH: LazyLock<PathBuf> = LazyLock::new(|| APP_PATH.db_dir.join("database.db"));

pub async fn init() -> Result<()> {
    let mut conn = Connection::open(DB_PATH.as_path())?;
    conn.pragma_update(None, "journal_mode", "WAL")?;
    create_database(&mut conn);
    Ok(())
}

fn create_database(conn: &mut Connection) {}
