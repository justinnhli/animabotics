"""Utilities for caching results."""

from collections.abc import Hashable
from typing import TypeVar, Generic, Optional, Iterator


KT = TypeVar('KT', bound=Hashable)
VT = TypeVar('VT')


class LRUCacheNode(Generic[KT, VT]):
    """A linked list node."""

    def __init__(
            self,
            key:KT,
            value:VT,
            head:Optional[LRUCacheNode[KT, VT]]=None,
            tail:Optional[LRUCacheNode[KT, VT]]=None,
        ):
        self.key = key
        self.value = value
        self.head = head
        self.tail = tail


class LRUCache(Generic[KT, VT]):
    """A least recently used cache.

    Unlike functools.lru_cache, this can be used as part of object instances.
    """

    def __init__(self, maxsize:int=1024) -> None:
        if maxsize <= 0:
            raise ValueError(f'maxsize must be > 1, but got {maxsize}')
        self.max_size:int = maxsize
        self.size:int = 0
        self.head:Optional[LRUCacheNode[KT, VT]] = None
        self.tail:Optional[LRUCacheNode[KT, VT]] = None
        self.nodes:dict[KT, LRUCacheNode[KT, VT]] = {}

    @property
    def most_recent(self) -> tuple[KT, VT]:
        """Get the most recently used key-value."""
        assert self.head is not None
        return (self.head.key, self.head.value)

    def __len__(self) -> int:
        return self.size

    def __contains__(self, key:KT) -> bool:
        return key in self.nodes

    def __getitem__(self, key:KT) -> VT:
        assert self.head is not None
        assert self.tail is not None
        self.touch(key)
        return self.head.value

    def __setitem__(self, key:KT, value:VT) -> None:
        if key in self.nodes:
            assert self.head is not None
            self.touch(key)
            self.head.value = value
            return
        self.head = LRUCacheNode(key, value, head=None, tail=self.head)
        self.nodes[key] = self.head
        if self.size == 0:
            self.tail = self.head
        else:
            assert self.head.tail is not None
            self.head.tail.head = self.head
            if self.size == self.max_size:
                assert self.tail is not None
                del self.nodes[self.tail.key]
                self.tail = self.tail.head
                assert self.tail is not None
                assert self.tail.tail is not None
                self.tail.tail = None
                return
        self.size += 1

    def clear(self) -> None:
        """Clear the cache."""
        self.size = 0
        self.head = None
        self.tail = None
        self.nodes = {}

    def touch(self, key:KT) -> None:
        """Touch a key and move it to the front of the cache."""
        assert self.head is not None
        if self.head.key == key:
            return
        node = self.nodes[key]
        if self.tail == node:
            self.tail = node.head
        else:
            assert node.tail is not None
            node.tail.head = node.head
        assert node.head is not None
        node.head.tail = node.tail
        self.head.head = node
        node.tail = self.head
        self.head = node

    def items(self) -> Iterator[tuple[KT, VT]]:
        """Get the items in the cache, most recently used first."""
        curr = self.head
        while curr:
            yield (curr.key, curr.value)
            curr = curr.tail
