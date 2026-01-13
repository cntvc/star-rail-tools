use rusqlite::{OptionalExtension, params};

use crate::{Result, logger};

pub fn select(conn: &rusqlite::Connection, key: &str) -> Result<Option<String>> {
    logger::debug!("Getting setting: {}", key);
    let mut stmt = conn.prepare("SELECT value FROM setting WHERE key = ?;")?;
    let result = stmt
        .query_row(params![&key], |row| row.get::<_, Option<String>>(0))
        .optional()?;
    Ok(result.flatten())
}

pub fn update(conn: &rusqlite::Connection, key: &str, value: &str) -> Result<bool> {
    logger::debug!("Setting setting: {}, value: {}", key, value);
    let mut stmt = conn.prepare("INSERT OR REPLACE INTO setting (key, value) VALUES (?1, ?2);")?;
    let res = stmt.execute(params![key, value])?;
    Ok(res > 0)
}
