"""Tests for caching.py."""

from collections import defaultdict
from functools import cached_property

from animabotics.caching import CachedMetaclass, LRUCache, cached_method


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


def assert_lrucache_contents(cache, expected):
    assert len(cache) == len(expected)
    assert tuple(cache.items()) == expected
    for key, value in reversed(expected):
        assert cache[key] == value
    if expected:
        assert cache.most_recent == expected[0]


def test_lrucache():
    # type: () -> None
    try:
        cache = LRUCache(0) # type: LRUCache[int, int]
        assert False
    except ValueError:
        pass
    cache = LRUCache(4)
    assert_lrucache_contents(cache, ())
    cache[0] = 0
    assert_lrucache_contents(cache, ((0, 0),))
    cache[1] = 1
    assert_lrucache_contents(cache, ((1, 1), (0, 0)))
    cache[2] = 4
    assert_lrucache_contents(cache, ((2, 4), (1, 1), (0, 0)))
    cache[3] = 9
    assert_lrucache_contents(cache, ((3, 9), (2, 4), (1, 1), (0, 0)))
    cache[4] = 16
    assert_lrucache_contents(cache, ((4, 16), (3, 9), (2, 4), (1, 1)))
    cache.touch(2)
    assert_lrucache_contents(cache, ((2, 4), (4, 16), (3, 9), (1, 1)))
    cache.touch(2)
    assert_lrucache_contents(cache, ((2, 4), (4, 16), (3, 9), (1, 1)))
    cache.touch(1)
    assert_lrucache_contents(cache, ((1, 1), (2, 4), (4, 16), (3, 9)))
    cache[2] = 0
    assert_lrucache_contents(cache, ((2, 0), (1, 1), (4, 16), (3, 9)))
    cache[3] = 0
    assert_lrucache_contents(cache, ((3, 0), (2, 0), (1, 1), (4, 16)))
    try:
        cache.touch(0)
        assert False
    except KeyError:
        pass
    cache.clear()
    assert_lrucache_contents(cache, ())


class CachedMethodDummy:
    """A class to test the cached_method decorator."""

    def __init__(self, n=1):
        # type: (int) -> None
        self.n = n
        self.log = defaultdict(int)

    @cached_method(is_property=True)
    def add_0(self):
        # type: () -> int
        """Add one to the value."""
        self.log['add_0'] += 1
        return self.n

    @cached_method(is_property=True)
    def add_1(self):
        # type: () -> int
        """Add one to the value."""
        self.log['add_1'] += 1
        return self.n + 1

    @cached_method()
    def add_2(self):
        # type: () -> int
        """Add one to the value."""
        self.log['add_2'] += 1
        return self.n + 2

    @cached_method()
    def add_n(self, n):
        # type: (int) -> int
        """Add n to the value."""
        self.log['add_n'] += 1
        return self.n + n

    @cached_method()
    def add_nm(self, n, m=2):
        # type: (int, int) -> int
        """Add n and m to the value."""
        self.log['add_nm'] += 1
        return self.n + n + m


def test_cached_method():
    # type: () -> None
    """Run the test function."""
    t = CachedMethodDummy(0)
    # test setting a property before a normal call
    t.add_0 = 2
    assert t.log['add_0'] == 0
    # test property
    assert t.log['add_1'] == 0
    assert t.add_1 == 1
    assert t.log['add_1'] == 1
    assert t.add_1 == 1
    assert t.log['add_1'] == 1
    # test setting a property
    t.add_1 = 2
    assert t.add_1 == 2
    assert t.log['add_1'] == 1
    assert t.add_1 == 2
    assert t.log['add_1'] == 1
    # test clearing a property
    del t.add_1
    assert t.add_1 == 1
    assert t.log['add_1'] == 2
    # test method with no parameters
    assert t.log['add_2'] == 0
    assert t.add_2() == 2
    assert t.log['add_2'] == 1
    assert t.add_2() == 2
    assert t.log['add_2'] == 1
    # test method with one parameter
    assert t.log['add_n'] == 0
    assert t.add_n(0) == 0
    assert t.log['add_n'] == 1
    assert t.add_n(0) == 0
    assert t.log['add_n'] == 1
    assert t.add_n(1) == 1
    assert t.log['add_n'] == 2
    assert t.add_n(1) == 1
    assert t.log['add_n'] == 2
    # test method with optional parameter, using the default value
    assert t.log['add_nm'] == 0
    assert t.add_nm(1) == 3
    assert t.log['add_nm'] == 1
    assert t.add_nm(1) == 3
    assert t.log['add_nm'] == 1
    # test method with optional parameter, passing positionally
    assert t.add_nm(1, 2) == 3
    assert t.log['add_nm'] == 2
    assert t.add_nm(1, 2) == 3
    assert t.log['add_nm'] == 2
    # test method with optional parameter, passing by keyword
    assert t.log['add_nm'] == 2
    assert t.add_nm(1, m=2) == 3
    assert t.log['add_nm'] == 3
    assert t.add_nm(1, m=2) == 3
    assert t.log['add_nm'] == 3
    # test method with optional parameter, with new parameters
    assert t.add_nm(2, m=3) == 5
    assert t.log['add_nm'] == 4
    assert t.add_nm(2, m=3) == 5
    assert t.log['add_nm'] == 4
    # test that setting a method is an error
    try:
        t.add_nm = 0
        assert False
    except AttributeError:
        pass


def test_cached_method_multiple_objects():
    """Test the caches are not shared between instances."""
    dummy1 = CachedMethodDummy(1)
    dummy2 = CachedMethodDummy(2)
    assert dummy1.add_0 == 1
    assert dummy2.add_0 == 2
