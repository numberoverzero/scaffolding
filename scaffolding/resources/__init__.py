import falcon
import logging
from ..openapi import Specification, Operation
from .tags import tag, get_tag, get_tags
from typing import Set

__all__ = ["tag", "get_tags", "get_tag", "autowire_resources"]
logger = logging.getLogger(__name__)


def autowire_resources(api: falcon.API, spec: Specification, resources: list, ignore_errors: bool=False) -> None:
    """Resources must be annotated with @tag(path=)
    You can inspect each operation's ``handler`` attribute to find the routed function.

    .. code-block: python

        >>> @tag(path="/users{userId}/widgets")
        ... class WidgetCollectionResource:
        ...     def on_get(self): ...
    """
    def fail(msg: str) -> None:
        if ignore_errors:
            logger.warning(msg)
        else:
            raise RuntimeError(msg)

    for resource in resources:
        cls = resource.__class__
        path = get_tag("path", resource)
        if not path:
            fail(f"{cls} does not have an @tag(path=) annotation")
            continue
        defined_operations = spec.operations.with_path(path)
        if not defined_operations:
            fail(f"{cls}@{path} has no known operations")
        has_operations = {o for o in defined_operations if hasattr(resource, f"on_{o.verb}")}  # type: Set[Operation]
        missing_operations = [o for o in (defined_operations - has_operations)]
        if missing_operations:
            missing_operations.sort(key=lambda o: o.id)
            fail(
                f"{cls}@{path} is missing the following handlers:" +
                "".join(f"\n    {o.id}::on_{o.verb}" for o in missing_operations)
                 )
        api.add_route(path, resource)
        for o in has_operations:
            logger.info(f"added route for {o.id} {o.verb} {o.path}")
            o.handler = getattr(resource, f"on_{o.verb}")
    missing_operations = [o.id for o in spec.operations if not o.handler]
    if missing_operations:
        missing_operations.sort()
        fail(
            "The following operations do not have handlers:" +
            "".join(f"\n    {o}" for o in missing_operations))
