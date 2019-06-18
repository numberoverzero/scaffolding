{% block header %}import falcon
import json
import os
import scaffolding
from scaffolding.middleware import OpenApiAuthentication, OpenApiRequestValidation
from scaffolding.openapi import Specification
from scaffolding.prototype import serve, global_cors
from scaffolding.resources import tag

HERE = os.path.abspath(os.path.dirname(__file__))

format = lambda r, p: {"auth": r.context["principal"], "params": p, "body": r.media}
dump = lambda o: json.dumps(o, indent=2, sort_keys=True)


class MyAuthentication(OpenApiAuthentication):
    def get_login_principal(self, req: falcon.Request, username: str, password: str) -> tuple:
        # TODO load AccountModel from database, dynamodb..
        return "user", (username, password)

    def get_token_principal(self, req: falcon.Request, token: str) -> tuple:
        # TODO load AccountModel from database, dynamodb..
        return "token", token
{% endblock %}
{% block resource %}

@tag(path="{{ path }}")
class {{ resource }}:{% for op in operations %}
    def on_{{ op.verb }}(self, req: falcon.Request, resp: falcon.Response, **params) -> None:
        """{{ op.id }}"""
        resp.media = ctx = format(req, params)
        print(dump(ctx))
{% endfor %}{%  endblock %}
{% block footer %}

spec = Specification.from_file(f"{HERE}/v1.yaml")
api = falcon.API(
    middleware=[
        global_cors,
        MyAuthentication(spec),
        OpenApiRequestValidation(spec)
    ],
)
api.add_error_handler(scaffolding.error_handler)

resources = [{% for resource in resources %}
    {{ resource }}(),{% endfor %}
]
serve(api, spec, resources)
{%  endblock %}
