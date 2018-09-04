import click
from .openapi import Specification
from .openapi.codegen import generate_resources


@click.group()
def cli():
    pass


@cli.command("generate-stubs")
@click.option("--spec", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", type=click.Path(dir_okay=False))
def generate_stubs(spec, out):
    spec = Specification.from_file(spec)
    generate_resources(spec, out)
