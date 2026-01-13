use rusqlite::{OptionalExtension, params};

use crate::database::DatabaseService;
use crate::{Result, logger};

pub fn select(key: &str) -> Result<Option<String>> {
    logger::debug!("Getting app status: {}", key);
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare("SELECT value FROM app_status WHERE key = ?;")?;
    let result = stmt
        .query_row(params![&key], |row| row.get::<_, Option<String>>(0))
        .optional()?;
    Ok(result.flatten())
}
pub fn update(key: &str, value: &str) -> Result<bool> {
    logger::debug!("Updating app status: {}", key);
    let conn = DatabaseService::connection()?;
    let res = conn.execute(
        "INSERT OR REPLACE INTO app_status (key, value) VALUES (?1, ?2);",
        params![key, value],
    )?;
    Ok(res > 0)
}
pub fn update_to_null(key: &str) -> Result<bool> {
    logger::debug!("Updating app status to null: {}", key);
    let conn = DatabaseService::connection()?;
    let mut stmt =
        conn.prepare("INSERT OR REPLACE INTO app_status (key, value) VALUES (?1, ?2);")?;
    let res = stmt.execute(params![key, None::<String>])?;
    Ok(res > 0)
}
