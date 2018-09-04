import logging
from typing import Optional

import falcon
from werkzeug.contrib.profiler import ProfilerMiddleware
from werkzeug.serving import run_simple

from .openapi import Specification
from .resources import autowire_resources


__all__ = ["serve"]


def serve(
        api: falcon.API,
        spec: Optional[Specification]=None,
        resources: Optional[list]=None,
        autowire: bool=True,
        autowire_ignore_errors: bool=True,
        port: int=8080, local: bool=True,
        debug: bool=True,
        profile: bool=True) -> None:

    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    if autowire:
        if not spec or not resources:
            raise RuntimeError("must provide spec and resources when autowiring")
        autowire_resources(api, spec, resources, ignore_errors=autowire_ignore_errors)

    host = "localhost" if local else "127.0.0.1"
    if spec:
        has_handler = False
        for o in spec.operations:
            if o.handler:
                has_handler = True
                print(f"  {o.id} {o.verb.upper()} {o.path}")
        if has_handler:
            print()
    if profile:
        # limit output to top 10% of calls
        api = ProfilerMiddleware(api, restrictions=(0.1,))
    print(f"serving on {host}:{port}")
    run_simple(host, port, api, use_reloader=True)
