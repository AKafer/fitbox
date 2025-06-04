from pydantic import BaseModel, conint

TINY_INT = conint(ge=0, le=1)


class ResponseErrorBody(BaseModel):
    detail: str | dict | list


class RetryableResponseErrorBody(ResponseErrorBody):
    retry: bool
