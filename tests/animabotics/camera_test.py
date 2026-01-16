"""Tests for camera.py."""

from animabotics.camera import Camera
from animabotics.canvas import Canvas
from animabotics.polygon import Polygon
from animabotics.simplex import Point2D

from image_test_utils import check_image


def test_canvas_pixel():
    # type: () -> None
    """Test drawing a pixel."""
    canvas = Canvas(3, 3, 'test')
    camera = Camera(canvas)
    camera.draw_geometry(Point2D(0, 0))
    check_image(canvas.image, 'canvas__pixel.ppm')


def test_canvas_rect():
    # type: () -> None
    """Test drawing a rectangle."""
    canvas = Canvas(5, 5, 'test')
    camera = Camera(canvas)
    camera.draw_geometry(Polygon.rectangle(2, 2))
    check_image(canvas.image, 'canvas__rect_outline.ppm')


def test_camera_collision_geometry():
    canvas = Canvas(100, 100, 'test')
    camera = Camera(canvas)
    assert camera.collision_geometry == Polygon((
        Point2D(-50, 50),
        Point2D(-50, -50),
        Point2D(50, -50),
        Point2D(50, 50),
    ))
    camera.zoom_level = 1
    assert camera.collision_geometry == Polygon((
        Point2D(-40, 40),
        Point2D(-40, -40),
        Point2D(40, -40),
        Point2D(40, 40),
    ))
    camera.zoom_level = -1
    assert round(camera.collision_geometry, 1) == round(Polygon((
        Point2D(-62.5, 62.5),
        Point2D(-62.5, -62.5),
        Point2D(62.5, -62.5),
        Point2D(62.5, 62.5),
    )), 1)
