"""Component hierarchy begining with Drawable."""

from typing import Any, Union

from .component import Component, NeedsUpdates
from .positionable import Positionable
from ..animation import Shape, Sprite, AnimationController
from ..utilitypes import MaybeSequence


class Drawable(Positionable):
    """A component for entities that can be drawn on screen."""

    def __init__(self, z_level=0, **kwargs):
        # type: (int, **Any) -> None
        super().__init__(**kwargs)
        self.z_level = z_level

    @property
    def sprite(self):
        # type: () -> Sprite
        """Get the current sprite."""
        raise NotImplementedError

    def transformed_sprite(self):
        return self.transform @ self.sprite


class Unanimated(Drawable):
    """A component for entities with a static appearance."""

    def __init__(self, sprite_or_shapes, **kwargs):
        # type: (Union[Sprite, MaybeSequence[Shape]], **Any) -> None
        super().__init__(**kwargs)
        if isinstance(sprite_or_shapes, Sprite):
            self._sprite = sprite_or_shapes
        else:
            self._sprite = Sprite(sprite_or_shapes)

    @property
    def sprite(self):
        # type: () -> Sprite
        return self._sprite


class Animated(Drawable, NeedsUpdates):
    """A component for entities with a changing appearance."""

    def __init__(self, animation_controller, **kwargs):
        # type: (AnimationController, **Any) -> None
        super().__init__(**kwargs)
        self.animation = animation_controller

    @property
    def sprite(self):
        # type: () -> Sprite
        return self.animation.get_sprite()

    def update(self, elapsed_msec, _):
        # type: (int, int) -> None
        """Advance the animation state."""
        self.animation.advance_state(elapsed_msec)
