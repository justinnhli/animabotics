"""Utility data structures."""

from collections.abc import Collection, Mapping, Iterator, MutableSet
from collections.abc import KeysView, ValuesView, ItemsView
from typing import Any, Optional, Union
from typing import Callable
from typing import TypeVar, Generic
from typing import cast

from ..utilitypes import ComparableT


KT = TypeVar('KT', bound=ComparableT[Any])
VT = TypeVar('VT')


class _AVLView(Generic[KT, VT]):

    def __init__(self, tree):
        # type: (SortedDict[KT, VT]) -> None
        self.tree = tree
        self.node = None # type: Optional[_AVLNode[KT, VT]]

    def __len__(self):
        # type: () -> int
        return len(self.tree)

    def __contains__(self, key):
        # type: (Any) -> bool
        return key in self.tree

    def __iter__(self):
        # type: () -> Iterator[Any]
        self._set_forward()
        yield from self._yield_next()

    def __reversed__(self):
        # type: () -> Iterator[Any]
        self._set_reverse()
        yield from self._yield_prev()

    @property
    def mapping(self):
        # type: () -> Mapping[KT, VT]
        """Return the original dictionary."""
        # FIXME should in theory be read only
        return self.tree

    def _set_forward(self):
        # type: () -> None
        self.node = self.tree.head

    def _set_reverse(self):
        # type: () -> None
        self.node = self.tree.tail

    def _yield_prev_node(self):
        # type: () -> Iterator[_AVLNode[KT, VT]]
        if not self.node:
            return
        yield self.node
        curr = self.node
        while curr.prev is not None:
            curr = curr.prev
            yield curr

    def _yield_next_node(self):
        # type: () -> Iterator[_AVLNode[KT, VT]]
        if not self.node:
            return
        yield self.node
        curr = self.node
        while curr.next is not None:
            curr = curr.next
            yield curr

    def _yield_prev(self):
        # type: () -> Iterator[Any]
        raise NotImplementedError()

    def _yield_next(self):
        # type: () -> Iterator[Any]
        raise NotImplementedError()


class _KeysView(_AVLView[KT, VT], KeysView[KT]):

    def _yield_prev(self):
        # type: () -> Iterator[KT]
        for node in self._yield_prev_node():
            yield node.key

    def _yield_next(self):
        # type: () -> Iterator[KT]
        for node in self._yield_next_node():
            yield node.key


class _ValuesView(_AVLView[KT, VT], ValuesView[VT]):

    def _yield_prev(self):
        # type: () -> Iterator[VT]
        for node in self._yield_prev_node():
            yield node.value

    def _yield_next(self):
        # type: () -> Iterator[VT]
        for node in self._yield_next_node():
            yield node.value


class _ItemsView(_AVLView[KT, VT], ItemsView[KT, VT]):

    def _yield_prev(self):
        # type: () -> Iterator[tuple[KT, VT]]
        for node in self._yield_prev_node():
            yield (node.key, node.value)

    def _yield_next(self):
        # type: () -> Iterator[tuple[KT, VT]]
        for node in self._yield_next_node():
            yield (node.key, node.value)


