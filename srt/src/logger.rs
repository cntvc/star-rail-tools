use std::io::{Result as IoResult, Write};
use std::path::Path;
use std::sync::{Arc, OnceLock};

use regex::Regex;
pub use tracing::Level;
pub use tracing::{debug, error, info, trace, warn};
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::{filter::EnvFilter, fmt, fmt::MakeWriter, prelude::*, reload};

use crate::Result;

#[cfg(debug_assertions)]
const MAX_LOG_FILES: usize = 5;

#[cfg(not(debug_assertions))]
const MAX_LOG_FILES: usize = 30;

type ReloadHandle = reload::Handle<EnvFilter, tracing_subscriber::Registry>;

static LOG_LEVEL_HANDLE: OnceLock<ReloadHandle> = OnceLock::new();
static LOG_GUARD: OnceLock<WorkerGuard> = OnceLock::new();

/// 使用词边界 \b 避免误匹配含这些词的普通参数名（如 gacha_type）。
fn make_redact_regex() -> Regex {
    Regex::new(r"(?i)\b(authkey|token)=([^&\s]+)").expect("invalid redaction regex")
}

#[derive(Clone)]
struct Redactor {
    regex: Arc<Regex>,
}

impl Redactor {
    fn new() -> Self {
        Self {
            regex: Arc::new(make_redact_regex()),
        }
    }

    fn redact<'a>(&self, input: &'a str) -> std::borrow::Cow<'a, str> {
        self.regex.replace_all(input, "${1}=***")
    }
}

struct RedactWriter<W> {
    inner: W,
    redactor: Redactor,
}

impl<W: Write> Write for RedactWriter<W> {
    fn write(&mut self, buf: &[u8]) -> IoResult<usize> {
        let text = String::from_utf8_lossy(buf);
        let redacted = self.redactor.redact(&text);
        self.inner.write(redacted.as_bytes())?;
        Ok(buf.len())
    }

    fn flush(&mut self) -> IoResult<()> {
        self.inner.flush()
    }
}

#[derive(Clone)]
struct RedactMakeWriter<M> {
    inner: M,
    redactor: Redactor,
}

impl<M> RedactMakeWriter<M> {
    fn new(inner: M) -> Self {
        Self {
            inner,
            redactor: Redactor::new(),
        }
    }
}

impl<'a, M> MakeWriter<'a> for RedactMakeWriter<M>
where
    M: MakeWriter<'a> + Clone,
{
    type Writer = RedactWriter<M::Writer>;

    fn make_writer(&'a self) -> Self::Writer {
        RedactWriter {
            inner: self.inner.make_writer(),
            redactor: self.redactor.clone(),
        }
    }
}

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
        // 在 non_blocking writer 外层包裹 RedactMakeWriter
        .with_writer(RedactMakeWriter::new(non_blocking_writer))
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
    let filter = build_filter(&level);
    let (filter_layer, reload_handle) = reload::Layer::new(filter);

    tracing_subscriber::registry()
        .with(filter_layer)
        .with(format_layer)
        .init();

    LOG_LEVEL_HANDLE.set(reload_handle).ok();

    LOG_GUARD.set(guard).ok();
    info!("Logger initialized with default level: {}", level);
    Ok(())
}

pub fn update_level(level: Level) -> Result<()> {
    let handle = LOG_LEVEL_HANDLE
        .get()
        .ok_or_else(|| std::io::Error::other("Logger not initialized"))?;

    let filter = build_filter(&level.to_string());

    handle
        .reload(filter)
        .map_err(|e| std::io::Error::other(format!("Failed to reload log filter: {}", e)))?;
    // 如果级别过低，可能无法在日志看到 level 更新信息
    error!("Log level updated to: {:?}", level);
    Ok(())
}

fn build_filter(level: &str) -> EnvFilter {
    EnvFilter::new(level)
        .add_directive("hyper=off".parse().unwrap())
        .add_directive("reqwest=off".parse().unwrap())
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
