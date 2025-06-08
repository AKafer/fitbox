import sqlalchemy
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from database.models import Slots
from dependencies import get_db_session
from starlette.exceptions import HTTPException

from main_schemas import ResponseErrorBody
from web.slots.schemas import (
    Slot,
    SlotCreateInput,
    SlotUpdateInput,
)
from web.slots.services import update_slot_in_db
from web.users.users import current_superuser

router = APIRouter(
    prefix='/slots',
    tags=['slots'],
    dependencies=[Depends(current_superuser)],
)


@router.get('/', response_model=list[Slot])
async def get_all_slots(
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(Slots).order_by(Slots.id.desc())
    slots = await db_session.execute(query)
    return slots.scalars().all()


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
)
async def get_slot_by_id(
    slot_id: int, db_session: AsyncSession = Depends(get_db_session)
):
    query = select(Slots).filter(Slots.id == slot_id)
    slot = await db_session.scalar(query)
    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Slot with id {slot_id} not found',
        )
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
)
async def create_slot(
    slot_input: SlotCreateInput,
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        db_slot = Slots(**slot_input.dict())
        db_session.add(db_slot)
        await db_session.commit()
        await db_session.refresh(db_slot)
        return db_slot
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
        return await update_slot_in_db(
            db_session, slot, **update_input.dict(exclude_none=True)
        )
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
    await db_session.delete(slot)
    await db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
