use rusqlite::{OptionalExtension, params};
use tracing::instrument;

use crate::database::DatabaseService;
use crate::{Result, logger};

pub fn insert(uid: &str) -> Result<()> {
    logger::debug!("Adding account: {}", uid);
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare("INSERT INTO account (uid) VALUES (?1);")?;
    stmt.execute(params![uid])?;
    Ok(())
}

pub fn select_one(uid: &str) -> Result<Option<String>> {
    logger::debug!("Querying account: {}", uid);
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare("SELECT uid FROM account WHERE uid = ?1;")?;
    let res = stmt
        .query_row(params![uid], |row| row.get::<_, String>(0))
        .optional()?;
    Ok(res)
}

pub fn select_all() -> Result<Vec<String>> {
    logger::debug!("Querying all accounts");
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare("SELECT uid FROM account ORDER BY uid;")?;
    let rows = stmt.query_map([], |row| row.get::<_, String>(0))?;
    let res = rows.collect::<Result<Vec<_>, _>>()?;
    Ok(res)
}

#[instrument(level = "debug", skip_all)]
pub fn delete_all_data(uid: &str) -> Result<()> {
    logger::debug!("Deleting all data for account: {}", uid);
    let mut conn = DatabaseService::connection()?;
    let tx = conn.transaction()?;
    tx.execute(
        "UPDATE app_state SET value = NULL WHERE key = 'DEFAULT_ACCOUNT' AND value = ?1;",
        params![uid],
    )?;
    tx.execute("DELETE FROM account WHERE uid = ?1;", params![uid])?;
    tx.execute("DELETE FROM gacha_record WHERE uid = ?1;", params![uid])?;
    tx.execute("DELETE FROM gacha_update_log WHERE uid = ?1;", params![uid])?;
    tx.execute("DELETE FROM gacha_analysis WHERE uid = ?1;", params![uid])?;
    tx.commit()?;
    Ok(())
}
