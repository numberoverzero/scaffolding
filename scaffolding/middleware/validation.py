import falcon
import marshmallow as ma

from ..exc import Exceptions
from ..openapi import Operation, Specification


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
    def __init__(self, spec: Specification) -> None:
        self.spec = spec

    def process_resource(self, req: falcon.Request, resp: falcon.Response, resource, params: dict) -> None:
        operation = self.spec.operations.by_req(req)
        OpenApiRequestValidation.collect_params(operation, req, params)
        OpenApiRequestValidation.validate_params(operation, params)

    @staticmethod
    def collect_params(operation: Operation, req: falcon.Request, params: dict) -> None:
        schema = operation.param_schema
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

    @staticmethod
    def validate_params(operation: Operation, params: dict) -> None:
        schema = operation.param_schema
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
