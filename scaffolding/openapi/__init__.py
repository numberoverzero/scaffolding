from typing import Tuple
import falcon
from .spec import Specification, walk_path

__all__ = ["OperationKey", "Specification", "op_key", "walk_path"]


OperationKey = Tuple[str, str]


def op_key(req: falcon.Request) -> OperationKey:
    """falcon.Request -> (/users/{userId}/widgets, post)"""
    return req.uri_template, req.method.lower()
