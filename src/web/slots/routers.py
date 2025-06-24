import sqlalchemy
from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from database.models import Slots, User
from dependencies import get_db_session
from starlette.exceptions import HTTPException

from main_schemas import ResponseErrorBody
from web.slots.filters import SlotsFilter
from web.slots.schemas import (
    Slot,
    SlotCreateInput,
    SlotUpdateInput,
    BulkSlotCreateInput, BindInput,
)
from web.slots.services import update_slot_in_db, calculate_free_places, check_bookings, ExistingBookingsError, \
    check_complete_bindings, BindingsError
from web.users.users import current_superuser, current_user

router = APIRouter(
    prefix='/slots',
    tags=['slots'],
)


@router.get('/', response_model=list[Slot], dependencies=[Depends(current_user)],)
async def get_all_slots(
    slots_filter: SlotsFilter = FilterDepends(SlotsFilter),
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    query = select(Slots).order_by(Slots.id.desc())
    query = slots_filter.filter(query)
    result = await db_session.execute(query)
    slots = result.scalars().all()
    for slot in slots:
        slot.free_places = await calculate_free_places(slot, db_session)
        if not user.is_superuser:
            slot.bookings = []
            slot.bindings = None
    return slots


@router.get(
    '/{slot_id:int}',
    response_model=Slot,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_user)]
)
async def get_slot_by_id(
    slot_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    query = select(Slots).filter(Slots.id == slot_id)
    slot = await db_session.scalar(query)
    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Slot with id {slot_id} not found',
        )
    slot.free_places = await calculate_free_places(slot, db_session)
    if not user.is_superuser:
        slot.bookings = []
        slot.bindings = None
    return slot


@router.post(
    '/',
    response_model=Slot,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_superuser)]
)
async def create_slot(
    slot_input: SlotCreateInput,
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        db_slot = Slots(**slot_input.model_dump())
        db_session.add(db_slot)
        await db_session.commit()
        await db_session.refresh(db_slot)
        db_slot.free_places = await calculate_free_places(db_slot, db_session)
        return db_slot
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Slot with this title already exists: {e}',
        )


@router.post(
    '/binding',
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_superuser)]
)
async def save_bindings(
    bind_input: BindInput,
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(Slots).where(Slots.id == bind_input.slot_id)
    slot = await db_session.scalar(query)
    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Slot with id {bind_input.slot_id} not found',
        )
    try:
        result = await check_complete_bindings(bind_input, db_session)
        slot.bindings = {str(b.user_id): b.sensor_id for b in bind_input.bindings}
        await db_session.commit()
        return result
    except (sqlalchemy.exc.IntegrityError, BindingsError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Error while making binding: {e}',
        )


@router.post(
    '/bulk',
    response_model=list[Slot],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_superuser)]
)
async def bulk_create_slot(
    bulk_slot_input: BulkSlotCreateInput,
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        slots: list[Slots] = []
        for slot_input in bulk_slot_input.slots:
            db_slot = Slots(**slot_input.model_dump())
            db_session.add(db_slot)
            slots.append(db_slot)
        await db_session.commit()
        for db_slot in slots:
            await db_session.refresh(db_slot)
            db_slot.free_places = await calculate_free_places(db_slot, db_session)
        return slots
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Slot with this title already exists: {e}',
        )


@router.patch(
    '/{slot_id:int}',
    response_model=Slot,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_superuser)]
)
async def update_slot(
    slot_id: int,
    update_input: SlotUpdateInput,
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(Slots).where(Slots.id == slot_id)
    slot = await db_session.scalar(query)
    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Slot with id {slot_id} not found',
        )
    try:
         slot_db = await update_slot_in_db(
            db_session, slot, **update_input.model_dump(exclude_none=True)
        )
         slot_db.free_places = await calculate_free_places(slot_db, db_session)
         return slot_db
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Slot with this title already exists: {e}',
        )


@router.delete(
    '/{slot_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_superuser)]
)
async def delete_slot(
    slot_id: int,
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(Slots).filter(Slots.id == slot_id)
    slot = await db_session.scalar(query)
    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Slot with id {slot_id} not found',
        )
    try:
        await check_bookings(slot, db_session)
    except ExistingBookingsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'{e}',
        )
    await db_session.delete(slot)
    await db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
