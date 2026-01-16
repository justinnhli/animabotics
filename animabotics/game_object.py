"""GameObject and its hierarchy."""

from typing import Sequence

from .animation import AnimationController, Sprite
from .simplex import Point2D, Vector2D
from .transformable import Collidable


class GameObject(Collidable):
    """A basic game object."""

    def __init__(
        self,
        position=None, rotation=0,
        collision_groups=None,
    ): # pylint: disable = unused-argument
        # type: (Point2D, float, Sequence[str]) -> None
        """Initialize the GameObject."""
        super().__init__(position, rotation, collision_groups)
        self.animation = None # type: AnimationController
        self.children = [] # type: list[GameObject]
        self.z_level = 0

    def __hash__(self):
        # type: () -> int
        return id(self)

    def __repr__(self):
        # type: () -> str
        return f'{type(self).__name__}({self.position})'

    @property
    def sprite(self):
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
        self.center_of_mass = Point2D() # FIXME
        self.mass = 1
        self.velocity = Vector2D()
        self.angular_velocity = 0.0
        self.forces = []

    @property
    def kinetic_energy(self):
        # type: () -> float
        """Calculate the kinetic energy."""
        return 0.5 * self.mass * self.velocity.magnitude ** 2

    def update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        """Update the velocity and the position."""
        super().update(elapsed_msec, elapsed_msec_squared)
        net_force, net_torque = PhysicsObject.sum_forces(self.forces, self.center_of_mass)
        self.forces.clear()
        acceleration = net_force / self.mass
        angular_acceleration = net_torque / self.mass
        if self.velocity or acceleration:
            self.move_by(
                self.velocity * elapsed_msec
                + 0.5 * acceleration * elapsed_msec_squared
            )
        if self.angular_velocity or angular_acceleration:
            self.rotate_by(
                self.angular_velocity * elapsed_msec
                + 0.5 * angular_acceleration * elapsed_msec_squared
            )
        self.velocity += acceleration * elapsed_msec
        self.angular_velocity += angular_acceleration * elapsed_msec

    def apply_force(self, vector, position=None):
        # type: (Vector2D, Point2D) -> None
        """Apply a force at the position."""
        if position is None:
            position = Point2D()
        self.forces.append((vector, position))

    @staticmethod
    def sum_forces(forces, center_of_mass):
        # type: (list[tuple[Vector2D, Point2D]], Point2D) -> tuple[Vector2D, float]
        """Sum up forces to determine net force and net torque."""
        net_force = Vector2D()
        net_torque = 0.0
        for force, position in forces:
            net_force += force
            net_torque += (position - center_of_mass).matrix.cross(force.matrix).z
        return net_force, net_torque
