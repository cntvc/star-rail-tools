use rusqlite::{OptionalExtension, params};

use crate::config::ConfigItem;
use crate::{AppConfig, DatabaseService, Result, logger};

pub fn select(conn: &rusqlite::Connection, key: &str) -> Result<Option<String>> {
    logger::debug!("Getting setting: {}", key);
    let mut stmt = conn.prepare("SELECT value FROM setting WHERE key = ?;")?;
    let result = stmt
        .query_row(params![&key], |row| row.get::<_, Option<String>>(0))
        .optional()?;
    Ok(result.flatten())
}

pub fn update_all(config: AppConfig) -> Result<bool> {
    logger::debug!("Save config {:?}", config);
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
