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
