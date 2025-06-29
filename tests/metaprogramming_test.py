"""Tests for metaprogramming.py."""

from functools import cached_property
from typing import Self

from animabotics.metaprogramming import CachedMetaclass


class CachedClassDummy(metaclass=CachedMetaclass):
    """A dummy class to test cached_class."""

    def __init__(self, x): # pylint: disable = unused-argument
        # type: (int) -> None
        self.x = x
        self.num_calls = 0

    @cached_property
    def prop(self):
        # type: () -> str
        """Test property."""
        self.num_calls += 1
        return f'prop {self.x}'


def test_cached_class():
    # type: () -> None
    """Test cached_class."""
    x = CachedClassDummy(0)
    y = CachedClassDummy(0)
    z = CachedClassDummy(1)
    w = CachedClassDummy(2)
    assert x is y
    assert x is not z
    assert x is not w
    assert z is not w
    assert x.prop == 'prop 0'
    assert y.prop == 'prop 0'
    assert z.prop == 'prop 1'
    assert x.num_calls == 1
    assert z.num_calls == 1
    assert w.num_calls == 0
