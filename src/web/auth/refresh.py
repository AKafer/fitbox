import logging

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
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
    response: Response,
    creds: HTTPAuthorizationCredentials = Depends(bearer_refresh),
    user_manager: UserManager = Depends(get_user_manager),
    refresh_token: str | None = None,
):
    logger.info('***REFRESH TOKEN***')

    if refresh_token is None:
        token = request.cookies.get('refresh_token')
        if token is None:
            raise HTTPException(
                status_code=401, detail='Missing refresh token'
            )
    else:
        token = refresh_token

    user = await verify_refresh(token, user_manager)

    jwt_strategy = get_jwt_strategy()
    new_access = await jwt_strategy.write_token(user)
    return {
        'access_token': new_access,
        'expires_in': ACCESS_TTL,
        'token_type': 'bearer',
    }
