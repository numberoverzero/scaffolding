import logging
import marshmallow as ma
from ..exc import Exceptions
from .parsing import walk_path

# XXX @numberoverzero
# XXX starting with marshmallow 3.x,
# XXX this can simply use the truthy={True}, falsy={False} __init__ kwargs
# XXX https://github.com/marshmallow-code/marshmallow/issues/762
ma.fields.Boolean.truthy = {True}
ma.fields.Boolean.falsy = {False}

logger = logging.getLogger(__name__)
error_messages = {
    "null": "missing",
    "required": "missing",
    "invalid": "type",
    "type": "type",
    "validator_failed": "type"
}
field_classes = {
    "boolean": ma.fields.Boolean,
    "integer": ma.fields.Integer,
    "number": ma.fields.Number,
    "string": ma.fields.String,
    # "object": ma.fields.Nested  # TODO: support nested objects eventually
}

__all__ = ["new_param_schema", "validate_params", "validate_body", "new_body_schema"]


def new_param_schema(operation: dict) -> ma.Schema:
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
    id = operation["operationId"]
    schema = type(f"{id}#parameters", (ma.Schema,), fields)()
    return schema


def new_body_schema(operation: dict) -> ma.Schema:
    body = walk_path(
        operation,
        "requestBody", "content", "application/json", "schema",
        default={
            "required": [],
            "properties": {},
            "type": "object"
        })
    if body["type"] != "object":
        raise RuntimeError("requestBody must be an object or empty")

    fields = {}
    for name, param in body["properties"].items():
        t = param["type"]
        field = field_classes[t](
            required=name in body.get("required", []),
            missing=param.get("default", ma.missing),
            error_messages=error_messages,
        )
        field.type_name = t
        fields[name] = field
    id = operation["operationId"]
    schema = type(f"{id}#body", (ma.Schema,), fields)()
    return schema


def validate_params(schema: ma.Schema, params: dict) -> None:
    data, errors = schema.load(params)
    if errors:
        # TODO for now just send back the first error
        name, error = next(iter(errors.items()))
        if len(error) > 1:
            logger.info(f"multiple errors for param {name} but only returning first {error}")
        error = error[0]
        if error == "type":
            raise Exceptions.invalid_parameter(name, params[name], type=schema.fields[name].type_name)
        elif error == "missing":
            raise Exceptions.missing_parameter(name)
        else:
            raise Exceptions.internal_error()
    params.clear()
    params.update(data)


def validate_body(schema: ma.Schema, body: dict) -> None:
    data, errors = schema.load(body)
    if errors:
        # TODO for now just send back the first error
        name, error = next(iter(errors.items()))
        if len(error) > 1:
            logger.info(f"multiple errors for param {name} but only returning first {error}")
        error = error[0]
        if error == "type":
            raise Exceptions.invalid_parameter(name, body[name], type=schema.fields[name].type_name)
        elif error == "missing":
            raise Exceptions.missing_parameter(name)
        else:
            raise Exceptions.internal_error()
    body.clear()
    body.update(data)
