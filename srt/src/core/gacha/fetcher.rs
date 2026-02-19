use std::time::Duration;

use serde::{Deserialize, Serialize};
use serde_with::{DisplayFromStr, serde_as};
use tokio::time;
use url::Url;

use super::entity::{GachaRecordItem, MihoyoApiResponse};
use super::types::GachaType;
use crate::{Result, logger};

#[serde_as]
#[derive(Debug, Serialize, Deserialize)]
struct GachaRecordData {
    #[serde_as(as = "DisplayFromStr")]
    pub page: u8,

    #[serde_as(as = "DisplayFromStr")]
    pub size: u8,

    pub list: Vec<GachaRecordItem>,

    pub region: String,

    pub region_time_zone: i8,
}

pub struct Fetcher {
    http_client: reqwest::Client,
}

impl Fetcher {
    const COLLABORATION_WARP_PATH: &'static str = "common/gacha_record/api/getLdGachaLog";

    const WAPR_PATH: &'static str = "common/gacha_record/api/getGachaLog";

    const DEFAULT_PAGE_SIZE: usize = 20;

    pub fn new() -> Self {
        let http_client = reqwest::Client::builder().build().unwrap();
        Self { http_client }
    }

    async fn fetch_page_by_type(
        &self,
        url: &Url,
        gacha_type: &GachaType,
        size: usize,
        end_id: i64,
    ) -> Result<MihoyoApiResponse<GachaRecordData>> {
        let path = match gacha_type {
            GachaType::CharacterCollaborationWarp => Self::COLLABORATION_WARP_PATH,
            GachaType::LightConeCollaborationWarp => Self::COLLABORATION_WARP_PATH,
            _ => Self::WAPR_PATH,
        };
        // 防止请求过于频繁
        time::sleep(Duration::from_millis(200)).await;

        let mut url = url.clone();
        url.set_path(path);
        url.query_pairs_mut()
            .append_pair("size", size.to_string().as_str())
            .append_pair("gacha_type", gacha_type.as_str())
            .append_pair("end_id", end_id.to_string().as_str());

        logger::info!("[GET]: {}", url);

        let resp = self
            .http_client
            .get(url.as_str())
            .send()
            .await?
            .json::<MihoyoApiResponse<GachaRecordData>>()
            .await?;

        Ok(resp)
    }

    pub async fn fetch_uid(&self, url: &Url) -> Result<Option<String>> {
        logger::info!("Fetching UID from URL");

        for gacha_type in &GachaType::as_array() {
            let resp = self
                .fetch_page_by_type(url, gacha_type, 1, 0)
                .await?
                .into_result()?;

            match resp {
                None => {
                    continue;
                }
                Some(data) => {
                    if !data.list.is_empty() {
                        return Ok(Some(data.list[0].uid.clone()));
                    }
                }
            }
        }
        Ok(None)
    }

    pub async fn fetch_all_records(
        &self,
        url: &Url,
        stop_id: &Option<i64>,
    ) -> Result<Vec<GachaRecordItem>> {
        logger::info!("Fetching Gacha Record from URL");
        let mut records: Vec<GachaRecordItem> = Vec::new();

        for gacha_type in &GachaType::as_array() {
            let mut end_id: i64 = 0;
            loop {
                let resp = self
                    .fetch_page_by_type(url, gacha_type, Self::DEFAULT_PAGE_SIZE, end_id)
                    .await?
                    .into_result()?;

                let data = match resp {
                    None => {
                        break;
                    }
                    Some(data) => data,
                };

                let page_size = data.list.len();

                records.extend(data.list);

                if page_size < Self::DEFAULT_PAGE_SIZE {
                    break;
                }
                // 此处已确认 records 不为空
                let latest_item = records.last().unwrap();

                if let Some(stop) = stop_id
                    && latest_item.id <= *stop
                {
                    break;
                }

                end_id = latest_item.id;
            }
        }
        Ok(records)
    }
}
