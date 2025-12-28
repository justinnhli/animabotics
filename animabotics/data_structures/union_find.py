"""Union Find."""

from collections.abc import  Iterable, Iterator, Hashable
from typing import Optional

class UnionFind:
    """UnionFind for discrete sets."""

    def __init__(self, nodes=None):
        # type: (Optional[Iterable[Hashable]]) -> None
        """Initialize the UnionFind."""
        if nodes is None:
            nodes = []
        self.parents = {node: node for node in nodes}

    def __len__(self):
        # type: () -> int
        return len(self.parents)

    def __contains__(self, node):
        # type: (Hashable) -> bool
        return node in self.parents

    def __getitem__(self, node):
        # type: (Hashable) -> Hashable
        path = []
        while self.parents[node] != node:
            path.append(node)
            node = self.parents[node]
        path.append(node)
        rep = path[-1]
        for step in path:
            self.parents[step] = rep
        return rep

    def __iter__(self):
        # type: () -> Iterator[Hashable]
        return iter(self.parents)

    def add(self, node, parent=None):
        # type: (Hashable, Optional[Hashable]) -> bool
        """Add a node."""
        if node in self.parents:
            return False
        if parent is None:
            parent = node
        self.parents[node] = parent
        return True

    def union(self, node1, node2):
        # type: (Hashable, Hashable) -> None
        """Join two discrete sets."""
        self.add(node1)
        rep1 = self[node1]
        self.add(node2)
        rep2 = self[node2]
        self.parents[rep2] = rep1

    def same(self, node1, node2):
        # type: (Hashable, Hashable) -> bool
        """Check if two members are in the same set."""
        return self[node1] == self[node2]
