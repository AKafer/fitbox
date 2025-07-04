import logging

from fastapi import APIRouter
from main_schemas import ResponseErrorBody
from starlette import status
from web.auth.login import router as login_router
from web.auth.refresh import router as refresh_router
from web.bookings.routers import router as bookings_router
from web.records.routers import router as records_router
from web.sensors.routers import router as sensors_router
from web.slots.routers import router as slots_router
from web.transactions.routers import router as transactions_router
from web.users.routers import router as users_router
from web.users.schemas import UserCreate, UserRead
from web.users.users import fastapi_users

logger = logging.getLogger('control')


api_v1_router = APIRouter(
    prefix='/api/v1',
    dependencies=[],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            'model': ResponseErrorBody,
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            'model': ResponseErrorBody,
        },
    },
)

# Stock authentication routes switched off for now - custom implementation
# api_v1_router.include_router(
#     fastapi_users.get_auth_router(auth_backend),
#     prefix='/auth/jwt',
#     tags=['auth'],
# )

api_v1_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)

api_v1_router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix='/auth',
    tags=['auth'],
)

api_v1_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix='/auth',
    tags=['auth'],
)


api_v1_router.include_router(refresh_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(slots_router)
api_v1_router.include_router(bookings_router)
api_v1_router.include_router(records_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(sensors_router)
api_v1_router.include_router(login_router)
api_v1_router.include_router(refresh_router)