class _AVLCursor(Generic[KT, VT]):

    def __init__(self, tree, node):
        # type: (SortedDict[KT, VT], _AVLNode[KT, VT]) -> None
        self.tree = tree
        self.node = node

    def __bool__(self):
        # type: () -> bool
        return self.node is not None

    def __repr__(self):
        # type: () -> str
        if self.node:
            return f'_AVLCursor({self.key}, {self.value})'
        else:
            return '_AVLCursor(None)'

    @property
    def key(self):
        # type: () -> KT
        """Get the key at the current node."""
        return self.node.key

    @property
    def value(self):
        # type: () -> VT
        """Get the value at the current node."""
        return self.node.value

    @value.setter
    def value(self, value):
        # type: (VT) -> None
        self.node.value = value

    @property
    def has_prev(self):
        # type: () -> bool
        """Return whether the cursor has a previous node."""
        return self.node.prev is not None

    @property
    def has_next(self):
        # type: () -> bool
        """Return whether the cursor has a next node."""
        return self.node.next is not None

    def prev(self, relative_index=1):
        # type: (int) -> _AVLCursor[KT, VT]
        """Move the cursor to the previous node."""
        if relative_index == 0:
            return self
        if relative_index < 0:
            return self.next(-relative_index)
        curr = self.node
        for _ in range(relative_index):
            curr = curr.prev
            if curr is None:
                raise IndexError()
        return _AVLCursor(self.tree, curr)

    def next(self, relative_index=1):
        # type: (int) -> _AVLCursor[KT, VT]
        """Move the cursor to the next node."""
        if relative_index == 0:
            return self
        if relative_index < 0:
            return self.prev(-relative_index)
        curr = self.node
        for _ in range(relative_index):
            curr = curr.next
            if curr is None:
                raise IndexError()
        return _AVLCursor(self.tree, curr)


class _AVLNode(Generic[KT, VT]):
    """An AVL tree node."""

    def __init__(self, key, value, prev_node=None, next_node=None):
        # type: (KT, VT, _AVLNode[KT, VT], _AVLNode[KT, VT]) -> None
        """Initialize the _AVLNode."""
        self.key = key # type: KT
        self.value = value # type: VT
        self.left = None # type: Optional[_AVLNode[KT, VT]]
        self.right = None # type: Optional[_AVLNode[KT, VT]]
        self.prev = prev_node # type: Optional[_AVLNode[KT, VT]]
        if self.prev is not None:
            self.prev.next = self
        self.next = next_node # type: Optional[_AVLNode[KT, VT]]
        if self.next is not None:
            self.next.prev = self
        self.height = 1
        self.balance = 0

    def update_metadata(self):
        # type: () -> None
        """Update the height and balance of the node."""
        left_height = (self.left.height if self.left else 0)
        right_height = (self.right.height if self.right else 0)
        self.height = max(left_height, right_height) + 1
        self.balance = right_height - left_height


