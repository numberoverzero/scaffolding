"""
Used to generate models, controllers, views, and a valid OAS3 yaml spec.

Sample protospec::

    meta:
      pagination-header: continuationToken
      pagination-size: 100
      response-wrappers: false

    models:
      User:
        id:
          type: str
          hash_key: true
          dynamo_name: i
        email: str
        verified: bool

    endpoints:
      - model: User
        path: /users/{id}
        operations: Get, Update, Delete
      - model: User
        path: /users
        operations:
          - Create
          - List
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml

from ..misc import Missing


@dataclass
class Field:
    name: str
    type: str
    kwargs: Dict[str, Any]


@dataclass
class Model:
    name: str
    fields: Dict[str, Field]


@dataclass
class Endpoint:
    model: Model
    path: str
    operation: str


class ProtoSpec:
    raw: dict
    source_filename: Optional[str] = None
    models: Dict[str, Model]
    endpoints: List[Endpoint]

    def __init__(self, raw: dict) -> None:
        self.raw = raw

        self.meta = self.raw.get("meta", {})
        self.models = _parse_models(raw)
        self.endpoints = _parse_endpoints(raw, self.models)

    @classmethod
    def from_file(cls, path: str) -> "ProtoSpec":
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
        spec = cls(raw)
        spec.source_filename = path
        return spec


def _parse_models(raw: dict) -> Dict[str, Model]:
    models = {}
    for model_name, raw_fields in raw.get("models", {}).items():
        model_fields = {}
        for field_name, field_values in raw_fields.items():
            # shorthand for a typed field:  "verified: bool"
            if isinstance(field_values, str):
                field_type = field_values
                field_values = {}

            else:
                # copy of values since we're going to mutate it
                field_values = dict(field_values)
                field_type = field_values.pop("type", Missing)
                if field_type is Missing:
                    raise ValueError(f"model {model_name} field {field_name} must specify a type")
            model_fields[field_name] = Field(field_name, field_type, field_values)
        models[model_name] = Model(model_name, model_fields)
    return models


def _parse_endpoints(raw: dict, models: Dict[str, Model]) -> List[Endpoint]:
    endpoints = []
    for raw_endpoint in raw.get("endpoints", {}):
        path = raw_endpoint["path"]
        model = models[raw_endpoint["model"]]
        raw_operations = raw_endpoint["operations"]
        if isinstance(raw_operations, str):
            raw_operations = [x.strip() for x in raw_operations.split(",")]
        for operation in raw_operations:
            endpoints.append(Endpoint(model, path, operation))
    return endpoints
