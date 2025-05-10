"""Tests for data_structures.py."""

from itertools import permutations

from animabotics.data_structures import UnionFind, SortedDict, SortedSet, PriorityQueue


def test_unionfind():
    # type: () -> None
    """Test UnionFind."""
    assert not UnionFind()
    union_find = UnionFind(range(4))
    assert all(i in union_find for i in range(len(union_find)))
    assert set(union_find) == set(range(4))
    for i in range(4, 8):
        union_find.add(i)
    assert all(union_find[i] == i for i in range(len(union_find)))
    for i in range(1, 8, 2):
        union_find.union(1, i)
    assert all(union_find.same(5, i) for i in range(1, 8, 2))
    assert set(union_find[i] for i in range(0, 8, 2)) == set(range(0, 8, 2))


def test_sorteddict():
    # type: () -> None
    """Test SortedDict."""
    # pylint: disable = use-implicit-booleaness-not-comparison
    sorted_dict = SortedDict() # type: SortedDict[int, int]
    assert not sorted_dict
    assert 0 not in sorted_dict
    assert (
        list(sorted_dict)
        == list(sorted_dict.keys())
        == list(sorted_dict.values())
        == list(sorted_dict.items())
        == []
    )
    assert repr(sorted_dict) == 'SortedDict()'
    assert str(sorted_dict) == 'SortedDict()'
    size = 7
    for permutation in permutations(range(size)):
        sorted_dict = SortedDict()
        for key in permutation:
            try:
                sorted_dict[key] += 1
                assert False
            except KeyError:
                pass
            if key % 2 == 0:
                sorted_dict[key] = key
            else:
                assert sorted_dict.setdefault(key, key) == key
            sorted_dict[key] = key * key
        assert str(sorted_dict) == 'SortedDict(0=0, 1=1, 2=4, 3=9, 4=16, 5=25, 6=36)'
        assert len(sorted_dict) == size
        assert list(sorted_dict) == list(range(size))
        assert sorted_dict.keys().mapping is sorted_dict
        assert list(sorted_dict.keys()) == list(range(size))
        assert list(reversed(sorted_dict.keys())) == list(reversed(range(size)))
        assert list(sorted_dict.items()) == [(num, num * num) for num in range(size)]
        assert list(reversed(sorted_dict.items())) == list(reversed([(num, num * num) for num in range(size)]))
        for num in range(size):
            assert num in sorted_dict
            assert sorted_dict[num] == num * num
            assert sorted_dict.get(num) == num * num
        for num in range(size):
            if num % 2 == 0:
                del sorted_dict[num]
            else:
                assert sorted_dict.pop(num) == num * num
            assert num not in sorted_dict
            assert len(sorted_dict) == size - num - 1
            assert sorted_dict.get(num, -1) == -1
            assert sorted_dict.pop(num, -1) == -1
    src_dict = {num: num * num for num in range(101)}
    assert SortedDict.from_dict(src_dict).to_dict() == src_dict
    # defaultdict check
    sorted_dict_set = SortedDict(factory=set) # type: SortedDict[int, set[int]]
    for i in range(10):
        for j in range(i, i + 5):
            sorted_dict_set[i].add(j)
    for i in range(10):
        assert sorted_dict_set[i] == set(range(i, i + 5))
    sorted_dict_set.clear()
    assert len(sorted_dict_set) == 0
    assert list(sorted_dict_set) == []
    # 2020-06-05
    sorted_dict_str = SortedDict() # type: SortedDict[int, str]
    for i in [5, 2, 9, 1, 4, 7, 11, 0, 3, 6, 8, 10, 12]:
        sorted_dict_str[i] = str(i)
    del sorted_dict_str[5]
    assert list(sorted_dict_str.keys()) == [*range(5), *range(6, 13)]


def test_sorteddict_views():
    # type: () -> None
    """Test SortedDict views."""
    # adapted from Python documentation on dictionary view objects
    # https://docs.python.org/dev/library/stdtypes.html#dict-views
    dishes = SortedDict() # type: SortedDict[str, int]
    dishes['bacon'] = 1
    dishes['eggs'] = 2
    dishes['sausage'] = 1
    dishes['spam'] = 500
    keys = dishes.keys()
    values = dishes.values()
    # iteration
    assert sum(values) == 504
    # keys and values are iterated over in the same (lexicographical) order
    assert list(keys) == ['bacon', 'eggs', 'sausage', 'spam']
    assert list(values) == [1, 2, 1, 500]
    # view objects are dynamic and reflect dict changes
    del dishes['eggs']
    del dishes['sausage']
    assert list(keys) == ['bacon', 'spam']
    # set operations
    assert keys & {'eggs', 'bacon', 'salad'} == {'bacon'}
    assert keys ^ {'sausage', 'juice'} == {'juice', 'sausage', 'bacon', 'spam'}
    assert keys | ['juice', 'juice', 'juice'] == {'bacon', 'spam', 'juice'}
    # get back a read-only proxy for the original dictionary
    assert values.mapping['spam'] == 500


def test_sortedset():
    # type: () -> None
    """Test SortedSet."""
    size = 7
    for permutation in permutations(range(size)):
        sorted_set = SortedSet() # type: SortedSet[int]
        for element in permutation:
            sorted_set.add(element)
        assert len(sorted_set) == size
        assert list(e for e in sorted_set) == list(range(size))
        assert list(reversed(sorted_set)) == list(reversed(range(size)))
        for num in range(size):
            assert num in sorted_set
        for num in range(size):
            sorted_set.discard(num)
            assert len(sorted_set) == size - num - 1
            assert list(e for e in sorted_set) == list(range(num + 1, size))
    src_set = set(range(101))
    assert SortedSet.from_set(src_set).to_set() == src_set


def test_priorityqueue():
    # type: () -> None
    """Test PriorityQueue."""
    queue = PriorityQueue() # type: PriorityQueue[int, int]
    try:
        queue.peek()
        assert False
    except (IndexError, KeyError, StopIteration):
        pass
    try:
        queue.pop()
        assert False
    except (IndexError, KeyError, StopIteration):
        pass
    for i in reversed(range(100)):
        size = 2 * (99 - i)
        queue.push(i, i)
        assert len(queue) == size + 1
        queue.push(i, i)
        assert len(queue) == size + 2
    prev_item = -1
    while queue:
        priority, curr_item = queue.peek()
        assert priority == prev_item + 1
        assert curr_item == prev_item + 1
        priority, curr_item = queue.pop()
        assert priority == prev_item + 1
        assert curr_item == prev_item + 1
        priority, curr_item = queue.peek()
        assert priority == prev_item + 1
        assert curr_item == prev_item + 1
        priority, curr_item = queue.pop()
        assert priority == prev_item + 1
        assert curr_item == prev_item + 1
        prev_item = curr_item
