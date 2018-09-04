{% block header %}import falcon
import json
from scaffolding import API
from scaffolding.middleware import OpenApiAuthentication, OpenApiRequestValidation
from scaffolding.openapi import Specification
from scaffolding.prototype import serve
from scaffolding.resources import tag


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
class {{ resource }}:{% for verb in verbs %}
    def on_{{ verb }}(self, req: falcon.Request, resp: falcon.Response, **params) -> None:
        resp.media = ctx = format(req, params)
        print(dump(ctx))
{% endfor %}{%  endblock %}
{% block footer %}

spec = Specification.from_file("{{ spec_path }}")
api = API(
    middleware=[
        MyAuthentication(spec),
        OpenApiRequestValidation(spec)
    ],
)
resources = [{% for resource in resources %}
    {{ resource }}(),{% endfor %}
]
serve(api, spec, resources)
{%  endblock %}
