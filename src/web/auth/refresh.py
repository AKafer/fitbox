import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from jwt import ExpiredSignatureError
from starlette import status

from web.users.users import (
    ACCESS_TTL,
    UserManager,
    get_jwt_strategy,
    get_user_manager,
    verify_refresh,
)

bearer_refresh = HTTPBearer(auto_error=False)
router = APIRouter(prefix='/auth/jwt', tags=['auth'])

logger = logging.getLogger('control')


@router.post('/refresh', summary='Renew JWT')
async def refresh_tokens(
    request: Request,
    user_manager: UserManager = Depends(get_user_manager),
    refresh_token: str | None = None,
):
    if refresh_token is None:
        token = request.cookies.get('refresh_token')
        if token is None:
            raise HTTPException(
                status_code=401, detail='Missing refresh token'
            )
    else:
        token = refresh_token

    try:
        user = await verify_refresh(token, user_manager)
    except ExpiredSignatureError:
        logger.warning('Refresh token has expired')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token has expired',
        )
    jwt_strategy = get_jwt_strategy()
    new_access = await jwt_strategy.write_token(user)
    return {
        'access_token': new_access,
        'expires_in': ACCESS_TTL,
        'token_type': 'bearer',
    }
