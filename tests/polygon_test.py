"""Tests for polygon.py."""

from animabotics.polygon import Polygon, _simplify_perimeter
from animabotics.simplex import Point2D, Segment


def test_polygon():
    # type: () -> None
    """Test Polygon."""
    rectangle = Polygon.rectangle(2, 2)
    assert rectangle.area == 4
    assert rectangle.centroid == Point2D()
    ellipse = round(Polygon.ellipse(20, 10, num_points=4), 3)
    point1 = Point2D(-20, 0)
    point2 = Point2D(-0, -10)
    point3 = Point2D(20, 0)
    point4 = Point2D(0, 10)
    assert set(ellipse.points) == set([
        point1, point2, point3, point4
    ])
    assert set(ellipse.segments) == set([
        Segment(point1, point2),
        Segment(point2, point3),
        Segment(point3, point4),
        Segment(point4, point1),
    ])


def test_simplify_perimeter():
    # type: () -> None
    """Test simplifying a polygon."""
    # horizontal
    points = (
        Point2D(-3, 0), Point2D(-1, -1), Point2D(1, -1),
        Point2D(3, 0), Point2D(2, 1), Point2D(0, 1), Point2D(-2, 1),
    )
    want = [
        Point2D(-3, 0), Point2D(-1, -1), Point2D(1, -1),
        Point2D(3, 0), Point2D(2, 1), Point2D(-2, 1),
    ]
    have = _simplify_perimeter(points)
    assert have == want, have
    # vertical (simplifying slope == infinity)
    points = (
        Point2D(0, 3), Point2D(-1, 1), Point2D(-1, -1),
        Point2D(0, -3), Point2D(1, -2), Point2D(1, 0), Point2D(1, 2),
    )
    want = [
        Point2D(0, 3), Point2D(-1, 1), Point2D(-1, -1),
        Point2D(0, -3), Point2D(1, -2), Point2D(1, 2),
    ]
    have = _simplify_perimeter(points)
    assert have == want, have
    # vertical (simplifying slope == -infinity)
    points = (
        Point2D(0, -3), Point2D(1, -1), Point2D(1, 1),
        Point2D(0, 3), Point2D(-1, 2), Point2D(-1, 0), Point2D(-1, -2),
    )
    want = [
        Point2D(0, -3), Point2D(1, -1), Point2D(1, 1),
        Point2D(0, 3), Point2D(-1, 2), Point2D(-1, -2),
    ]
    have = _simplify_perimeter(points)
    assert have == want, have
    # degenerate case: reduces to a single point?
    points = (
        Point2D(-2, 0), Point2D(0, 0), Point2D(2, 0), Point2D(3, 0),
        Point2D(1, 0), Point2D(-1, 0), Point2D(-3, 0),
    )
    want = []
    have = _simplify_perimeter(points)
    assert have == want, have
