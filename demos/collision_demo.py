#!/home/justinnhli/.local/share/venv/animabotics/bin/python3
"""Demo for object collisions."""

# pylint: disable = wrong-import-position

import sys
from random import Random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from animabotics import Game
from animabotics import GameObject, PhysicsObject
from animabotics import Polygon
from animabotics import Point2D, Vector2D
from animabotics import Collidable
from animabotics import AnimationController, Shape


class Ball(PhysicsObject, Collidable):
    """A bouncy ball."""

    RADIUS = 15
    ELLIPSE = Polygon.ellipse(RADIUS, RADIUS)
    SHAPE = Shape(ELLIPSE)

    def __init__(self):
        # type: () -> None
        super().__init__()
        self.collision_geometry = Ball.ELLIPSE
        self.animation = AnimationController.create_static_animation(Ball.SHAPE)

    def bounce_vertical(self, _):
        # type: (GameObject) -> None
        """Bounce the ball vertically."""
        self.velocity = Vector2D.from_matrix(self.velocity.matrix.y_reflection)

    def bounce_horizontal(self, _):
        # type: (GameObject) -> None
        """Bounce the ball horizontally."""
        self.velocity = Vector2D.from_matrix(self.velocity.matrix.x_reflection)


class Wall(GameObject):
    """A boundary wall."""

    def __init__(self, width, height):
        # type: (int, int) -> None
        super().__init__()
        self.width = width
        self.height = height
        self.collision_geometry = Polygon.rectangle(width, height)
        self.animation = AnimationController.create_static_animation(
            Shape(self.collision_geometry),
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
            wall = Wall(window_width + 2 * wall_thickness, wall_thickness)
            wall.add_to_collision_group('h_walls')
            wall.move_to(Point2D(0, indicator * (window_height + wall_thickness) // 2))
            self.add_object(wall)
        # left and right walls
        for indicator in (-1, 1):
            wall = Wall(wall_thickness, window_height)
            wall.add_to_collision_group('v_walls')
            wall.move_to(Point2D(indicator * (window_width + wall_thickness) // 2, 0))
            self.add_object(wall)
        # add the balls
        area_width = window_width - wall_thickness - Ball.RADIUS
        area_height = window_height - wall_thickness - Ball.RADIUS
        for _ in range(self.num_balls):
            ball = Ball()
            ball.add_to_collision_group('balls')
            ball.move_to(Point2D(
                self.rng.randrange(
                    -(area_width // 2),
                    (area_width // 2) + 1,
                ),
                self.rng.randrange(
                    -(area_height // 2),
                    (area_height // 2) + 1,
                ),
            ))
            ball.velocity = Vector2D(
                self.rng.randrange(-5, 6) / 100,
                self.rng.randrange(-5, 6) / 100,
            )
            self.add_object(ball)

    def register_collisions(self):
        # type: () -> None
        """Register the collision callbacks."""
        # add collision detection
        self.on_collision('balls', 'h_walls', Ball.bounce_vertical)
        self.on_collision('balls', 'v_walls', Ball.bounce_horizontal)


def main(): # pragma: no cover
    # type: () -> None
    """Provide a CLI entry point."""
    CollisionDemo(20).start()


if __name__ == '__main__': # pragma: no cover
    main()
