"""
When constructing a new API, use either of the following forms::

    >>> import scaffolding
    >>> api = scaffolding.API(
    ...     middleware=[...]
    ... )
    >>> api = falcon.API(
    ...     request_type=scaffolding.Request,
    ...     middleware=[...]
    ... )

otherwise using the default falcon.Request class,
reading an empty-but-valid json body twice raises:

    https://github.com/falconry/falcon/issues/1234
    https://github.com/falconry/falcon/pull/1311
"""
import falcon
import functools
from .exc import Exceptions
from .misc import Missing, Sentinel
from .patches import Request

__all__ = ["Sentinel", "Missing", "Request", "API"]


class API(falcon.API):
    @functools.wraps(falcon.API.__init__)
    def __init__(
            self,
            media_type=falcon.DEFAULT_MEDIA_TYPE,
            request_type=Request,
            response_type=falcon.Response,
            middleware=None,
            router=None,
            independent_middleware=False):
        super().__init__(media_type, request_type, response_type, middleware, router, independent_middleware)
        self.add_error_handler(Exceptions.cls)
