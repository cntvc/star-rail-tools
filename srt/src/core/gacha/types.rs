#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[allow(clippy::enum_variant_names)]
pub enum GachaType {
    RegularWarp = 1,
    StarterWarp = 2,
    CharacterEventWarp = 11,
    CharacterCollaborationWarp = 21,
    LightConeEventWarp = 12,
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
            GachaType::RegularWarp,
            GachaType::CharacterEventWarp,
            GachaType::LightConeEventWarp,
            GachaType::CharacterCollaborationWarp,
            GachaType::LightConeCollaborationWarp,
            GachaType::StarterWarp,
        ]
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
