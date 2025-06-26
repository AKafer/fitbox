from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING
from fastapi import Request

if TYPE_CHECKING:
    from state import SensorsState
from gmqtt import Client as MQTTClient
from database.orm import Session


async def get_db_session() -> AsyncSession:
    async with Session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_state(request: Request) -> "SensorsState":
    return request.app.state.sensors


def get_mqtt(request: Request) -> MQTTClient:
    return request.app.state.mqtt
