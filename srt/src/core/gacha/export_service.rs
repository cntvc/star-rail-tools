use std::path::Path;

use super::entity::{GachaRecordItem, Metadata};
use super::types::GachaItemType;
use super::uigf::*;
use crate::core::Account;
use crate::database::GachaRecordRepo;
use crate::utils::data_utils;
use crate::{APP_NAME, APP_VERSION, Result, logger};
use i18n::{I18nKey, Lang};

pub(super) struct ExportService;

impl ExportService {
    pub async fn export_to_uigf(
        uid: &str,
        dir: &Path,
        export_lang: &Lang,
        metadata: &Metadata,
    ) -> Result<()> {
        logger::info!(
            "Exporting gacha record for {} with lang {}",
            uid,
            export_lang.as_str()
        );
        let user = Account::new(uid)?;
        let records = {
            let uid = uid.to_string();
            tokio::task::spawn_blocking(move || GachaRecordRepo::select_all(&uid)).await??
        };

        let info = UigfInfo {
            export_time: data_utils::now_offset_time(user.server_time_zone)?,
            export_timestamp: data_utils::now_offset(user.server_time_zone)?.unix_timestamp()
                as u64,
            export_app: APP_NAME.to_string(),
            export_app_version: APP_VERSION.to_string(),
            version: UIGF_VERSION.to_string(),
        };

        let export_records: Vec<GachaRecordItem> = records
            .iter()
            .map(|r| {
                let meta = metadata.get(&r.item_id).ok_or_else(|| {
                    crate::AppError::new(I18nKey::MetadataItemNotFound, vec![r.item_id.to_string()])
                })?;

                Ok(GachaRecordItem {
                    id: r.id,
                    uid: r.uid.clone(),
                    gacha_id: r.gacha_id,
                    gacha_type: r.gacha_type,
                    item_id: r.item_id,
                    time: r.time.clone(),
                    count: 1,
                    rank_type: r.rank_type,
                    // 上面校验过 Metadata 必定存在
                    name: meta.names.get(export_lang.as_str()).cloned().unwrap(),
                    item_type: match GachaItemType::from_str(&meta.item_type) {
                        GachaItemType::Character => i18n::loc(I18nKey::GachaItemTypeCharacter),
                        GachaItemType::LightCone => i18n::loc(I18nKey::GachaItemTypeLightCone),
                    }
                    .to_string(),
                    lang: export_lang.as_str().to_string(),
                })
            })
            .collect::<Result<Vec<_>>>()?;

        let data = UigfGameData {
            uid: uid.to_string(),
            timezone: user.server_time_zone,
            lang: export_lang.as_str().to_string(),
            list: export_records,
        };

        let uigf = Uigf {
            info,
            hkrpg: vec![data],
        };

        let json_data = serde_json::to_string_pretty(&uigf)?;

        let path = dir.join(format!("GachaRecord_UIGF_{uid}.json"));
        std::fs::create_dir_all(dir)?;
        std::fs::write(path, json_data)?;
        Ok(())
    }
}
