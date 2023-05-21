import enum
from collections import namedtuple
from typing import Dict, List, Union

__all__ = ["i18n", "set_locales", "LanguageType"]

"""语言包无法支持同级别既为字符串又有下级的情况
error eg:
{
    "como":"home",
    "como.next":"home next",
}
"""

from star_rail.i18n.en_us import en_us_lang_pack
from star_rail.i18n.zh_cn import zh_cn_lang_pack

_default_language = zh_cn_lang_pack


class LazyLanguagePack:
    _language_pack_cache = {}

    def __init__(self, raw_lang_pack: dict):
        self.raw_lang_pack = parse_lang_pack(raw_lang_pack)
        """原始语言包字典，多层级"""
        self._lang_pack = None
        """解析完成的语言包字典，可链式调用"""

    def _load_language_pack(self):
        language_pack = self._language_pack_cache.get(id(self.raw_lang_pack))
        if language_pack is None:
            language_pack = dict_to_namedtuple("LanguagePack", self.raw_lang_pack)
            self._language_pack_cache[id(self.raw_lang_pack)] = language_pack
        self._lang_pack = language_pack

    def set_language_pack(self, language_pack):
        self.raw_lang_pack = language_pack

    def __getattr__(self, name):
        self._load_language_pack()
        return getattr(self._lang_pack, name)

    def get_by_header(self, header: Union[str, List[str]]):
        """根据成员层级获取对象

        Args:
            header (Union[str, List[str]]): eg："a.b.c" | ["a", "b", "c"]

        Returns:
            obj: self.a.b.c
        """
        if isinstance(header, str):
            parts = header.split(".")
        else:
            parts = header

        cur_obj = self
        for attr in parts:
            cur_obj = getattr(cur_obj, attr)
        return cur_obj


class LanguageType(str, enum.Enum):
    ZH_CN = "zh_cn"
    EN_US = "en_us"


_lang_pack_dict: Dict[LanguageType, Dict] = {
    LanguageType.ZH_CN: zh_cn_lang_pack,
    LanguageType.EN_US: en_us_lang_pack,
}


def dict_to_namedtuple(name, dictionary):
    """
    将字典转换为命名元组
    """

    def convert_dict_to_namedtuple(name, d: dict):
        for key, value in d.items():
            if isinstance(value, dict):
                d[key] = convert_dict_to_namedtuple(key, value)
        return namedtuple(name, d.keys())(**d)

    return convert_dict_to_namedtuple(name, dictionary)


def parse_lang_pack(dictionary: Dict[str, str]) -> Dict[str, Dict]:
    """单层级字典->多层级

    {"a.b.c":"v"} -> {"a":{"b":{"c":"v"}}}
    """
    result = {}

    for key, value in dictionary.items():
        parts = key.split(".")
        current_dict = result

        for part in parts[:-1]:
            if part not in current_dict:
                current_dict[part] = {}
            # 将 current_dict 更新为当前级别字典
            current_dict = current_dict[part]
        # 循环结束，current_dict 为最后一级
        current_dict[parts[-1]] = value

    return result


i18n = LazyLanguagePack(_default_language)


def set_locales(lang_type: LanguageType):
    from star_rail.config import settings

    settings.set_and_save("LANGUAGE", lang_type.value)
    lang_pack = parse_lang_pack(_lang_pack_dict[lang_type])
    i18n.set_language_pack(lang_pack)
