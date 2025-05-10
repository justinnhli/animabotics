#!/home/justinnhli/.local/share/venv/animabotics/bin/python3
"""Demo for object collisions."""

# pylint: disable = wrong-import-position

import sys
from random import Random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from animabotics import Game
from animabotics import Polygon
from animabotics import Point2D, Vector2D
from animabotics import Collidable, Newtonian, Unanimated
from animabotics import Shape


class Ball(Collidable, Newtonian, Unanimated):
    """A bouncy ball."""

    RADIUS = 15
    ELLIPSE = Polygon.ellipse(RADIUS, RADIUS)
    SHAPE = Shape(ELLIPSE)

    def __init__(self, position, velocity):
        # type: (Point2D, Vector2D) -> None
        super().__init__(
            position=position,
            velocity=velocity,
            mass=1,
            physics_geometry=Ball.ELLIPSE,
            sprite_or_shapes=Shape(Ball.ELLIPSE),
            collision_groups=['balls'],
        )

    def bounce_vertical(self, _):
        # type: (Collidable) -> None
        """Bounce the ball vertically."""
        self.velocity = Vector2D.from_matrix(self.velocity.matrix.y_reflection)

    def bounce_horizontal(self, _):
        # type: (Collidable) -> None
        """Bounce the ball horizontally."""
        self.velocity = Vector2D.from_matrix(self.velocity.matrix.x_reflection)


class Wall(Collidable, Unanimated):
    """A boundary wall."""

    def __init__(self, width, height, position, collision_groups):
        # type: (int, int, Point2D, list[str]) -> None
        geometry = Polygon.rectangle(width, height)
        super().__init__(
            position=position,
            sprite_or_shapes=Shape(geometry),
            physics_geometry=geometry,
            collision_groups=collision_groups,
        )


class CollisionDemo(Game):
    """A bouncing ball collision demonstration."""

    def __init__(self, num_balls, random_seed=None):
        # type: (int, int) -> None
        super().__init__(600, 400)
        self.rng = Random(random_seed)
        self.num_balls = num_balls
        self.create_objects()
        self.register_collisions()

    def create_objects(self):
        # type: () -> None
        """Create the objects."""
        # add walls
        wall_thickness = 50
        window_width = self.window_width - (wall_thickness // 2)
        window_height = self.window_height - (wall_thickness // 2)
        # top and bottom walls
        for indicator in (-1, 1):
            wall = Wall(
                width=window_width + 2 * wall_thickness,
                height=wall_thickness,
                position=Point2D(0, indicator * (window_height + wall_thickness) // 2),
                collision_groups=['h_walls'],
            )
            self.add_entity(wall)
        # left and right walls
        for indicator in (-1, 1):
            wall = Wall(
                width=wall_thickness,
                height=window_height,
                position=Point2D(indicator * (window_width + wall_thickness) // 2, 0),
                collision_groups=['v_walls'],
            )
            self.add_entity(wall)
        # add the balls
        area_width = window_width - wall_thickness - Ball.RADIUS
        area_height = window_height - wall_thickness - Ball.RADIUS
        for _ in range(self.num_balls):
            ball = Ball(
                position=Point2D(
                    self.rng.randrange(
                        -(area_width // 2),
                        (area_width // 2) + 1,
                    ),
                    self.rng.randrange(
                        -(area_height // 2),
                        (area_height // 2) + 1,
                    ),
                ),
                velocity=Vector2D(
                    self.rng.randrange(-5, 6) / 100,
                    self.rng.randrange(-5, 6) / 100,
                ),
            )
            self.add_entity(ball)

    def register_collisions(self):
        # type: () -> None
        """Register the collision callbacks."""
        # add collision detection
        self.on_collision('balls', 'h_walls', Ball.bounce_vertical)
        self.on_collision('balls', 'v_walls', Ball.bounce_horizontal)


def main(): # pragma: no cover
    # type: () -> None
    """Provide a CLI entry point."""
    CollisionDemo(20, random_seed=8675309).start()


if __name__ == '__main__': # pragma: no cover
    main()
