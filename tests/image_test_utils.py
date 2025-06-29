"""Utilities for comparing against PPM images."""

from itertools import batched
from pathlib import Path
from typing import Iterator

from PIL import Image, ImageGrab

from animabotics.canvas import Canvas


def ppm_value_generator(path):
    # type: (Path) -> Iterator[str]
    """Read from a ppm file one value at a time."""
    with path.open() as fd:
        for line in fd:
            yield from line.strip().split()


def read_ppm(path):
    # type: (Path) -> tuple[int, int, list[tuple[int, int, int]]]
    """Read an image from a ppm file."""
    # create the generator
    generator = ppm_value_generator(path)
    # read the magic number
    assert next(generator) == 'P3'
    # read the width and height
    width, height = int(next(generator)), int(next(generator))
    # read (and discard) the bit depth
    next(generator)
    # create the pixel map
    pixels = [
        (int(r), int(g), int(b))
        for r, g, b in batched(generator, n=3)
    ]
    return width, height, pixels


def grab_screen(canvas):
    # type: (Canvas) -> Image
    """Take a screenshot of a canvas."""
    canvas.display_page()
    canvas.canvas.update()
    x0 = canvas.tk.winfo_rootx() + canvas.canvas.winfo_x() + 1
    y0 = canvas.tk.winfo_rooty() + canvas.canvas.winfo_y() + 1
    x1 = x0 + canvas.canvas.winfo_width() - 2
    y1 = y0 + canvas.canvas.winfo_height() - 2
    result = ImageGrab.grab().crop((x0, y0, x1, y1))
    canvas.tk.destroy()
    return result


def check_image(image, filename):
    # type: (Image, str) -> None
    """Check that a canvas matches the file."""
    ppm_path = Path(__file__).parent / 'images' / filename
    width, height, ppm_pixels = read_ppm(ppm_path)
    assert image.width == width
    assert image.height == height
    pixels = image.getdata()
    for x in range(width):
        for y in range(height):
            index = y * width + x
            assert pixels[index] == ppm_pixels[index]


def save_image(image, filename):
    # type: (Image, str) -> None
    """Save an image to file."""
    ppm_path = Path(__file__).parent / 'images' / filename
    pixels = image.getdata()
    with ppm_path.open('w') as fd:
        fd.write('P3\n')
        fd.write(f'{image.width} {image.height}\n')
        fd.write('255\n')
        for r in range(400):
            row = []
            for c in range(600):
                index = r * image.width + c
                row.append(' '.join(str(n) for n in pixels[index]))
            fd.write('  '.join(row))
            fd.write('\n')
