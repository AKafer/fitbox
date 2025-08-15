from typing import Sequence

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from constants import DEFAULT_BLINK_INTERVAL
from database.models import Slots, Bookings, User, Sprints
from web.bookings.services import calculate_sprints_data, calculate_booking_metrics
from web.sensors.services import calculate_sprint_metrics
from web.slots.schemas import BindInput


class ExistingBookingsError(Exception):
    pass


class BindingsError(Exception):
    pass


class SprintResultException(Exception):
    pass


class SlotResultException(Exception):
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
        raise BindingsError(
            f'Slot with id {bind_input.slot_id} does not exist.'
        )

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
        'possible_bindings': possible_bindings_count,
    }


async def get_slot_energy_list(
    slot: Slots, user: User, db_session: AsyncSession
) -> tuple[list[dict[str, int | str | float | None]], bool]:
    bookings = slot.bookings
    user_can_see_results = False
    energy_list = []
    for booking in bookings:
        if not booking.is_done:
            raise SlotResultException(
                f'Not all bookings are done for slot {slot.id}',
            )
        if booking.user_id == user.id:
            user_can_see_results = True
        energy_list.append(
            {
                'id': str(booking.user.id),
                'name': booking.user.name,
                'last_name': booking.user.last_name,
                'photo_url': booking.user.photo_url,
                'power': booking.power,
                'tempo': booking.tempo,
                'energy': booking.energy,
            }
        )
    return energy_list, user_can_see_results


async def get_sprint_energy_list(
    slot_id: int, sprint_id: int, user: User, db_session: AsyncSession
) -> tuple[list[dict[str, int | str | float | None]], bool]:
    query = select(Slots).filter(Slots.id == slot_id)
    slot = await db_session.scalar(query)
    if slot is None:
        raise SprintResultException(f'Slot with id {slot_id} not found')
    query = select(Sprints).where(
        Sprints.slot_id == slot_id, Sprints.sprint_id == sprint_id
    )
    result = await db_session.scalars(query)
    sprints = result.all()
    user_can_see_results = False
    energy_list = []
    query = select(User).where(User.id.in_(slot.bindings.keys()))
    result = await db_session.scalars(query)
    users = result.all()
    sensor_dict = {}
    for key, value in slot.bindings.items():
        for user in users:
            if str(user.id) == key:
                sensor_dict[value] = user
    for sprint in sprints:
        current_user = sensor_dict.get(sprint.sensor_id)
        if current_user is None:
            raise SprintResultException(
                f'User with sensor_id {sprint.sensor_id} not found in slot {slot_id}',
            )
        if current_user.id == user.id:
            user_can_see_results = True
        sprint_result = sprint.result or {}
        energy_list.append(
            {
                'id': str(current_user.name),
                'name': current_user.name,
                'last_name': current_user.last_name,
                'photo_url': current_user.photo_url,
                'power': sprint_result.get('power', 0),
                'tempo': sprint_result.get('tempo', 0),
                'energy': sprint_result.get('energy', 0),
            }
        )
    return energy_list, user_can_see_results


async def update_sprint_in_db(sprints: Sequence[Sprints]) -> Sequence[Sprints]:
    for sprint in sprints:
        sprint.result = calculate_sprint_metrics(
            sprint.data.get('hits', []),
            float(sprint.data.get('blink_interval') or DEFAULT_BLINK_INTERVAL),
            int(sprint.data.get('total_hits', 0)),
        )
    return sprints


async def recalculate_sprint_results(
    slot_id: int, sprint_id: int, db_session: AsyncSession
) -> None:
    query = (
        select(Sprints)
        .where(
            and_(
                Sprints.slot_id == slot_id,
                Sprints.sprint_id == sprint_id,
            )
        )
        .with_for_update()
    )
    result = await db_session.scalars(query)
    sprints = result.all()
    await update_sprint_in_db(sprints)
    await db_session.commit()


async def recalculate_all_sprints_results(
    slot_id: int, db_session: AsyncSession
) -> None:
    query = select(Sprints).where(Sprints.slot_id == slot_id).with_for_update()
    result = await db_session.scalars(query)
    sprints = result.all()
    await update_sprint_in_db(sprints)
    await db_session.commit(
)

async def recalculate_bookings_results(
    bookings: Sequence[Bookings],
    db_session: AsyncSession,
) -> Sequence[Bookings]:
    for booking in bookings:
        sprints_data = await calculate_sprints_data(booking, db_session)
        booking.sprints_data = sprints_data
        calculate_booking_metrics(booking, sprints_data)
    return bookings
