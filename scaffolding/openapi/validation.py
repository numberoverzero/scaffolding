import marshmallow as ma
from ..exc import Exceptions

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

__all__ = ["new_param_schema", "validate_params"]


def new_param_schema(operation: dict) -> ma.Schema:
    id = operation["operationId"]
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
    return schema


def validate_params(schema: ma.Schema, params: dict) -> None:
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
