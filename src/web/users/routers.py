from datetime import date

import sqlalchemy
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_users import exceptions, models, schemas
from fastapi_users.manager import BaseUserManager
from fastapi_users.router.common import ErrorCode, ErrorModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from dependencies import get_db_session
from web.users.filters import UsersFilter
from web.users.schemas import (
    UserRead,
    UserUpdate,
    UserListRead
)
from web.users.services import calc_age
from web.users.users import (
    current_active_user,
    current_superuser,
    get_user_manager,
)

router = APIRouter(prefix='/users', tags=['users'])


@router.get(
    '/',
    response_model=list[UserListRead],
    dependencies=[Depends(current_superuser)],
)
async def get_all_users(
    user_filter: UsersFilter = FilterDepends(UsersFilter),
    db_session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(User)
        .where(User.is_superuser == False)
    )
    query = user_filter.filter(query)
    result = await db_session.execute(query)
    users = result.scalars().unique().all()
    for user in users:
        user.age = calc_age(user.date_of_birth, date.today())
    return users


@router.get(
    '/paginated',
    response_model=Page[UserListRead],
    dependencies=[Depends(current_superuser)],
)
async def get_paginated_users(
    user_filter: UsersFilter = Depends(UsersFilter),
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(User).where(User.is_superuser == False)
    query = user_filter.filter(query)
    page = await paginate(db_session, query)
    for user in page.items:
        user.age = calc_age(user.date_of_birth, date.today())
    return page


async def get_user_or_404(
    request: Request,
    id: str,
    user_manager: BaseUserManager[models.UP, models.ID] = Depends(
        get_user_manager
    ),
) -> models.UP:
    try:
        parsed_id = user_manager.parse_id(id)
        user = await user_manager.get(parsed_id)
        return user
    except (exceptions.UserNotExists, exceptions.InvalidID) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from e


@router.get(
    '/me',
    response_model=UserRead,
    name='users:current_user',
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            'description': 'Missing token or inactive user.',
        },
    },
)
async def me(
    request: Request,
    user: models.UP = Depends(current_active_user),
):
    return schemas.model_validate(UserRead, user)


@router.get(
    '/{id}',
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
    name='users:user',
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            'description': 'Missing token or inactive user.',
        },
        status.HTTP_403_FORBIDDEN: {
            'description': 'Not a superuser.',
        },
        status.HTTP_404_NOT_FOUND: {
            'description': 'The user does not exist.',
        },
    },
)
async def get_user(user=Depends(get_user_or_404)):
    user.age = calc_age(user.date_of_birth, date.today())
    return schemas.model_validate(UserRead, user)


@router.patch(
    '/{id}',
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
    name='users:patch_user',
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            'description': 'Missing token or inactive user.',
        },
        status.HTTP_403_FORBIDDEN: {
            'description': 'Not a superuser.',
        },
        status.HTTP_404_NOT_FOUND: {
            'description': 'The user does not exist.',
        },
        status.HTTP_400_BAD_REQUEST: {
            'model': ErrorModel,
            'content': {
                'application/json': {
                    'examples': {
                        ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS: {
                            'summary': 'A user with this email already exists.',
                            'value': {
                                'detail': ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS
                            },
                        },
                        ErrorCode.UPDATE_USER_INVALID_PASSWORD: {
                            'summary': 'Password validation failed.',
                            'value': {
                                'detail': {
                                    'code': ErrorCode.UPDATE_USER_INVALID_PASSWORD,
                                    'reason': 'Password should be'
                                    'at least 3 characters',
                                }
                            },
                        },
                    }
                }
            },
        },
    },
)
async def update_user(
    user_update: UserUpdate,  # type: ignore
    request: Request,
    user=Depends(get_user_or_404),
    user_manager: BaseUserManager[models.UP, models.ID] = Depends(
        get_user_manager
    ),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        user = await user_manager.update(
            user_update, user, safe=False, request=request
        )
        await db_session.refresh(user)
        user.age = calc_age(user.date_of_birth, date.today())
        return schemas.model_validate(UserRead, user)
    except exceptions.InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': ErrorCode.UPDATE_USER_INVALID_PASSWORD,
                'reason': e.reason,
            },
        )
    except exceptions.UserAlreadyExists:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS,
        )


@router.delete(
    '/{id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(current_superuser)],
    name='users:delete_user',
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            'description': 'Missing token or inactive user.',
        },
        status.HTTP_403_FORBIDDEN: {
            'description': 'Not a superuser.',
        },
        status.HTTP_404_NOT_FOUND: {
            'description': 'The user does not exist.',
        },
    },
)
async def delete_user(
    request: Request,
    user=Depends(get_user_or_404),
    user_manager: BaseUserManager[models.UP, models.ID] = Depends(
        get_user_manager
    ),
):
    await user_manager.delete(user, request=request)
    return None
