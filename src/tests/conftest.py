import os, sys

import pytest_asyncio

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)
import asyncio
import json
import pytest

from httpx import AsyncClient, ASGITransport

from app import create_app
from state import SensorsState
from dependencies import get_mqtt, get_state, get_db_session
from web.users.users import current_superuser


class FakeMQTT:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload=None, qos=0):
        if isinstance(payload, (dict, list)):
            payload = json.loads(json.dumps(payload))
        self.published.append((topic, payload, qos))


class FakeDBSession:
    def __init__(self):
        self._objects = []

    async def scalar(self, _query):
        return None

    def add(self, obj):
        self._objects.append(obj)

    async def commit(self):
        pass


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    app = create_app()
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    app.state.sensors = SensorsState()
    app.state.mqtt = FakeMQTT()
    app.dependency_overrides[get_state] = lambda: app.state.sensors
    app.dependency_overrides[get_mqtt] = lambda: app.state.mqtt
    app.dependency_overrides[current_superuser] = lambda: True
    app.dependency_overrides[get_db_session] = lambda: FakeDBSession()
    return app


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url='http://test/api/v1'
    ) as ac:
        yield ac
