import contextlib
import logging
from logging import config as logging_config

import settings
from database.models.users import get_user_db
from dependencies import get_db_session
from fastapi_users.exceptions import UserAlreadyExists
from sqlalchemy.ext.asyncio import AsyncSession
from web.users.schemas import UserCreate
from web.users.users import get_user_manager

logging_config.dictConfig(settings.LOGGING)
logger = logging.getLogger('control')


get_async_session_context = contextlib.asynccontextmanager(get_db_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


class SuperUserCreate(UserCreate):
    pass


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    name: str,
    last_name: str,
):
    try:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                user = await user_manager.create(
                    SuperUserCreate(
                        email=email,
                        password=password,
                        name=name,
                        last_name=last_name,
                    )
                )
                user.is_superuser = True
                await session.commit()
                await session.refresh(user)
                logger.info(f'User created {user}')
                return user
    except UserAlreadyExists:
        logger.error(f'User {email} already exists')
