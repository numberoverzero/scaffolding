from typing import Dict

import falcon
import marshmallow as ma

from ..exc import Exceptions
from ..openapi import OperationKey, Specification, op_key


error_messages = {
    "null": "missing",
    "required": "missing",
    "type": "type",
    "validator_failed": "type"
}
field_classes = {
    "boolean": ma.fields.Boolean,
    "integer": ma.fields.Integer,
    "number": ma.fields.Number,
    "string": ma.fields.String,
}


class OpenApiRequestValidation:
    param_schemas: Dict[OperationKey, ma.Schema]

    def __init__(self, spec: Specification) -> None:
        self.spec = spec
        self._init_param_schemas()

    def _init_param_schemas(self) -> None:
        self.param_schemas = {}
        for id, operation in self.spec.operations.items():
            key = operation["_key"]
            fields = {}
            for param in operation["parameters"]:
                t = param["schema"]["type"]
                field = field_classes[t](
                    required=param.get("required", True),
                    missing=param.get("default", ma.missing),
                    error_messages=error_messages,
                )
                field.location = param["in"]
                field.type_name = t
                fields[param["name"]] = field
            schema = type(f"{id}#parameters", (ma.Schema,), fields)()
            self.param_schemas[key] = schema

    def process_resource(self, req: falcon.Request, resp: falcon.Response, resource, params: dict) -> None:
        key = op_key(req)
        self.collect_params(key, req, params)
        self.validate_params(key, params)

    def collect_params(self, key: OperationKey, req: falcon.Request, params: dict) -> None:
        schema = self.param_schemas[key]
        # cache since req.cookies creates a copy
        cookies = req.cookies
        for name, f in schema.fields.items():
            default = f.missing
            if f.location == "query":
                v = params[name] = req.get_param(name, default=default)
            elif f.location == "header":
                v = params[name] = req.get_header(name, default=default)
            elif f.location == "path":
                v = params[name] = params.get(name, default)
            elif f.location == "cookie":
                v = params[name] = cookies.get(name, default)
            else:
                raise Exceptions.internal_error()
            if f.required and v is ma.missing:
                raise Exceptions.missing_parameter(name)

    def validate_params(self, key: OperationKey, params: dict) -> None:
        schema = self.param_schemas[key]
        data, errors = schema.load(params)
        if errors:
            # TODO for now just send back the first error
            name, error = next(iter(errors.items()))
            if error == "type":
                raise Exceptions.invalid_parameter(name, params[name], type=schema.fields[name].type_name)
            elif error == "missing":
                raise Exceptions.missing_parameter(name)
            else:
                raise Exceptions.internal_error()
        params.clear()
        params.update(data)
