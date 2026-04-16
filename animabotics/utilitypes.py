"""Abstract types."""

from typing import TypeVar, Protocol, Any, Union, overload

T = TypeVar('T')
T_contra = TypeVar("T_contra", contravariant=True)


class ComparableT(Protocol[T_contra]):
    """Abstract class for __eq__ and __lt__ types."""

    def __eq__(self, __other):
        # type: (Any) -> bool
        ...

    def __lt__(self, __other):
        # type: (T_contra) -> bool
        ...


MaybeSequence = Union[list[T], tuple[T, ...], T]


@overload
def unwrap_maybe_sequence(arg: list[T]) -> tuple[T, ...]:
    # pylint: disable = unused-argument
    ...


@overload
def unwrap_maybe_sequence(arg: tuple[T, ...]) -> tuple[T, ...]:
    # pylint: disable = unused-argument
    ...


@overload
def unwrap_maybe_sequence(arg: T) -> tuple[T, ...]:
    # pylint: disable = unused-argument
    ...


def unwrap_maybe_sequence(arg: MaybeSequence[T]) -> tuple[T, ...]:
    """Convert either a sequence or a naked element into a tuple."""
    if isinstance(arg, tuple):
        return arg
    elif isinstance(arg, list):
        return tuple(arg)
    else:
        return (arg, )
