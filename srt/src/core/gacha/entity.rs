use std::collections::HashMap;
use std::ops::{Deref, DerefMut};

use serde::{Deserialize, Serialize};
use serde_with::{DisplayFromStr, serde_as};

use crate::Result;
use crate::database::FromRow;
use crate::{bail, err_args};
use i18n::I18nKey;

#[serde_as]
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GachaRecordItem {
    #[serde_as(as = "DisplayFromStr")]
    pub gacha_id: u32,

    #[serde_as(as = "DisplayFromStr")]
    pub gacha_type: u8,

    #[serde_as(as = "DisplayFromStr")]
    pub item_id: u32,

    pub time: String,

    #[serde_as(as = "DisplayFromStr")]
    pub id: i64,

    #[serde(default)]
    #[serde_as(as = "DisplayFromStr")]
    pub count: u8,

    #[serde(default)]
    pub name: String,

    #[serde(default)]
    #[serde_as(as = "DisplayFromStr")]
    pub rank_type: u8,

    #[serde(default)]
    pub uid: String,

    #[serde(default)]
    pub lang: String,

    #[serde(default)]
    pub item_type: String,
}

#[derive(Debug, FromRow, Clone)]
pub struct GachaRecordEntity {
    pub id: i64,
    pub uid: String,
    pub gacha_id: u32,
    pub gacha_type: u8,
    pub item_id: u32,
    pub time: String,
    pub rank_type: u8,
}

/// Consumes the `GachaRecordItem` and converts it into a `GachaRecordEntity`.
///
/// This is a zero-copy conversion that transfers ownership of `String` fields
/// (`uid` and `time`), making it efficient for processing large batches of records.
impl From<GachaRecordItem> for GachaRecordEntity {
    fn from(item: GachaRecordItem) -> Self {
        Self {
            id: item.id,
            uid: item.uid,
            gacha_id: item.gacha_id,
            gacha_type: item.gacha_type,
            item_id: item.item_id,
            time: item.time,
            rank_type: item.rank_type,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MihoyoApiResponse<T> {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
    pub retcode: i32,
    pub message: String,
}

impl<T> MihoyoApiResponse<T> {
    pub fn into_result(self) -> Result<Option<T>> {
        if self.retcode == 0 {
            return Ok(self.data);
        }

        let key = match self.retcode {
            -108 => I18nKey::MihoyoApiInvalidLanguage,
            -101 => I18nKey::MihoyoApiAuthkeyExpired,
            -100 => I18nKey::MihoyoApiInvalidAuthkey,
            -110 => I18nKey::MihoyoApiRequestTooFrequent,
            -111 => I18nKey::MihoyoApiInvalidGameBiz,
            _ => I18nKey::MihoyoApiUnknownError,
        };

        bail!(key, err_args!(self.retcode, self.message))
    }
}

#[allow(unused)]
#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct GachaUpdateLogEntity {
    pub batch_id: u32,
    pub uid: String,
    pub time: String,
    pub source: String,
}

#[derive(Debug, Serialize, Deserialize, FromRow, Clone)]
pub struct GachaPullInfoEntity {
    pub gacha_type: u8,
    pub id: i64,
    pub item_id: u32,
    pub time: String,
    pub pull_index: u8,
}

#[derive(Debug, Serialize, Deserialize, Default, Clone)]
pub struct GachaAnalysisEntity {
    pub uid: String,
    pub gacha_type: u8,
    pub pity_count: u8,
    pub total_count: u32,
    pub rank5: Vec<GachaPullInfoEntity>,
}

impl FromRow for GachaAnalysisEntity {
    fn from_row(row: &rusqlite::Row) -> rusqlite::Result<Self> {
        let rank5_json: String = row.get("rank5")?;
        let rank5: Vec<GachaPullInfoEntity> = serde_json::from_str(&rank5_json).map_err(|e| {
            rusqlite::Error::FromSqlConversionFailure(
                rank5_json.len(),
                rusqlite::types::Type::Text,
                Box::new(e),
            )
        })?;

        Ok(GachaAnalysisEntity {
            uid: row.get("uid")?,
            gacha_type: row.get("gacha_type")?,
            pity_count: row.get("pity_count")?,
            total_count: row.get("total_count")?,
            rank5,
        })
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GachaMetadataEntity {
    pub item_id: u32,
    pub rarity: u8,
    pub item_type: String,
    /// HashMap: lang -> item_name
    pub names: HashMap<String, String>,
}

impl FromRow for GachaMetadataEntity {
    fn from_row(row: &rusqlite::Row) -> rusqlite::Result<Self> {
        let names_json: String = row.get("names")?;
        let names: HashMap<String, String> = serde_json::from_str(&names_json).map_err(|e| {
            rusqlite::Error::FromSqlConversionFailure(
                names_json.len(),
                rusqlite::types::Type::Text,
                Box::new(e),
            )
        })?;

        Ok(GachaMetadataEntity {
            item_id: row.get("item_id")?,
            rarity: row.get("rarity")?,
            item_type: row.get("item_type")?,
            names,
        })
    }
}

#[derive(Default)]
pub struct Metadata {
    inner: HashMap<u32, GachaMetadataEntity>,
}

impl Metadata {
    pub fn get_item_name(&self, item_id: u32, lang: &str) -> Option<&String> {
        self.inner
            .get(&item_id)
            .and_then(|entity| entity.names.get(lang))
    }
}

impl Deref for Metadata {
    type Target = HashMap<u32, GachaMetadataEntity>;

    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

impl DerefMut for Metadata {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.inner
    }
}

impl FromIterator<(u32, GachaMetadataEntity)> for Metadata {
    fn from_iter<I: IntoIterator<Item = (u32, GachaMetadataEntity)>>(iter: I) -> Self {
        Self {
            inner: iter.into_iter().collect(),
        }
    }
}

#[derive(Default)]
pub struct GachaAnalysisResult {
    inner: HashMap<u8, GachaAnalysisEntity>,
}

impl GachaAnalysisResult {
    pub fn new(data: HashMap<u8, GachaAnalysisEntity>) -> Self {
        Self { inner: data }
    }
}

impl Deref for GachaAnalysisResult {
    type Target = HashMap<u8, GachaAnalysisEntity>;

    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

impl DerefMut for GachaAnalysisResult {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.inner
    }
}

impl FromIterator<(u8, GachaAnalysisEntity)> for GachaAnalysisResult {
    fn from_iter<I: IntoIterator<Item = (u8, GachaAnalysisEntity)>>(iter: I) -> Self {
        Self {
            inner: iter.into_iter().collect(),
        }
    }
}
