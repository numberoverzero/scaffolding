import functools
import os

import jinja2


__all__ = ["Missing", "Sentinel", "Template"]


class Template:
    def __init__(self, tpl: jinja2.Template, strip_blocks=True) -> None:
        self.tpl = tpl
        self.strip_blocks = strip_blocks

    def render_block(self, __name: str, **kwargs) -> str:
        block = self.tpl.blocks[__name]
        ctx = self.tpl.new_context(vars=kwargs)
        t = "".join(block(ctx))
        if self.strip_blocks:
            t = t.strip()
        return t

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

    @classmethod
    def from_pkg(cls, tpl_name, *, pkg_name="scaffolding", pkg_path="templates") -> "Template":
        env = jinja2.Environment(loader=jinja2.PackageLoader(pkg_name, pkg_path))
        tpl = env.get_template(tpl_name)
        return cls(tpl)


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
