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


async def update_booking_in_db(
        db_session: AsyncSession,
        booking: Bookings,
        **update_data: dict
) -> Bookings:
    for field, value in update_data.items():
        setattr(booking, field, value)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking


async def calculate_sprints_data(
    booking: Bookings,
    db_session: AsyncSession,
):
    return {
        '1': {
            'power': 16,
            'energy': 80,
            'tempo': 100,
        },
        '2': {
            'power': 70,
            'energy': 80,
            'tempo': 91,
        }
    }
