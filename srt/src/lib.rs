pub(crate) mod config;
pub mod core;
pub(crate) mod database;
pub(crate) mod error;
pub mod logger;
pub mod updater;
pub(crate) mod utils;

pub use config::AppConfig;
pub use error::AppError;

pub use database::DatabaseService;

use std::{path::PathBuf, sync::LazyLock};

pub static APP_NAME: &str = "StarRailTools";

pub static APP_PATH: LazyLock<AppPath> = LazyLock::new(AppPath::new);

pub static APP_VERSION: &str = env!("CARGO_PKG_VERSION");

pub type Result<T, E = error::AppError> = std::result::Result<T, E>;

pub struct AppPath {
    pub root_dir: PathBuf,
    pub log_dir: PathBuf,
    pub cache_dir: PathBuf,
    pub db_dir: PathBuf,
    pub import_dir: PathBuf,
}

impl AppPath {
    pub fn new() -> AppPath {
        let root_dir = get_root_dir();
        let log_dir = root_dir.join("Logs");
        let cache_dir = root_dir.join("Cache");
        let db_dir = root_dir.join("Database");
        let import_dir = root_dir.join("Import");
        AppPath {
            root_dir,
            log_dir,
            cache_dir,
            db_dir,
            import_dir,
        }
    }

    pub fn init(&self) -> Result<()> {
        std::fs::create_dir_all(&self.log_dir)?;
        std::fs::create_dir_all(&self.cache_dir)?;
        std::fs::create_dir_all(&self.db_dir)?;
        std::fs::create_dir_all(&self.import_dir)?;
        Ok(())
    }
}

impl Default for AppPath {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(not(debug_assertions))]
fn get_root_dir() -> PathBuf {
    let exe_path = std::env::current_exe().expect("failed to get app path");
    let exe_path = exe_path.parent().expect("failed to get app parent path");
    exe_path.join(APP_NAME)
}

#[cfg(debug_assertions)]
fn get_root_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join(APP_NAME)
}
