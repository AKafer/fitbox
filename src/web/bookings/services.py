from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import (
    DEFAULT_BLINK_INTERVAL,
    KOEF_POWER,
    DEGREE_POWER,
    TEMPO_BORDER_PERCENT,
)
from database.models import Slots, Bookings, User, Sprints


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
            raise DuplicateBookingError(
                'Already exist booking for this user in this slot.'
            )
    query = select(Bookings).filter(Bookings.slot_id == slot_id)
    result = await db_session.execute(query)
    exists_slot_bookings = result.scalars().all()
    if len(exists_slot_bookings) >= slot.number_of_places:
        raise ExcessiveBookingError('This slot is already fully booked.')


async def update_booking_in_db(
    db_session: AsyncSession, booking: Bookings, **update_data: dict
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
    query = select(Sprints).where(
        Sprints.slot_id == booking.slot_id,
        Sprints.sensor_id == booking.sensor_id,
    )
    result = await db_session.execute(query)
    sprints = result.scalars().all()
    if not sprints:
        return {}

    sprints_data = {}
    for sprint in sprints:
        sprints_data[str(sprint.sprint_id)] = sprint.result or {}
    return sprints_data


def calculate_booking_metrics(booking, sprints_data: dict) -> None:
    len_sprints_data = len(sprints_data)
    if len_sprints_data > 0:
        sum_power, sum_energy, sum_tempo = 0, 0, 0
        for key, value in sprints_data.items():
            sum_power += value.get('power', 0)
            sum_energy += value.get('energy', 0)
            sum_tempo += value.get('tempo', 0)
        booking.power = round(sum_power / len_sprints_data, 2)
        booking.energy = round(sum_energy / len_sprints_data, 2)
        booking.tempo = round(sum_tempo / len_sprints_data, 2)
