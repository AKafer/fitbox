from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

import settings


BaseModel = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_POOL_MAX_OVERFLOW
)
Session = async_sessionmaker(
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession,
    bind=engine
)
