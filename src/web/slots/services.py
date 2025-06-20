from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Slots, Bookings


class ExistingBookingsError(Exception):
    pass


async def update_slot_in_db(
    db_session: AsyncSession, slot: Slots, **update_data: dict
) -> Slots:
    for field, value in update_data.items():
        setattr(slot, field, value)
    await db_session.commit()
    await db_session.refresh(slot)
    return slot


async def calculate_free_places(slot: Slots, db_session: AsyncSession) -> int:
    query = select(Bookings).filter(Bookings.slot_id == slot.id)
    result = await db_session.execute(query)
    exists_slot_bookings = result.scalars().all()
    return max(0, slot.number_of_places - len(exists_slot_bookings))


async def check_bookings(slot: Slots, db_session: AsyncSession) -> None:
    query = select(Bookings).filter(Bookings.slot_id == slot.id)
    result = await db_session.execute(query)
    exists_slot_bookings = result.scalars().all()
    for booking in exists_slot_bookings:
        if booking.is_done:
            raise ExistingBookingsError('This slot already has done bookings.')
        if any([booking.power, booking.energy, booking.tempo]):
            raise ExistingBookingsError(
                'This slot already has bookings with power, energy or tempo set.'
            )
