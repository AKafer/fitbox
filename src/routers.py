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

bearer_refresh = HTTPBearer(auto_error=False)

refresh_router = APIRouter(prefix='/auth', tags=['auth'])


@refresh_router.post("/auth/jwt/refresh", summary="Renew JWT")
async def refresh_tokens(
    request: Request,
    refresh_token: str | None,
    response: Response,
    creds: HTTPAuthorizationCredentials = Depends(bearer_refresh),
    user_manager: UserManager = Depends(get_user_manager),
):
    logger.info("***REFRESH TOKEN***")

    if refresh_token is None:
        token = request.cookies.get("refresh_token")
        if token is None:
            raise HTTPException(status_code=401, detail="Missing refresh token")
    else:
        token = refresh_token

    user = await verify_refresh(token, user_manager)

    jwt_strategy = get_jwt_strategy()
    new_access  = await jwt_strategy.write_token(user)
    return {
        "access_token": new_access,
        "expires_in":  ACCESS_TTL,
        "token_type":  "bearer",
        "refresh_token": build_refresh_token(user),
    }


# @refresh_router.post("/auth/jwt/refresh_ios", summary="Renew JWT")
# async def refresh_tokens(
#     request: Request,
#     token: str,
#     response: Response,
#     creds: HTTPAuthorizationCredentials = Depends(bearer_refresh),
#     user_manager: UserManager = Depends(get_user_manager),
# ):
#     logger.info("***REFRESH TOKEN***")
#
#     user = await verify_refresh(token, user_manager)
#     jwt_strategy = get_jwt_strategy()
#     new_access  = await jwt_strategy.write_token(user)
#     return {
#         "access_token": new_access,
#         "expires_in":  ACCESS_TTL,
#         "token_type":  "bearer",
#         "refresh_token": build_refresh_token(user),
#     }



class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"



@api_v1_router.post(
    "/auth/jwt/login",
    response_model=TokenPair,
    name="auth:login",
    tags=["auth"]
)
async def login(
    request: Request,
    response: Response,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager=Depends(get_user_manager),
):
    user = await user_manager.authenticate(credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_CREDENTIALS",
        )
    access_token = await auth_backend.get_strategy().write_token(user)
    refresh_token = build_refresh_token(user)
    await user_manager.on_after_login(user, request, response)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@api_v1_router.post(
    "/auth/jwt/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    name="auth:logout",
    tags=["auth"],
    dependencies=[Depends(current_user)]
)
async def logout(
    response: Response,
    # refresh_token: str | None = Cookie(default=None),
):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="none",
        secure=True,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

api_v1_router.include_router(refresh_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(slots_router)
api_v1_router.include_router(bookings_router)
api_v1_router.include_router(records_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(sensors_router)
