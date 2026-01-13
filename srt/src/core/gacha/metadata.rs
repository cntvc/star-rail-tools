use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use serde_with::{DisplayFromStr, serde_as};

use super::entity::Metadata;
use super::entity::{GachaMetadataEntity, MihoyoApiResponse};
use super::types::GachaItemType;
use crate::database::MetadataRepo;
use crate::{Result, logger};

#[serde_as]
#[derive(Debug, Serialize, Deserialize)]
struct GachaConfigApiItem {
    #[serde_as(as = "DisplayFromStr")]
    pub item_id: u32,

    #[serde_as(as = "DisplayFromStr")]
    pub rarity: u8,

    pub item_name: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct GachaConfigCnResp {
    pub avatar: Vec<GachaConfigApiItem>,
    pub equipment: Vec<GachaConfigApiItem>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GachaConfigGlobalResp {
    pub list: Vec<GachaConfigApiItem>,
}

enum MetadataItemType {
    Character,
    LightCone,
}

impl MetadataItemType {
    pub const fn as_str(&self) -> &'static str {
        match self {
            MetadataItemType::Character => "avatar",
            MetadataItemType::LightCone => "equipment",
        }
    }
}

pub struct MetadataApiClient {
    client: reqwest::Client,
}

impl MetadataApiClient {
    pub fn new() -> Result<Self> {
        let client = reqwest::Client::builder().build()?;
        Ok(Self { client })
    }

    #[tracing::instrument(level = "debug", skip(self))]
    pub async fn fetch_all_metadata(&self) -> Result<Vec<GachaMetadataEntity>> {
        let ((cn_character, cn_lightcone), en_character, en_lightcone) = tokio::try_join!(
            self.fetch_cn_metadata(),
            self.fetch_global_metadata(MetadataItemType::Character),
            self.fetch_global_metadata(MetadataItemType::LightCone)
        )?;

        let mut merged_list =
            Self::merge_metadata_items(cn_character, en_character, GachaItemType::Character);

        merged_list.extend(Self::merge_metadata_items(
            cn_lightcone,
            en_lightcone,
            GachaItemType::LightCone,
        ));

        Ok(merged_list)
    }

    async fn fetch_cn_metadata(
        &self,
    ) -> Result<(Vec<GachaConfigApiItem>, Vec<GachaConfigApiItem>)> {
        let url = "https://api-takumi.mihoyo.com/event/rpgsimulator/config?game=hkrpg";
        logger::info!("[GET] {}", url);

        let resp = self
            .client
            .get(url)
            .send()
            .await?
            .json::<MihoyoApiResponse<GachaConfigCnResp>>()
            .await?;

        let data = resp
            .into_result()?
            .ok_or_else(|| crate::AppError::new(i18n::I18nKey::MihoyoApiDataIsNone, vec![]))?;
        Ok((data.avatar, data.equipment))
    }

    async fn fetch_global_metadata(
        &self,
        fetch_type: MetadataItemType,
    ) -> Result<Vec<GachaConfigApiItem>> {
        let mut page = 1;
        let size = 100;
        let mut result = Vec::new();
        loop {
            let url = format!(
                "https://sg-public-api.hoyolab.com/event/rpgcalc/{}/list?game=hkrpg&lang={}&tab_from=TabAll&page={}&size={}",
                fetch_type.as_str(),
                "en-us",
                page,
                size
            );

            logger::info!("[GET] {}", url);

            let resp = self
                .client
                .get(url)
                .send()
                .await?
                .json::<MihoyoApiResponse<GachaConfigGlobalResp>>()
                .await?;
            let data = resp
                .into_result()?
                .ok_or_else(|| crate::AppError::new(i18n::I18nKey::MihoyoApiDataIsNone, vec![]))?;
            let is_last_page = data.list.len() < size;

            result.extend(data.list);

            if is_last_page {
                break;
            }

            page += 1;
        }
        Ok(result)
    }

    fn merge_metadata_items(
        cn_items: Vec<GachaConfigApiItem>,
        en_items: Vec<GachaConfigApiItem>,
        item_type: GachaItemType,
    ) -> Vec<GachaMetadataEntity> {
        let cn_map: HashMap<u32, String> = cn_items
            .into_iter()
            .map(|i| (i.item_id, i.item_name))
            .collect();
        en_items
            .into_iter()
            .map(|i| {
                let item_id = i.item_id;
                let mut names = HashMap::new();
                // en-us 数据可能比 zh-cn 条目多，因此条目不存在时，zh-cn 用默认值
                // 通常多出的条目是尚未实装的数据
                names.insert(
                    "zh-cn".to_string(),
                    cn_map.get(&item_id).cloned().unwrap_or_default(),
                );
                names.insert("en-us".to_string(), i.item_name);

                GachaMetadataEntity {
                    item_id: i.item_id,
                    item_type: item_type.as_str().to_string(),
                    rarity: i.rarity,
                    names,
                }
            })
            .collect()
    }
}

pub struct MetadataService;

impl MetadataService {
    /// 加载全量 metadata（包含所有语言）
    pub async fn load_metadata() -> Result<Metadata> {
        logger::info!("Loading full metadata");
        let res = tokio::task::spawn_blocking(MetadataRepo::select_all).await??;
        let metadata_map: Metadata = res.into_iter().map(|i| (i.item_id, i)).collect();
        Ok(metadata_map)
    }

    pub async fn sync_metadata() -> Result<()> {
        logger::info!("Syncing metadata from remote API");

        let api_client = MetadataApiClient::new()?;
        let metadata = api_client.fetch_all_metadata().await?;
        let cnt = tokio::task::spawn_blocking(move || MetadataRepo::insert(metadata)).await??;

        logger::info!("Synced {} metadata items", cnt);
        Ok(())
    }
}
