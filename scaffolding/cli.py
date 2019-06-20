import click

from .openapi import ProtoSpec, Specification
from .openapi.codegen import generate_models, generate_resources
from .openapi.codegen.models import list_backends


@click.group()
def cli():
    pass


@cli.command("generate-resources")
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", type=click.Path(dir_okay=False))
def generate_resource_stubs(spec, out):
    spec = Specification.from_file(spec)
    generate_resources(spec, out)


@cli.command("generate-models")
@click.option("--backend", type=click.Choice(list_backends()))
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", type=click.Path(dir_okay=False))
def generate_model_stubs(backend, spec, out):
    proto_spec = ProtoSpec.from_file(spec)
    generate_models(backend, proto_spec, out)
