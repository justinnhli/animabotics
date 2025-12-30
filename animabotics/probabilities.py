"""Classes and functions to work with probabilities."""

from collections import defaultdict
from collections.abc import Mapping
from fractions import Fraction
from itertools import product
from random import Random
from typing import Any, TypeVar, Callable, Iterator


ValueT = TypeVar('ValueT')
OtherT = TypeVar('OtherT')
Real = TypeVar('Real', int, Fraction)


class DiscreteDistribution(Mapping[ValueT, Fraction]):
    """A discrete probability distribution."""

    def __init__(self, probabilities):
        # type: (dict[ValueT, Real]) -> None
        """Initialize a DiscreteDistribution."""
        total = sum(probabilities.values())
        assert total != 0
        self._probabilities = {
            value: Fraction(prob, total)
            for value, prob in probabilities.items()
            if prob > 0
        }

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, DiscreteDistribution)
            and self._probabilities == other._probabilities
        )

    def __len__(self):
        # type: () -> int
        return len(self._probabilities)

    def __getitem__(self, value):
        # type: (ValueT) -> Fraction
        return self._probabilities.get(value, Fraction(0))

    def __iter__(self):
        # type: () -> Iterator[ValueT]
        yield from self._probabilities

    def __str__(self):
        # type: () -> str
        return ' '.join(
            f'{value}:{prob:0.3f}'
            for value, prob in sorted(self._probabilities.items())
        )

    @property
    def values_set(self):
        # type: () -> set[ValueT]
        """Get the values of the distribution as a set."""
        return set(self._probabilities.keys())

    @property
    def probabilities(self):
        # type: () -> Iterator[tuple[ValueT, Fraction]]
        """Get the values and probabilities of the distribution as a list."""
        yield from self._probabilities.items()

    def cross(self, other):
        # type: (DiscreteDistribution[OtherT]) -> DiscreteDistribution[tuple[ValueT, OtherT]]
        """Compute the joint with another distribution."""
        assert isinstance(other, DiscreteDistribution)
        return DiscreteDistribution({
            (value1, value2): prob1 * prob2
            for (value1, prob1), (value2, prob2)
            in product(self.probabilities, other.probabilities)
        })

    def map_values(self, map_fn):
        # type: (Callable[[ValueT], OtherT]) -> DiscreteDistribution[OtherT]
        """Change the values of the distribution (and potentially merging them)."""
        result = defaultdict(Fraction) # type: dict[OtherT, Fraction]
        for value, prob in self._probabilities.items():
            result[map_fn(value)] += prob
        return DiscreteDistribution(result)

    def condition(self, condition_fn):
        # type: (Callable[[ValueT], bool]) -> DiscreteDistribution[ValueT]
        """Condition the distribution on where condition_fn is true."""
        return DiscreteDistribution({
            value: prob
            for value, prob in self.probabilities
            if condition_fn(value)
        })

    def draw(self, rng=None):
        # type: (Random) -> ValueT
        """Draw a value from the distribution."""
        if rng is None:
            rng = Random()
        values, probabilities = zip(*self.probabilities)
        return rng.choices(values, weights=probabilities)[0]
