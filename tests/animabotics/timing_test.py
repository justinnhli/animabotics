"""Tests for timing.py."""

from animabotics import InterruptibleAlgorithm, get_msec


class SieveOfEratosthenes(InterruptibleAlgorithm):
    """An interruptible Sieve of Eratosthenes."""

    def __init__(self, max_num, batch_size=100):
        # type: (int, int) -> None
        super().__init__()
        assert max_num >= 2
        self.max_num = max_num
        self.batch_size = batch_size
        self.count = 2
        self.primes = [2]

    @property
    def completed(self):
        # type: () -> bool
        return self.count >= self.max_num

    def restart(self):
        # type: () -> None
        self.count = 0
        self.primes = [2]

    def resume(self):
        # type: () -> None
        while self.count < self.max_num:
            for self.count in range(self.count, min(self.count + self.batch_size, self.max_num + 1)):
                if not any(self.count % k == 0 for k in self.primes):
                    self.primes.append(self.count)
            yield


def test_interruptible_algorithm():
    # type: () -> None
    """Test the interruptible Sieve of Eratosthenes algorithm."""
    time_budget = 500
    sieve = SieveOfEratosthenes(100_000, batch_size=1000)
    assert not sieve.completed
    pre_msec = get_msec()
    sieve.run_for_msec(500)
    assert not sieve.completed
    aft_msec = get_msec()
    diff = aft_msec - pre_msec
    assert len(sieve.primes) > 2
    assert 0.9 * time_budget <= diff <= 1.1 * time_budget
    sieve.run()
    assert len(sieve.primes) == 9592
    assert sieve.completed
    sieve.restart()
    assert not sieve.completed
