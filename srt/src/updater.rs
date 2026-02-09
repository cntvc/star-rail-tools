use crate::{APP_NAME, APP_VERSION, AppError, Result, bail, err_args, logger};
use i18n::I18nKey;

const GITHUB_RELEASE_API: &str =
    "https://api.github.com/repos/cntvc/star-rail-tools/releases?page=1&per_page=1";

pub async fn get_latest_release_version() -> Result<Option<String>> {
    logger::info!("Checking for updates from GitHub API");

    let http_client = reqwest::Client::new();
    let resp_result = http_client
        .get(GITHUB_RELEASE_API)
        .header(
            reqwest::header::USER_AGENT,
            format!("{APP_NAME}/{APP_VERSION}"),
        )
        .send()
        .await;

    let resp = match resp_result {
        Ok(r) => r.json::<serde_json::Value>().await?,
        Err(_) => bail!(I18nKey::CheckUpdateFailed),
    };

    if let Some(message) = resp.get("message").and_then(|v| v.as_str()) {
        bail!(I18nKey::CheckUpdateFailed, err_args!(message));
    }

    let tag_name = resp[0]["tag_name"].as_str().ok_or_else(|| {
        AppError::new(
            I18nKey::CheckUpdateFailed,
            err_args!("Invalid response format"),
        )
    })?;

    if APP_VERSION < tag_name {
        logger::info!(
            "New version available: {} (current: {})",
            tag_name,
            APP_VERSION
        );
        return Ok(Some(tag_name.to_string()));
    }

    logger::debug!("Already on latest version: {}", APP_VERSION);

    Ok(None)
}
