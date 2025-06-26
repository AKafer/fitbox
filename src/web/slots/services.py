from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Slots, Bookings
from web.slots.schemas import BindInput


class ExistingBookingsError(Exception):
    pass


class BindingsError(Exception):
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

async def check_complete_bindings(
    bind_input: BindInput, db_session: AsyncSession
):
    if not bind_input.bindings:
        return
    for binding in bind_input.bindings:
        if not binding.sensor_id or not binding.user_id:
            raise BindingsError(
                'Each binding must have both sensor_id and user_id set.'
            )
    query = select(Slots).filter(Slots.id == bind_input.slot_id)
    result = await db_session.execute(query)
    slot = result.scalar_one_or_none()
    if not slot:
        raise BindingsError(f'Slot with id {bind_input.slot_id} does not exist.')

    bindings = {str(b.user_id): b.sensor_id for b in bind_input.bindings}
    slot.bindings = bindings
    accepted_bindings_count = len(slot.bindings)
    possible_bindings_count = 0
    query = select(Bookings).filter(Bookings.slot_id == bind_input.slot_id)
    bookings = await db_session.execute(query)
    for booking in bookings.scalars().all():
        if str(booking.user_id) in bindings:
            booking.sensor_id = bindings[str(booking.user_id)]
            possible_bindings_count += 1
    return {
        'accepted_bindings': accepted_bindings_count,
        'possible_bindings': possible_bindings_count
    }
