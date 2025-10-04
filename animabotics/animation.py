"""Classes for sprites and animations."""

from collections import defaultdict
from functools import cached_property
from inspect import signature
from math import inf as INF
from typing import Any, Callable, Iterator, Sequence

from .color import Color
from .simplex import Geometry, Point2D
from .metaprogramming import CachedMetaclass
from .transform import Transform
from .transformable import Transformable


class Shape(Transformable, metaclass=CachedMetaclass):
    """A colored polygon."""
    polygon: Geometry
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
        """Initialize the Shape."""
        Transformable.__init__(self, position, rotation)
        self.polygon = polygon
        self.fill_color = fill_color
        self.line_color = line_color

    def __rmatmul__(self, other):
        # type: (Transform) -> Shape
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
        # type: (Sequence[Shape]|Shape) -> None
        if isinstance(shapes, Shape):
            self.shapes = (shapes,) # type: tuple[Shape, ...]
        else:
            self.shapes = tuple(shapes)

    def __iter__(self):
        # type: () -> Iterator[Shape]
        yield from self.shapes

    def __rmatmul__(self, other):
        # type: (Transform) -> Sprite
        assert isinstance(other, Transform)
        return Sprite(tuple(other @ shape for shape in self.shapes))


class Clip:
    """A single animation."""

    def __init__(self, duration_msec, **components):
        # type: (int|float, **Any|Callable[[Any], Any]) -> None
        self.duration_msec = duration_msec
        self.components = components
        self.order = [] # type: list[str]
        self.parameters = {'t': set()} # type: dict[str, set[str]]
        self.result_component = None # type: str
        self.cache = {} # type: dict[int, Sprite]
        self._process_components(components)

    def _process_components(self, components):
        # type: (dict[str, Callable[[Any], Any]]) -> None
        num_dependencies = {} # type: dict[str, int]
        dependents = defaultdict(set) # type: dict[str, set[str]]
        ready = ['t']
        for name, function in components.items():
            if not callable(function):
                ready.append(name)
                continue
            parameters = set(signature(function).parameters)
            # check for unreachable components
            assert all(
                (parameter == 't' or parameter in components)
                for parameter in parameters
            )
            num_dependencies[name] = len(parameters)
            self.parameters[name] = parameters
            for parameter in parameters:
                dependents[parameter].add(name)
        terminals = set(components.keys()) - set(dependents.keys())
        assert len(terminals) == 1
        self.result_component = terminals.pop()
        assert ready
        while ready:
            component = ready.pop(0)
            self.order.append(component)
            for dependent in dependents[component]:
                num_dependencies[dependent] -= 1
                if num_dependencies[dependent] == 0:
                    ready.append(dependent)
        assert self.order[0] == 't'
        self.order = self.order[1:]
        assert len(self.order) == len(components)

    def get_sprite(self, msec):
        # type: (int) -> Sprite
        """Get the Sprite some time into the clip."""
        if msec not in self.cache:
            values = {'t': msec} # type: dict[str, Any]
            for component in self.order:
                if callable(self.components[component]):
                    values[component] = self.components[component](**{
                        parameter: values[parameter]
                        for parameter in self.parameters[component]
                    })
                else:
                    values[component] = self.components[component]
            result = values[self.result_component]
            assert isinstance(result, Sprite), type(result)
            self.cache[msec] = result
        return self.cache[msec]

    @staticmethod
    def create_static_clip(arg):
        # type: (Shape|Sprite) -> Clip
        if isinstance(arg, Shape):
            arg = Sprite([arg])
        assert isinstance(arg, Sprite)
        return Clip(INF, sprite=arg)


class AnimationController:
    """A state machine to control animation sprites/frames."""

    def __init__(self):
        # type: () -> None
        self.clips = {} # type: dict[str, Clip]
        self.transitions = {} # type: dict[str, str]
        self.state = None # type: str
        self.elapsed_msec = 0

    def add_state(self, name, clip, next_state=None):
        # type: (str, Clip, str) -> None
        """Associate a state with a sprite."""
        if next_state is None:
            next_state = name
        self.clips[name] = clip
        self.transitions[name] = next_state
        if self.state is None:
            self.state = name

    def set_state(self, state):
        # type: (str) -> None
        """Set the current state."""
        assert state in self.clips
        self.state = state
        self.elapsed_msec = 0

    def advance_state(self, elapsed_msec):
        # type: (int) -> None
        """Change state based on elapsed time."""
        self.elapsed_msec += elapsed_msec
        while True:
            duration_msec = self.clips[self.state].duration_msec
            if self.elapsed_msec < duration_msec:
                return
            self.state = self.transitions[self.state]
            self.elapsed_msec -= duration_msec

    def get_sprite(self, elapsed_msec=0):
        # type: (int) -> Sprite
        """Get the sprite for the current state."""
        if elapsed_msec:
            self.advance_state(elapsed_msec)
        return self.clips[self.state].get_sprite(self.elapsed_msec)

    @staticmethod
    def create_static_animation(arg):
        # type: (Shape|Sprite|Clip) -> AnimationController
        """Create an "animation" that is a static image."""
        if isinstance(arg, (Shape, Sprite)):
            arg = Clip.create_static_clip(arg)
        assert isinstance(arg, Clip)
        animation = AnimationController()
        animation.add_state('default', arg, 'default')
        animation.set_state('default')
        return animation
