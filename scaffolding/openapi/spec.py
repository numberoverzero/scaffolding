import falcon
import yaml
from typing import Optional, Callable, Any, Set
from . import parsing, validation

__all__ = ["Specification", "Operation"]


class Specification:
    raw: dict
    operations: "Operations"

    def __init__(self, spec: dict) -> None:
        self.raw = parsing.flatten_spec(spec)
        self.operations = Operations(self)

    @classmethod
    def from_file(cls, path: str) -> "Specification":
        with open(path, "r") as f:
            spec = yaml.safe_load(f)
        return cls(spec)

    @property
    def paths(self) -> Set[str]:
        return set(self.raw["paths"].keys())


class Operation:
    id: str
    verb: str
    path: str
    raw: dict
    spec: Specification
    handler: Optional[Callable[[Any], None]] = None

    __hash__ = object.__hash__

    def __init__(self, raw: dict, spec: Specification) -> None:
        self.id = parsing.get_id(raw)
        self.path, self.verb = parsing.get_route(raw)
        self.raw = raw
        self.spec = spec
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

    @property
    def ids(self) -> Set[str]:
        return set(self._by_id.keys())

    def __iter__(self):
        return iter(list(self._by_id.values()))
