#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[allow(clippy::enum_variant_names)]
pub enum GachaType {
    /// 常驻跃迁
    RegularWarp = 1,
    /// 始发跃迁
    StarterWarp = 2,
    /// 角色活动跃迁
    CharacterEventWarp = 11,
    /// 角色联动跃迁
    CharacterCollaborationWarp = 21,
    /// 光锥活动跃迁
    LightConeEventWarp = 12,
    /// 光锥联动跃迁
    LightConeCollaborationWarp = 22,
}

impl GachaType {
    #[inline]
    pub const fn as_str(&self) -> &'static str {
        match *self as u8 {
            1 => "1",
            2 => "2",
            11 => "11",
            12 => "12",
            21 => "21",
            22 => "22",
            _ => unreachable!(),
        }
    }

    pub const fn as_array() -> [GachaType; 6] {
        [
            GachaType::CharacterEventWarp,
            GachaType::LightConeEventWarp,
            GachaType::RegularWarp,
            GachaType::CharacterCollaborationWarp,
            GachaType::LightConeCollaborationWarp,
            GachaType::StarterWarp,
        ]
    }

    pub const fn name(&self) -> &'static str {
        match *self as u8 {
            1 => "RegularWarp",
            2 => "StarterWarp",
            11 => "CharacterEventWarp",
            12 => "LightConeEventWarp",
            21 => "CharacterCollaborationWarp",
            22 => "LightConeCollaborationWarp",
            _ => unreachable!(),
        }
    }
}

pub enum GachaItemType {
    Character,
    LightCone,
}

impl GachaItemType {
    pub const fn as_str(&self) -> &'static str {
        match self {
            GachaItemType::Character => "character",
            GachaItemType::LightCone => "lightcone",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s {
            "character" => GachaItemType::Character,
            "lightcone" => GachaItemType::LightCone,
            _ => unreachable!("Invalid gacha item type: {}", s),
        }
    }
}
