use std::ops::Deref;
use std::sync::LazyLock;

use regex::Regex;

use super::game_biz::GameBiz;
use crate::database::AccountRepo;
use crate::{Result, bail, logger};
use i18n::I18nKey;

static UID_RE: LazyLock<Regex> = LazyLock::new(|| Regex::new("^[1-9][0-9]{8}$").unwrap());

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AcountUid {
    inner: String,
}

impl AcountUid {
    pub fn new(uid: &str) -> Result<Self> {
        if !Self::is_valid(uid) {
            bail!(I18nKey::InvalidUidFormat);
        }
        Ok(Self {
            inner: uid.to_string(),
        })
    }

    pub fn is_valid(uid: &str) -> bool {
        UID_RE.is_match(uid)
    }
}

impl Deref for AcountUid {
    type Target = str;

    fn deref(&self) -> &str {
        &self.inner
    }
}

impl AsRef<str> for AcountUid {
    fn as_ref(&self) -> &str {
        &self.inner
    }
}

impl From<AcountUid> for String {
    fn from(value: AcountUid) -> Self {
        value.inner
    }
}

#[derive(Debug, Clone)]
pub struct Account {
    pub uid: AcountUid,
    pub game_biz: GameBiz,
    pub server_time_zone: i8,
}

impl Account {
    pub fn new(uid: &str) -> Result<Self> {
        if !AcountUid::is_valid(uid) {
            bail!(I18nKey::InvalidUidFormat);
        }
        let game_biz = GameBiz::from_uid(uid);
        let server_time_zone = Self::calc_server_time_zone(uid);
        Ok(Self {
            uid: AcountUid::new(uid)?,
            game_biz,
            server_time_zone,
        })
    }

    fn calc_server_time_zone(uid: &str) -> i8 {
        let first_number = uid.chars().nth(0).unwrap();

        // - 6 开头: UTC-5 (美服)
        // - 7 开头: UTC+1 (欧服)
        // - 其他: UTC+8 (亚服)
        match first_number {
            '6' => -5,
            '7' => 1,
            _ => 8,
        }
    }
}

pub struct AccountService;

impl AccountService {
    pub async fn register(uid: &str) -> Result<()> {
        logger::debug!("Registering account: {}", uid);
        if Self::is_registered(uid).await? {
            bail!(I18nKey::AccountAlreadyExists);
        } else {
            let uid = uid.to_string();
            tokio::task::spawn_blocking(move || AccountRepo::insert(&uid)).await??;
            Ok(())
        }
    }

    pub async fn unregister(uid: &str) -> Result<()> {
        logger::debug!("Unregistering account: {}", uid);
        if !Self::is_registered(uid).await? {
            bail!(I18nKey::AccountNotFound);
        }
        tokio::task::spawn_blocking({
            let uid = uid.to_string();
            move || AccountRepo::delete_all_data(&uid)
        })
        .await??;
        Ok(())
    }

    pub async fn is_registered(uid: &str) -> Result<bool> {
        logger::debug!("Checking if account exists: {}", uid);
        let uid = uid.to_string();
        let existing_account =
            tokio::task::spawn_blocking(move || AccountRepo::select_one(&uid)).await??;
        Ok(existing_account.is_some())
    }

    pub async fn get_all_uid_list() -> Result<Vec<String>> {
        logger::debug!("Getting all account UIDs");
        let account_list = tokio::task::spawn_blocking(AccountRepo::select_all).await??;
        Ok(account_list)
    }
}
