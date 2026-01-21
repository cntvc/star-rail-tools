use std::path::Path;
use std::sync::OnceLock;

use regex::Regex;
pub use tracing::Level;
pub use tracing::{debug, error, info, warn};
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::filter::EnvFilter;
use tracing_subscriber::{fmt, prelude::*, reload};

use crate::Result;

#[cfg(debug_assertions)]
const MAX_LOG_FILES: usize = 5;

#[cfg(not(debug_assertions))]
const MAX_LOG_FILES: usize = 30;

type ReloadHandle = reload::Handle<EnvFilter, tracing_subscriber::Registry>;

static LOG_LEVEL_HANDLE: OnceLock<ReloadHandle> = OnceLock::new();
static LOG_GUARD: OnceLock<WorkerGuard> = OnceLock::new();

pub fn init(path: &Path, level: Option<Level>) -> Result<()> {
    clean_logs(path)?;

    let now = time::OffsetDateTime::now_local().unwrap();
    let format = time::macros::format_description!("[year][month][day]-[hour][minute][second]");
    let file_name = format!(
        "star-rail-tools-{}.log",
        now.format(&format).expect("Failed to format time")
    );

    let file_appender = tracing_appender::rolling::never(path, file_name);

    let (non_blocking_writer, guard) = tracing_appender::non_blocking(file_appender);

    let format_layer = fmt::layer()
        .with_writer(non_blocking_writer)
        .with_timer(FormatTime)
        .with_thread_ids(true)
        .with_level(true)
        .with_target(false)
        .with_line_number(true)
        .with_file(true)
        .with_ansi(false)
        // 显示 span 关闭时的耗时
        // 由于异步任务机制，导致有过多 enter 日志，这里仅显示 close 日志
        .with_span_events(fmt::format::FmtSpan::CLOSE);

    // 创建过滤器：默认显示所有 info 日志，但屏蔽常见的嘈杂第三方库
    let level = level.map_or("info".to_string(), |l| l.to_string());
    let filter = EnvFilter::new(&level)
        .add_directive("hyper=off".parse().unwrap())
        .add_directive("reqwest=off".parse().unwrap());
    let (filter_layer, reload_handle) = reload::Layer::new(filter);

    tracing_subscriber::registry()
        .with(filter_layer)
        .with(format_layer)
        .init();

    LOG_LEVEL_HANDLE.set(reload_handle).ok();
    // TODO: 保存 guard 待确认实现方式
    LOG_GUARD.set(guard).ok();
    info!("Logger initialized with default level: {}", level);
    Ok(())
}

pub fn update_level(level: Level) -> Result<()> {
    let handle = LOG_LEVEL_HANDLE
        .get()
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::Other, "Logger not initialized"))?;

    let filter = EnvFilter::new(level.to_string())
        .add_directive("hyper=off".parse().unwrap())
        .add_directive("reqwest=off".parse().unwrap());

    handle.reload(filter).map_err(|e| {
        std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("Failed to reload log filter: {}", e),
        )
    })?;
    // 如果级别过低，可能无法在日志看到 level 更新信息
    error!("Log level updated to: {:?}", level);
    Ok(())
}

/// Explicitly flush logs by signaling the guard should be dropped at shutdown.
/// Note: The guard in OnceLock will be automatically dropped when the program exits.
/// This function is provided for documentation purposes.
pub fn flush_logs() {
    // The WorkerGuard stored in LOG_GUARD will be automatically dropped
    // when the program exits, ensuring all buffered logs are flushed.
    // There's no need for manual intervention in most cases.
}

struct FormatTime;

impl fmt::time::FormatTime for FormatTime {
    fn format_time(&self, w: &mut fmt::format::Writer<'_>) -> std::fmt::Result {
        let format = time::macros::format_description!(
            "[year]-[month]-[day] [hour]:[minute]:[second] [subsecond digits:6]"
        );
        let now = time::OffsetDateTime::now_local().unwrap();
        write!(w, "{}", now.format(&format).expect("Failed to format time"))
    }
}

fn clean_logs(log_dir: &Path) -> Result<()> {
    if !log_dir.exists() {
        return Ok(());
    }

    let re = Regex::new(r"^star-rail-tools-\d{8}-\d{6}\.log$").unwrap();
    let mut entries: Vec<_> = std::fs::read_dir(log_dir)?
        .filter_map(std::result::Result::ok)
        .filter(|e| {
            e.path()
                .file_name()
                .and_then(|s| s.to_str())
                .is_some_and(|s| re.is_match(s))
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

pub struct Sensitive<T>(T);

impl<T> Sensitive<T> {
    pub fn new(value: T) -> Self {
        Self(value)
    }

    pub fn into_inner(self) -> T {
        self.0
    }
}

impl std::fmt::Display for Sensitive<String> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "***")
    }
}

impl std::fmt::Debug for Sensitive<String> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Sensitive(***)")
    }
}

impl std::fmt::Display for Sensitive<&url::Url> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let mut url = self.0.clone();
        url.query_pairs_mut()
            .clear()
            .extend_pairs(self.0.query_pairs().map(|(k, v)| {
                if k == "authkey" {
                    (k, "***".into())
                } else {
                    (k, v)
                }
            }));
        write!(f, "{}", url)
    }
}
