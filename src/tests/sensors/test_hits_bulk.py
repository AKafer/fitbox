import os, sys, asyncio, json, pytest
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from state import SensorsState
from dependencies import get_mqtt, get_state, get_db_session
from web.users.users import current_superuser


class FakeMQTT:
    def __init__(self): self.published = []
    def publish(self, topic, payload=None, qos=0):
        if isinstance(payload, (dict, list)): payload = json.loads(json.dumps(payload))
        self.published.append((topic, payload, qos))

class FakeDBSessionPersist:
    def __init__(self, fail_commits: int = 0):
        self._objects = []
        self._commit_calls = 0
        self._fail_commits = fail_commits

    async def scalar(self, _query):
        return self._objects[-1] if self._objects else None

    def add(self, obj):
        if obj not in self._objects:
            self._objects.append(obj)

    async def commit(self):
        from sqlalchemy.exc import IntegrityError
        self._commit_calls += 1
        if self._commit_calls <= self._fail_commits:

            raise IntegrityError("INSERT ...", {}, Exception("duplicate key"))

    async def rollback(self):
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
    app.dependency_overrides[get_db_session] = lambda: FakeDBSessionPersist()
    return app

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test/api/v1') as ac:
        yield ac

@pytest.mark.asyncio
async def test_hits_bulk_ok_simple(client, app):
    payload = {
        "session_id": "10",
        "sprint_id": "20",
        "device_id": "DEV-1",
        "hits": [],
        "blink_interval": "100",
        "is_last": False,
    }
    r = await client.post('/sensors/hits/bulk', json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["total"] >= 0
    assert body["is_last"] is False

@pytest.mark.asyncio
async def test_hits_bulk_retries_once_on_integrity_error(client, app):
    session = FakeDBSessionPersist(fail_commits=1)
    old = app.dependency_overrides.get(get_db_session)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        payload = {
            "session_id": "11",
            "sprint_id": "21",
            "device_id": "DEV-2",
            "hits": [],
            "blink_interval": "120",
            "is_last": True,
        }
        r = await client.post('/sensors/hits/bulk', json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["is_last"] is True
        assert session._commit_calls >= 2
    finally:
        app.dependency_overrides[get_db_session] = old

@pytest.mark.asyncio
async def test_hits_bulk_returns_409_after_two_failures(client, app):
    session = FakeDBSessionPersist(fail_commits=2)
    old = app.dependency_overrides.get(get_db_session)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        payload = {
            "session_id": "12",
            "sprint_id": "22",
            "device_id": "DEV-3",
            "hits": [],
            "blink_interval": "150",
            "is_last": True,
        }
        r = await client.post('/sensors/hits/bulk', json=payload)
        assert r.status_code == 409
    finally:
        app.dependency_overrides[get_db_session] = old
