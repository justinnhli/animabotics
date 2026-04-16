#!/home/justinnhli/.local/share/venv/animabotics/bin/python3
"""Demo for camera movement and controls."""

import sys
from math import sqrt
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).parent.parent))

from animabotics import BasicWindow
from animabotics import Color
from animabotics import Point2D, Polygon
from animabotics import Transform


def create_einstein(width):
    # type: (int) -> tuple[Polygon, Polygon, Polygon, Polygon]
    """Create the Einstein tile."""
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


def main(): # pragma: no cover
    # type: () -> None
    """Provide a CLI entry point."""
    left_hexagon, down_hexagon, up_hexagon, einstein = create_einstein(100)
    window = BasicWindow(600, 400)
    window.add_geometry(left_hexagon)
    window.add_geometry(down_hexagon)
    window.add_geometry(up_hexagon)
    window.add_geometry(
        einstein,
        line_color=Color(0, 1, 1),
        z_level=1,
    )
    window.camera.move_to(einstein.centroid)
    window.start()


if __name__ == '__main__':
    main()
