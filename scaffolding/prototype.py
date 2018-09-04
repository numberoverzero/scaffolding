import falcon
from .openapi import Specification
from wsgiref import simple_server
from typing import Optional
from .resources import autowire_resources

__all__ = ["serve"]


def serve(
        api: falcon.API,
        spec: Optional[Specification]=None,
        resources: Optional[list]=None,
        autowire: bool=True,
        autowire_ignore_errors: bool=True,
        port: int=8080, local: bool=True) -> None:

    if autowire:
        if not spec or not resources:
            raise RuntimeError("must provide spec and resources when autowiring")
        autowire_resources(api, spec, resources, ignore_errors=autowire_ignore_errors)

    host = "localhost" if local else "127.0.0.1"
    httpd = simple_server.make_server(host, port, api)
    print(f"\n\nServing API on http://{host}:{port}")
    if spec:
        has_handler = False
        for o in spec.operations:
            if o.handler:
                has_handler = True
                print(f"  {o.id} {o.verb.upper()} {o.path}")
        if has_handler:
            print()
    httpd.serve_forever()
