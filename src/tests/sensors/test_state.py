import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from state import SensorsState


@pytest.mark.asyncio
async def test_upsert_sets_time_and_active():
    st = SensorsState()
    await st.upsert('BAG02-M', '192.168.1.47')
    snap = await st.snapshot()
    assert 'BAG02-M' in snap
    info = snap['BAG02-M']
    assert info.ip == '192.168.1.47'
    assert info.active is True
    assert isinstance(info.last_seen, datetime)


@pytest.mark.asyncio
async def test_touch_updates_time_and_keeps_active():
    st = SensorsState()
    await st.upsert('BAG02-M', '192.168.1.47')
    before = (await st.snapshot())['BAG02-M'].last_seen
    await asyncio.sleep(0.01)
    await st.touch('BAG02-M', ip='192.168.1.47')
    after = (await st.snapshot())['BAG02-M'].last_seen
    assert after > before
    assert (await st.snapshot())['BAG02-M'].active is True


@pytest.mark.asyncio
async def test_maintain_inactive_then_delete():
    st = SensorsState()
    await st.upsert('D1', '1.1.1.1')
    snap = await st.snapshot()
    snap['D1'].last_seen = datetime.now(timezone.utc) - timedelta(minutes=5)
    await st.maintain(
        inactive_after=timedelta(minutes=1), delete_after=timedelta(minutes=20)
    )
    info = (await st.snapshot())['D1']
    assert info.active is False
    snap['D1'].last_seen = datetime.now(timezone.utc) - timedelta(minutes=25)
    await st.maintain(
        inactive_after=timedelta(minutes=1), delete_after=timedelta(minutes=20)
    )
    snap2 = await st.snapshot()
    assert 'D1' not in snap2


@pytest.mark.asyncio
async def test_update_on_hit_revives_if_not_mismatch():
    st = SensorsState()
    await st.upsert('D2', '2.2.2.2')
    s = await st.snapshot()
    s['D2'].active = False
    await st.update_on_hit('D2')
    assert (await st.snapshot())['D2'].active is True


@pytest.mark.asyncio
async def test_touch_ip_mismatch_quarantine_policy():
    st = SensorsState(ip_mismatch_policy='quarantine')
    await st.upsert('D3', '3.3.3.3')
    await st.touch('D3', ip='9.9.9.9')
    info = (await st.snapshot())['D3']
    assert info.active is False
    assert info.ip_mismatch is True
    assert info.mismatch_ip == '9.9.9.9'
    assert info.ip == '3.3.3.3'


@pytest.mark.asyncio
async def test_touch_ip_mismatch_update_policy():
    st = SensorsState(ip_mismatch_policy='update')
    await st.upsert('D4', '4.4.4.4')
    await st.touch('D4', ip='10.10.10.10')
    info = (await st.snapshot())['D4']
    assert info.active is True
    assert info.ip_mismatch is False
    assert info.ip == '10.10.10.10'


@pytest.mark.asyncio
async def test_touch_ip_mismatch_drop_policy():
    st = SensorsState(ip_mismatch_policy='drop')
    await st.upsert('D5', '5.5.5.5')
    await st.touch('D5', ip='11.11.11.11')
    snap = await st.snapshot()
    assert 'D5' not in snap
