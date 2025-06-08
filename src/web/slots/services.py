from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Slots


async def update_slot_in_db(
        db_session: AsyncSession,
        slot: Slots,
        **update_data: dict
) -> Slots:
    for field, value in update_data.items():
        setattr(slot, field, value)
    await db_session.commit()
    await db_session.refresh(slot)
    return slot