import logging

from ...misc import Template
from ..proto_spec import ProtoSpec
from ..spec import Specification
from .models import render_models


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
    sp = "\n\n\n"
    with open(out_path, "wt") as out:
        out.write(f"{header}{sp}{sp.join(resources)}{sp}{footer}\n")


def generate_models(backend_name: str, proto_spec: ProtoSpec, out_path: str) -> None:
    data = render_models(backend_name, proto_spec)
    with open(out_path, "wt") as out:
        out.write(data)
