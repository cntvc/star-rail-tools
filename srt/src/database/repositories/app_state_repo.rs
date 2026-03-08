use rusqlite::{OptionalExtension, params};

use tracing::instrument;

use crate::Result;
use crate::core::FromAppStateValue;
use crate::database::DatabaseService;

pub fn select<T>(key: &str) -> Result<Option<T>>
where
    T: FromAppStateValue,
{
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare("SELECT value FROM app_state WHERE key = ?;")?;
    let result = stmt
        .query_row(params![&key], |row| row.get::<_, Option<String>>(0))
        .optional()?;
    match result.flatten() {
        Some(s) => Ok(Some(T::from_state_value(s)?)),
        None => Ok(None),
    }
}

#[instrument(level = "debug")]
pub fn update(key: &str, value: &str) -> Result<bool> {
    let conn = DatabaseService::connection()?;
    let res = conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?1, ?2);",
        params![key, value],
    )?;
    Ok(res > 0)
}
