"""Tests for caching.py."""

from animabotics.caching import LRUCache


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
