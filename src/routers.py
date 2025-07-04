import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette import status

from main_schemas import ResponseErrorBody

from web.users.routers import router as users_router
from web.users.schemas import UserRead, UserCreate
from web.slots.routers import router as slots_router
from web.bookings.routers import router as bookings_router
from web.records.routers import router as records_router
from web.transactions.routers import router as transactions_router
from web.sensors.routers import router as sensors_router
from web.auth.login import router as login_router
from web.auth.refresh import router as refresh_router
from web.users.users import (
    auth_backend,
    current_superuser,
    UserManager,
    get_user_manager,
    verify_refresh,
    get_jwt_strategy,
    ACCESS_TTL, fastapi_users, REFRESH_TTL, build_refresh_token, current_user
)


logger = logging.getLogger("control")


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
    prefix="/auth",
    tags=["auth"],
)

api_v1_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
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
