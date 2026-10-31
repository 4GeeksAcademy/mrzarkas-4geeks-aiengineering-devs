"""OpenAPI descriptions of existing errors; no exception handling changes."""

from http import HTTPStatus

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    # FastAPI validation uses a list; business HTTPExceptions use a string.
    detail: str | list[dict]


def error_responses(*codes: int) -> dict:
    return {code: {"model": ErrorResponse, "description": HTTPStatus(code).phrase} for code in codes}
