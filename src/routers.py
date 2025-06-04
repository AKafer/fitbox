from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from src.main_schemas import ResponseErrorBody

api_v1_router = APIRouter(
    prefix='/api/v1',
    dependencies=[],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            'model': ResponseErrorBody,
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            'model': ResponseErrorBody,
        },
    },
)
