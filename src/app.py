import asyncio
import logging.config
import json

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from gmqtt import Client as MQTTClient
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.responses import PlainTextResponse
from starlette.staticfiles import StaticFiles

import settings
from core.simple_cache import Cache
from monitoring.instumentator import verify_metrics_creds
from routers import api_v1_router
from settings import (
    LOGGING,
    MQTT_BROKER,
    MQTT_PORT,
    INACTIVE_AFTER,
    CLEAN_PERIOD,
    DELETE_AFTER,
)
from state import SensorsState


logging.config.dictConfig(LOGGING)


logger = logging.getLogger('control')


def setup_routes(app: FastAPI):
    app.include_router(api_v1_router)
    app.add_route('/ping/', lambda _request: PlainTextResponse('pong'))


origins = [
    'capacitor://localhost',
    '192.168.1.121',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://0.0.0.0:3000',
    'http://51.250.86.226',
    'http://app.fitboxing.pro',
    'https://app.fitboxing.pro',
    'http://localhost:4000',
    'http://localhost:8500',
    'https://fitbox.bounceme.net',
    'https://683da30323fc1d0008f313d3--sunny-bonbon-2effb7.netlify.app',
    'https://tver.fitboxing.pro',
    'http://tver.fitboxing.pro',
]


def create_app() -> FastAPI:
    app = FastAPI(
        debug=True,
        docs_url='/api/v1/docs',
        openapi_url='/api/openapi.json',
    )
    setup_routes(app)
    add_pagination(app)
    app.mount(
        f'/api/{settings.STATIC_FOLDER}',
        StaticFiles(directory='static'),
        name='static',
    )
    # logging_config.dictConfig(settings.LOGGING)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
    ).instrument(app, metric_namespace='fitbox').expose(
        app,
        endpoint='/metrics',
        include_in_schema=False,
        dependencies=[Depends(verify_metrics_creds)],
    )

    @app.on_event('startup')
    async def _startup() -> None:
        client = MQTTClient('api-backend')
        app.state.mqtt = client
        app.state.sensors = SensorsState()
        app.state.cache = Cache(
            settings.REDIS_URL,
            namespace="fitbox",
        )

        try:
            await app.state.cache.set("init:ping", "1", ttl=5)
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.exception("Redis connect failed: %s", e)

        def _on_connect(client, flags, rc, properties):
            logger.info("🔌 MQTT connected: flags=%s rc=%s", flags, rc)
            client.subscribe('fitbox/ping', qos=1)
            logger.info("📡 Subscribed to fitbox/ping")

        def _on_disconnect(client, packet, exc=None):
            logger.warning("🔌 MQTT disconnected: exc=%s", exc)

        def _on_subscribe(client, mid, qos, properties=None):
            logger.info("✅ MQTT subscribe ack mid=%s qos=%s", mid, qos)

        client.on_connect = _on_connect
        client.on_disconnect = _on_disconnect
        client.on_subscribe = _on_subscribe

        async def _on_msg(client, topic, payload, qos, properties):
            try:
                logger.debug("📥 MQTT message: topic=%s qos=%s payload=%r", topic, qos, payload)
                if topic == 'fitbox/ping':
                    data = json.loads(payload)
                    device_id = str(data.get('device_id') or '').strip()
                    ip = data.get('ip')
                    if device_id:
                        await app.state.sensors.touch(device_id, ip=ip)
                        logger.debug('🟢 touched %s (ip=%s)', device_id, ip)
            except Exception as e:
                logger.exception("❌ error in on_message: %s", e)

        client.on_message = _on_msg


        async def _connect():
            try:
                await asyncio.wait_for(
                    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30),
                    timeout=5,
                )
                logger.info('✅ MQTT connected')
                client.subscribe('fitbox/ping', qos=1)
                logger.info("📡 (fallback) Subscribed to fitbox/ping")
            except (asyncio.TimeoutError, OSError) as e:
                logger.warning('⚠️  MQTT not connected: %s', e)

        asyncio.create_task(_connect())

        async def _janitor():
            while True:
                await app.state.sensors.maintain(INACTIVE_AFTER, DELETE_AFTER)
                await asyncio.sleep(CLEAN_PERIOD)

        asyncio.create_task(_janitor())

    @app.on_event('shutdown')
    async def _shutdown() -> None:
        await app.state.mqtt.disconnect()
        cache = getattr(app.state, "cache", None)
        if cache:
            await cache.close()

    return app
