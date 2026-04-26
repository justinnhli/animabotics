"""Utilities for caching results."""

from collections.abc import Hashable
from functools import lru_cache
from typing import TypeVar, Generic, ParamSpec, Concatenate
from typing import Callable, Any, Optional, Union, Iterator


class CachedMetaclass(type):
    """A metaclass to cache instances based on initialization arguments.

    Adapted from python_toolbox.caching: https://github.com/cool-RR/python_toolbox/
    """
    def __new__(mcs, *args, **kwargs):
        # type: (*Any, **Any) -> Any
        return super().__new__(mcs, *args, **kwargs)

    @lru_cache
    def __call__(cls, *args, **kwargs):
        # type: (*Any, **Any) -> Any
        return super().__call__(*args, **kwargs)


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


T = TypeVar('T') # instance
P = ParamSpec('P') # parameters
R = TypeVar('R') # return


class cached_method(Generic[T, P, R]): # pylint: disable = invalid-name
    """A caching class that implements the Descriptor protocol."""

    def __init__(self, is_property:bool=False, max_size:int=1024):
        self.is_property = is_property
        self.max_size = max_size
        self.func: Optional[Callable[Concatenate[T, P], R]] = None
        self.attr_name = ''
        self.__doc__ = ''
        self.__module__ = ''
        self.instance: Optional[T] = None

    def __set_name__(self, owner, name):
        # type: (Any, str) -> None
        if not self.attr_name:
            self.attr_name = name
        else:
            assert self.attr_name == name

    def __get__(self, instance:T, objtype:Any) -> Union[R, Callable[P, R]]:
        assert self.attr_name
        assert instance is not None
        if self.is_property:
            cache = self.get_cache(instance)
            if () not in cache:
                assert self.func is not None
                cache[()] = self.func(instance) # pyright: ignore
            return cache[()]
        else:
            return (lambda *args, **kwargs: self.wrapper_func(instance, *args, **kwargs))

    def __set__(self, instance:T, value:R) -> None:
        assert instance is not None
        if not self.is_property:
            raise AttributeError('trying to set method')
        self.get_cache(instance)[()] = value

    def __delete__(self, instance:T) -> None:
        self.get_cache(instance).clear()

    def __call__(self, func:Callable[Concatenate[T, P], R]) -> cached_method[T, P, R]:
        self.func = func
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
        return self

    def get_cache(self, instance:T) -> LRUCache[tuple[object | tuple[str, object], ...], R]:
        """Get the cache of the instance."""
        assert self.attr_name
        if self.attr_name not in instance.__dict__:
            instance.__dict__[self.attr_name] = LRUCache(self.max_size)
        return instance.__dict__[self.attr_name]

    def wrapper_func(self, instance:T, *args:P.args, **kwargs:P.kwargs) -> R:
        """Call the wrapped function and cache its results if necessary."""
        key = (
            *args,
            *sorted(kwargs.items()),
        )
        assert self.func is not None
        assert instance is not None
        cache = self.get_cache(instance)
        if key not in cache:
            cache[key] = self.func(instance, *args, **kwargs)
        return cache[key]
