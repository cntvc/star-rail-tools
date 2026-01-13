use std::str::FromStr;

#[derive(Debug, PartialEq, Clone)]
#[allow(clippy::upper_case_acronyms)]
pub enum GameBiz {
    GLOBAL,
    CN,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseGameBizError(pub String);

impl std::fmt::Display for ParseGameBizError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Invalid game_biz parameter: {}", self.0)
    }
}

impl std::error::Error for ParseGameBizError {}

impl FromStr for GameBiz {
    type Err = ParseGameBizError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "hkrpg_global" => Ok(GameBiz::GLOBAL),
            "hkrpg_cn" => Ok(GameBiz::CN),
            _ => Err(ParseGameBizError(s.to_string())),
        }
    }
}

impl GameBiz {
    pub fn from_uid(uid: &str) -> Self {
        let first_number = uid.chars().nth(0).unwrap();
        match first_number {
            '1'..='5' => GameBiz::CN,
            '6'..='9' => GameBiz::GLOBAL,
            _ => unreachable!("Invalid UID format: {}", uid),
        }
    }
}
