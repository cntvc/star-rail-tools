use serde::{Deserialize, Serialize};

use super::entity::GachaRecordItem;

pub const UIGF_VERSION: &str = "v4.1";

#[derive(Debug, Serialize, Deserialize)]
pub struct UigfInfo {
    #[serde(default)]
    pub export_time: String,
    pub export_timestamp: u64,
    pub export_app: String,
    pub export_app_version: String,
    /// UIGF Version. format: `v{major}.{minor}` (e.g., "v4.0")
    pub version: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UigfGameData {
    pub uid: String,
    pub timezone: i8,
    #[serde(default)]
    pub lang: String,
    pub list: Vec<GachaRecordItem>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Uigf {
    pub info: UigfInfo,
    pub hkrpg: Vec<UigfGameData>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SrgfInfo {
    pub uid: String,
    pub lang: String,
    pub region_time_zone: i8,
    #[serde(default)]
    pub export_timestamp: u64,
    #[serde(default)]
    pub export_app: String,
    #[serde(default)]
    pub export_app_version: String,
    pub srgf_version: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Srgf {
    pub info: SrgfInfo,
    pub list: Vec<GachaRecordItem>,
}
