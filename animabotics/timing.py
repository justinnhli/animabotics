"""Functions for system time."""

from time import monotonic_ns
from typing import Iterator


def get_msec():
    # type: () -> int
    """Return a millisecond-level time."""
    return monotonic_ns() // 1_000_000


class InterruptibleAlgorithm:
    """Abstract base class for an interruptible algorithm."""

    @property
    def completed(self):
        # type: () -> bool
        """Return whether the algorithm has completed."""
        raise NotImplementedError()

    def restart(self):
        # type: () -> None
        """Initialize any state as necessary."""
        raise NotImplementedError()

    def resume(self):
        # type: () -> Iterator[None]
        """Resume running the algorithm."""
        raise NotImplementedError()

    def run_for_msec(self, msecs):
        # type: (int) -> None
        """Run the algorithm for a fixed time."""
        deadline = get_msec() + msecs
        for _ in self.resume():
            if get_msec() >= deadline:
                break

    def run(self):
        # type: () -> None
        """Run the algorithm until completion."""
        for _ in self.resume():
            pass
