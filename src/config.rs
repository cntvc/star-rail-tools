use std::path::PathBuf;

use anyhow::Ok;
use serde::Deserialize;

use crate::APP_NAME;
use crate::APP_PATH;
use crate::Result;

pub struct AppPath {
    pub root_dir: PathBuf,
    pub log_dir: PathBuf,
    pub cache_dir: PathBuf,
    pub import_dir: PathBuf,
    pub db_dir: PathBuf,
}

impl AppPath {
    pub fn new() -> AppPath {
        let root_dir = get_root_dir();
        let log_dir = root_dir.join("Logs");
        let cache_dir = root_dir.join("Cache");
        let import_dir = root_dir.join("Import");
        let db_dir = root_dir.join("Database");
        AppPath {
            root_dir,
            log_dir,
            cache_dir,
            import_dir,
            db_dir,
        }
    }

    pub fn create_dir(&self) -> Result<()> {
        std::fs::create_dir_all(&self.log_dir)?;
        std::fs::create_dir_all(&self.cache_dir)?;
        std::fs::create_dir_all(&self.import_dir)?;
        std::fs::create_dir_all(&self.db_dir)?;
        Ok(())
    }
}

fn get_root_dir() -> PathBuf {
    let exe_path = std::env::current_exe().expect("failed to get current exe path");
    let exe_path = exe_path.parent().expect("failed to get parent path");
    return exe_path.join(APP_NAME);
}

#[derive(Debug, Deserialize)]
#[serde(default)]
pub struct Config {
    pub check_update: bool,
    pub thirdpart_metadata: bool,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            check_update: true,
            thirdpart_metadata: false,
        }
    }
}

impl Config {
    pub fn load() -> Config {
        let config_path = APP_PATH.root_dir.join("config.toml");
        if config_path.exists() {
            let content = std::fs::read_to_string(APP_PATH.root_dir.join("config.toml"))
                .expect("Failed to read file");
            let config: Config = toml::from_str(&content).expect("Failed to parse config file");
            config
        } else {
            Config::default()
        }
    }
}
