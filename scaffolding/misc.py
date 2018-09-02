import functools
__all__ = ["Sentinel"]


def singleton(cls):
    instances = {}

    @functools.wraps(cls)
    def get(name: str):
        try:
            return instances[name]
        except KeyError:
            o = instances[name] = cls(name)
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
