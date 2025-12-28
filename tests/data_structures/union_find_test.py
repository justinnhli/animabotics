"""Tests for data_structures/union_find.py."""

from animabotics.data_structures import UnionFind


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
