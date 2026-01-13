pub use db_helper_derive::FromRow;

pub trait FromRow: Sized {
    fn from_row(row: &rusqlite::Row) -> rusqlite::Result<Self>;
}
