use rusqlite::{OptionalExtension, params};

use tracing::instrument;

use crate::config::ConfigItem;
use crate::{AppConfig, DatabaseService, Result};

pub fn select(conn: &rusqlite::Connection, key: &str) -> Result<Option<String>> {
    let mut stmt = conn.prepare("SELECT value FROM setting WHERE key = ?;")?;
    let result = stmt
        .query_row(params![&key], |row| row.get::<_, Option<String>>(0))
        .optional()?;
    Ok(result.flatten())
}

#[instrument(level = "debug")]
pub fn update_all(config: AppConfig) -> Result<bool> {
    let mut conn = DatabaseService::connection()?;
    let tx = conn.transaction()?;
    {
        let sql = "INSERT OR REPLACE INTO setting (key, value) VALUES (?1, ?2);";
        let mut stmt = tx.prepare(sql)?;

        stmt.execute(params![
            ConfigItem::LogLevel.as_str(),
            config.log_level.as_str()
        ])?;
        stmt.execute(params![
            ConfigItem::Language.as_str(),
            config.language.as_str()
        ])?;
        stmt.execute(params![
            ConfigItem::CheckUpdate.as_str(),
            &config.check_update.to_string()
        ])?;
    }
    tx.commit()?;
    Ok(true)
}
