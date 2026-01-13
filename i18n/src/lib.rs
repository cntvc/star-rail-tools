include!(concat!(env!("OUT_DIR"), "/i18n_translations.rs"));

static mut S_LANGUAGE: Lang = Lang::zh_cn;

pub fn init(lang: Lang) {
    unsafe {
        S_LANGUAGE = lang;
    }
}

pub fn loc(id: I18nKey) -> &'static str {
    TRANSLATIONS[unsafe { S_LANGUAGE as usize }][id as usize]
}
