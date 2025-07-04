import logging
import uuid
from typing import Any, Dict, List, Optional, Union

import settings
import sqlalchemy
from database.models.users import User, get_user_db
from database.orm import Session
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    UUIDIDMixin,
    exceptions,
    models,
    schemas,
)
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.jwt import decode_jwt, generate_jwt
from sqlalchemy import func, select
from web.users.schemas import UserCreate
from web.users.services import calc_age, calc_count_booking_info, calc_score

logger = logging.getLogger('control')

SECRET = settings.SECRET_KEY

ACCESS_TTL = 60 * 60
REFRESH_TTL = 60 * 60 * 24 * 14

AUDIENCE: List[str] = ['fastapi-users:auth']
ALGORITHM = 'HS256'


class JWTDecodeError(Exception):
    pass


def build_refresh_token(user: models.UP) -> str:
    payload = {
        'sub': str(user.id),
        'aud': AUDIENCE,
        'type': 'refresh',
    }
    return generate_jwt(payload, SECRET, REFRESH_TTL, algorithm=ALGORITHM)


async def verify_refresh(token: str, user_manager: 'UserManager') -> User:
    try:
        data = decode_jwt(
            token,
            SECRET,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
        )
        if data.get('type') != 'refresh':
            raise JWTDecodeError('Not refresh token')

        user_id = uuid.UUID(str(data['sub']))
    except (JWTDecodeError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail='Invalid refresh token')

    print(f'[refresh] sub from token → {user_id}')

    try:
        parsed_id = user_manager.parse_id(user_id)
        user = await user_manager.get(parsed_id)
        print('user', user)
    except exceptions.UserNotExists:
        raise HTTPException(status_code=401, detail='User not found')

    if not user.is_active:
        raise HTTPException(status_code=401, detail='Inactive user')

    return user


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def create(
        self,
        user_create: schemas.UC,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> models.UP:
        user = await super().create(user_create, safe=safe, request=request)
        user.age = calc_age(user.date_of_birth, None)
        (
            user.count_trainings,
            user.energy,
            user.status,
        ) = calc_count_booking_info(user)
        user.score = calc_score(user)
        return user

    async def validate_password(
        self,
        password: str,
        user: Union[UserCreate, User],
    ) -> None:
        logger.debug(f'[validate_password] {user}')

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ):
        logger.debug(f'User {user.id} has registered.')

    async def on_after_update(
        self,
        user: User,
        update_dict: Dict[str, Any],
        request: Optional[Request] = None,
    ):
        logger.debug(f'User {user.id} has been updated.')

    async def on_before_delete(
        self, user: User, request: Optional[Request] = None
    ):
        logger.debug(f'User {user.id} is going to be deleted')

    async def on_after_login(
        self,
        user: models.UP,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        if user.is_superuser:
            logger.debug(f'Superuser {user.id} has logged in.')
        else:
            logger.debug(f'User {user.id} has logged in.')

        refresh_token = build_refresh_token(user)
        print('refresh_token', refresh_token)
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=REFRESH_TTL,
            httponly=True,
            samesite='none',
            secure=True,
        )

    async def get_by_phone(self, phone: str) -> User:
        query = select(User).where(User.phone == phone.lower())
        async with Session() as db_session:
            result = await db_session.execute(query)
            try:
                user = result.unique().scalar_one()
            except sqlalchemy.exc.MultipleResultsFound:
                raise exceptions.UserNotExists()
            if user is None:
                raise exceptions.UserNotExists()
            return user

    async def authenticate(
        self, credentials: OAuth2PasswordRequestForm
    ) -> Optional[models.UP]:
        """
        Authenticate and return a user following an email and a password.

        Will automatically upgrade password hash if necessary.

        :param credentials: The user credentials.
        """
        identifier = credentials.username
        try:
            if '@' in identifier:
                print('EMAIL')
                user = await self.get_by_email(identifier)
            else:
                print('PHONE')
                user = await self.get_by_phone(identifier)
        except exceptions.UserNotExists:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self.password_helper.hash(credentials.password)
            return None

        (
            verified,
            updated_password_hash,
        ) = self.password_helper.verify_and_update(
            credentials.password, user.hashed_password
        )
        if not verified:
            return None
        # Update password hash to a more robust one if needed
        if updated_password_hash is not None:
            await self.user_db.update(
                user, {'hashed_password': updated_password_hash}
            )

        return user

    async def on_after_forgot_password(
        self, user: models.UP, token: str, request: Optional[Request] = None
    ) -> None:
        logger.debug(f'***token***: {token}')


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl='auth/jwt/login')


class CustomJWTStrategy(JWTStrategy):
    async def write_token(self, user: models.UP) -> str:
        data = {
            'sub': str(user.id),
            'aud': self.token_audience,
            'is_superuser': user.is_superuser,
            'email': user.email,
        }
        return generate_jwt(
            data,
            self.encode_key,
            self.lifetime_seconds,
            algorithm=self.algorithm,
        )


def get_jwt_strategy() -> JWTStrategy:
    return CustomJWTStrategy(secret=SECRET, lifetime_seconds=ACCESS_TTL)


auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_user = fastapi_users.current_user()
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(superuser=True)
