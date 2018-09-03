import functools
from typing import Any, Optional


__all__ = ["set_tag", "get_tag"]


def set_tag(key: str, value: Any, resource_method=None):
    """
    .. code-block:: python

        >>> class MyResource:
        ...     @set_tag("auth", {"type": "user"})
        ...     def on_get(self, ...):
        ...         pass
        ...     @set_tag("cache-control", "no-cache")
        ...     def on_post(self, ...):
        ...         pass
        >>> get_tag("cache-control", MyResource, "post")
        "no-cache"
        >>> get_tag("auth", MyResource, "get")
        {"type": "user"}
    """
    if resource_method is None:
        return functools.partial(set_tag, key, value)
    if not hasattr(resource_method, "tags"):
        resource_method.tags = {}
    resource_method.tags[key] = value
    return resource_method


def get_tag(key: str, resource, verb: str) -> Optional[Any]:
    """
    .. code-block:: python

        >>> class MyResource:
        ...     @set_tag("auth", {"type": "user"})
        ...     def on_get(self, ...):
        ...         pass
        ...     @set_tag("cache-control", "no-cache")
        ...     def on_post(self, ...):
        ...         pass
        >>> get_tag("cache-control", MyResource, "post")
        "no-cache"
        >>> get_tag("auth", MyResource, "get")
        {"type": "user"}
    """
    try:
        return getattr(resource, "on_" + verb.lower()).tags[key]
    except (AttributeError, KeyError):
        return None
