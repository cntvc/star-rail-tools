pub mod data_utils {
    use time::{PrimitiveDateTime, UtcOffset};

    use crate::Result;
    use crate::error::AppResultExt;
    use crate::{AppError, err_args};
    use i18n::I18nKey;

    pub fn now_offset_time(offset: i8) -> Result<String> {
        let format =
            time::macros::format_description!("[year]-[month]-[day] [hour]:[minute]:[second]");
        now_offset(offset)?
            .format(&format)
            .with_context_key(I18nKey::FailedToFormatTime)
    }

    pub fn now_offset(offset: i8) -> Result<time::OffsetDateTime> {
        let utc_offset = time::UtcOffset::from_hms(offset, 0, 0)
            .map_err(|_| AppError::new(I18nKey::InvalidTimeOffset, err_args!(offset)))?;

        Ok(time::OffsetDateTime::now_utc().to_offset(utc_offset))
    }

    pub fn convert_time_zone(time: &mut String, src_offset: i8, dst_offset: i8) -> Result<()> {
        let src_offset = UtcOffset::from_hms(src_offset, 0, 0)
            .map_err(|_| AppError::new(I18nKey::InvalidTimeOffset, err_args!(src_offset)))?;
        let dst_offset = UtcOffset::from_hms(dst_offset, 0, 0)
            .map_err(|_| AppError::new(I18nKey::InvalidTimeOffset, err_args!(dst_offset)))?;

        let format =
            time::macros::format_description!("[year]-[month]-[day] [hour]:[minute]:[second]");
        let naive_dt = PrimitiveDateTime::parse(time, &format)?;
        let datetime_in_src = naive_dt.assume_offset(src_offset);
        let datetime_in_dst = datetime_in_src.to_offset(dst_offset);
        *time = datetime_in_dst
            .format(&format)
            .with_context_key(I18nKey::FailedToFormatTime)?;
        Ok(())
    }
}
