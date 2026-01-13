use crate::Result;
use crate::database::AppStatusRepo;
use crate::logger;

#[derive(Debug)]
pub enum AppStatusItem {
    DefaultAccount,
}

impl From<AppStatusItem> for &'static str {
    fn from(item: AppStatusItem) -> Self {
        match item {
            AppStatusItem::DefaultAccount => "DEFAULT_ACCOUNT",
        }
    }
}

struct AppStatusService;

impl AppStatusService {
    pub async fn get(item: AppStatusItem) -> Result<Option<String>> {
        logger::info!("get app status: {:?}", item);
        tokio::task::spawn_blocking(move || AppStatusRepo::select(item.into())).await?
    }

    pub async fn set(item: AppStatusItem, value: &str) -> Result<bool> {
        logger::info!("set app status: {:?} = {}", item, value);
        tokio::task::spawn_blocking({
            let val = value.to_string();
            move || AppStatusRepo::update(item.into(), &val)
        })
        .await?
    }

    pub async fn clear(item: AppStatusItem) -> Result<bool> {
        logger::info!("set null: {:?}", item);
        tokio::task::spawn_blocking(move || AppStatusRepo::update_to_null(item.into())).await?
    }
}

pub struct AppStatus;

impl AppStatus {
    pub async fn get_default_uid() -> Result<Option<String>> {
        let default_uid = match AppStatusService::get(AppStatusItem::DefaultAccount).await? {
            Some(uid) => Ok(Some(uid)),
            None => Ok(None),
        };
        logger::info!("get default uid: {:?}", default_uid);
        default_uid
    }

    pub async fn set_default_uid(uid: &str) -> Result<()> {
        logger::info!("set default uid: {}", uid);

        AppStatusService::set(AppStatusItem::DefaultAccount, &uid.to_string()).await?;
        Ok(())
    }

    pub async fn clear_default_uid() -> Result<()> {
        logger::info!("reset default uid");
        AppStatusService::clear(AppStatusItem::DefaultAccount).await?;
        Ok(())
    }
}
