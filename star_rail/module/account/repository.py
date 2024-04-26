from star_rail.database import AsyncDBClient


class AccountRepository:
    async def delete_account(self, uid: str) -> None:
        """Delete an account by ID."""
        async with AsyncDBClient() as db:
            await db.start_transaction()
            await db.execute("delete from user where uid = ?;", uid)
            await db.execute("delete from month_info_item where uid = ?;", uid)
            await db.execute("delete from gacha_record_batch where uid = ?;", uid)
            await db.execute("delete from gacha_record_item where uid = ?;", uid)
            await db.commit_transaction()
