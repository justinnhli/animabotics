"""An abstract class for something that is transformable."""

from math import pi as PI
from functools import cached_property

from .simplex import Point2D, Vector2D
from .transform import Transform


class Transformable:
    """An abstract class for something that is transformable."""

    def __init__(self, position=None, rotation=0):
        # type: (Point2D, float) -> None
        if position is None:
            self._position = Point2D()
        else:
            self._position = position
        self._rotation = rotation

    @property
    def position(self):
        # type: () -> Point2D
        """Return the position."""
        return self._position

    @property
    def rotation(self):
        # type: () -> float
        """Return the rotation in 2pi radians."""
        return self._rotation

    @property
    def radians(self):
        # type: () -> float
        """Return the rotation in radians."""
        return self.rotation * PI

    @cached_property
    def transform(self):
        # type: () -> Transform
        """The transform defined by the position of this object."""
        return Transform(self.position.x, self.position.y, self.rotation)

    def _clear_cache(self, rotated=False):
        # type: (bool) -> None
        """Clear the cached_property cache."""
        # pylint: disable = unused-argument
        # need to provide a default to avoid KeyError
        self.__dict__.pop('transform', None)

    def move_to(self, point):
        # type: (Point2D) -> None
        """Move the object to the point."""
        self._position = point
        self._clear_cache()

    def move_by(self, vector):
        # type: (Vector2D) -> None
        """Move the object by the vector."""
        self._position += vector
        self._clear_cache()

    def rotate_to(self, rotation):
        # type: (float) -> None
        """Rotate the object to the angle."""
        self._rotation = rotation
        self._clear_cache(rotated=True)

    def rotate_by(self, rotation):
        # type: (float) -> None
        """Rotate the object by the angle."""
        self._rotation += rotation
        self._clear_cache(rotated=True)
