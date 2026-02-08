use std::collections::HashMap;

use db_helper::FromRow;
use rusqlite::{OptionalExtension, params};
use tracing::instrument;

use crate::core::{
    GachaAnalysisEntity, GachaAnalysisResult, GachaPullInfoEntity, GachaRecordEntity, GachaType,
};
use crate::database::DatabaseService;
use crate::{Result, logger};

#[instrument(level = "debug", skip_all)]
pub fn insert_or_update_records(
    uid: &str,
    gacha_records: Vec<GachaRecordEntity>,
    source: &str,
    replace: bool,
) -> Result<usize> {
    logger::debug!(
        "Saving or updating {} records for user: {}, source: {}, replace: {}",
        gacha_records.len(),
        uid,
        source,
        replace
    );

    if gacha_records.is_empty() {
        return Ok(0);
    }

    let mut conn = DatabaseService::connection()?;
    let tx = conn.transaction()?;

    {
        let mut stmt = tx.prepare(
            "INSERT INTO gacha_update_log (uid, time, source)
                VALUES (?1, strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'), ?2);",
        )?;
        stmt.execute(params![uid, source])?;
    }
    let batch_id = tx.last_insert_rowid() as u32;

    let insert_opt = match replace {
        true => "INSERT OR REPLACE",
        false => "INSERT OR IGNORE",
    };
    let sql = format!(
        "{insert_opt} INTO gacha_record (id, batch_id, uid, gacha_id, gacha_type, item_id, time, rank_type)
        VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8);",
    );

    let mut new_record_count = 0;
    {
        let mut stmt = tx.prepare(&sql)?;
        for record in &gacha_records {
            let count = stmt.execute(params![
                record.id,
                batch_id,
                record.uid,
                record.gacha_id,
                record.gacha_type,
                record.item_id,
                record.time,
                record.rank_type
            ])?;
            new_record_count += count;
        }
    }

    if new_record_count == 0 {
        tx.rollback()?;
        return Ok(0);
    }

    tx.commit()?;
    logger::debug!("Saved {} new records", new_record_count);
    Ok(new_record_count)
}

#[instrument(level = "debug", skip_all)]
pub fn select_latest_gacha_id(uid: &str) -> Result<Option<i64>> {
    logger::debug!("Querying latest gacha id for user: {}", uid);
    let db = DatabaseService::connection()?;
    let mut stmt =
        db.prepare("SELECT id FROM gacha_record WHERE uid = ?1 ORDER BY id DESC LIMIT 1;")?;
    let result = stmt
        .query_row(params![uid], |row| row.get::<_, i64>(0))
        .optional()?;

    Ok(result)
}

#[instrument(level = "debug", skip_all)]
pub fn calc_current_pity(uid: &str) -> Result<Vec<(u8, u8)>> {
    logger::debug!("Calculating current pity for user: {}", uid);
    let sql = "
        WITH RankedPulls AS (SELECT gacha_type,
                            rank_type,
                            ROW_NUMBER() OVER (PARTITION BY gacha_type ORDER BY id) AS pull_number
                        FROM gacha_record
                        WHERE uid = ?1)
        SELECT gacha_type,
            MAX(pull_number) - MAX(CASE WHEN rank_type = 5 THEN pull_number ELSE 0 END) AS pity
        FROM RankedPulls
        GROUP BY gacha_type;";

    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare(sql)?;
    let rows = stmt.query_map(params![uid], |row| {
        let gacha_type: u8 = row.get(0)?;
        let pity: u8 = row.get(1)?;
        Ok((gacha_type, pity))
    })?;
    let res = rows.collect::<Result<Vec<_>, _>>()?;
    Ok(res)
}

