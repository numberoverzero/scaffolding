"""
When constructing a new API, register the scaffolding exceptions handler::

    >>> import falcon
    >>> import scaffolding
    >>> api = falcon.API(
    ...     middleware=[...]
    ... )
    >>> api.add_error_handler(scaffolding.error_handler)
    scaffolding.install_error_handler(api)
"""
from .exc import Exceptions
from .misc import Missing, Sentinel


error_handler = Exceptions.cls
