"""Component hierarchy begining with Drawable."""

from typing import Any

from .component import Component, NeedsUpdates
from ..animation import OneOrMoreShapes, Sprite, AnimationController


class Drawable(Component):
    """A component for entities that can be drawn on screen."""

    def __init__(self, z_level=0, **kwargs):
        # type: (int, **Any) -> None
        super().__init__(**kwargs)
        self.z_level = z_level

    def get_sprite(self):
        # type: () -> Sprite
        """Get the current sprite."""
        raise NotImplementedError


class Unanimated(Drawable):
    """A component for entities with a static appearance."""

    def __init__(self, sprite_or_shapes, **kwargs):
        # type: (OneOrMoreShapes | Sprite, **Any) -> None
        super().__init__(**kwargs)
        if isinstance(sprite_or_shapes, Sprite):
            self.sprite = sprite_or_shapes
        else:
            self.sprite = Sprite(sprite_or_shapes)

    def get_sprite(self):
        # type: () -> Sprite
        return self.sprite


class Animated(Drawable, NeedsUpdates):
    """A component for entities with a changing appearance."""

    def __init__(self, animation_controller, **kwargs):
        # type: (AnimationController, **Any) -> None
        super().__init__(**kwargs)
        self.animation = animation_controller

    def get_sprite(self):
        # type: () -> Sprite
        return self.animation.get_sprite()

    def update(self, elapsed_msec, _):
        # type: (int, int) -> None
        """Advance the animation state."""
        self.animation.advance_state(elapsed_msec)
