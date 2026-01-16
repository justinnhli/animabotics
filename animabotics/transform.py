"""The Transform class."""

from dataclasses import dataclass
from functools import cached_property
from math import sin, cos, pi as PI
from typing import Any

from .matrix import Matrix, identity
from .metaprogramming import CachedMetaclass


@dataclass(frozen=True, order=True)
class Transform(metaclass=CachedMetaclass):
    """A transform."""
    x: float = 0
    y: float = 0
    theta: float = 0
    scale: float = 1

    def __round__(self, ndigits=0):
        # type: (int) -> Transform
        """Round the transform."""
        return Transform(
            round(self.x, ndigits),
            round(self.y, ndigits),
            round(self.theta, ndigits),
            round(self.scale, ndigits),
        )

    def __matmul__(self, other):
        # type: (Any) -> Any
        """Matrix multiplication."""
        if isinstance(other, Transform):
            # from https://gamedev.stackexchange.com/a/207764
            return Transform(
                self.x + self.scale * (other.x * cos(self.theta) - other.y * sin(self.theta)),
                self.y + self.scale * (other.x * sin(self.theta) + other.y * cos(self.theta)),
                other.theta + self.theta,
                other.scale * self.scale,
            )
        else:
            # allow other classes to implement the reciprocal dunder method
            return NotImplemented

    @cached_property
    def matrix(self):
        # type: () -> Matrix
        """Create the transformation matrix."""
        return (
            identity()
            .scale(self.scale, self.scale, self.scale)
            .rotate_z(self.theta)
            .translate(self.x, self.y, 0)
        )

    @cached_property
    def inverse(self):
        # type: () -> Transform
        """Return the inverse transform.

        Equivalent to:

        return (
            Transform(scale=(1 / self.scale))
            @ Transform(theta=-self.theta)
            @ Transform(-self.x, -self.y)
        )
        """
        sin_radians = sin(self.theta)
        cos_radians = cos(self.theta)
        return Transform(
            (-self.x * cos_radians - self.y * sin_radians) / self.scale,
            (self.x * sin_radians - self.y * cos_radians) / self.scale,
            -self.theta,
            1 / self.scale,
        )
