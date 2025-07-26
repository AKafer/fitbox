import asyncio
import logging.config

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from gmqtt import Client as MQTTClient
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.responses import PlainTextResponse

from monitoring.instumentator import verify_metrics_creds
from routers import api_v1_router
from settings import LOGGING, MQTT_BROKER, MQTT_PORT
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

        async def _connect():
            try:
                await asyncio.wait_for(
                    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30),
                    timeout=5,
                )
                logger.info('✅ MQTT connected')
            except (asyncio.TimeoutError, OSError) as e:
                logger.warning('⚠️  MQTT not connected: %s', e)

        asyncio.create_task(_connect())

    @app.on_event('shutdown')
    async def _shutdown() -> None:
        await app.state.mqtt.disconnect()

    return app
