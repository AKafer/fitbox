import sqlalchemy
from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from database.models import User, Records
from dependencies import get_db_session
from starlette.exceptions import HTTPException

from main_schemas import ResponseErrorBody
from web.records.filters import RecordsFilter
from web.records.schemas import Record, RecordCreateInput, RecordCreateByAdminInput
from web.users.users import current_superuser, current_user

router = APIRouter(
    prefix='/records',
    tags=['records'],
)

@router.get(
    '/',
    response_model=list[Record],
    dependencies=[Depends(current_superuser)]
)
async def get_all_records(
    db_session: AsyncSession = Depends(get_db_session),
    records_filter: RecordsFilter = FilterDepends(RecordsFilter),
):
    query = select(Records).order_by(Records.id.desc())
    query = records_filter.filter(query)
    records = await db_session.execute(query)
    return records.scalars().all()


@router.post(
    '/',
    response_model=Record,
    status_code=status.HTTP_201_CREATED,
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
async def create_user_record(
    record_input: RecordCreateInput,
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Superuser cannot create records',
        )
    try:
        query = select(Records).filter(
            Records.date == record_input.date,
            Records.user_id == user.id
        )
        existing_records = await db_session.scalars(query)
        if existing_records:
            for record in existing_records:
                await db_session.delete(record)
        db_record =  Records(**record_input.model_dump())
        db_record.user_id = user.id
        db_session.add(db_record)
        await db_session.commit()
        await db_session.refresh(db_record)
        return db_record
    except sqlalchemy.exc.IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Some error while creating new Record: {e}',
        )


@router.post(
    '/by-admin',
    response_model=Record,
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
async def create_admin_record(
    record_input: RecordCreateByAdminInput,
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(User).filter(User.id == record_input.user_id)
    user = await db_session.scalar(query)
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Superuser cannot create records',
        )

    try:
        query = select(Records).filter(
            Records.date == record_input.date,
            Records.user_id == user.id
        )
        existing_records = await db_session.scalars(query)
        if existing_records:
            for record in existing_records:
                await db_session.delete(record)
        db_record = Records(**record_input.model_dump())
        db_session.add(db_record)
        await db_session.commit()
        await db_session.refresh(db_record)
        return db_record
    except sqlalchemy.exc.IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Some error while creating new Record: {e}',
        )


@router.delete(
    '/{record_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_user)]
)
async def delete_record(
    record_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    query = select(Records).filter(Records.id == record_id)
    record = await db_session.scalar(query)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Record with id {record_id} not found',
        )
    if not  user.is_superuser:
        if record.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have permission to delete this record',
            )
    await db_session.delete(record)
    await db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
