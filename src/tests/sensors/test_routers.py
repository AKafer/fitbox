from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from settings import (
    INACTIVE_AFTER,
    DELETE_AFTER,
    MQTT_TOPIC_START,
    MQTT_TOPIC_STOP,
)
from web.users.users import current_superuser


@pytest.mark.asyncio
async def test_register_and_status_fields(client, app):
    r = await client.post(
        '/sensors/register',
        json={'device_id': 'BAG02-M', 'ip': '192.168.1.47'},
    )
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'registered'

    r = await client.get('/sensors/status')
    assert r.status_code == 200
    status = r.json()
    assert status['devices_registered'] == 1
    dev = status['devices']['BAG02-M']
    assert dev['ip'] == '192.168.1.47'
    assert dev['active'] is True
    assert dev['ip_mismatch'] is False
    assert dev['mismatch_ip'] is None
    assert 'T' in dev['last_seen']


@pytest.mark.asyncio
async def test_inactive_then_deleted_via_maintain_and_status(client, app):
    await app.state.sensors.upsert('OLD', '10.0.0.1')
    snap = await app.state.sensors.snapshot()
    snap['OLD'].last_seen = datetime.now(timezone.utc) - timedelta(minutes=2)
    await app.state.sensors.maintain(INACTIVE_AFTER, DELETE_AFTER)

    r = await client.get('/sensors/status')
    dev = r.json()['devices']['OLD']
    assert dev['active'] is False
    snap['OLD'].last_seen = datetime.now(timezone.utc) - timedelta(minutes=25)
    await app.state.sensors.maintain(INACTIVE_AFTER, DELETE_AFTER)
    r = await client.get('/sensors/status')
    assert 'OLD' not in r.json()['devices']


@pytest.mark.asyncio
async def test_hits_bulk_actualizes_state(client, app, monkeypatch):
    await app.state.sensors.upsert('BAG02-M', '192.168.1.47')
    snap = await app.state.sensors.snapshot()
    snap['BAG02-M'].active = False

    payload = {
        'session_id': '1',
        'sprint_id': '1',
        'device_id': 'BAG02-M',
        'hits': [],
        'blink_interval': '100',
    }
    resp = await client.post('/sensors/hits/bulk', json=payload)
    assert resp.status_code == 200
    r = await client.get('/sensors/status')
    dev = r.json()['devices']['BAG02-M']
    assert dev['active'] is True


@pytest.mark.asyncio
async def test_start_all_publishes_and_sets_training_active(client, app):
    body = {
        'session_id': '7',
        'sprint_id': '3',
        'blink_interval': 250,
        'led_on_ms': 120,
    }
    r = await client.post('/sensors/start_all', json=body)
    assert r.status_code == 200
    data = r.json()
    assert data['training_active'] is True
    published = app.state.mqtt.published
    assert any(t == MQTT_TOPIC_START for (t, _, _) in published), published


@pytest.mark.asyncio
async def test_stop_all_publishes_and_unsets_training_active(client, app):
    await client.post(
        '/sensors/start_all',
        json={
            'session_id': '7',
            'sprint_id': '3',
            'blink_interval': 100,
            'led_on_ms': 50,
        },
    )
    r = await client.get('/sensors/stop_all')
    assert r.status_code == 200
    data = r.json()
    assert data['training_active'] is False
    published = app.state.mqtt.published
    assert any(t == MQTT_TOPIC_STOP for (t, _, _) in published), published


@pytest.mark.asyncio
async def test_ip_mismatch_reflected_in_status(client, app):
    await client.post(
        '/sensors/register', json={'device_id': 'X1', 'ip': '172.16.0.10'}
    )
    await app.state.sensors.touch('X1', ip='172.16.0.99')
    r = await client.get('/sensors/status')
    dev = r.json()['devices']['X1']
    assert dev['active'] is False
    assert dev['ip_mismatch'] is True
    assert dev['mismatch_ip'] == '172.16.0.99'


@pytest.mark.asyncio
async def test_status_requires_auth(client, app):
    def deny_dep():
        raise HTTPException(status_code=401, detail='unauthorized')

    old = app.dependency_overrides.get(current_superuser)
    app.dependency_overrides[current_superuser] = deny_dep
    try:
        r = await client.get('/sensors/status')
        assert r.status_code == 401
    finally:
        if old is None:
            app.dependency_overrides.pop(current_superuser, None)
        else:
            app.dependency_overrides[current_superuser] = old
