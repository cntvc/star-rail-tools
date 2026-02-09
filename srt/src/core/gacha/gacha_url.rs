use std::{
    io::Read,
    path::{Path, PathBuf},
    str::FromStr,
    sync::LazyLock,
};

use regex::Regex;
use url::Url;

use crate::error::AppResultExt;
use crate::{APP_PATH, Result, bail, core::Account, core::game_biz::GameBiz, logger};
use i18n::I18nKey;

static GAME_PATH_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new("([A-Z]:/.+StarRail_Data)").unwrap());

static GACHA_URL_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new("https://.+?&auth_appid=webview_gacha&.+?authkey=.+?&game_biz=hkrpg_(?:cn|global)")
        .unwrap()
});

/// A validated and normalized Gacha URL.
///
/// This type guarantees that the URL has been validated and contains all required parameters.
/// It can be dereferenced to `&Url` for convenient access to URL methods.
#[derive(Clone, Debug)]
pub struct UrlValidator;

impl UrlValidator {
    const REQUIRED_PARAMS: [&'static str; 4] = ["authkey", "lang", "game_biz", "authkey_ver"];
    const URL_HOST_CN: &'static str = "https://public-operation-hkrpg.mihoyo.com/";
    const URL_HOST_GLOBAL: &'static str = "https://public-operation-hkrpg-sg.hoyoverse.com/";

    /// Validates and normalizes a Gacha URL.
    ///
    /// This method validates that all required parameters are present,
    /// normalizes the URL structure, and sets the correct host based on game_biz.
    pub fn validate_and_normalize(url: String) -> Result<Url> {
        logger::info!("Validating and normalizing Gacha URL");
        logger::debug!("raw url: {}", url);

        let url = Url::parse(&url)?;
        let required_params = url
            .query_pairs()
            .filter(|(key, _)| Self::REQUIRED_PARAMS.contains(&key.as_ref()))
            .map(|(key, value)| (key.to_string(), value.to_string()))
            .collect::<std::collections::HashMap<_, _>>();

        let missing_params: Vec<String> = Self::REQUIRED_PARAMS
            .iter()
            .filter(|k| !required_params.contains_key(**k))
            .map(|s| s.to_string())
            .collect();

        if !missing_params.is_empty() {
            bail!(I18nKey::UrlMissingRequiredParameters, missing_params);
        }

        let game_biz = GameBiz::from_str(&required_params.get("game_biz").unwrap().to_lowercase())
            .with_context_key(I18nKey::InvalidGameBizParameter)?;
        let host = match game_biz {
            GameBiz::CN => Self::URL_HOST_CN,
            GameBiz::GLOBAL => Self::URL_HOST_GLOBAL,
        };
        let mut new_url = Url::parse(host)?;
        new_url.query_pairs_mut().extend_pairs(required_params);

        logger::debug!("validated url: {}", new_url);

        Ok(new_url)
    }
}

pub struct UrlLocator;

impl UrlLocator {
    const LOG_PATH_CN: &'static str = "miHoYo/崩坏：星穹铁道/";

    const LOG_PATH_GLOBAL: &'static str = "Cognosphere/Star Rail/";

    fn resolve_log_path(uid: &str) -> Result<PathBuf> {
        logger::debug!("get log path");
        let user_home = std::env::var("USERPROFILE").unwrap();
        let user = Account::new(uid)?;
        let dir_name = match user.game_biz {
            GameBiz::CN => Self::LOG_PATH_CN,
            GameBiz::GLOBAL => Self::LOG_PATH_GLOBAL,
        };
        Ok(PathBuf::from(user_home)
            .join("AppData")
            .join("LocalLow")
            .join(dir_name)
            .join("Player.log"))
    }

    fn parse_game_path(log_path: &PathBuf) -> Result<String> {
        logger::debug!("parse game path");
        if !log_path.exists() {
            bail!(I18nKey::GameLogFileNotFound);
        }
        let content = std::fs::read_to_string(log_path)?;
        match GAME_PATH_RE.captures(&content) {
            Some(cap) => {
                let game_path = cap
                    .get(1)
                    .expect("Regex capture group 1 should always exist")
                    .as_str();
                Ok(game_path.to_string())
            }
            None => bail!(I18nKey::GameInstallPathNotFound),
        }
    }

    fn find_latest_cache_file(cache_dir: &Path) -> Result<PathBuf> {
        logger::debug!("get latest cache file");

        let mut results = Vec::new();

        for entry in std::fs::read_dir(cache_dir)? {
            let entry = entry?;
            if entry.file_type()?.is_dir() {
                let cache_file = entry.path().join("Cache").join("Cache_Data").join("data_2");

                if cache_file.exists() && cache_file.is_file() {
                    results.push(cache_file);
                }
            }
        }

        results.sort_by_key(|pf| {
            std::fs::metadata(pf)
                .and_then(|m| m.created())
                .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
        });

        match results.last() {
            Some(pf) => Ok(pf.to_path_buf()),
            None => bail!(I18nKey::GameCacheFileNotFound),
        }
    }

    fn parse_cache_file(cache_file: &PathBuf) -> Result<Option<String>> {
        logger::debug!("parse cache file");
        let tmp_file_path = APP_PATH.cache_dir.join("data.tmp");

        std::fs::copy(cache_file, &tmp_file_path)?;

        let mut file = std::fs::File::open(&tmp_file_path)?;
        let mut buf = Vec::new();
        file.read_to_end(&mut buf)?;

        std::fs::remove_file(tmp_file_path)?;

        let content = String::from_utf8_lossy(&buf);

        let latest_url = GACHA_URL_RE
            .find_iter(&content)
            .last()
            .map(|m| m.as_str().to_string());

        Ok(latest_url)
    }

    pub fn extract_url_from_cache(uid: &str) -> Result<Option<String>> {
        logger::info!("extracting gacha url from cache");
        let log_path = Self::resolve_log_path(uid)?;
        let game_data_path = Self::parse_game_path(&log_path)?;

        let cache_dir = PathBuf::from(&game_data_path).join("webCaches");
        let cache_file = Self::find_latest_cache_file(&cache_dir)?;

        let url = Self::parse_cache_file(&cache_file)?;
        Ok(url)
    }
}
