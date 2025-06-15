import sqlalchemy
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from database.models import Bookings, User
from dependencies import get_db_session
from starlette.exceptions import HTTPException

from main_schemas import ResponseErrorBody
from web.bookings.schemas import Booking, BookingCreateInput
from web.bookings.services import check_before_create, NotFoundSlotError, DuplicateBookingError, ExcessiveBookingError
from web.users.users import current_superuser, current_user

router = APIRouter(
    prefix='/bookings',
    tags=['bookings'],
)

@router.get(
    '/',
    response_model=list[Booking],
    dependencies=[Depends(current_superuser)]
)
async def get_all_bookings(
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(Bookings).order_by(Bookings.id.desc())
    bookings = await db_session.execute(query)
    return bookings.scalars().all()


@router.post(
    '/',
    response_model=Booking,
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
async def create_booking(
    booking_input: BookingCreateInput,
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Superuser cannot create bookings',
        )
    try:
        await check_before_create(booking_input.slot_id, user,  db_session)
    except (
        NotFoundSlotError,
        DuplicateBookingError,
        ExcessiveBookingError
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Can not create new Booking: {e}',
        )
    try:
        db_booking = Bookings(**booking_input.model_dump())
        db_booking.user_id = user.id
        db_session.add(db_booking)
        await db_session.commit()
        await db_session.refresh(db_booking)
        return db_booking
    except sqlalchemy.exc.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Some error while creating new Booking: {e}',
        )


@router.delete(
    '/{booking_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_user)]
)
async def delete_booking(
    booking_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    query = select(Bookings).filter(Bookings.id == booking_id)
    booking = await db_session.scalar(query)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Booking with id {booking_id} not found',
        )
    if not  user.is_superuser:
        if booking.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have permission to delete this booking',
            )
    await db_session.delete(booking)
    await db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
