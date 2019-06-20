import logging

from ...misc import Template
from ..spec import Specification
from .models import ModelBackend


logger = logging.getLogger(__name__)


def generate_resources(spec: Specification, out_path: str) -> None:
    tpl = Template.from_pkg("falcon.tpl")
    resources = []
    classes = []
    tags = spec.operations.tags
    if not tags:
        logging.warning("no tags found in spec, nothing to render")
    header = tpl.block("header")
    for tag in tags:
        resource_cls = f"{tag[0].upper()}{tag[1:]}Resource"
        classes.append(resource_cls)
        operations = spec.operations.with_tag(tag)
        verbs = [o.verb for o in operations]
        path = next(iter(operations)).path
        resources.append(tpl.block("resource", resource=resource_cls, verbs=verbs, operations=operations, path=path))
    footer = tpl.block("footer", resources=classes, spec_path=spec.source_filename)
    with open(out_path, "wt") as out:
        out.write(header)
        out.write("".join(resources))
        out.write(footer)


def generate_models(spec: Specification, backend_name: str, out_path: str) -> None:
    backend = ModelBackend.get_backend(backend_name)
    data = backend.render_spec(spec)
    with open(out_path, "wt") as out:
        out.write(data)
