include!(concat!(env!("OUT_DIR"), "/i18n_translations.rs"));

static mut S_LANGUAGE: Lang = Lang::zh_cn;

pub fn set_lang(lang: Lang) {
    unsafe {
        S_LANGUAGE = lang;
    }
}

pub fn loc(id: I18nKey) -> &'static str {
    TRANSLATIONS[unsafe { S_LANGUAGE as usize }][id as usize]
}

pub fn lang() -> &'static str {
    unsafe { S_LANGUAGE }.as_str()
}
