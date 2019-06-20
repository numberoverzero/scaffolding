import click

from .openapi import ProtoSpec, Specification
from .openapi.codegen import (
    generate_models,
    generate_oas_spec,
    generate_resources,
    list_model_backends,
    list_resource_backends,
)


@click.group()
def cli():
    pass


@cli.command("generate-resources")
@click.option("--backend", type=click.Choice(list_resource_backends()))
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", type=click.Path(dir_okay=False))
def generate_resource_stubs(backend, spec, out):
    spec = Specification.from_file(spec)
    generate_resources(backend, spec, out)


@cli.command("generate-models")
@click.option("--backend", type=click.Choice(list_model_backends()))
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", type=click.Path(dir_okay=False))
def generate_model_stubs(backend, spec, out):
    proto_spec = ProtoSpec.from_file(spec)
    generate_models(backend, proto_spec, out)


@cli.command("generate-oas3")
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", type=click.Path(dir_okay=False))
def generate_oas3_spec(spec, out):
    proto_spec = ProtoSpec.from_file(spec)
    generate_oas_spec(proto_spec, out)
