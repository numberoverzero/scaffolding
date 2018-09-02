import base64
import enum
import logging
from typing import Any, List, Optional, Tuple

import falcon

from ..exc import Exceptions
logger = logging.getLogger(__name__)
MISSING = Exceptions.missing_authentication()
MALFORMED = Exceptions.malformed_authentication()


__all__ = ["AuthenticationMiddleware"]


def parse_basic(req: falcon.Request) -> Optional[Tuple[str, str]]:
    header = req.auth  # type: str
    if not header:
        return None
    if not header.startswith("Basic "):
        return None
    payload = header[6:]
    try:
        decoded = base64.b64decode(payload.encode()).decode()
    except Exception:
        raise MALFORMED
    if ":" not in decoded:
        raise MALFORMED
    username, password = decoded.split(":", 1)
    return username, password


def parse_bearer(req: falcon.Request) -> Optional[str]:
    header = req.auth  # type: str
    if not header:
        return None
    if not header.startswith("Bearer "):
        return None
    token = header[7:]
    if not token:
        raise MALFORMED
    return token


def parse_none(req: falcon.Request) -> None:
    return None


class AuthenticationMiddleware:
    """
    You must implement the following methods:
        get_auth_mechanisms_for_route
        get_login_principal
        get_token_principal
    """
    class Mechanism(enum.Enum):
        NoAuth = 0
        Basic = 1
        Bearer = 2

    def __init__(self):
        self._pipelines = {
            self.Mechanism.Basic: (parse_basic, self.get_login_principal),
            self.Mechanism.Bearer: (parse_bearer, self.get_token_principal),
            self.Mechanism.NoAuth: (None, self.get_anonymous_principal)
        }

    def get_auth_mechanisms_for_route(self, req: falcon.Request) -> List["AuthenticationMiddleware.Mechanism"]:
        """
        For a resource that optionally requires an api token, this should return:
        [self.Mechanism.Bearer, self.Mechanism.NoAuth]
        """
        raise NotImplementedError

    def get_login_principal(self, username: str, password: str, req: falcon.Request) -> Tuple(str, Any):
        """
        Should return something like:
            ("user", UserObject)
            ("company", CompanyObject)
        These will be wired into the request as:
            >>> req.context["principal"]
            {"type": "user",
             "value": UserObject}
            >>> req.context["principal"]
            {"type": "company",
             "value": CompanyObject}
        """
        raise NotImplementedError

    def get_token_principal(self, token: str, req: falcon.Request) -> Tuple(str, Any):
        """
        Should return something like:
            ("user", UserObject)
            ("company", CompanyObject)
        These will be wired into the request as:
            >>> req.context["principal"]
            {"type": "user",
             "value": UserObject}
            >>> req.context["principal"]
            {"type": "company",
             "value": CompanyObject}
        """
        raise NotImplementedError

    # noinspection PyMethodMayBeStatic
    def get_anonymous_principal(self, req: falcon.Request) -> Tuple(str, Any):
        """
        By default, returns ("none", None)
        This is wired into the requst as:
            >>> req.context["principal"]
            {"type": "none",
             "value": None}
        """
        return "none", None

    def process_request(self, req: falcon.Request, resp: falcon.Response) -> None:
        mechanisms = self.get_auth_mechanisms_for_route(req)
        if not mechanisms:
            logger.warning(f"no auth mechanism for request {req.method} {req.path} {req.uri_template}")
            return

        last_exc = None
        for mechanism in mechanisms:
            parser, handler = self._pipelines[mechanism]
            material = tuple()
            if parser:
                # noinspection PyBroadException
                try:
                    material = parser(req)
                except Exception:
                    last_exc = MALFORMED
                    continue
                else:
                    if material is None:
                        last_exc = MISSING
                        continue
            if handler:
                # handlers may raise Exceptions.invalid_login, Exceptions.invalid_token
                # let that bubble up, don't fall back through invalid credentials
                type, value = handler(*material, req)
                req.context["principal"] = {
                    "type": type,
                    "value": value
                }
                return
        if last_exc:
            raise last_exc
        raise RuntimeError("Failed to configure credentials and failed to raise")
