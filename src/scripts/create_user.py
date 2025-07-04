import asyncio

import settings
from web.common.services import create_user, get_async_session_context


async def main():
    async with get_async_session_context() as session:
        await create_user(
            session=session,
            email=settings.SUPERUSER_EMAIL,
            password=settings.SUPERUSER_PASSWORD,
            name=settings.SUPERUSER_NAME,
            last_name=settings.SUPERUSER_LAST_NAME,
        )


if __name__ == '__main__':
    asyncio.run(main())
