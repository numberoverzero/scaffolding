import functools
import logging

import marshmallow as ma

from ..exc import Exceptions
from .parsing import walk_path


logger = logging.getLogger(__name__)
error_messages = {
    "null": "missing",
    "required": "missing",
    "invalid": "type",
    "type": "type",
    "validator_failed": "type"
}
field_classes = {
    "boolean": functools.partial(ma.fields.Boolean, truthy={True}, falsy={False}),
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
    schema = type(f"{id}#parameters", (ma.Schema,), fields)(unknown=ma.RAISE)
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
    schema = type(f"{id}#body", (ma.Schema,), fields)(unknown=ma.RAISE)
    return schema


def validate_params(schema: ma.Schema, params: dict) -> None:
    _validate(schema, params)


def validate_body(schema: ma.Schema, body: dict) -> None:
    _validate(schema, body)


def _validate(schema: ma.Schema, blob: dict) -> None:
    sn = schema.__class__.__name__
    logger.debug(f"{sn} started validation")
    try:
        loaded_blob = schema.load(blob)
    except ma.ValidationError as e:
        logger.debug(f"{sn} failed validation")
        errors = e.messages
        # TODO for now just send back the first error
        name, error = next(iter(errors.items()))
        if len(error) > 1:
            logger.info(f"multiple errors for param {name} but only returning first {error}")
        error = error[0]
        if error == "type":
            raise Exceptions.invalid_parameter(name, blob[name], type=schema.fields[name].type_name)
        elif error == "missing":
            raise Exceptions.missing_parameter(name)
        elif error not in error_messages:
            # XXX @numberoverzero marshmallow doesn't have a complete list
            # XXX of keys to provide for default_errors, and some (like Unknown field)
            # XXX don't have a key at all.  So we'll have to be do some string inspection here :(
            if error == "Unknown field.":
                raise Exceptions.unknown_parameter(name)
        else:
            logger.warning(f"unexpected error message during validation: {name} {error}")
            raise Exceptions.internal_error()
    else:
        logger.debug(f"{sn} succeeded validation")
        blob.clear()
        blob.update(loaded_blob)
