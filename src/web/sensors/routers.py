import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from gmqtt import Client as MQTTClient
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import StreamingResponse

from constants import ALL_DEVICES_ID, CMD_START, DEFAULT_BLINK_INTERVAL
from database.models import Sprints
from dependencies import get_db_session, get_mqtt, get_state
from main_schemas import ResponseErrorBody
from settings import MQTT_TOPIC_START, MQTT_TOPIC_STOP
from state import SensorsState
from web.sensors.schemas import HitsChunk, StartSprintInptut, RegisterInput
from web.sensors.services import (
    build_sprint_hits_excel,
    calculate_sprint_metrics,
)
from web.users.users import current_superuser

router = APIRouter(
    prefix='/sensors',
    tags=['sensors'],
)

logger = logging.getLogger('control')


@router.post('/register')
async def register_device(
    reg_input: RegisterInput, st: SensorsState = Depends(get_state)
) -> dict:
    d_id = reg_input.device_id
    ip = reg_input.ip

    if not d_id or not ip:
        raise HTTPException(400, 'device_id и ip required')

    await st.upsert(d_id, ip)
    logger.info('✅ Registered %s → %s', d_id, ip)
    snapshot = await st.snapshot()
    return {'status': 'registered', 'count': len(snapshot)}


@router.post('/start_all', dependencies=[Depends(current_superuser)])
async def start_all(
    start_input: StartSprintInptut,
    mqtt: MQTTClient = Depends(get_mqtt),
    st: SensorsState = Depends(get_state),
) -> dict:
    payload = {
        'cmd': CMD_START,
        'device_id': ALL_DEVICES_ID,
        'session_id': start_input.session_id,
        'sprint_id': start_input.sprint_id,
        'blink_interval': start_input.blink_interval,
        'led_on_ms': start_input.led_on_ms,
    }
    mqtt.publish(MQTT_TOPIC_START, payload=payload, qos=1)
    st.training_active = True
    return {
        'status': 'start sent',
        'training_active': st.training_active,
        'sent': payload,
    }


@router.get('/stop_all', dependencies=[Depends(current_superuser)])
async def stop_all(
    mqtt: MQTTClient = Depends(get_mqtt),
    st: SensorsState = Depends(get_state),
) -> dict:
    mqtt.publish(MQTT_TOPIC_STOP, 'ALL', qos=1)
    st.training_active = False
    logger.info('📢 STOP all devices')
    return {'status': 'stop sent', 'training_active': st.training_active}


@router.get(
    '/status',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_superuser)],
)
async def get_status(st: SensorsState = Depends(get_state)) -> dict:
    snapshot = await st.snapshot()
    return {
        'devices_registered': len(snapshot),
        'training_active': st.training_active,
        'devices': {
            did: {
                'ip': info.ip,
                'last_seen': info.last_seen.isoformat(),
                'active': info.active,
                'ip_mismatch': info.ip_mismatch,
                'mismatch_ip': info.mismatch_ip,
            }
            for did, info in snapshot.items()
        },
    }


@router.post(
    '/hits/bulk',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_409_CONFLICT: {
            'model': ResponseErrorBody,
            'description': 'Concurrent update, please retry',
        }
    }
)
async def receive_hits(
    input_chunk: HitsChunk,
    db_session: AsyncSession = Depends(get_db_session),
    st: SensorsState = Depends(get_state),
) -> dict:
    logger.info(
        '(slot_id %s, sprint_id %s, sensor_id %s): accept: %d hits - is_last: %s',
        input_chunk.session_id,
        input_chunk.sprint_id,
        input_chunk.device_id,
        len(input_chunk.hits),
        input_chunk.is_last,
    )
    await st.update_on_hit(input_chunk.device_id)
    for _ in range(2):
        try:
            query = (
                select(Sprints)
                .where(
                    and_(
                        Sprints.slot_id == int(input_chunk.session_id),
                        Sprints.sprint_id == int(input_chunk.sprint_id),
                        Sprints.sensor_id == input_chunk.device_id,
                    )
                )
                .with_for_update()
            )
            sprint = await db_session.scalar(query)
            if sprint is None:
                sprint = Sprints(
                    slot_id=int(input_chunk.session_id),
                    sprint_id=int(input_chunk.sprint_id),
                    sensor_id=input_chunk.device_id,
                    created_at=datetime.now(timezone.utc),
                    data={'hits': []},
                )
            db_session.add(sprint)

            hits_list = sprint.data.setdefault('hits', [])
            new_hits = [h.model_dump() for h in input_chunk.hits]
            hits_list.extend(new_hits)
            sprint.data['total_hits'] = len(hits_list)
            sprint.data['hits'] = hits_list
            sprint.data['blink_interval'] = input_chunk.blink_interval

            logger.debug(
                '(slot_id %s, sprint_id %s, sensor_id %s): added: %d, total %d',
                input_chunk.session_id,
                input_chunk.sprint_id,
                input_chunk.device_id,
                len(new_hits),
                sprint.data['total_hits'],
            )

            if input_chunk.is_last:
                sprint.result = calculate_sprint_metrics(
                    sprint.data.get('hits', []),
                    float(sprint.data.get('blink_interval') or DEFAULT_BLINK_INTERVAL),
                    int(sprint.data.get('total_hits', 0)),
                )
            await db_session.commit()

            return {
                'status': 'ok',
                'added': len(new_hits),
                'total': sprint.data['total_hits'],
                'is_last': input_chunk.is_last,
                'result': sprint.result or {},
            }
        except IntegrityError:
            await db_session.rollback()
            continue

    raise HTTPException(409, 'Concurrent update, please retry')


@router.get('/hits/export')
async def export_sprint_hits(
    slot_id: int,
    sprint_id: int,
    db_session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(Sprints)
        .where(
            and_(
                Sprints.slot_id == slot_id,
                Sprints.sprint_id == sprint_id,
            )
        )
        .order_by(Sprints.sensor_id.asc())
    )
    sprints = (await db_session.scalars(query)).all()
    if not sprints:
        raise HTTPException(
            status_code=404,
            detail='No sprints found for the given slot and sprint IDs.',
        )

    xlsx_bytes = build_sprint_hits_excel(slot_id, sprint_id, sprints)
    filename = f'sprint_{slot_id}_{sprint_id}.xlsx'

    return StreamingResponse(
        iter([xlsx_bytes]),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
