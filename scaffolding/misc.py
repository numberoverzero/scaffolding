import functools
import os

import jinja2

__all__ = ["Missing", "Sentinel", "Template"]


class Template:
    def __init__(self, tpl: jinja2.Template) -> None:
        self.tpl = tpl

    def render_block(self, __name: str, **kwargs) -> str:
        block = self.tpl.blocks[__name]
        ctx = self.tpl.new_context(vars=kwargs)
        return "".join(block(ctx))

    block = render_block

    @classmethod
    def from_file(cls, path: str) -> "Template":
        with open(path, "r") as stream:
            tpl = jinja2.Template(stream.read())
        return cls(tpl)

    @classmethod
    def from_here(cls, __file__: str, *path: str) -> "Template":
        here = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(here, *path)
        return cls.from_file(path)


def singleton(func):
    instances = {}

    @functools.wraps(func)
    def get(*args):
        try:
            return instances[args]
        except KeyError:
            o = instances[args] = func(*args)
            return o
    return get


@singleton
class Sentinel:
    """Singleton object with a templated representation"""
    template = "<{}>"

    def __init__(self, name):
        """
        >>> Sentinel('a') is Sentinel('a')
        True
        >>> Sentinel('a') is Sentinel('b')
        False
        """
        self.name = name

    def __repr__(self):
        return Sentinel.template.format(self.name, name=self.name)


Missing = Sentinel("scaffolding.missing")
