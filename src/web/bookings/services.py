from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import DEFAUL_BLINK_INTERVAL, KOEF_POWER, DEGREE_POWER
from database.models import Slots, Bookings, User, Sprints


tempo_border = 150


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


def is_synced_hit(time_ms: int, blink_interval: float) -> bool:
    if time_ms is None or blink_interval <= 0:
        return False
    k = round(time_ms / blink_interval)
    nearest = k * blink_interval
    return abs(time_ms - nearest) <= tempo_border


def calculate_sprint_metrics(hits: list, blink_interval: float, hit_count: int):
    if not hits or hit_count == 0:
        return 0, 0, 0
    max_punch = max(float(hit.get('maxAccel', 0)) for hit in hits)
    sum_punches = sum(float(hit.get('maxAccel', 0)) for hit in hits)
    average_punch = sum_punches / hit_count if hit_count > 0 else 0
    power = (average_punch / max_punch) * KOEF_POWER if max_punch > 0 else 0
    synced_hits = 0
    for hit in hits:
        time_ms = hit.get('timeMs')
        if time_ms is not None:
            if is_synced_hit(int(time_ms), blink_interval):
                synced_hits += 1
    tempo = synced_hits / hit_count * 100  if blink_interval > 0 else 0
    energy = tempo * (power / KOEF_POWER)**DEGREE_POWER
    return tempo, power, energy


async def calculate_sprints_data(
    booking: Bookings,
    db_session: AsyncSession,
):
    query = (
        select(Sprints)
        .where(
            Sprints.slot_id == booking.slot_id,
            Sprints.sensor_id == booking.sensor_id
        )
    )
    result = await db_session.execute(query)
    sprints = result.scalars().all()

    if not sprints:
        return {}

    sprints_data = {}
    for sprint in sprints:
        current_sprint_data = (sprint.data or {}).get('hits', [])
        if not current_sprint_data:
            continue
        blink_interval = float(sprint.data.get('blink_interval', DEFAUL_BLINK_INTERVAL)) or DEFAUL_BLINK_INTERVAL
        if not blink_interval:
            continue
        hit_count = len(current_sprint_data)
        tempo, power, energy = calculate_sprint_metrics(current_sprint_data, blink_interval, hit_count)
        sprints_data[str(sprint.sprint_id)] = {
            'power': round(power, 2),
            'energy': round(energy, 2),
            'tempo': round(tempo, 2),
        }

    return sprints_data