class SortedDict(Mapping[KT, VT]):
    # pylint: disable = too-many-public-methods
    """A sorted dictionary backed by an AVL tree."""

    def __init__(self, factory=None):
        # type: (Callable[[], VT]) -> None
        """Initialize the SortedDict."""
        self.factory = factory
        self.size = 0
        self.root = None # type: Optional[_AVLNode[KT, VT]]
        self.head = None # type: Optional[_AVLNode[KT, VT]]
        self.tail = None # type: Optional[_AVLNode[KT, VT]]

    def __eq__(self, other):
        # type: (Any) -> bool
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        if len(self) != len(other):
            return False
        return all(
            pair1 == pair2 for pair1, pair2
            in zip(self.items(), other.items())
        )

    def __lt__(self, other):
        # type: (Any) -> bool
        for pair1, pair2 in zip(self.items(), other.items()):
            if pair1 < pair2:
                return True
            if pair1 > pair2:
                return False
        return len(self) < len(other)

    def __len__(self):
        # type: () -> int
        return self.size

    def __bool__(self):
        # type: () -> bool
        return self.size > 0

    def __contains__(self, key):
        # type: (Any) -> bool
        return self._get_node(cast(KT, key)) is not None

    def __setitem__(self, key, value):
        # type: (KT, VT) -> None
        self._put(key, value)

    def __getitem__(self, key):
        # type: (KT) -> VT
        node = self._get_node(key)
        if node is not None:
            return node.value
        if self.factory is None:
            raise KeyError(key)
        result = self.factory()
        self[key] = result
        return result

    def __delitem__(self, key):
        # type: (KT) -> None
        self._del(key)

    def __iter__(self):
        # type: () -> Iterator[KT]
        node = self.head
        while node is not None:
            yield node.key
            node = node.next

    def __reversed__(self):
        # type: () -> Iterator[KT]
        node = self.tail
        while node is not None:
            yield node.key
            node = node.prev

    def __str__(self):
        # type: () -> str
        return self.__repr__()

    def __repr__(self):
        # type: () -> str
        return 'SortedDict(' + ', '.join(f'{k}={v}' for k, v in self.items()) + ')'

    def _put_helper(self, key, value, node=None, prev_node=None, next_node=None):
        # type: (KT, VT, _AVLNode[KT, VT], _AVLNode[KT, VT], _AVLNode[KT, VT]) -> _AVLNode[KT, VT]
        if node is None:
            self.size += 1
            new_node = _AVLNode[KT, VT](key, value, prev_node, next_node)
            if prev_node is None:
                self.head = new_node
            if next_node is None:
                self.tail = new_node
            return new_node
        if key == node.key:
            node.value = value
            return node
        if key < node.key:
            node.left = self._put_helper(key, value, node.left, prev_node, node)
        else:
            node.right = self._put_helper(key, value, node.right, node, next_node)
        return self._balance(node)

    def _put(self, key, value):
        # type: (KT, VT) -> None
        self.root = self._put_helper(key, value, self.root, None, None)

    def _get_node(self, key):
        # type: (KT) -> Optional[_AVLNode[KT, VT]]
        return SortedDict._get_node_helper(key, self.root)[1]

    def _del_helper(self, key, node=None):
        # type: (KT, _AVLNode[KT, VT]) -> tuple[Optional[_AVLNode[KT, VT]], VT]
        # pylint: disable = too-many-branches
        value = None
        if node is None:
            raise KeyError(key)
        if key < node.key:
            node.left, value = self._del_helper(key, node.left)
        elif node.key < key:
            node.right, value = self._del_helper(key, node.right)
        elif node.left is not None:
            assert node.prev is not None
            value = node.value
            node.key = node.prev.key
            node.value = node.prev.value
            node.left, _ = self._del_helper(node.prev.key, node.left)
        elif node.right is not None:
            assert node.next is not None
            value = node.value
            node.key = node.next.key
            node.value = node.next.value
            node.right, _ = self._del_helper(node.next.key, node.right)
        else:
            self.size -= 1
            if node.prev is not None:
                node.prev.next = node.next
            else:
                self.head = node.next
            if node.next is not None:
                node.next.prev = node.prev
            else:
                self.tail = node.prev
            return None, node.value
        return self._balance(node), value

    def _del(self, key):
        # type: (KT) -> VT
        self.root, value = self._del_helper(key, self.root)
        return value

    def clear(self):
        # type: () -> None
        """Remove all elements from the SortedDict."""
        self.size = 0
        self.root = None
        self.head = None
        self.tail = None

    def setdefault(self, key, default=None):
        # type: (KT, Optional[VT]) -> Optional[VT]
        """Get the value of a key, or set it to the default."""
        node = self._get_node(key)
        if node is None:
            self._put(key, default)
            node = self._get_node(key)
        return node.value

    def update(self, *mappings):
        # type: (*Union[set[tuple[KT, VT]], Mapping[KT, VT]]) -> None
        """Add the key and values to the map, overwriting existing values."""
        for mapping in mappings:
            if isinstance(mapping, Mapping):
                for key, value in mapping.items():
                    self._put(key, value)
            else:
                for key, value in mapping:
                    self._put(key, value)

    def get(self, key, default=None):
        # type: (Any, Any) -> Optional[VT]
        """Return the value for the key, or the default if it doesn't exist."""
        node = self._get_node(key)
        if node is None:
            return default
        else:
            return node.value

    def pop(self, key, default=None):
        # type: (KT, Optional[VT]) -> Optional[VT]
        """Remove the key and return the value, or the default if it doesn't exist."""
        try:
            value = self._del(key)
            return value
        except KeyError:
            return default

    def cursor(self, key):
        # type: (KT) -> _AVLCursor[KT, VT]
        """Get a cursor at the key."""
        node = self._get_node(key)
        if node is None:
            raise KeyError()
        return _AVLCursor(self, node)

    def bracket(self, key):
        # type: (KT) -> tuple[_AVLCursor[KT, VT], _AVLCursor[KT, VT]]
        """Get two cursors that bracket the key."""
        prev_node, curr_node, next_node = SortedDict._get_node_helper(key, self.root)
        if curr_node is None:
            return _AVLCursor(self, prev_node), _AVLCursor(self, next_node)
        else:
            return _AVLCursor(self, curr_node), _AVLCursor(self, curr_node)

    def keys(self):
        # type: () -> _KeysView[KT, VT]
        """Create a generator of the keys."""
        return _KeysView(self)

    def values(self):
        # type: () -> _ValuesView[KT, VT]
        """Create a generator of the values."""
        return _ValuesView(self)

    def items(self):
        # type: () -> _ItemsView[KT, VT]
        """Create a generator of the key-value pairs."""
        return _ItemsView(self)

    def to_dict(self):
        # type: () -> dict[KT, VT]
        """Return the keys and values in a normal dict."""
        return dict(self.items())

    @staticmethod
    def from_dict(src_dict):
        # type: (Mapping[KT, VT]) -> SortedDict[KT, VT]
        """Create an SortedDict (as a dict) from a dictionary."""
        tree = SortedDict() # type: SortedDict[KT, VT]
        tree.update(src_dict)
        return tree

    @staticmethod
    def _get_node_helper(key, node=None, prev_node=None, next_node=None):
        # pylint: disable = line-too-long
        # type: (KT, _AVLNode[KT, VT], _AVLNode[KT, VT], _AVLNode[KT, VT]) -> tuple[_AVLNode[KT, VT], _AVLNode[KT, VT], _AVLNode[KT, VT]]
        if node is None:
            return prev_node, None, next_node
        elif key < node.key:
            return SortedDict._get_node_helper(key, node.left, prev_node, node)
        elif node.key < key:
            return SortedDict._get_node_helper(key, node.right, node, next_node)
        else:
            return prev_node, node, next_node

    @staticmethod
    def _balance(node):
        # type: (_AVLNode[KT, VT]) -> _AVLNode[KT, VT]
        node.update_metadata()
        if node.balance < -1:
            if node.left.balance == 1:
                node.left = SortedDict._rotate_ccw(node.left)
            return SortedDict._rotate_cw(node)
        elif node.balance > 1:
            if node.right.balance == -1:
                node.right = SortedDict._rotate_cw(node.right)
            return SortedDict._rotate_ccw(node)
        else:
            return node

    @staticmethod
    def _rotate_cw(node):
        # type: (_AVLNode[KT, VT]) -> _AVLNode[KT, VT]
        left = node.left
        node.left = left.right
        left.right = node
        node.update_metadata()
        left.update_metadata()
        return left

    @staticmethod
    def _rotate_ccw(node):
        # type: (_AVLNode[KT, VT]) -> _AVLNode[KT, VT]
        right = node.right
        node.right = right.left
        right.left = node
        node.update_metadata()
        right.update_metadata()
        return right


