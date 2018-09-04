import enum
import logging
from typing import Any

import falcon


__all__ = ["Exceptions", "install_handler"]
logger = logging.getLogger(__name__)


class _ErrorCode(enum.Enum):
    NotFound = (404, falcon.status.HTTP_404, "NotFound")
    NotAuthenticated = (401, falcon.status.HTTP_401, "NotAuthenticated")
    InvalidParameter = (400, falcon.status.HTTP_400, "InvalidParameter")
    MissingParameter = (400, falcon.status.HTTP_400, "MissingParameter")
    InternalError = (500, falcon.status.HTTP_500, "InternalError")

    def __init__(self, http_status_code: int, http_status_line: str, id: str) -> None:
        self.http_status_code = http_status_code
        self.http_status_line = http_status_line
        self.id = id

    def new(self, message: str) -> "_StructuredError":
        return _StructuredError(self, message)


class _StructuredError(Exception):
    def __init__(self, code: _ErrorCode, message: str):
        self.code = code
        self.message = message

    @staticmethod
    def handle(ex: "_StructuredError", req: falcon.Request, resp: falcon.Response, *_, **__) -> None:
        log = logger.error if ex.code.http_status_code == 500 else logger.info
        log(f"{ex.code.http_status_code} {ex.code.id} during {req.method} {req.path}")
        resp.status = ex.code.http_status_line
        resp.media = {
            "code": ex.code.id,
            "message": ex.message
        }


class Exceptions:
    cls = _StructuredError

    @staticmethod
    def invalid_parameter(name: str, value: Any, constraint: str=None, type: str=None) -> Exception:
        if constraint:
            message = f"{name!r} was {value!r} but must {constraint}"
        elif type:
            message = f"{name!r} was {value!r} but must be a {type}"
        else:
            message = f"{name!r} cannot be {value!r}"
        return _ErrorCode.InvalidParameter.new(message)

    @staticmethod
    def missing_parameter(name: str) -> Exception:
        message = f"{name!r} is required and must not be null"
        return _ErrorCode.MissingParameter.new(message)

    @staticmethod
    def invalid_login() -> Exception:
        message = "username or password are invalid"
        return _ErrorCode.NotAuthenticated.new(message)

    @staticmethod
    def invalid_token() -> Exception:
        message = "api token is invalid"
        return _ErrorCode.NotAuthenticated.new(message)

    @staticmethod
    def malformed_authentication() -> Exception:
        message = "authentication mechanism is malformed"
        return _ErrorCode.NotAuthenticated.new(message)

    @staticmethod
    def missing_authentication() -> Exception:
        message = "authentication is missing"
        return _ErrorCode.NotAuthenticated.new(message)

    @staticmethod
    def internal_error() -> Exception:
        message = "An internal error occurred"
        return _ErrorCode.InternalError.new(message)


def install_handler(api: falcon.API) -> None:
    api.add_error_handler(_StructuredError)
