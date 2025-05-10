"""Functions for system time."""

from time import monotonic_ns


def get_msec():
    # type: () -> int
    """Return a millisecond-level time."""
    return monotonic_ns() // 1_000_000
