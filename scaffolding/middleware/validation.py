import logging

import falcon
import marshmallow as ma

from ..exc import Exceptions
from ..openapi import Operation, Specification


logger = logging.getLogger(__name__)

__all__ = ["OpenApiRequestValidation"]


class OpenApiRequestValidation:
    def __init__(self, spec: Specification) -> None:
        self.spec = spec

    def process_resource(self, req: falcon.Request, resp: falcon.Response, resource, params: dict) -> None:
        operation = self.spec.operations.by_req(req)
        self.collect_params(operation, req, params)
        if operation.has_params:
            operation.validate_params(params)
        else:
            logger.debug(f"{operation.id} has no params, skipping validation")
        if operation.has_body:
            operation.validate_body(req.media)
        else:
            logger.debug(f"{operation.id} has no body, skipping validation")

    @staticmethod
    def collect_params(operation: Operation, req: falcon.Request, params: dict) -> None:
        schema = operation.param_schema
        # cache since req.cookies creates a copy
        cookies = req.cookies
        for name, f in schema.fields.items():
            default = f.missing
            if f.location == "query":
                v = params[name] = req.get_param(name, default=default)
            elif f.location == "header":
                v = params[name] = req.get_header(name, default=default)
            elif f.location == "path":
                v = params[name] = params.get(name, default)
            elif f.location == "cookie":
                v = params[name] = cookies.get(name, default)
            else:
                raise Exceptions.internal_error()
            if f.required and v is ma.missing:
                raise Exceptions.missing_parameter(name)
