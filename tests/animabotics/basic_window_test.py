"""Tests for basic_window.py."""

from math import sqrt

from animabotics.basic_window import BasicWindow
from animabotics.canvas import Input
from animabotics.color import Color
from animabotics.polygon import Polygon
from animabotics.simplex import Point2D
from animabotics.transform import Transform

from image_test_utils import check_image


def create_einstein():
    # type: () -> tuple[Polygon, Polygon, Polygon, Polygon]
    """Create the Einstein tile."""
    width = 100
    left_hexagon = Polygon.ellipse(width, width, num_points=6)
    down_hexagon = (
        Transform(
            x=3 * width / 2,
            y=-sqrt(3) * width / 2,
        ) @ left_hexagon
    )
    up_hexagon = (
        Transform(
            x=3 * width / 2,
            y=sqrt(3) * width / 2,
        ) @ left_hexagon
    )
    # build the einstein tile
    einstein = Polygon((
        left_hexagon.points[3] + (left_hexagon.points[4] - left_hexagon.points[3]) / 2,
        left_hexagon.points[4],
        left_hexagon.points[5],
        left_hexagon.points[5] + (left_hexagon.points[0] - left_hexagon.points[5]) / 2,
        Point2D(3 * width / 2, -sqrt(3) * width / 2),
        down_hexagon.points[0] + (down_hexagon.points[1] - down_hexagon.points[0]) / 2,
        down_hexagon.points[1],
        down_hexagon.points[1] + (down_hexagon.points[2] - down_hexagon.points[1]) / 2,
        Point2D(3 * width / 2, sqrt(3) * width / 2),
        up_hexagon.points[2] + (up_hexagon.points[3] - up_hexagon.points[2]) / 2,
        up_hexagon.points[3],
        left_hexagon.points[1] + (left_hexagon.points[2] - left_hexagon.points[1]) / 2,
        Point2D(),
    ))
    return left_hexagon, down_hexagon, up_hexagon, einstein


def test_rectangle():
    # type: () -> None
    """Draw a basic rectangle."""
    # create and display the window
    window = BasicWindow(5, 5)
    window.add_geometry(Polygon.rectangle(2, 2))
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__rectangle.ppm')


def test_einstein():
    # type: () -> None
    """Draw and center the Einstein tile."""
    left_hexagon, down_hexagon, up_hexagon, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(left_hexagon)
    window.add_geometry(down_hexagon)
    window.add_geometry(up_hexagon)
    window.add_geometry(einstein, line_color=Color(0, 1, 1))
    window.camera.move_to(einstein.centroid)
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__einstein.ppm')


def test_up():
    # type: () -> None
    """Move the camera up."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='w'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__up.ppm')


def test_down():
    # type: () -> None
    """Move the camera down."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='s'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__down.ppm')


def test_left():
    # type: () -> None
    """Move the camera left."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='a'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__left.ppm')


def test_right():
    # type: () -> None
    """Move the camera right."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='d'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__right.ppm')


def test_clockwise():
    # type: () -> None
    """Rotate the camera clockwise."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='e'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__clockwise.ppm')


def test_counter_clockwise():
    # type: () -> None
    """Rotate the camera counter-clockwise."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='q'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__counter_clockwise.ppm')


def test_zoom_in():
    # type: () -> None
    """Zoom the camera in."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='r'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__in.ppm')


def test_zoom_out():
    # type: () -> None
    """Zoom the camera out."""
    *_, einstein = create_einstein()
    window = BasicWindow(600, 400)
    window.add_geometry(einstein)
    for _ in range(3):
        window.key_callback(
            Input('KeyPress', key_button='f'),
            Point2D(),
        )
    window.prestart()
    window.dispatch_tick()
    check_image(window.canvas.image, 'basic_window__out.ppm')
