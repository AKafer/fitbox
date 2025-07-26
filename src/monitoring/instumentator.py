import logging.config
import os
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from starlette import status
from starlette.exceptions import HTTPException

from settings import LOGGING

logging.config.dictConfig(LOGGING)


security = HTTPBasic()


def verify_metrics_creds(creds: HTTPBasicCredentials = Depends(security)):
    """Basic‑auth guard for /metrics."""
    u_ok = secrets.compare_digest(
        creds.username, os.getenv('METRICS_USER', '')
    )
    p_ok = secrets.compare_digest(
        creds.password, os.getenv('METRICS_PASSWORD', '')
    )
    if not (u_ok and p_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={'WWW-Authenticate': 'Basic'},
        )
