mod action;
mod app;
mod component;
mod events;
mod notification;
mod task;

use app::App;
use srt::{APP_PATH, Result, logger};

#[tokio::main]
async fn main() -> Result<()> {
    APP_PATH.init()?;
    logger::init(&APP_PATH.log_dir, Some(logger::Level::INFO))?;
    srt::DatabaseService::init()?;
    let mut app = App::new();
    app.init().await?;

    let mut terminal = ratatui::init();
    let result = app.run(&mut terminal).await;

    ratatui::restore();
    result
}
