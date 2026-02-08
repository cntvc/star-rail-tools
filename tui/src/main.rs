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
    logger::init(&APP_PATH.log_dir, Some(logger::Level::DEBUG))?;
    srt::DatabaseService::init()?;

    let mut terminal = ratatui::init();

    let mut app = App::new();
    app.init().await?;
    let result = app.run(&mut terminal).await;
    ratatui::restore();

    result
}
