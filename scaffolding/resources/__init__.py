import falcon
from ..openapi import Specification
from .tags import tag, get_tag, get_tags
from typing import Any, Dict, Optional

__all__ = ["tag", "get_tags", "get_tag", "autowire_by_operation", "autowire_by_path"]


def autowire_by_path(api: falcon.API, spec: Specification, routes: list) -> Dict[str, Optional[Any]]:
    """Resources must be annotated with @tag(path=)
    Returns a dict of {operation_id: [method or None]}

    .. code-block: python

        >>> @tag(path="/users{userId}/widgets")
        ... class WidgetCollectionResource:
        ...     def on_get(self): ...
    """


def autowire_by_operation(api: falcon.API, spec: Specification, routes: list) -> Dict[str, Optional[Any]]:
    """Each on_* method must be annotated with @tag(operation=)
    Returns a dict of {operation_id: [method or None]}

    .. code-block: python

        >>> class WidgetCollectionResource:
        ...     @tag(operation="listWidgets")
        ...     def on_get(self): ...
    """
