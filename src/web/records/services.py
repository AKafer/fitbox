from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Slots, Bookings, User


class DuplicateBookingError(Exception):
    pass

class NotFoundSlotError(Exception):
    pass

class ExcessiveBookingError(Exception):
    pass

async def check_before_create(
    slot_id: int,
    user: User,
    db_session: AsyncSession,
) -> None:
    query = select(Slots).filter(Slots.id == slot_id)
    slot = await db_session.scalar(query)
    if slot is None:
        raise NotFoundSlotError(f'Slot with id {slot_id} not found')
    query = select(Bookings).filter(Bookings.user_id == user.id)
    result = await db_session.execute(query)
    exists_user_bookings = result.scalars().all()
    for booking in exists_user_bookings:
        if booking.slot_id == slot_id:
            raise DuplicateBookingError('Already exist booking for this user in this slot.')
    query = select(Bookings).filter(Bookings.slot_id == slot_id)
    result = await db_session.execute(query)
    exists_slot_bookings = result.scalars().all()
    if len(exists_slot_bookings) >= slot.number_of_places:
        raise ExcessiveBookingError('This slot is already fully booked.')



