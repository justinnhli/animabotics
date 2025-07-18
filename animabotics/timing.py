from time import monotonic_ns as get_nsec_msec


def get_msec():
    # type: () -> int
    """Return a millisecond-level time."""
    return get_nsec_msec() // 1_000_000
