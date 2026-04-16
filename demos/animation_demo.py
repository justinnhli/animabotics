#!/home/justinnhli/.local/share/venv/animabotics/bin/python3
"""Demo for animations."""

# pylint: disable = wrong-import-position

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from animabotics import Game, HookTrigger
from animabotics import Collidable, Animated, Unanimated, Newtonian
from animabotics import Component
from animabotics import Polygon
from animabotics import Point2D, Vector2D
from animabotics import AnimationController, Clip, Sprite, Shape
from animabotics import Transform


class Ball(Newtonian, Collidable):
    """A bouncy ball."""

    RADIUS = 50
    ELLIPSE = Polygon.ellipse(RADIUS, RADIUS)

    def __init__(self, **kwargs):
        # type: (**Any) -> None
        super().__init__(
            mass=1,
            physics_geometry=Ball.ELLIPSE,
            velocity=Vector2D(0, 0),
            collision_groups=['balls'],
            **kwargs,
        )

    def bounce_vertical(self, ground):
        # type: (Component) -> None
        """Bounce the ball vertically.

        This function cheats physics a bit by:
        * forcibly putting the ball above ground, to avoid visual glitches
        * hard-coding the bounce velocity to obey conservation of energy
        """
        assert isinstance(ground, Ground)
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


class StoicBall(Ball, Unanimated):
    """A stoic bouncy ball."""

    def __init__(self, **kwargs):
        # type: (**Any) -> None
        super().__init__(
            sprite_or_shapes=Shape(Ball.ELLIPSE),
            **kwargs,
        )


class AnimatedBall(Ball, Animated):
    """An animated bouncy ball."""

    def __init__(self, **kwargs):
        # type: (**Any) -> None
        animation = AnimationController()
        animation.add_state(
            'default',
            Clip.create_static_clip(
                Shape(Polygon.ellipse(50, 50)),
            ),
        )
        animation.add_state(
            'bouncing',
            Clip(
                150,
                y_offset=(lambda t: 20 * (t / 150) - 20),
                width_radius=(lambda t: -10 * (t / 150) + 60),
                height_radius=(lambda t: 20 * (t / 150) + 30),
                ellipse=(lambda width_radius, height_radius: # pylint: disable = unnecessary-lambda
                    Polygon.ellipse(width_radius, height_radius)
                ),
                sprite=(lambda y_offset, ellipse:
                    Transform(y=y_offset) @ Sprite(Shape(ellipse))
                ),
            ),
            'default',
        )
        super().__init__(
            animation_controller=animation,
            **kwargs,
        )

    def bounce_vertical(self, ground):
        # type: (Component) -> None
        super().bounce_vertical(ground)
        self.animation.set_state('bouncing')

    def update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        Newtonian.update(self, elapsed_msec, elapsed_msec_squared)
        Animated.update(self, elapsed_msec, elapsed_msec_squared)


class Ground(Collidable, Unanimated):
    """The ground."""

    def __init__(self, width, height, **kwargs):
        # type: (int, int, **Any) -> None
        super().__init__(
            physics_geometry=Polygon.rectangle(width, height),
            sprite_or_shapes=Shape(Polygon.rectangle(width, height)),
            **kwargs,
        )
        self.height = height


class AnimationDemo(Game):
    """A bouncing ball animation demonstration."""

    def __init__(self):
        # type: () -> None
        super().__init__(600, 800)
        self.stoic_ball = None # type: StoicBall
        self.anime_ball = None # type: AnimatedBall
        self.create_objects()
        self.register_collisions()
        self.camera.zoom_level = -5
        self.register_hook(HookTrigger.PRE_UPDATE, self.apply_gravity)

    def create_objects(self):
        # type: () -> None
        """Create the objects."""
        # position the ground so ball.position.y == 0 at rest
        ground = Ground(
            width=575,
            height=30,
            position=Point2D(0, -65),
            collision_groups='ground',
        )
        self.add_entity(ground)
        self.stoic_ball = StoicBall(
            position=Point2D(-200, 825),

        )
        self.add_entity(self.stoic_ball)
        self.anime_ball = AnimatedBall(
            position=Point2D(200, 825),
        )
        self.add_entity(self.anime_ball)

    def register_collisions(self):
        # type: () -> None
        """Register the collision callbacks."""
        # add collision detection
        self.on_collision(
            'balls', 'ground',
            (lambda ball, ground: ball.bounce_vertical(ground)),
        )

    def apply_gravity(self, _):
        # type: (int) -> None
        """Apply gravity to the balls."""
        self.stoic_ball.apply_force(Vector2D(0, -0.001))
        self.anime_ball.apply_force(Vector2D(0, -0.001))


def main(): # pragma: no cover
    # type: () -> None
    """Provide a CLI entry point."""
    AnimationDemo().start()


if __name__ == '__main__': # pragma: no cover
    main()
