use crate::Result;
use crate::database::AppStatusRepo;
use crate::logger;

#[derive(Debug)]
pub enum AppStateItem {
    DefaultAccount,
    LatestMetadataSyncTime,
}

impl From<AppStateItem> for &'static str {
    fn from(item: AppStateItem) -> Self {
        match item {
            AppStateItem::DefaultAccount => "DEFAULT_ACCOUNT",
            AppStateItem::LatestMetadataSyncTime => "LATEST_METADATA_SYNC_TIME",
        }
    }
}

pub trait FromAppStateValue: Sized {
    fn from_state_value(value: String) -> crate::Result<Self>;
}

impl FromAppStateValue for String {
    fn from_state_value(value: String) -> crate::Result<Self> {
        Ok(value)
    }
}

impl FromAppStateValue for i64 {
    fn from_state_value(value: String) -> crate::Result<Self> {
        value.parse::<i64>().map_err(|e| {
            crate::error::AppError::new(
                i18n::I18nKey::DatabaseError,
                vec![format!("Failed to parse i64: {}", e)],
            )
        })
    }
}

pub struct AppStateService;

impl AppStateService {
    pub async fn get<T>(item: AppStateItem) -> Result<Option<T>>
    where
        T: FromAppStateValue + Send + 'static,
    {
        logger::info!("get app status: {:?}", item);
        match tokio::task::spawn_blocking(move || AppStatusRepo::select(item.into())).await?? {
            Some(v) => Ok(Some(v)),
            None => Ok(None),
        }
    }

    pub async fn set<T: ToString>(item: AppStateItem, value: T) -> Result<bool> {
        let val = value.to_string();
        logger::info!("set app status: {:?} = {}", item, val);
        tokio::task::spawn_blocking(move || AppStatusRepo::update(item.into(), &val)).await?
    }
}
