import logging

from fastapi import APIRouter, Depends, HTTPException
from gmqtt import Client as MQTTClient

from state import SensorsState
from dependencies import get_mqtt, get_state
from settings import MQTT_TOPIC_START, MQTT_TOPIC_STOP
from web.sensors.schemas import HitsChunk
from web.users.users import current_superuser

router = APIRouter(
    prefix='/sensors',
    tags=['sensors'],
)

logger = logging.getLogger(__name__)


@router.post('/register')
async def register_device(
    device: dict,
    st: SensorsState = Depends(get_state),
) -> dict:
    if not (d_id := device.get('device_id')) or not (ip := device.get('ip')):
        raise HTTPException(400, 'device_id и ip обязательны')
    st.devices[d_id] = ip
    logger.info('✅ Зарегистрировано %s → %s', d_id, ip)
    return {'status': 'registered', 'count': len(st.devices)}


@router.get('/start_all', dependencies=[Depends(current_superuser)])
async def start_all(
    mqtt: MQTTClient = Depends(get_mqtt),
    st: SensorsState = Depends(get_state),
) -> dict:
    mqtt.publish(MQTT_TOPIC_START, 'ALL', qos=1)
    st.training_active = True
    return {'status': 'start sent', 'training_active': st.training_active}


@router.get('/stop_all', dependencies=[Depends(current_superuser)])
async def stop_all(
    mqtt: MQTTClient = Depends(get_mqtt),
    st: SensorsState = Depends(get_state),
) -> dict:
    mqtt.publish(MQTT_TOPIC_STOP, 'ALL', qos=1)
    st.training_active = False
    logger.info('📢 STOP всем устройствам')
    return {'status': 'stop sent', 'training_active': st.training_active}


@router.get('/status', dependencies=[Depends(current_superuser)])
async def status(st: SensorsState = Depends(get_state)) -> dict:
    return {
        'devices_registered': len(st.devices),
        'training_active': st.training_active,
        'devices': st.devices,
    }


@router.post('/api/v1/hits/bulk')
async def receive_hits(data: HitsChunk) -> dict:
    logger.info(
        '📥 Пакет от %s (sess %s), %d ударов',
        data.device_id,
        data.session_id,
        len(data.hits),
    )
    return {'status': 'received', 'hits': len(data.hits)}
