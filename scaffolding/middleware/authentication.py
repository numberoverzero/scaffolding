import base64
import logging
from typing import Any, Dict, List, Optional, Tuple

import falcon

from ..exc import Exceptions
from ..openapi import Specification


logger = logging.getLogger(__name__)
MISSING = Exceptions.missing_authentication()
MALFORMED = Exceptions.malformed_authentication()


__all__ = [
    "AuthenticationMiddleware", "OpenApiAuthentication",
    "api_key_auth", "basic_auth", "bearer_auth", "no_auth",
]


class AuthenticationMiddleware:
    """
    You must implement the following methods:
        get_auth_mechanisms_for_route
        get_login_principal
        get_token_principal
    """
    def __init__(self):
        self.handlers = {
            "basic": self.get_login_principal,
            "token": self.get_token_principal,
            "none": self.get_anonymous_principal,
        }

    def get_auth_mechanisms_for_route(self, req: falcon.Request) -> List[Tuple[str, callable]]:
        """
        For a resource that optionally requires an api token, this should return:
        [self.Mechanism.Bearer, self.Mechanism.NoAuth]
        """
        raise NotImplementedError

    def get_login_principal(self, req: falcon.Request, username: str, password: str) -> Tuple(str, Any):
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

    def get_token_principal(self, req: falcon.Request, token: str) -> Tuple(str, Any):
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
        This is wired into the request as:
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
        for type, parser in mechanisms:
            handler = self.handlers[type]
            material = tuple()
            # mechanisms may not parse requests
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
            # Handlers may raise Exceptions.invalid_login, Exceptions.invalid_token
            # We let that bubble up, don't fall back through invalid credentials
            type, value = handler(req, *material)
            req.context["principal"] = {
                "type": type,
                "value": value
            }
            return
        if last_exc:
            raise last_exc
        raise RuntimeError("Failed to configure credentials and failed to raise")


class OpenApiAuthentication(AuthenticationMiddleware):
    """
        You must implement the following methods:
            get_login_principal
            get_token_principal
        """
    def __init__(self, spec: Specification) -> None:
        super().__init__()
        self.spec = spec
        self.mechanism_cache = {}  # type: Dict[Tuple[str, str], List[Tuple[str, callable]]]

    def get_auth_mechanisms_for_route(self, req: falcon.Request) -> List[Tuple[str, callable]]:
        key = req.uri_template, req.method.lower()
        try:
            return self.mechanism_cache[key]
        except KeyError:
            schemes = self.mechanism_cache[key] = [
                OpenApiAuthentication.translate_scheme_mechanism(scheme)
                for scheme in self.spec.get_security_schemes(*key)
            ]
            return schemes

    @staticmethod
    def translate_scheme_mechanism(scheme: dict) -> Tuple[str, callable]:
        if not scheme:
            return no_auth()
        t = scheme["type"]
        if t == "http":
            s = scheme["scheme"]
            if s == "basic":
                return basic_auth()
            elif s == "bearer":
                return bearer_auth()
            else:
                raise RuntimeError(f"unexpected scheme {s!r} for type 'http'")
        elif t == "apiKey":
            return api_key_auth(scheme["name"], scheme["loc"])
        else:
            raise RuntimeError(f"only basic and bearer schemes are supported")


def basic_auth() -> Tuple[str, callable]:
    """Returns a tuple for use in AuthenticationMiddleware.get_auth_mechanisms_for_route"""
    def parse(req: falcon.Request) -> Optional[Tuple[str, str]]:
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
    return "basic", parse


def bearer_auth() -> Tuple[str, callable]:
    """Returns a tuple for use in AuthenticationMiddleware.get_auth_mechanisms_for_route"""
    def parse(req: falcon.Request) -> Optional[str]:
        header = req.auth  # type: str
        if not header:
            return None
        if not header.startswith("Bearer "):
            return None
        token = header[7:]
        if not token:
            raise MALFORMED
        return token
    return "token", parse


def api_key_auth(name: str, loc: str) -> Tuple[str, callable]:
    """Returns a tuple for use in AuthenticationMiddleware.get_auth_mechanisms_for_route"""
    def parse(req: falcon.Request) -> Optional[str]:
        if loc == "cookie":
            return req.cookies.get(name)
        elif loc == "header":
            return req.get_header(name)
        elif loc == "query":
            return req.get_param(name)
        else:
            raise RuntimeError(f"unknown apiKey location {loc!r}")
    return "token", parse


def no_auth() -> Tuple[str, callable]:
    """Returns a tuple for use in AuthenticationMiddleware.get_auth_mechanisms_for_route"""
    # no method of parsing the request
    return "none", None
