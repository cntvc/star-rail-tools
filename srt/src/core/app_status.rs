use crate::Result;
use crate::database::AppStatusRepo;
use crate::logger;

#[derive(Debug)]
enum AppStateItem {
    DefaultAccount,
}

impl From<AppStateItem> for &'static str {
    fn from(item: AppStateItem) -> Self {
        match item {
            AppStateItem::DefaultAccount => "DEFAULT_ACCOUNT",
        }
    }
}

pub struct AppStateService;

impl AppStateService {
    async fn get(item: AppStateItem) -> Result<Option<String>> {
        logger::info!("get app status: {:?}", item);
        tokio::task::spawn_blocking(move || AppStatusRepo::select(item.into())).await?
    }

    async fn set(item: AppStateItem, value: &str) -> Result<bool> {
        logger::info!("set app status: {:?} = {}", item, value);
        tokio::task::spawn_blocking({
            let val = value.to_string();
            move || AppStatusRepo::update(item.into(), &val)
        })
        .await?
    }

    async fn clear(item: AppStateItem) -> Result<bool> {
        logger::info!("set null: {:?}", item);
        tokio::task::spawn_blocking(move || AppStatusRepo::update_to_null(item.into())).await?
    }

    pub async fn get_default_uid() -> Result<Option<String>> {
        let default_uid = match AppStateService::get(AppStateItem::DefaultAccount).await? {
            Some(uid) => Ok(Some(uid)),
            None => Ok(None),
        };
        logger::info!("get default uid: {:?}", default_uid);
        default_uid
    }

    pub async fn set_default_uid(uid: &str) -> Result<()> {
        logger::info!("set default uid: {}", uid);

        AppStateService::set(AppStateItem::DefaultAccount, &uid.to_string()).await?;
        Ok(())
    }

    pub async fn clear_default_uid() -> Result<()> {
        logger::info!("reset default uid");
        AppStateService::clear(AppStateItem::DefaultAccount).await?;
        Ok(())
    }
}
