#!/home/justinnhli/.local/share/venv/animabotics/bin/python3
"""Demo for animations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from animabotics import Game
from animabotics import GameObject, PhysicsObject
from animabotics import Polygon
from animabotics import Point2D, Vector2D
from animabotics import Transform
from animabotics import AnimationController, Clip, Sprite, Shape


class Ball(PhysicsObject):

    RADIUS = 50
    ELLIPSE = Polygon.ellipse(RADIUS, RADIUS)

    def __init__(self):
        # type: () -> None
        super().__init__()
        self.collision_geometry = Ball.ELLIPSE
        self.collision_radius = Ball.RADIUS
        self.velocity = Vector2D(0, 0)
        self.acceleration = Vector2D(0, -0.001)

    def bounce_vertical(self, ground):
        # type: (GameObject) -> None
        """Bounce the ball vertically.

        This function cheats physics a bit by:
        * forcibly putting the ball above ground, to avoid visual glitches
        * hard-coding the bounce velocity to obey conservation of energy
        """
        self.move_to(Point2D(
            self.position.x,
            ground.position.y + ground.height / 2 + Ball.RADIUS,
        ))
        self.velocity = Vector2D(0, 1.275)

    def energy_update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        """Print kinetic and potential energy after updating."""
        super().update(elapsed_msec, elapsed_msec_squared)
        ke = self.kinetic_energy
        pe = self.mass * abs(self.acceleration.y) * self.position.y
        print(f'y={self.position.y:.5f}, v={self.velocity.y:.5f}')
        print(f'KE = {ke:.5f} = 0.5 * {abs(self.velocity.y):.5f} ** 2')
        print(f'PE = {pe:.5f} = {abs(self.acceleration.y):.5f} * {self.position.y:.5f}')
        print(f'\u03A3E = {ke + pe:.5f}')
        print()


class StoicBall(Ball):
    """A stoic bouncy ball."""

    def __init__(self):
        # type: () -> None
        super().__init__()
        self.animation = AnimationController.create_static_animation(Sprite([Shape(Ball.ELLIPSE)]))


class AnimatedBall(Ball):
    """An animated bouncy ball."""

    def __init__(self):
        # type: () -> None
        super().__init__()
        self.animation = AnimationController()
        self.animation.add_state(
            'default', # name
            Clip.create_static_clip(
                Shape(Polygon.ellipse(50, 50)),
            ),
        )
        self.animation.add_state(
            'bouncing',
            Clip(
                150,
                y_offset=(lambda t: 20 * (t / 150) - 20),
                width_radius=(lambda t: -10 * (t / 150) + 60),
                height_radius=(lambda t: 20 * (t / 150) + 30),
                ellipse=(lambda width_radius, height_radius:
                    Polygon.ellipse(width_radius, height_radius)
                ),
                sprite=(lambda y_offset, ellipse:
                    Transform(y=y_offset) @ Sprite([
                        Shape(ellipse),
                    ])
                ),
            ),
            'default',
        )

    def bounce_vertical(self, ground):
        # type: (GameObject) -> None
        super().bounce_vertical(ground)
        self.animation.set_state('bouncing')


class Ground(GameObject):
    """The ground."""

    def __init__(self):
        # type: () -> None
        super().__init__()
        self.width = 575
        self.height = 30
        self.collision_geometry = Polygon.rectangle(self.width, self.height)
        self.animation = AnimationController.create_static_animation(Sprite([
            Shape(self.collision_geometry),
        ]))
        self.collision_radius = max(self.width, self.height) / 2


class Bouncy(Game):
    """A bouncing ball animation demonstration."""

    def __init__(self):
        # type: () -> None
        super().__init__(600, 800)
        self.create_objects()
        self.register_collisions()
        self.camera.zoom_level = -5

    def create_objects(self):
        # type: () -> None
        """Create the objects."""
        # position the ground so ball.position.y == 0 at rest
        ground = Ground()
        ground.move_to(Point2D(0, -65))
        ground.add_to_collision_group('ground')
        self.add_object(ground)
        stoic_ball = StoicBall()
        stoic_ball.move_to(Point2D(-200, 825))
        stoic_ball.add_to_collision_group('balls')
        self.add_object(stoic_ball)
        anime_ball = AnimatedBall()
        anime_ball.move_to(Point2D(200, 825))
        anime_ball.add_to_collision_group('balls')
        self.add_object(anime_ball)

    def register_collisions(self):
        # type: () -> None
        """Register the collision callbacks."""
        # add collision detection
        self.on_collision(
            'balls', 'ground',
            (lambda ball, ground: ball.bounce_vertical(ground)),
        )


def main():
    # type: () -> None
    """Provide a CLI entry point."""
    Bouncy().start()


if __name__ == '__main__':
    main()
