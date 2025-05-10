"""Functions for system time."""

from time import monotonic_ns
from typing import Iterator


def get_msec():
    # type: () -> int
    """Return a millisecond-level time."""
    return monotonic_ns() // 1_000_000


class InterruptibleAlgorithm:
    """Abstract base class for an interruptible algorithm."""

    def __init__(self):
        # type: () -> None
        self._process = None # type: Iterator[None]

    @property
    def completed(self):
        # type: () -> bool
        """Return whether the algorithm has completed."""
        raise NotImplementedError()

    def restart(self):
        # type: () -> None
        """Initialize any state as necessary."""
        raise NotImplementedError()

    def hurry_up_and_wait(self):
        # type: () -> Iterator[None]
        """Run the algorithm, yielding when appropriate."""
        raise NotImplementedError()

    def step(self):
        # type: () -> None
        """Take a step in the algorithm until the next yield."""
        if self.completed:
            return
        if self._process is None:
            self._process = self.hurry_up_and_wait()
        try:
            next(self._process)
        except StopIteration:
            self._process = None

    def run_for_msec(self, msecs):
        # type: (int) -> None
        """Run the algorithm for a fixed time."""
        deadline = get_msec() + msecs
        while get_msec() < deadline and not self.completed:
            self.step()

    def run(self):
        # type: () -> None
        """Run the algorithm until completion."""
        while not self.completed:
            self.step()
