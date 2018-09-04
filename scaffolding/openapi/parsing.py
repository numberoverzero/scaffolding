from typing import Any, Generator, Tuple, TypeVar

from ..misc import Missing


__all__ = ["iter_operations", "walk_path", "flatten_spec", "get_route", "get_id", "iter_security_schemas"]

_T = TypeVar("T")
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
ROUTE_KEY = "_route"


def get_id(operation: dict) -> str:
    return operation["operationId"]


def get_route(operation: dict) -> Tuple[str, str]:
    return operation[ROUTE_KEY]


def iter_security_schemas(operation: dict) -> Generator[Tuple[str, list], None, None]:
    for schema_dict in operation["security"]:
        if schema_dict:
            (name, args), = schema_dict.items()
            yield name, args
        else:
            yield None, []


def iter_operations(spec: dict) -> Generator[Tuple[str, str, dict], None, None]:
    for path, path_obj in spec["paths"].items():
        for verb in path_obj.keys():
            if verb not in PATH_VERBS:
                continue
            operation = path_obj[verb]
            yield path, verb, operation


def walk_path(spec, *path: str, default=Missing) -> Any:
    for segment in path:
        # drop leading/trailing "/" so we can
        # easily split "/foo/bar/" into ["foo", "bar"]
        if not segment:
            continue
        try:
            spec = spec[segment]
        except (KeyError, IndexError):
            if default is Missing:
                raise
            return default
    return spec


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
    _ensure_tags(spec)
    _inject_operation_routes(spec)
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


def _ensure_tags(spec: dict) -> dict:
    for *_, operation in iter_operations(spec):
        operation.setdefault("tags", [])
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
    for *_, operation in iter_operations(spec):
        security = operation.setdefault("security", [])
        if not security:
            security.append({})
    return spec


def _inject_operation_routes(spec: dict) -> dict:
    for path, verb, operation in iter_operations(spec):
        operation[ROUTE_KEY] = path, verb
    return spec

