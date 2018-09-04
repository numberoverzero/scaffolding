import logging
from typing import Any, Callable, List, Optional, Set

import falcon
import yaml

from . import parsing, validation


__all__ = ["Specification", "Operation"]
logger = logging.getLogger(__name__)


class Specification:
    raw: dict
    operations: "Operations"
    source_filename: Optional[str]=None

    def __init__(self, raw: dict) -> None:
        self.raw = parsing.flatten_spec(raw)
        self.operations = Operations(self)

    @classmethod
    def from_file(cls, path: str) -> "Specification":
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        spec = cls(raw)
        spec.source_filename = path
        return spec

    @property
    def paths(self) -> Set[str]:
        return set(self.raw["paths"].keys())

    def get_security_schema(self, name: str) -> dict:
        return self.raw["components"]["securitySchemes"][name]


class Operation:
    id: str
    verb: str
    path: str
    tags: List[str]
    raw: dict
    spec: Specification
    handler: Optional[Callable[[Any], None]] = None

    __hash__ = object.__hash__

    def __init__(self, raw: dict, spec: Specification) -> None:

        self.raw = raw
        self.spec = spec

        self.id = parsing.get_id(raw)
        self.path, self.verb = parsing.get_route(raw)
        # TODO move to parsing.get_tags
        self.tags = raw["tags"]

        self.body_schema = validation.new_body_schema(raw)
        self.param_schema = validation.new_param_schema(raw)

    @property
    def has_params(self) -> bool:
        return bool(self.param_schema.fields)

    @property
    def has_body(self) -> bool:
        return bool(self.body_schema.fields)

    def validate_params(self, params: dict) -> None:
        validation.validate_params(self.param_schema, params)

    def validate_body(self, body: dict) -> None:
        validation.validate_body(self.body_schema, body)

    @property
    def security_schemas(self) -> List[Optional[dict]]:
        schemas = []
        for name, args in parsing.iter_security_schemas(self.raw):
            if args:
                logger.warning("scaffolding.Operation doesn't support security args")
            if name:
                schemas.append(self.spec.get_security_schema(name))
            else:
                schemas.append(None)
        return schemas


class Operations:
    spec: Specification

    def __init__(self, spec: Specification) -> None:
        self.spec = spec

        self._by_id = {}
        self._by_key = {}
        for _, verb, raw_operation in parsing.iter_operations(spec.raw):
            id = parsing.get_id(raw_operation)
            route = parsing.get_route(raw_operation)
            operation = Operation(raw_operation, spec)
            self._by_id[id] = operation
            self._by_key[route] = operation

    def by_id(self, operation_id: str) -> Operation:
        return self._by_id[operation_id]

    def by_route(self, path: str, method: str) -> Operation:
        return self._by_key[path, method]

    def by_req(self, req: falcon.Request) -> Operation:
        return self.by_route(req.uri_template, req.method.lower())

    def with_path(self, path: str) -> Set[Operation]:
        return {op for op in self if op.path == path}

    def with_tag(self, tag: str) -> Set[Operation]:
        return {op for op in self if tag in op.tags}

    @property
    def ids(self) -> Set[str]:
        return set(self._by_id.keys())

    @property
    def tags(self) -> List[str]:
        seen = set()
        uniq_tags = []
        for op in self:
            for tag in op.tags:
                if tag not in seen:
                    uniq_tags.append(tag)
                    seen.add(tag)
        return uniq_tags

    def __iter__(self):
        return iter(list(self._by_id.values()))
