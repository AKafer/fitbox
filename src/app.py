from logging import config as logging_config

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse
from routers import api_v1_router


def setup_routes(app: FastAPI):
    app.include_router(api_v1_router)
    app.add_route("/ping/", lambda _request: PlainTextResponse('pong'))


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "http://localhost:4000",
    "http://localhost:8500",
    "https://ins-front.ddns.net",
]


def create_app() -> FastAPI:
    app = FastAPI(
        debug=True,
        docs_url="/api/v1/docs",
        openapi_url="/api/openapi.json",
    )
    setup_routes(app)
    add_pagination(app)
    # app.mount(f"/api/{settings.STATIC_FOLDER}", StaticFiles(directory='static'), name='static')
    # logging_config.dictConfig(settings.LOGGING)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