class SortedSet(MutableSet[KT]):
    """A sorted set."""

    def __init__(self):
        # type: () -> None
        """Initialize the SortedSet."""
        self.tree = SortedDict() # type: SortedDict[KT, None]

    def __len__(self):
        # type: () -> int
        return len(self.tree)

    def __bool__(self):
        # type: () -> bool
        return len(self.tree) > 0

    def __contains__(self, key):
        # type: (Any) -> bool
        return key in self.tree

    def __iter__(self):
        # type: () -> Iterator[KT]
        return iter(self.tree)

    def __reversed__(self):
        # type: () -> Iterator[KT]
        return reversed(self.tree)

    def add(self, value):
        # type: (KT) -> None
        """Add an element to the SortedDict (set)."""
        self.tree[value] = None

    def remove(self, value):
        # type: (KT) -> None
        """Remove an element from the set."""
        del self.tree[value]

    def discard(self, value):
        # type: (KT) -> None
        """Remove an element from the set if it is present."""
        try:
            del self.tree[value]
        except KeyError:
            pass

    def is_disjoint(self, other):
        # type: (Collection[KT]) -> bool
        """Check if the two sets are disjoint."""
        return all((element not in other) for element in self)

    def is_subset(self, other):
        # type: (Collection[KT]) -> bool
        """Check if this is a subset of another set."""
        return (
            len(self) < len(other)
            and all((element in other) for element in self)
        )

    def is_superset(self, other):
        # type: (Collection[KT]) -> bool
        """Check if this is a superset of another set."""
        return (
            len(self) > len(other)
            and all((element in self) for element in other)
        )

    def union(self, *others):
        # type: (*Collection[KT]) -> SortedSet[KT]
        """Create the union of this and other sets."""
        result = SortedSet() # type: SortedSet[KT]
        result.union_update(self, *others)
        return result

    def intersection(self, *others):
        # type: (*Collection[KT]) -> SortedSet[KT]
        """Create the intersection of this and other sets."""
        new_set = SortedSet() # type: SortedSet[KT]
        min_set = others[0]
        for other in others:
            if len(other) < len(min_set):
                min_set = other
        new_set.union_update(min_set)
        new_set.intersection_update(self)
        new_set.intersection_update(*others)
        return new_set

    def difference(self, *others):
        # type: (*Collection[KT]) -> SortedSet[KT]
        """Create the difference of this and other sets."""
        new_set = SortedSet() # type: SortedSet[KT]
        new_set.union_update(self)
        new_set.difference_update(*others)
        return new_set

    def union_update(self, *others):
        # type: (*Collection[KT]) -> None
        """Update this set to be the union of this and other sets."""
        for other in others:
            for element in other:
                self.add(element)

    def intersection_update(self, *others):
        # type: (*Collection[KT]) -> None
        """Keep only the intersection of this and other sets."""
        sorted_others = sorted(others, key=len)
        for element in self:
            if any((element not in other) for other in sorted_others):
                self.remove(element)

    def difference_update(self, *others):
        # type: (*Collection[KT]) -> None
        """Keep only the difference of this and other sets."""
        union = SortedSet() # type: SortedSet[KT]
        union.union_update(*others)
        for element in self:
            if element in union:
                self.remove(element)

    def to_set(self):
        # type: () -> set[KT]
        """Return the elements in a normal set."""
        return set(self)

    @staticmethod
    def from_set(src_set):
        # type: (set[KT]) -> SortedSet[KT]
        """Create an SortedDict (as a set) from a set."""
        result = SortedSet() # type: SortedSet[KT]
        result.union_update(src_set)
        return result


