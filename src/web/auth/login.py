from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette import status
from starlette.requests import Request
from starlette.responses import Response
from web.common.common import get_cookie_domain_from_url
from web.users.users import (
    auth_backend,
    build_refresh_token,
    current_user,
    get_user_manager,
)

router = APIRouter(
    prefix='/auth/jwt',
    tags=['auth'],
)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


@router.post(
    '/login',
    response_model=TokenPair,
    name='auth:login',
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
            detail='INVALID_CREDENTIALS',
        )
    access_token = await auth_backend.get_strategy().write_token(user)
    refresh_token = build_refresh_token(user)
    await user_manager.on_after_login(user, request, response)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    '/logout',
    status_code=status.HTTP_204_NO_CONTENT,
    name='auth:logout',
    dependencies=[Depends(current_user)],
)
async def logout(
    request: Request,
    response: Response,
):
    domain = get_cookie_domain_from_url(request.url.hostname)
    response.delete_cookie(
        key='refresh_token',
        domain=domain,
        httponly=True,
        samesite='none',
        secure=True,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
