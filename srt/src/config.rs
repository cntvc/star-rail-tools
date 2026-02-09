use crate::Result;
use crate::database::{ConfigRepo, DatabaseService};
use crate::logger::Level;
use i18n::Lang;

#[derive(Debug)]
pub enum ConfigItem {
    CheckUpdate,
    Language,
    LogLevel,
}

impl ConfigItem {
    pub const fn as_str(&self) -> &'static str {
        match self {
            ConfigItem::CheckUpdate => "CHECK_UPDATE",
            ConfigItem::Language => "LANGUAGE",
            ConfigItem::LogLevel => "LOG_LEVEL",
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct AppConfig {
    pub log_level: Level,
    pub language: Lang,
    pub check_update: bool,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            log_level: Level::INFO,
            language: Lang::zh_cn,
            check_update: true,
        }
    }
}

impl AppConfig {
    fn parse_config_value<T>(conn: &rusqlite::Connection, item: ConfigItem, default: T) -> Result<T>
    where
        T: std::str::FromStr,
    {
        Ok(ConfigRepo::select(conn, item.as_str())?
            .and_then(|s| s.parse().ok())
            .unwrap_or(default))
    }

    pub async fn load_config() -> Result<AppConfig> {
        tokio::task::spawn_blocking(|| {
            let conn = DatabaseService::connection()?;

            let log_level = Self::parse_config_value(&conn, ConfigItem::LogLevel, Level::INFO)?;
            let language =
                Self::parse_config_value(&conn, ConfigItem::Language, i18n::Lang::zh_cn)?;
            let check_update = Self::parse_config_value(&conn, ConfigItem::CheckUpdate, true)?;

            Ok(AppConfig {
                log_level,
                language,
                check_update,
            })
        })
        .await?
    }

    pub async fn save_config(config: &AppConfig) -> Result<()> {
        tokio::task::spawn_blocking({
            let config = *config;
            move || {
                ConfigRepo::update_all(&config)?;
                Ok(())
            }
        })
        .await?
    }
}
