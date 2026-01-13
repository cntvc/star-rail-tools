use std::path::Path;

use super::entity::{GachaRecordEntity, GachaRecordItem, Metadata};
use super::uigf::*;
use crate::core::Account;
use crate::database::GachaRecordRepo;
use crate::utils::data_utils;
use crate::{Result, bail, logger};
use i18n::I18nKey;

pub(super) struct ImportService;

#[derive(Debug)]
enum GachaFileFormat {
    Uigf,
    Srgf,
}

struct ImportData {
    uid: String,
    source: String,
    time_zone: i8,
    list: Vec<GachaRecordEntity>,
}

impl ImportService {
    pub async fn import_from_file(uid: &str, path: &Path, metadata: &Metadata) -> Result<usize> {
        logger::info!(
            "Importing gacha records for uid: {} from file: {}",
            uid,
            path.display()
        );

        if metadata.is_empty() {
            bail!(I18nKey::MetadataNotAvailable);
        }

        let content = tokio::fs::read_to_string(path).await?;

        let format = Self::detect_format(&content)?;
        logger::debug!("Detected format: {:?}", format);

        let data = match format {
            GachaFileFormat::Uigf => Self::parse_uigf(uid, &content, metadata)?,
            GachaFileFormat::Srgf => Self::parse_srgf(uid, &content, metadata)?,
        };

        let mut data = match data {
            Some(data) => data,
            None => {
                return Ok(0);
            }
        };

        logger::info!("Parsed {} records from file", data.list.len());

        Self::try_convert_time_zone(&mut data)?;

        let count = tokio::task::spawn_blocking(move || {
            GachaRecordRepo::insert_or_update_records(&data.uid, data.list, &data.source, false)
        })
        .await??;
        logger::info!("Imported {} new records to database", count);
        Ok(count)
    }

    fn detect_format(content: &str) -> Result<GachaFileFormat> {
        if content.contains("\"info\"") && content.contains("\"hkrpg\"") {
            return Ok(GachaFileFormat::Uigf);
        }

        if content.contains("\"info\"")
            && content.contains("\"srgf_version\"")
            && content.contains("\"list\"")
        {
            return Ok(GachaFileFormat::Srgf);
        }

        bail!(I18nKey::InvalidUIGFFormat);
    }

    fn parse_uigf(uid: &str, content: &str, metadata: &Metadata) -> Result<Option<ImportData>> {
        logger::debug!("Parsing UIGF format file");
        let uigf: Uigf = serde_json::from_str(content)?;
        for i in uigf.hkrpg {
            if i.uid != uid {
                continue;
            }

            if i.list.is_empty() {
                return Ok(None);
            }

            let source = format!("{}_{}", uigf.info.export_app, uigf.info.export_app_version);
            let list = Self::convert_to_entities(uid, &i.list, metadata)?;

            return Ok(Some(ImportData {
                uid: i.uid,
                source,
                time_zone: i.timezone,
                list,
            }));
        }

        bail!(I18nKey::GachaUidMismatch)
    }

    fn parse_srgf(uid: &str, content: &str, metadata: &Metadata) -> Result<Option<ImportData>> {
        logger::debug!("Parsing SRGF format file");
        let srgf: Srgf = serde_json::from_str(content)?;
        if uid != srgf.info.uid {
            bail!(I18nKey::GachaUidMismatch);
        }

        if srgf.list.is_empty() {
            return Ok(None);
        }

        let source = if srgf.info.export_app.is_empty() {
            "unknown".to_string()
        } else {
            format!("{}_{}", srgf.info.export_app, srgf.info.export_app_version)
        };
        let list = Self::convert_to_entities(uid, &srgf.list, metadata)?;

        Ok(Some(ImportData {
            uid: srgf.info.uid,
            source,
            time_zone: srgf.info.region_time_zone,
            list,
        }))
    }

    fn convert_to_entities(
        uid: &str,
        items: &[GachaRecordItem],
        metadata: &Metadata,
    ) -> Result<Vec<GachaRecordEntity>> {
        let mut result = Vec::with_capacity(items.len());
        for item in items {
            let rank_type = if item.rank_type == 0 {
                metadata
                    .get(&item.item_id)
                    .map(|m| m.rarity)
                    .ok_or_else(|| {
                        crate::AppError::new(
                            I18nKey::MetadataItemNotFound,
                            vec![item.item_id.to_string()],
                        )
                    })?
            } else {
                item.rank_type
            };

            result.push(GachaRecordEntity {
                id: item.id,
                uid: uid.to_string(),
                gacha_id: item.gacha_id,
                gacha_type: item.gacha_type,
                item_id: item.item_id,
                time: item.time.clone(),
                rank_type,
            });
        }
        Ok(result)
    }

    fn try_convert_time_zone(data: &mut ImportData) -> Result<()> {
        let user = Account::new(&data.uid)?;
        let target_time_zone = user.server_time_zone;
        if user.server_time_zone == data.time_zone {
            return Ok(());
        }

        for item in &mut data.list {
            data_utils::convert_time_zone(&mut item.time, data.time_zone, target_time_zone)?;
        }
        Ok(())
    }
}
