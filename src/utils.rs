use std::path::Path;

use regex::Regex;
use tracing::level_filters::LevelFilter;
use tracing_subscriber::{fmt, prelude::*};

use crate::APP_PATH;
use crate::Result;

const MAX_LOG_FILES: usize = 30;

pub fn init_logging() -> Result<()> {
    clean_logs()?;

    let now = time::OffsetDateTime::now_utc();
    let format = time::macros::format_description!("[year][month][day]-[hour][minute][second]");
    let file_name = format!(
        "star-rail-tools-{}.log",
        now.format(&format).expect("Failed to format time")
    );

    let file_appender = tracing_appender::rolling::never(&APP_PATH.log_dir, file_name);

    let (non_blocking_writer, guard) = tracing_appender::non_blocking(file_appender);

    let format_layer = fmt::layer()
        .with_writer(non_blocking_writer)
        .with_timer(FormatTime)
        .with_thread_ids(true)
        .with_level(true)
        .with_target(false)
        .with_line_number(true)
        .with_file(true)
        .with_ansi(false);

    tracing_subscriber::registry()
        .with(LevelFilter::INFO)
        .with(format_layer)
        .init();

    std::mem::forget(guard);
    Ok(())
}

struct FormatTime;

impl fmt::time::FormatTime for FormatTime {
    fn format_time(&self, w: &mut fmt::format::Writer<'_>) -> std::fmt::Result {
        let format = time::macros::format_description!(
            "[year]-[month]-[day] [hour]:[minute]:[second] [subsecond digits:6]"
        );
        let now = time::OffsetDateTime::now_utc();
        write!(w, "{}", now.format(&format).expect("Failed to format time"))
    }
}

fn clean_logs() -> Result<()> {
    let path = Path::new(&APP_PATH.log_dir);
    if !path.exists() {
        return Ok(());
    }

    let re = Regex::new(r"^app-\d{8}-\d{6}\.log$")?;
    let mut entries: Vec<_> = std::fs::read_dir(path)?
        .filter_map(Result::ok)
        .filter(|e| {
            e.path()
                .file_name()
                .and_then(|s| s.to_str())
                .map_or(false, |s| re.is_match(s))
        })
        .collect();

    if entries.len() <= MAX_LOG_FILES {
        return Ok(());
    }

    entries.sort_by_key(|item| {
        item.metadata()
            .and_then(|m| m.created())
            .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
    });

    let to_delete_count = entries.len() - MAX_LOG_FILES;
    for entry in entries.iter().take(to_delete_count) {
        std::fs::remove_file(entry.path())?;
    }
    Ok(())
}
