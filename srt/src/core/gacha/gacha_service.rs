use std::collections::HashMap;
use std::path::Path;

use tracing::instrument;

use super::entity::{GachaAnalysisEntity, GachaAnalysisResult, GachaRecordEntity, Metadata};
use super::export_service::ExportService;
use super::fetcher::Fetcher;
use super::gacha_url::{UrlLocator, UrlValidator};
use super::import_service::ImportService;
use super::types::GachaType;

use crate::database::GachaRecordRepo;
use crate::{APP_NAME, APP_VERSION, Result, bail, logger};
use i18n::{I18nKey, Lang};

pub struct GachaService;

impl GachaService {
    #[instrument(level = "info", skip_all)]
    pub async fn refresh_gacha_record(uid: &str, fetch_all: bool) -> Result<usize> {
        logger::info!(
            "Refreshing gacha record. uid: {}, fetch_all: {}",
            uid,
            fetch_all
        );

        let url_raw = UrlLocator::extract_url_from_cache(uid)?;
        let url = url_raw.ok_or_else(|| crate::AppError::new(I18nKey::GachaUrlNotFound, vec![]))?;

        let gacha_url = UrlValidator::validate_and_normalize(url)?;
        let fetcher = Fetcher::new();
        let origin_uid = fetcher.fetch_uid(&gacha_url).await?;

        let origin_uid =
            origin_uid.ok_or_else(|| crate::AppError::new(I18nKey::GachaRecordIsEmpty, vec![]))?;

        logger::info!("Fetched UID: {}", origin_uid);

        if origin_uid != uid {
            bail!(I18nKey::GachaUidMismatch);
        }

        let stop_id = if fetch_all {
            None
        } else {
            tokio::task::spawn_blocking({
                let uid = uid.to_string();
                move || GachaRecordRepo::select_latest_gacha_id(&uid)
            })
            .await??
        };

        logger::debug!("latest gacha ID: {stop_id:?}");

        let records = fetcher.fetch_all_records(&gacha_url, &stop_id).await?;

        logger::info!("Fetched {} gacha records from API", records.len());

        if records.is_empty() {
            return Ok(0);
        }

        let record_entities: Vec<GachaRecordEntity> =
            records.into_iter().map(GachaRecordEntity::from).collect();

        let count = tokio::task::spawn_blocking({
            let source = format!("{APP_NAME}_{APP_VERSION}");
            let uid = uid.to_string();
            move || {
                GachaRecordRepo::insert_or_update_records(&uid, record_entities, &source, fetch_all)
            }
        })
        .await??;
        logger::info!("Saved {} new records to database", count);
        Ok(count)
    }

    #[instrument(level = "debug", skip_all)]
    async fn analyze_gacha_records(uid: &str) -> Result<GachaAnalysisResult> {
        logger::info!("Analyzing gacha record for {}", uid);

        let calc_current_pity_task = tokio::task::spawn_blocking({
            let uid = uid.to_string();
            move || GachaRecordRepo::calc_current_pity(&uid)
        });
        let calc_pull_history_task = tokio::task::spawn_blocking({
            let uid = uid.to_string();
            move || GachaRecordRepo::calc_pull_history(&uid)
        });
        let get_total_count_task = tokio::task::spawn_blocking({
            let uid = uid.to_string();
            move || GachaRecordRepo::calc_total_count(&uid)
        });
        let (current_pity_res, pull_history_res, total_count_res) = tokio::try_join!(
            calc_current_pity_task,
            calc_pull_history_task,
            get_total_count_task
        )?;

        let mut current_pity: HashMap<u8, _> = current_pity_res?.into_iter().collect();
        let mut pull_history: HashMap<u8, _> = pull_history_res?.into_iter().collect();
        let mut total_count: HashMap<u8, _> = total_count_res?.into_iter().collect();

        let analysis_map: GachaAnalysisResult = GachaType::as_array()
            .into_iter()
            .map(|gt| {
                let gacha_type = gt as u8;
                let entity = GachaAnalysisEntity {
                    uid: uid.to_string(),
                    gacha_type,
                    pity_count: current_pity.remove(&gacha_type).unwrap_or(0),
                    total_count: total_count.remove(&gacha_type).unwrap_or(0),
                    rank5: pull_history.remove(&gacha_type).unwrap_or_default(),
                };
                (gacha_type, entity)
            })
            .collect();
        Ok(analysis_map)
    }

    #[instrument(level = "debug", skip_all)]
    pub async fn update_analysis(uid: &str) -> Result<GachaAnalysisResult> {
        logger::info!("Refreshing gacha analysis for {}", uid);
        let analysis_result = Self::analyze_gacha_records(uid).await?;

        let analysis_result = tokio::task::spawn_blocking({
            let uid = uid.to_string();
            move || -> Result<_> {
                GachaRecordRepo::insert_or_update_analysis_result(&uid, &analysis_result)?;
                Ok(analysis_result)
            }
        })
        .await??;

        Ok(analysis_result)
    }

    #[instrument(level = "debug", skip_all)]
    pub async fn load_analysis(uid: &str) -> Result<GachaAnalysisResult> {
        logger::info!("Loading gacha analysis for {}", uid);
        let uid = uid.to_string();
        let analysis_result =
            tokio::task::spawn_blocking(move || GachaRecordRepo::select_analysis_result(&uid))
                .await??;
        Ok(analysis_result)
    }

    #[instrument(level = "info", skip_all)]
    pub async fn import_record(uid: &str, path: &Path, metadata: &Metadata) -> Result<usize> {
        ImportService::import_from_file(uid, path, metadata).await
    }

    #[instrument(level = "info", skip_all)]
    pub async fn export_to_uigf(
        uid: &str,
        dir: &Path,
        export_lang: &Lang,
        metadata: &Metadata,
    ) -> Result<()> {
        ExportService::export_to_uigf(uid, dir, export_lang, metadata).await
    }
}
