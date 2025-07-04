pub mod app;
pub mod config;
pub mod db;
pub mod event;
pub mod tui;
pub mod utils;

use std::sync::LazyLock;

pub use anyhow::Result;

pub static APP_NAME: &str = "StarRailTools";

pub static APP_PATH: LazyLock<config::AppPath> = LazyLock::new(|| config::AppPath::new());

pub static CONFIG: LazyLock<config::Config> = LazyLock::new(|| config::Config::load());
