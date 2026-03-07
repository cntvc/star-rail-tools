use std::path::PathBuf;
use std::sync::{Arc, LazyLock};
use tokio::sync::Mutex;

use tokio::sync::mpsc::UnboundedSender;

use srt::{
    APP_PATH, AppConfig, Result,
    core::{
        AccountService, AppStateItem, AppStateService, GachaService, Metadata, MetadataService,
    },
    logger, updater,
};

use super::action::{
    AccountAction, Action, ExportAction, GachaAction, ImportAction, MetadataAction, SettingAction,
};
use crate::notification::NotificationType;

pub async fn sync_metadata(tx: UnboundedSender<Action>) -> Result<()> {
    MetadataService::sync_metadata().await?;
    let _ = tx.send(Action::Metadata(MetadataAction::SyncSuccess));
    Ok(())
}

pub async fn reload_metadata(tx: UnboundedSender<Action>) -> Result<()> {
    let metadata = MetadataService::load_metadata().await?;
    let _ = tx.send(Action::Metadata(MetadataAction::ReloadSuccess(metadata)));
    Ok(())
}

pub async fn update_sync_metadata_time(tx: UnboundedSender<Action>) -> Result<()> {
    let now_utc_timestamp = time::OffsetDateTime::now_utc().unix_timestamp();
    MetadataService::update_sync_metadata_time(now_utc_timestamp).await?;
    let _ = tx.send(Action::Metadata(MetadataAction::UpdateSyncTimeSuccess(
        now_utc_timestamp,
    )));
    Ok(())
}

static METADATA_SYNC_LOCK: LazyLock<Mutex<()>> = LazyLock::new(|| Mutex::new(()));

async fn force_sync_metadata(tx: UnboundedSender<Action>) -> Result<Arc<Metadata>> {
    logger::debug!("Waiting to acquire METADATA_SYNC_LOCK...");
    let _lock = METADATA_SYNC_LOCK.lock().await;
    logger::debug!("Acquired METADATA_SYNC_LOCK.");

    let now_utc_timestamp = time::OffsetDateTime::now_utc().unix_timestamp();

    // 防抖双重检查
    if let Ok(Some(last_sync)) = MetadataService::get_latest_sync_time().await
        && now_utc_timestamp - last_sync < 20
    {
        logger::info!("Metadata was recently synced by another task. Skipping.");
        let metadata = MetadataService::load_metadata().await?;
        return Ok(Arc::new(metadata));
    }

    logger::info!("Detected missing metadata during import, triggering sync...");

    MetadataService::sync_metadata().await?;
    MetadataService::update_sync_metadata_time(now_utc_timestamp).await?;

    let metadata = MetadataService::load_metadata().await?;
    let metadata_arc = Arc::new(metadata);

    let _ = tx.send(Action::Metadata(MetadataAction::UpdateSyncTimeSuccess(
        now_utc_timestamp,
    )));
    let _ = tx.send(Action::Metadata(MetadataAction::ReloadSuccess(
        (*metadata_arc).clone(),
    )));

    Ok(metadata_arc)
}

pub async fn register_account(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    AccountService::register(&uid).await?;
    let _ = tx.send(Action::Account(AccountAction::AddSuccess(uid)));
    Ok(())
}

pub async fn load_analysis(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    let analysis = GachaService::load_analysis(&uid).await?;
    let _ = tx.send(Action::Gacha(GachaAction::AnalysisLoaded(analysis)));
    Ok(())
}

pub async fn set_default_account(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    AppStateService::set(AppStateItem::DefaultAccount, &uid).await?;
    let _ = tx.send(Action::Account(AccountAction::LoginSuccess(uid)));
    Ok(())
}

pub async fn unregister_account(tx: UnboundedSender<Action>, uid: String) -> Result<()> {
    AccountService::unregister(&uid).await?;
    let _ = tx.send(Action::Account(AccountAction::DeleteSuccess));
    Ok(())
}

pub async fn refresh_gacha_records(
    tx: UnboundedSender<Action>,
    uid: String,
    fetch_all: bool,
    metadata: Arc<Metadata>,
) -> Result<()> {
    let count = GachaService::refresh_gacha_record(&uid, fetch_all).await?;
    let _ = tx.send(Action::Gacha(GachaAction::RefreshSuccess(count)));

    if count > 0 {
        let analysis = GachaService::update_analysis(&uid).await?;

        let mut missing_metadata = false;
        for (_, entity) in analysis.iter() {
            for pull in &entity.rank5 {
                if metadata.get(&pull.item_id).is_none() {
                    logger::warn!("Cache miss for item_id: {} in analysis list", pull.item_id);
                    missing_metadata = true;
                    break;
                }
            }
            if missing_metadata {
                break;
            }
        }

        if missing_metadata {
            force_sync_metadata(tx.clone()).await?;
        }

        let _ = tx.send(Action::Gacha(GachaAction::AnalysisLoaded(analysis)));
    }
    Ok(())
}

pub async fn save_config(tx: UnboundedSender<Action>, config: AppConfig) -> Result<()> {
    AppConfig::save_config(config).await?;
    let _ = tx.send(Action::Setting(SettingAction::SaveSuccess(config)));
    Ok(())
}

pub async fn check_update(tx: UnboundedSender<Action>) -> Result<()> {
    let latest_version = updater::get_latest_release_version().await?;
    let msg = match latest_version {
        Some(version) => {
            i18n::loc(i18n::I18nKey::NotifyNewVersionAvailable).replace("{0}", &version)
        }
        None => i18n::loc(i18n::I18nKey::NotifyAlreadyLatestVersion).to_string(),
    };

    let _ = tx.send(Action::Notify {
        message: msg,
        notification_type: NotificationType::Info,
    });
    Ok(())
}

pub async fn scan_import_file_list(tx: UnboundedSender<Action>) -> Result<()> {
    let files = GachaService::get_json_file_list(&APP_PATH.import_dir).await?;
    let _ = tx.send(Action::Import(ImportAction::ScanFileSuccess(files)));
    Ok(())
}

pub async fn import_gacha_record(
    tx: UnboundedSender<Action>,
    uid: String,
    file_path: PathBuf,
    metadata: Arc<Metadata>,
) -> Result<()> {
    let import_res = GachaService::import_record(&uid, &file_path, Arc::clone(&metadata)).await;

    let count = match import_res {
        Ok(c) => c,
        Err(e) => {
            if e.msg.key == i18n::I18nKey::MetadataItemNotFound
                || e.msg.key == i18n::I18nKey::MetadataNotAvailable
            {
                logger::warn!("Import failed due to missing metadata: {:?}", e.msg.key);
                let arc_metadata = force_sync_metadata(tx.clone()).await?;

                logger::info!("Retrying import record...");
                GachaService::import_record(&uid, &file_path, arc_metadata).await?
            } else {
                return Err(e);
            }
        }
    };

    let _ = tx.send(Action::Import(ImportAction::ImportSuccess(count)));
    if count > 0 {
        let analysis = GachaService::update_analysis(&uid).await?;
        let _ = tx.send(Action::Gacha(GachaAction::AnalysisLoaded(analysis)));
    }
    Ok(())
}

pub async fn export_gacha_record(
    tx: UnboundedSender<Action>,
    uid: String,
    lang: i18n::Lang,
    metadata: Arc<Metadata>,
) -> Result<()> {
    let export_dir = APP_PATH.root_dir.join(&uid);
    GachaService::export_to_uigf(&uid, &export_dir, lang, metadata).await?;
    let _ = tx.send(Action::Export(ExportAction::ExportSuccess));
    Ok(())
}
