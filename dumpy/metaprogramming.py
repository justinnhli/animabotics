"""Utility code for metaprogramming."""

from collections import namedtuple
from functools import lru_cache, wraps


def cached_class(cls, max_size=1024):
    """Cache instances of classes based on initialization arguments.

    Adapted from https://stackoverflow.com/questions/75453502/caching-python-class-instances
    """

    @wraps(cls.__new__)
    def __new__(cls, *args, **kwargs):
        return cls.__cache__(cls, args, tuple(sorted(kwargs.items())))

    @lru_cache(max_size)
    def __cache__(cls, args, kwargs):
        return cls.__orig_new__(cls, *args, **dict(kwargs))

    cls.__cache__ = __cache__
    cls.__orig_new__ = cls.__new__
    cls.__new__ = __new__
    return cls
