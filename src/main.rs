use srt::Result;
use srt::utils::init_logging;
use srt::{APP_PATH, CONFIG};

use srt::app::App;

#[tokio::main]
async fn main() -> Result<()> {
    APP_PATH.create_dir()?;
    init_logging()?;
    // db::init().await;
    let mut terminal = ratatui::init();
    let app_result = App::new().run(&mut terminal).await;
    ratatui::restore();

    return app_result;
}
