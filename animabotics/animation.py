"""Classes for sprites and animations."""

from functools import cached_property
from dataclasses import dataclass
from typing import Any, Iterator, Sequence

from .color import Color
from .polygon import Polygon
from .simplex import Point2D
from .metaprogramming import CachedMetaclass
from .transform import Transform
from .transformable import Transformable


class Shape(Transformable, metaclass=CachedMetaclass):
    """A colored polygon."""
    polygon: Polygon
    fill_color: Color
    line_color: Color

    def __init__(
            self,
            polygon,
            fill_color=None,
            line_color=None,
            position=None, rotation=0,
        ):
        # type: (Geometry, Color, Color, Point2D, float) -> None
        """Initialize the Shape.

        The use of object.__setattr__ is due to a conflict between frozen dataclasses
        that also do define a custom __init__; see https://github.com/python/cpython/issues/82625
        """
        Transformable.__init__(self, position, rotation)
        self.polygon = polygon
        self.fill_color = fill_color
        self.line_color = line_color

    def __rmatmul__(self, other):
        # type: (Transform) -> Self
        assert isinstance(other, Transform)
        return Shape(
            other @ self.polygon,
            fill_color=self.fill_color,
            line_color=self.line_color,
        )

    @cached_property
    def transformed_geometry(self):
        # type: () -> Geometry
        """The transformed Geometry."""
        return self.transform @ self.polygon


class Sprite:
    """Multiple shapes that make up a single image."""

    def __init__(self, shapes):
        # type: (Shape|Sequence[Shape]) -> None
        if isinstance(shapes, Shape):
            self.shapes = (shapes,) # type: tuple[Shape, ...]
        else:
            self.shapes = tuple(shapes)

    def __iter__(self):
        # type: () -> Iterator[Shape]
        yield from self.shapes

    def __rmatmul__(self, other):
        # type: (Transform) -> Self
        assert isinstance(other, Transform)
        return Sprite(other @ shape for shape in self.shapes)


class Animation:
    """A state machine to control animation sprites/frames."""

    def __init__(self):
        # type: () -> None
        self.sprites = {} # type: dict[str, Sprite]
        self.transitions = {} # type: dict[str, tuple[int, str]]
        self.state = None # type: str
        self.remainder_msec = 0

    def add_state(self, state, sprite):
        # type: (str, Sprite) -> None
        """Associate a state with a sprite."""
        self.sprites[state] = sprite
        if self.state is None:
            self.state = state

    def set_state(self, state):
        # type: (str) -> None
        """Set the current state."""
        assert state in self.sprites
        self.state = state

    def add_timed_transition(self, src, dst, duration_msec):
        # type: (str, str, int) -> None
        """Add a timed transition between states."""
        self.transitions[src] = (duration_msec, dst)

    def advance_state(self, elapsed_msec):
        # type: (int) -> None
        """Change state based on elapsed time."""
        # FIXME optimize
        self.remainder_msec += elapsed_msec
        while True:
            duration, next_state = self.transitions[self.state]
            if duration > self.remainder_msec:
                return
            self.remainder_msec -= duration
            self.state = next_state

    def get_sprite(self, elapsed_msec=0):
        # type: (int) -> Sprite
        """Get the sprite for the current state."""
        if elapsed_msec:
            self.advance_state(elapsed_msec)
        return self.sprites[self.state]

    @staticmethod
    def create_fixed_fps_animation(frame_duration_msec, sprites):
        # type: (int, Sequence[Sprite]) -> Animation
        """Create an animation with fixed timing."""
        animation = Animation()
        for i, sprite in enumerate(sprites):
            animation.add_state(str(i), sprite)
        for i in range(len(sprites) - 1):
            animation.add_timed_transition(str(i), str(i + 1), frame_duration_msec)
        animation.add_timed_transition(str(len(sprites) - 1), str(0), frame_duration_msec)
        return animation

    @staticmethod
    def create_static_animation(sprite):
        # type: (Sprite) -> Animation
        """Create an "animation" that is a static image."""
        animation = Animation()
        animation.add_state('0', sprite)
        animation.add_timed_transition('0', '0', float('Inf'))
        return animation
