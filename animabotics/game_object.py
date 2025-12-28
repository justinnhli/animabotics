"""GameObject and its hierarchy."""

from functools import cached_property
from typing import Sequence, Iterator

from .animation import AnimationController, Sprite
from .simplex import Geometry, Point2D, Vector2D
from .transformable import Collidable


class GameObject(Collidable):
    """A basic game object."""

    def __init__(
        self,
        position=None, rotation=0,
        collision_groups=None,
    ): # pylint: disable = unused-argument
        # type: (Sequence[str], Point2D, float) -> None
        """Initialize the GameObject."""
        super().__init__(position, rotation, collision_groups)
        self.animation = None # type: AnimationController
        self.children = [] # type: list[GameObject]

    def __hash__(self):
        # type: () -> int
        return id(self)

    def __repr__(self):
        # type: () -> str
        return f'{type(self).__name__}({self.position})'

    def get_sprite(self):
        # type: () -> Sprite
        """Get the current animation sprite."""
        return self.transform @ self.animation.get_sprite()

    def update(self, elapsed_msec, _):
        # type: (int, int) -> None
        """Update the object."""
        if self.animation is not None:
            self.animation.advance_state(elapsed_msec)

    def squared_distance(self, other):
        # type: (GameObject) -> float
        """Calculate the squared distance to another object."""
        return self.position.squared_distance(other.position)


class PhysicsObject(GameObject):
    """A game object with kinematics."""

    def __init__(self):
        # type: () -> None
        """Initialize the PhysicsObject."""
        super().__init__()
        self.mass = 1
        self.velocity = Vector2D()
        self.angular_velocity = 0.0
        self.acceleration = Vector2D()
        self.angular_acceleration = 0.0

    @property
    def kinetic_energy(self):
        # type: () -> float
        """Calculate the kinetic energy."""
        return 0.5 * self.mass * self.velocity.magnitude ** 2

    def update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        """Update the velocity and the position."""
        super().update(elapsed_msec, elapsed_msec_squared)
        if self.velocity or self.acceleration:
            self.move_by(
                self.velocity * elapsed_msec
                + 0.5 * self.acceleration * elapsed_msec_squared
            )
        if self.angular_velocity or self.angular_acceleration:
            self.rotate_by(
                self.angular_velocity * elapsed_msec
                + 0.5 * self.angular_acceleration * elapsed_msec_squared
            )
        self.velocity += self.acceleration * elapsed_msec
        self.angular_velocity += self.angular_acceleration * elapsed_msec