#[instrument(level = "debug", skip_all)]
pub fn calc_pull_history(uid: &str) -> Result<Vec<(u8, Vec<GachaPullInfoEntity>)>> {
    logger::debug!("Calculating pull history for user: {}", uid);
    let sql = "
        WITH RankedPulls AS (SELECT id,
                            item_id,
                            gacha_type,
                            time,
                            rank_type,
                            ROW_NUMBER() OVER (ORDER BY id) AS pull_number
                        FROM gacha_record
                        WHERE uid = ?1
                        AND gacha_type = ?2),

        FiveStarPulls AS (SELECT * FROM RankedPulls WHERE rank_type = 5),

        PullCalculation AS (SELECT id,
                                    item_id,
                                    gacha_type,
                                    time,
                                    pull_number,
                                    LAG(pull_number, 1, 0) OVER (ORDER BY pull_number) AS prev_pull_number
                            FROM FiveStarPulls)

    SELECT id, item_id, gacha_type, time, (pull_number - prev_pull_number) AS pull_index
    FROM PullCalculation;";

    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare(sql)?;
    let mut results = Vec::new();
    for gacha_type in GachaType::as_array() {
        let rows = stmt.query_map(params![uid, gacha_type as u8], |row| {
            GachaPullInfoEntity::from_row(row)
        })?;
        let pity_result = rows.collect::<Result<Vec<_>, _>>()?;
        results.push((gacha_type as u8, pity_result));
    }
    Ok(results)
}

#[instrument(level = "debug", skip_all)]
pub fn calc_total_count(uid: &str) -> Result<Vec<(u8, u32)>> {
    logger::debug!("Calculating total count for user: {}", uid);

    let sql = "SELECT gacha_type, COUNT(*) AS count FROM gacha_record WHERE uid = ?1 GROUP BY gacha_type;";
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare(sql)?;
    let rows = stmt.query_map(params![uid], |row| {
        let gacha_type: u8 = row.get(0)?;
        let count: u32 = row.get(1)?;
        Ok((gacha_type, count))
    })?;
    let res = rows.collect::<Result<Vec<_>, _>>()?;
    Ok(res)
}

#[instrument(level = "debug", skip_all)]
pub fn insert_or_update_analysis_result(uid: &str, data: &GachaAnalysisResult) -> Result<()> {
    logger::debug!("Saving or updating analysis result for user: {}", uid);
    let mut conn = DatabaseService::connection()?;
    let tx = conn.transaction()?;
    {
        let sql = "INSERT OR REPLACE
            INTO gacha_analysis (uid, gacha_type, pity_count, total_count, rank5)
            VALUES (?1, ?2, ?3, ?4, ?5);";
        let mut stmt = tx.prepare(sql)?;

        for (gacha_type, analysis) in data.iter() {
            stmt.execute(params![
                uid,
                gacha_type,
                analysis.pity_count,
                analysis.total_count,
                serde_json::to_string(&analysis.rank5)?
            ])?;
        }
    }
    tx.commit()?;
    Ok(())
}

#[instrument(level = "debug", skip_all)]
pub fn select_analysis_result(uid: &str) -> Result<GachaAnalysisResult> {
    logger::debug!("Querying analysis result for user: {}", uid);
    let sql = "SELECT uid, gacha_type, pity_count, total_count, rank5 FROM gacha_analysis WHERE uid = ?1;";
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare(sql)?;
    let rows = stmt.query_map(params![uid], GachaAnalysisEntity::from_row)?;

    let mut results = HashMap::new();
    for row in rows {
        let i = row?;
        results.insert(i.gacha_type, i);
    }
    Ok(GachaAnalysisResult::new(results))
}

#[instrument(level = "debug", skip_all)]
pub fn select_all(uid: &str) -> Result<Vec<GachaRecordEntity>> {
    logger::debug!("Querying all gacha records for user: {}", uid);
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare("SELECT id, batch_id, uid, gacha_id, gacha_type, item_id, time, rank_type FROM gacha_record WHERE uid = ?1 ORDER BY id;")?;
    let rows = stmt.query_map(params![uid], GachaRecordEntity::from_row)?;
    let res = rows.collect::<Result<Vec<_>, _>>()?;
    Ok(res)
}
