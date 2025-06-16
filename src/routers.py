import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from main_schemas import ResponseErrorBody

from web.users.routers import router as users_router
from web.users.schemas import UserRead, UserCreate
from web.slots.routers import router as slots_router
from web.bookings.routers import router as bookings_router
from web.records.routers import router as records_router
from web.users.users import (
    auth_backend,
    current_superuser,
    UserManager,
    get_user_manager,
    verify_refresh,
    get_jwt_strategy,
    ACCESS_TTL, fastapi_users
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

api_v1_router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix='/auth/jwt',
    tags=['auth'],
)
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

bearer_refresh = HTTPBearer(auto_error=False)

refresh_router = APIRouter(prefix='/auth', tags=['auth'])


@refresh_router.post("/auth/jwt/refresh", summary="Renew JWT")
async def refresh_tokens(
    request: Request,
    response: Response,
    creds: HTTPAuthorizationCredentials = Depends(bearer_refresh),
    user_manager: UserManager = Depends(get_user_manager),
):
    logger.info("***REFRESH TOKEN***")

    token = request.cookies.get("refresh_token")
    if token is None:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    user = await verify_refresh(token, user_manager)

    jwt_strategy = get_jwt_strategy()
    new_access  = await jwt_strategy.write_token(user)
    return {
        "access_token": new_access,
        "expires_in":  ACCESS_TTL,
        "token_type":  "bearer",
    }

api_v1_router.include_router(refresh_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(slots_router)
api_v1_router.include_router(bookings_router)
api_v1_router.include_router(records_router)
