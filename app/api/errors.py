import logging

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.domain.errors import ConflictError, NotFoundError

logger = logging.getLogger(__name__)


def error_response(status, message):
    return JSONResponse(status_code=status, content={
        "success": False, "message": message, "data": None})


def register_error_handlers(app):
    @app.exception_handler(NotFoundError)
    async def not_found(request, error):
        return error_response(404, str(error))

    @app.exception_handler(ConflictError)
    async def conflict(request, error):
        return error_response(409, str(error))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, error):
        details = "; ".join(
            f"{'.'.join(map(str, item['loc']))}: {item['msg']}" for item in error.errors())
        return error_response(422, f"Validation error: {details}")

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        result = error_response(error.status_code, str(error.detail))
        if error.headers:
            result.headers.update(error.headers)
        return result

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        logger.error("Unhandled request error", exc_info=error)
        return error_response(500, "Internal server error")
