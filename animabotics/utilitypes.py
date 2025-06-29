"""Abstract types."""

from typing import TypeVar, Protocol, Any

T_contra = TypeVar("T_contra", contravariant=True)


class ComparableT(Protocol[T_contra]):
    """Abstract class for __eq__ and __lt__ types."""

    def __eq__(self, __other):
        # type: (Any) -> bool
        ...

    def __lt__(self, __other):
        # type: (T_contra) -> bool
        ...
