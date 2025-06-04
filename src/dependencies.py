from sqlalchemy.ext.asyncio import AsyncSession

from database.orm import Session


async def get_db_session() -> AsyncSession:
    async with Session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