class PriorityQueue(Generic[KT, VT]):
    """A priory queue."""

    def __init__(self, key=None):
        # type: (Callable[[VT], KT]) -> None
        """Initialize the PriorityQueue."""
        self.tree = SortedDict(list) # type: SortedDict[KT, list[VT]]
        self.size = 0
        self.key = key

    def __len__(self):
        # type: () -> int
        return self.size

    def __bool__(self):
        # type: () -> bool
        return self.size > 0

    def peek(self):
        # type: () -> tuple[KT, VT]
        """Return the next item to pop."""
        key = next(iter(self.tree))
        values = self.tree[key]
        return key, values[0]

    def push(self, value, priority=None):
        # type: (VT, KT) -> None
        """Put an item into the queue."""
        if priority is None:
            if self.key is not None:
                priority = self.key(value)
            else:
                priority = value
        self.tree[priority].append(value)
        self.size += 1

    def pop(self):
        # type: () -> tuple[KT, VT]
        """Remove the item with the highest priority."""
        if self.size == 0:
            raise KeyError('empty queue')
        key = next(iter(self.tree))
        values = self.tree[key]
        result = values[0]
        if len(values) == 1:
            del self.tree[key]
        else:
            self.tree[key].pop(0)
        self.size -= 1
        return key, result

    def remove(self, value, priority):
        # type: (VT, KT) -> None
        """Remove the specified item at the specified priority."""
        cursor = self.tree.cursor(priority)
        if len(cursor.value) == 1:
            del self.tree[priority]
        else:
            cursor.value.remove(value)
        self.size -= 1
