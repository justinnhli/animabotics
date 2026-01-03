"""Tests for canvas.py."""

from itertools import product

from animabotics.canvas import Canvas
from animabotics.color import Color

from image_test_utils import grab_screen, check_image


def test_canvas_pixel():
    # type: () -> None
    """Test drawing a pixel."""
    canvas = Canvas(3, 3, 'test')
    canvas.draw_pixel((1, 1))
    check_image(canvas.image, 'canvas__pixel.ppm')


def test_canvas_line():
    # type: () -> None
    """Test drawing a line."""
    # test all combinations of primes
    sizes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for width, height in product(sizes, repeat=2):
        canvas = Canvas(width, height, 'test')
        # draw NW to SE diagonal
        canvas.draw_line(
            (0, 0),
            (width - 1, height - 1),
        )
        # draw SW to NE diagonal
        canvas.draw_line(
            (0, height - 1),
            (width - 1, 0),
        )
        # get the resulting image
        image = canvas.image.convert('RGB')
        # identify the drawn pixels
        top_left_quadrant = set()
        all_quadrants = set()
        for row in range(height):
            for col in range(width):
                pixel = image.getpixel((col, row))
                if sum(pixel) / 3 >= 128:
                    continue
                all_quadrants.add((col, row))
                if col <= width / 2 and row <= height / 2:
                    top_left_quadrant.add((col, row))
        # test horizontal and vertical symmetry
        for col, row in sorted(top_left_quadrant):
            assert (width - col - 1, row) in all_quadrants
            assert (col, height - row - 1) in all_quadrants
            assert (width - col - 1, height - row - 1) in all_quadrants


def test_canvas_rect():
    # type: () -> None
    """Test drawing a filled rectangle."""
    canvas = Canvas(5, 5, 'test')
    canvas.draw_rect(
        (1, 1),
        (3, 3),
        fill_color=Color.from_hex('#000000'),
    )
    check_image(canvas.image, 'canvas__rect.ppm')


def test_canvas_rect_outline():
    # type: () -> None
    """Test drawing a rectangle outline."""
    canvas = Canvas(5, 5, 'test')
    canvas.draw_rect(
        (1, 1),
        (3, 3),
        line_color=Color.from_hex('#000000'),
    )
    check_image(canvas.image, 'canvas__rect_outline.ppm')


def test_canvas_display():
    # type: () -> None
    """Test an actual displayed canvas."""
    canvas = Canvas(3, 3, 'test')
    canvas.draw_pixel((1, 0))
    canvas.draw_pixel((2, 1))
    canvas.draw_pixel((0, 2))
    canvas.draw_pixel((1, 2))
    canvas.draw_pixel((2, 2))
    image = grab_screen(canvas)
    check_image(image, 'canvas__display.ppm')
