"""Tests for animation.py."""

from animabotics.animation import AnimationController, Clip, Sprite, Shape
from animabotics.polygon import Polygon
from animabotics.simplex import Point2D
from animabotics.transform import Transform


def test_clip():
    # type: () -> None
    """Test Clip."""
    # normal clip
    clip = Clip(
        500,
        y_offset=(lambda t: 20 * (t / 500) - 20),
        width_radius=(lambda t: -10 * (t / 500) + 60),
        height_radius=(lambda t: 20 * (t / 500) + 30),
        ellipse=(lambda width_radius, height_radius:
            Polygon.ellipse(width_radius, height_radius, num_points=4)
        ),
        sprite=(lambda y_offset, ellipse:
            Transform(y=y_offset) @ Sprite([Shape(ellipse)])
        ),
    )
    assert (
        round(clip.get_sprite(0).shapes[0].polygon).points
        == (Point2D(60, -20), Point2D(0, 10), Point2D(-60, -20), Point2D(0, -50))
    )
    assert (
        round(clip.get_sprite(250).shapes[0].polygon).points
        == (Point2D(55, -10), Point2D(0, 30), Point2D(-55, -10), Point2D(0, -50))
    )
    assert (
        round(clip.get_sprite(500).shapes[0].polygon).points
        == (Point2D(50, 0), Point2D(0, 50), Point2D(-50, 0), Point2D(0, -50))
    )
    # static clip
    clip = Clip.create_static_clip(
        Shape(Polygon.ellipse(50, 50, num_points=4)),
    )
    assert (
        round(clip.get_sprite(0).shapes[0].polygon).points
        == (Point2D(50, 0), Point2D(0, 50), Point2D(-50, 0), Point2D(0, -50))
    )
    assert (
        round(clip.get_sprite(500).shapes[0].polygon).points
        == (Point2D(50, 0), Point2D(0, 50), Point2D(-50, 0), Point2D(0, -50))
    )
    # extraneous variable
    try:
        clip = Clip(
            500,
            width_radius=(lambda t: -10 * (t / 500) + 60),
            height_radius=(lambda t: 20 * (t / 500) + 30),
            ellipse=(lambda width_radius, height_radius:
                Polygon.ellipse(width_radius, height_radius)
            ),
            sprite=(lambda ellipse: Sprite([ellipse])),
            # extraneous variable
            area=(lambda width_radius, height_radius:
                2 * width_radius * height_radius
            ),
        )
        assert False
    except AssertionError:
        pass
    # unreachable variable
    try:
        clip = Clip(
            500,
            width_radius=(lambda t: -10 * (t / 500) + 60),
            height_radius=(lambda t: 20 * (t / 500) + 30),
            ellipse=(lambda width_radius, height_radius:
                Polygon.ellipse(width_radius, height_radius)
            ),
            sprite=(lambda ellipse: Sprite([ellipse])),
            # unreachable variable
            volume=(lambda area: (area ** 0.5) ** 3),
        )
        assert False
    except AssertionError:
        pass

def test_animation_controller():
    # type: () -> None
    """Test AnimationController."""
    # static animation
    controller = AnimationController.create_static_animation(
        Shape(Polygon.ellipse(50, 50, num_points=4)),
    )
    assert (
        round(controller.get_sprite().shapes[0].polygon).points
        == (Point2D(50, 0), Point2D(0, 50), Point2D(-50, 0), Point2D(-0, -50))
    )
    # real animation
    controller = AnimationController()
    controller.add_state(
        '0',
        Clip.create_static_clip(
            Shape(Polygon.ellipse(50, 50, num_points=4)),
        ),
    )
    controller.add_state(
        '1',
        Clip(
            200,
            radius=(lambda t: 50 * ((200 - t) / 200) + 50),
            sprite=(lambda radius: Sprite(Shape(
                Polygon.ellipse(radius, radius, num_points=4),
            ))),
        ),
        '0',
    )
    controller.add_state(
        '2',
        Clip(
            200,
            radius=(lambda t: 100 * ((200 - t) / 200) + 100),
            sprite=(lambda radius: Sprite(Shape(
                Polygon.ellipse(radius, radius, num_points=4),
            ))),
        ),
        '1',
    )
    controller.set_state('0')
    assert controller.elapsed_msec == 0
    assert controller.state == '0'
    assert (
        round(controller.get_sprite().shapes[0].polygon).points
        == (Point2D(50, 0), Point2D(0, 50), Point2D(-50, 0), Point2D(-0, -50))
    )
    assert (
        round(controller.get_sprite(40).shapes[0].polygon).points
        == (Point2D(50, 0), Point2D(0, 50), Point2D(-50, 0), Point2D(-0, -50))
    )
    assert controller.elapsed_msec == 40
    controller.set_state('2')
    assert (
        round(controller.get_sprite().shapes[0].polygon).points
        == (Point2D(200, 0), Point2D(0, 200), Point2D(-200, 0), Point2D(-0, -200))
    )
    controller.advance_state(50)
    assert (
        round(controller.get_sprite().shapes[0].polygon).points
        == (Point2D(175, 0), Point2D(0, 175), Point2D(-175, 0), Point2D(-0, -175))
    )
    controller.advance_state(150)
    assert controller.state == '1'
    assert (
        round(controller.get_sprite().shapes[0].polygon).points
        == (Point2D(100, 0), Point2D(0, 100), Point2D(-100, 0), Point2D(-0, -100))
    )
    controller.advance_state(100)
    assert (
        round(controller.get_sprite().shapes[0].polygon).points
        == (Point2D(75, 0), Point2D(0, 75), Point2D(-75, 0), Point2D(-0, -75))
    )
    assert (
        round(controller.get_sprite(100).shapes[0].polygon).points
        == (Point2D(50, 0), Point2D(0, 50), Point2D(-50, 0), Point2D(-0, -50))
    )
