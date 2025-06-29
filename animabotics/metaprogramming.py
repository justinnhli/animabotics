"""Utility code for metaprogramming."""

from functools import lru_cache


class CachedMetaclass(type):
    """A metaclass to cache instances based on initialization arguments.

    Adapted from python_toolbox.caching: https://github.com/cool-RR/python_toolbox/
    """
    def __new__(mcs, *args, **kwargs):
        return super().__new__(mcs, *args, **kwargs)

    @lru_cache
    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)
