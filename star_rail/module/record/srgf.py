import typing

from star_rail.module.mihoyo.types import Region

from .model import GachaItem, GachaRecordInfo, SRGFData, SRGFInfo, SRGFRecordItem


def convert_to_gacha_record(
    data: SRGFData,
) -> typing.Tuple[GachaRecordInfo, typing.List[GachaItem]]:
    record_info = GachaRecordInfo(
        uid=data.info.uid,
        lang=data.info.lang,
        region=Region.get_by_uid(data.info.uid).value,
        region_time_zone=data.info.region_time_zone,
    )
    item_list = [
        GachaItem(uid=record_info.uid, lang=record_info.lang, **item.model_dump())
        for item in data.list
    ]

    return record_info, sorted(item_list, key=lambda item: item.id)


def convert_to_srgf(info: GachaRecordInfo, data: typing.List[GachaItem]):
    srgf_info = SRGFInfo.gen(info.uid, lang=info.lang, region_time_zone=info.region_time_zone)
    srgf_list = [SRGFRecordItem(**item.model_dump()) for item in data]
    return SRGFData(info=srgf_info, list=srgf_list)
