import re
from typing import ClassVar, Dict, Tuple, Union

from ...misc import Template
from ..proto_spec import ProtoSpec


def compile_known_types(known_types: Dict[str, Union[str, Tuple[str, str]]]) -> Dict[re.Pattern, Tuple[str, str]]:
    def sp(t: str) -> re.Pattern:
        if t.count("*") > 1:
            raise RuntimeError("Not a simple pattern")
        if t.count("*") == 1:
            i = t.index("*")
            t = re.escape(t[:i]) + "(.*?)" + re.escape(t[i + 1:])
        if not t.startswith("^"):
            t = "^" + t
        if not t.endswith("$"):
            t += "$"
        return re.compile(t)

    def sr(t: Union[str, Tuple[str, str]]) -> Tuple[str, str]:
        if isinstance(t, str):
            type_name = t
        else:
            type_name, t = t
        if t.count("*") > 1:
            raise RuntimeError("Not a simple replacement")
        if t.count("*") == 1:
            i = t.index("*")
            t = t[:i] + "\\1" + t[i + 1]
        return type_name, t

    return {sp(k): sr(v) for k, v in known_types.items()}


def extract_type(type_name: str, known_types: Dict[re.Pattern, Tuple[str, str]]) -> Tuple[str, str]:
    for pattern, (backend_name, replacement) in known_types.items():
        match = pattern.match(type_name)
        if not match:
            continue
        expanded_name = match.expand(replacement)
        return backend_name, expanded_name
    raise ValueError(f"no matching types for {type_name!r}")


class ModelBackend:
    _backends = {}

    name: ClassVar[str]
    known_types: ClassVar[Dict[re.Pattern, Tuple[str, str]]]
    t: ClassVar[Template]

    def __init_subclass__(cls, **kwargs):
        backends = ModelBackend._backends
        name = cls.name
        conflict = backends.get(name)
        if conflict:
            raise RuntimeError(f"name {name} used for both {cls} and {conflict}")
        backends[name] = cls
        cls.t = Template.from_pkg(f"{cls.name}.tpl")

    @staticmethod
    def get_backend(name: str) -> "ModelBackend":
        return ModelBackend._backends[name]()

    def render_spec(self, spec: ProtoSpec) -> str:
        self.validate_spec(spec)
        return self._render_spec(spec)

    def validate_spec(self, spec: ProtoSpec) -> None:
        raise NotImplementedError

    def _render_spec(self, spec: ProtoSpec) -> str:
        raise NotImplementedError


class PostgresBackend(ModelBackend):
    name = "pg-sqlalchemy"


class DynamoBackend(ModelBackend):
    name = "dynamodb-bloop"

    known_types = compile_known_types({
        "int": "Integer",
        "float": "Number",
        "bool": "Boolean",
        "bytes": "Binary",
        "str": "String",
        "uuid": "UUID",
        "datetime": "DateTime",
        "timestamp": "Timestamp",
        "set(*)": ("Set", "Set(*)"),
        "list(*)": ("List", "List(*)"),
        "map(*)": ("Map", "Map(*)"),
        "dynamic": "DynamicType",
        "list": "DynamicList",
        "map": "DynamicMap",
    })

    def validate_spec(self, spec: ProtoSpec) -> None:
        # TODO
        models = spec.models
