import asyncio
import contextlib
import logging
from logging import config as logging_config

from fastapi_users.exceptions import UserAlreadyExists
from sqlalchemy.ext.asyncio import AsyncSession

import settings
from database.models.users import get_user_db
from dependencies import get_db_session
from web.users.schemas import UserCreate
from web.users.users import get_user_manager

logging_config.dictConfig(settings.LOGGING)
logger = logging.getLogger("control")


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
                logger.info(f"User created {user}")
                return user
    except UserAlreadyExists:
        logger.error(f"User {email} already exists")


async def main():
    async with get_async_session_context() as session:
        await create_user(
            session=session,
            email=settings.SUPERUSER_EMAIL,
            password=settings.SUPERUSER_PASSWORD,
            name=settings.SUPERUSER_NAME,
            last_name=settings.SUPERUSER_LAST_NAME,
        )
        # await create_user(
        #     session=session,
        #     email=settings.SUPERUSER_EMAIL_2,
        #     password=settings.SUPERUSER_PASSWORD_2,
        #     name=settings.SUPERUSER_NAME_2,
        #     last_name=settings.SUPERUSER_LAST_NAME_2,
        # )


if __name__ == "__main__":
    asyncio.run(main())
