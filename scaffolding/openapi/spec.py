from typing import Any, Dict, TypeVar

import yaml


__all__ = ["Specification", "walk_path"]

_T = TypeVar("T")
MISSING = object()

PATH_VERBS = [
    "get",
    "put",
    "post",
    "delete",
    "options",
    "head",
    "patch",
    "trace"
]


class Specification:
    def __init__(self, spec: dict) -> None:
        self.raw = flatten_spec(spec)
        self.operations = _index_operations(spec)

    def get_operation(self, uri_template: str, verb: str) -> dict:
        return self.raw["paths"][uri_template][verb]

    @classmethod
    def from_file(cls, path: str) -> "Specification":
        with open(path, "r") as f:
            spec = yaml.safe_load(f)
        return cls(spec)


def walk_path(spec, *path: str, default=MISSING) -> Any:
    for segment in path:
        # drop leading/trailing "/" so we can
        # easily split "/foo/bar/" into ["foo", "bar"]
        if not segment:
            continue
        try:
            spec = spec[segment]
        except (KeyError, IndexError):
            if default is MISSING:
                raise
            return default
    return spec


def _index_operations(spec: dict) -> Dict[str, dict]:
    operations = {}
    for path in spec["paths"].values():
        for verb in path.keys():
            if verb not in PATH_VERBS:
                continue
            operation = path[verb]
            id = operation["operationId"]
            operation["_key"] = path, verb
            operations[id] = operation
    return operations


def flatten_spec(spec: dict) -> dict:
    def resolve(node: _T) -> _T:
        if not isinstance(node, dict):
            if isinstance(node, list):
                for i in range(len(node)):
                    node[i] = resolve(node[i])
            return node
        if "$ref" not in node:
            # copy keys into a new list so that we can modify the dict in-place
            for key in list(node.keys()):
                node[key] = resolve(node[key])
            return node
        ref = node["$ref"]  # type: str
        # for my own needs I don't care about non-local refs
        if not ref.startswith("#/"):
            raise RuntimeError(f"Non-local ref {ref!r} is not handled")
        ref = ref[2:]
        # walk to the ref location, from spec root along path=p1/p2/p3
        return walk_path(spec, *ref.split("/"))

    resolve(spec)
    _flatten_parameters(spec)
    _flatten_security(spec)
    return spec


def _flatten_parameters(spec: dict) -> dict:
    """
    OpenAPI 3.x allows parameter declarations at the path node, which apply to all operations below it.
    Because those won't change, we want to flatten them into each operation for constant lookup.

    paths:
      /foo/bar:
        parameters:
          - $ref: '#/components/parameters/HeaderParam'
        get:
          parameters:
            - $ref: '#/components/parameters/QueryParam'

    this should flatten so that `GET /foo/bar` has two parameters
    """
    for path in spec["paths"].values():
        shared = path.get("parameters", [])
        for verb in path.keys():
            if verb not in PATH_VERBS:
                continue
            local = path[verb].setdefault("parameters", [])
            # dedupe on unique (in, name) tuples.
            # don't add a shared variable whose tuple already exists (overwritten)
            pairs = {(p["in"], p["name"]) for p in local}
            for p in shared:
                if (p["in"], p["name"]) not in pairs:
                    local.append(p)
    return spec


def _flatten_security(spec: dict) -> dict:
    """Ensures every operation has at least one security option.
    If the "security" section is missing or empty, adds a no-auth option:

    input:
        /some/path:
          get:
            operationId:  getSomePath
            parameters: ...
            responses: ...

    output:
        /some/path:
          get:
            operationId:  getSomePath
            parameters: ...
            responses: ...
            security:  # <-- default no-auth added
              - {}
    """
    for path in spec["paths"].values():
        for verb in path.keys():
            if verb not in PATH_VERBS:
                continue
            security = path[verb].setdefault("security", [])
            if not security:
                security.append({})
    return spec
