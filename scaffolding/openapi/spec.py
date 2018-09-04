import falcon
import yaml

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


class Operation:
    id: str
    raw: dict
    spec: Specification

    def __init__(self, raw: dict, spec: Specification) -> None:
        self.id = raw["operationId"]
        self.raw = raw
        self.spec = spec
        self.body_schema = validation.new_body_schema(raw)
        self.param_schema = validation.new_param_schema(raw)

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
        for uri_template, verb, raw_operation in parsing.iter_operations(spec.raw):
            id = raw_operation["operationId"]
            route = raw_operation["_route"]
            operation = Operation(raw_operation, spec)
            self._by_id[id] = operation
            self._by_key[route] = operation

    def by_id(self, operation_id: str) -> Operation:
        return self._by_id[operation_id]

    def by_route(self, uri_template: str, method: str) -> Operation:
        return self._by_key[uri_template, method]

    def by_req(self, req: falcon.Request) -> Operation:
        return self.by_route(req.uri_template, req.method.lower())
