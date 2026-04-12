
from typing import Any

from .component import Component
from ..animation import AnimationController, Sprite, OneOrMoreShapes, Shape


class Drawable(Component):

    def __init__(self, z_level=0, **kwargs):
        # type: (int, **Any) -> None
        super().__init__(**kwargs)
        self.z_level = z_level

    def get_sprite(self):
        # type: () -> Sprite
        raise NotImplementedError


class Unanimated(Drawable):

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


class Animated(Drawable):

    def __init__(self, animation_controller, **kwargs):
        # type: (AnimationController, **Any) -> None
        super().__init__(**kwargs)
        self.animation = animation_controller

    def get_sprite(self):
        # type: () -> Sprite
        return self.animation.get_sprite()

    def advance_animation(self, elapsed_msec):
        # type: (int) -> None
        self.animation.advance_state(elapsed_msec)
