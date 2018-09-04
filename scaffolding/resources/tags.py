from typing import Any, Optional


__all__ = ["tag", "get_tag", "get_tags"]


def tag(**tags):
    """
    .. code-block:: python

        >>> class MyResource:
        ...     @tag(auth={"type": "user"})
        ...     def on_get(self, ...):
        ...         pass
        ...     @tag(cache_control="no-cache")
        ...     def on_post(self, ...):
        ...         pass
        >>> get_tag("cache_control", MyResource, "post")
        "no-cache"
        >>> get_tag("auth", MyResource, "get")
        {"type": "user"}

        >>> @tag(path="/users/{userId}/widgets")
        ... class WidgetResource:
        ...     def on_get(self, ...): ...
        >>> get_tag("path", WidgetResource)
        "/users/{userId}/widgets"
        >>> get_tags(WidgetResource)
        {"path": "/users/{userId}/widgets"}
    """
    def annotate(resource_or_method):
        if not hasattr(resource_or_method, "tags"):
            resource_or_method.tags = {}
        resource_or_method.tags.update(tags)
        return resource_or_method
    return annotate


def get_tags(resource, verb: str=None) -> Optional[dict]:
    """
    .. code-block:: python

        >>> class MyResource:
        ...     @tag(auth={"type": "user"})
        ...     def on_get(self, ...):
        ...         pass
        ...     @tag(cache_control="no-cache")
        ...     def on_post(self, ...):
        ...         pass
        >>> get_tag("cache_control", MyResource, "post")
        "no-cache"
        >>> get_tag("auth", MyResource, "get")
        {"type": "user"}

        >>> @tag(path="/users/{userId}/widgets")
        ... class WidgetResource:
        ...     def on_get(self, ...): ...
        >>> get_tag("path", WidgetResource)
        "/users/{userId}/widgets"
        >>> get_tags(WidgetResource)
        {"path": "/users/{userId}/widgets"}
    """
    if verb:
        try:
            return getattr(resource, f"on_{verb.lower()}").tags
        except AttributeError:
            return {}
    return getattr(resource, "tags", {})


def get_tag(key: str, resource, verb: str=None) -> Optional[Any]:
    """
    .. code-block:: python

        >>> class MyResource:
        ...     @tag(auth={"type": "user"})
        ...     def on_get(self, ...):
        ...         pass
        ...     @tag(cache_control="no-cache")
        ...     def on_post(self, ...):
        ...         pass
        >>> get_tag("cache_control", MyResource, "post")
        "no-cache"
        >>> get_tag("auth", MyResource, "get")
        {"type": "user"}

        >>> @tag(path="/users/{userId}/widgets")
        ... class WidgetResource:
        ...     def on_get(self, ...): ...
        >>> get_tag("path", WidgetResource)
        "/users/{userId}/widgets"
        >>> get_tags(WidgetResource)
        {"path": "/users/{userId}/widgets"}
    """
    return get_tags(resource, verb).get(key)
