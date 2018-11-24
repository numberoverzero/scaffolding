import logging
import os

import jinja2

from ..spec import Specification


logger = logging.getLogger(__name__)
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "falcon.tpl"), "r") as stream:
    tpl = jinja2.Template(stream.read())


def _render_b(_name: str, **kwargs) -> str:
    block = tpl.blocks[_name]
    ctx = tpl.new_context(vars=kwargs)
    return "".join(block(ctx))


def generate_resources(spec: Specification, out_filename: str) -> None:
    resources = []
    classes = []
    tags = spec.operations.tags
    if not tags:
        logging.warning("no tags found in spec, nothing to render")
    header = _render_b("header")
    for tag in tags:
        resource_cls = f"{tag[0].upper()}{tag[1:]}Resource"
        classes.append(resource_cls)
        operations = spec.operations.with_tag(tag)
        verbs = [o.verb for o in operations]
        path = next(iter(operations)).path
        resources.append(_render_b("resource", resource=resource_cls, verbs=verbs, operations=operations, path=path))
    footer = _render_b("footer", resources=classes, spec_path=spec.source_filename)
    with open(out_filename, "wt") as out:
        out.write(header)
        out.write("".join(resources))
        out.write(footer)
