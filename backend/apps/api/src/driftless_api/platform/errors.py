"""Map domain errors to consistent JSON problem responses."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from driftless_core.errors import (
    ConflictError,
    ConnectionFailedError,
    DriftlessError,
    NotFoundError,
    UnsupportedFeatureError,
)

_STATUS: dict[type[DriftlessError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    UnsupportedFeatureError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ConnectionFailedError: status.HTTP_502_BAD_GATEWAY,
}


def status_for(error: DriftlessError) -> int:
    for cls in type(error).__mro__:
        if cls in _STATUS:
            return _STATUS[cls]  # type: ignore[index]
    return status.HTTP_400_BAD_REQUEST


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DriftlessError)
    async def _handle(request: Request, exc: DriftlessError) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
        body = {"error": exc.to_dict(), "request_id": getattr(request.state, "request_id", None)}
        return JSONResponse(status_code=status_for(exc), content=body)
