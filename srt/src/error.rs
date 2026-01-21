use i18n::I18nKey;
use std::panic::Location;

use crate::logger;

#[derive(Debug)]
pub struct ErrorContext {
    pub key: I18nKey,
    pub args: Vec<String>, // 用于替换 i18n 返回文本中的占位符
}

impl ErrorContext {
    pub fn new(key: I18nKey, args: Vec<String>) -> Self {
        Self { key, args }
    }
}

impl std::fmt::Display for ErrorContext {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self.key)?;

        if self.args.is_empty() {
            return Ok(());
        }

        write!(f, " (")?;
        for (i, arg) in self.args.iter().enumerate() {
            if i > 0 {
                write!(f, ", ")?;
            }
            write!(f, "{}", arg)?;
        }
        write!(f, ")")
    }
}

#[derive(Debug)]
pub struct AppError {
    pub source: anyhow::Error,
    pub location: &'static Location<'static>,
    pub msg: ErrorContext,
}

impl AppError {
    #[track_caller]
    pub fn new(key: I18nKey, args: Vec<String>) -> Self {
        let location = Location::caller();
        let ctx = ErrorContext::new(key, args);

        let e = Self {
            source: anyhow::anyhow!("Logic Error"),
            location,
            msg: ctx,
        };

        logger::warn!("{:#}", e);

        e
    }
}

impl std::fmt::Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "\nError at {}:{} ",
            self.location.file(),
            self.location.line()
        )?;
        write!(f, "| {}", self.msg)?;

        write!(f, "\nCaused by:")?;
        for (i, cause) in self.source.chain().enumerate() {
            write!(f, "\n  {}: {:#}", i, cause)?;
        }
        Ok(())
    }
}

#[macro_export]
macro_rules! err_args {
    () => { Vec::<String>::new() };
    ($($arg:expr),+ $(,)?) => {
        vec![$( $arg.to_string() ),+]
    };
}

#[macro_export]
macro_rules! bail {
    ($key:expr, $args:expr) => {
        return Err($crate::error::AppError::new($key, $args))
    };
    ($key:expr) => {
        return Err($crate::error::AppError::new($key, Vec::new()))
    };
}

pub trait AppResultExt<T> {
    fn with_context(self, key: I18nKey, args: Vec<String>) -> Result<T, AppError>;

    fn with_context_key(self, key: I18nKey) -> Result<T, AppError>;
}

impl<T, E> AppResultExt<T> for Result<T, E>
where
    E: Into<anyhow::Error>,
{
    #[track_caller]
    fn with_context(self, key: I18nKey, args: Vec<String>) -> Result<T, AppError> {
        match self {
            Ok(v) => Ok(v),
            Err(e) => {
                let location = Location::caller();
                let source_err = e.into();

                let e = AppError {
                    source: source_err,
                    location,
                    msg: ErrorContext { key, args },
                };
                logger::warn!("{:#}", e);
                Err(e)
            }
        }
    }

    #[track_caller]
    fn with_context_key(self, key: I18nKey) -> Result<T, AppError> {
        self.with_context(key, Vec::new())
    }
}

macro_rules! impl_from_error {
    ($($error_type:ty => $i18n_key:ident),+ $(,)?) => {
        $(
            impl From<$error_type> for AppError {
                #[track_caller]
                fn from(error: $error_type) -> Self {
                    let location = Location::caller();

                    let e = AppError {
                        source: error.into(),
                        location,
                        msg: ErrorContext {
                            key: I18nKey::$i18n_key,
                            args: vec![],
                        },
                    };
                    logger::warn!("{:#}", e);
                    e
                }
            }
        )+
    };
}

impl_from_error! {
    tokio::task::JoinError => TaskExecutionFailed,
    url::ParseError => UrlParseError,
    reqwest::Error => NetworkRequestFailed,
    serde_json::Error => JsonParseError,
    glob::GlobError => IoError,
    glob::PatternError => IoError,
    time::error::Parse => TimeParseError,
    rusqlite::Error => DatabaseError,
}

impl From<std::io::Error> for AppError {
    #[track_caller]
    fn from(error: std::io::Error) -> Self {
        use std::io::ErrorKind;

        let key = match error.kind() {
            ErrorKind::NotFound => I18nKey::FileNotFound,
            ErrorKind::PermissionDenied => I18nKey::PermissionDenied,
            ErrorKind::AlreadyExists => I18nKey::FileAlreadyExists,
            _ => I18nKey::IoError,
        };

        let location = Location::caller();

        let e = AppError {
            source: error.into(),
            location,
            msg: ErrorContext { key, args: vec![] },
        };
        logger::warn!("{:#}", e);
        e
    }
}
