use rusqlite::params;
use tracing::instrument;

use crate::Result;
use crate::core::GachaMetadataEntity;
use crate::database::DatabaseService;
use crate::logger;
use db_helper::FromRow;

#[instrument(level = "debug", skip_all)]
pub fn insert(data: Vec<GachaMetadataEntity>) -> Result<usize> {
    logger::debug!("Saving all metadata, count: {}", data.len());

    let mut conn = DatabaseService::connection()?;
    let tx = conn.transaction()?;
    let mut cnt = 0;
    {
        let mut stmt = tx.prepare(
            "INSERT OR REPLACE INTO gacha_metadata (item_id, rarity, item_type, names) 
                VALUES (?1, ?2, ?3, ?4);",
        )?;
        for i in data {
            let names_json = serde_json::to_string(&i.names)?;
            cnt += stmt.execute(params![i.item_id, i.rarity, i.item_type, names_json])?;
        }
    }
    tx.commit()?;
    Ok(cnt)
}

#[instrument(level = "debug", skip_all)]
pub fn select_all() -> Result<Vec<GachaMetadataEntity>> {
    logger::debug!("Querying all metadata");
    let conn = DatabaseService::connection()?;
    let mut stmt = conn.prepare("SELECT item_id, rarity, item_type, names FROM gacha_metadata;")?;
    let rows = stmt.query_map([], |row| GachaMetadataEntity::from_row(&row))?;
    rows.collect::<std::result::Result<Vec<_>, _>>()
        .map_err(Into::into)
}
