"""Tests for simplex.py."""

from math import floor, ceil, pi as PI, inf as INF

from animabotics.simplex import Point2D, Vector2D, Segment, Triangle
from animabotics.transform import Transform


def test_point():
    # type: () -> None
    """Test Point2D and Vector2D."""
    point = Point2D(1, 2)
    assert Point2D.from_matrix(point.matrix) == point
    try:
        _ = point + Point2D(-1, -2)
        assert False
    except AssertionError:
        pass
    assert str(point) == 'Point2D(1, 2)'
    assert point.segments == ()
    assert point.area == 0
    assert point.centroid == point
    assert point.convex_partitions == (point,)
    assert -point == Point2D(-1, -2)
    assert point + Vector2D(-1, -2) == Point2D()
    assert point - point == Vector2D()
    assert point.distance(Point2D(4, 6)) == 5
    vector = Vector2D(1, 2)
    assert point.to_vector() == vector
    assert Vector2D.from_matrix(vector.matrix) == vector
    assert str(vector) == 'Vector2D(1, 2)'
    assert bool(vector)
    assert not bool(Vector2D(0, 0))
    assert -vector == Vector2D(-1, -2)
    assert vector + Point2D(-1, -2) == Point2D()
    assert vector + Vector2D(-1, -2) == Vector2D()
    assert 2 * vector == Vector2D(2, 4)
    assert vector * 2 == Vector2D(2, 4)
    assert vector / 2 == Vector2D(0.5, 1)
    assert vector // 2 == Vector2D(0, 1)
    assert point - vector == Point2D()
    assert vector - vector == Vector2D()
    assert vector.to_point() == point
    assert Vector2D(4, 3).magnitude == 5
    assert Vector2D(2, 0).normalized == Vector2D(1, 0)
    assert Vector2D(0, 2).normalized == Vector2D(0, 1)
    assert Vector2D(0, 0).normalized == Vector2D(0, 0)
    assert Vector2D(0, 1).project(Vector2D(1, 0)) == (Vector2D(0, 0), Vector2D(0, 1))
    assert Vector2D(0, -1).project(Vector2D(1, 0)) == (Vector2D(0, 0), Vector2D(0, -1))
    assert Vector2D(0, 1).project(Vector2D(0, -1)) == (Vector2D(0, 1), Vector2D(0, 0))
    assert Vector2D(0, -1).project(Vector2D(0, -1)) == (Vector2D(0, -1), Vector2D(0, 0))
    assert Vector2D(4, 3).project(Vector2D(1, 0)) == (Vector2D(4, 0), Vector2D(0, 3))
    assert Vector2D(4, 3).project(Vector2D(-1, 0)) == (Vector2D(4, 0), Vector2D(0, 3))


def test_segment():
    # type: () -> None
    """Test Segment."""
    segment = Segment(Point2D(1, 2), Point2D(3, 4))
    assert Segment.from_matrix(segment.matrix) == segment
    assert segment.points == (Point2D(1, 2), Point2D(3, 4))
    assert segment.min == Point2D(1, 2)
    assert segment.max == Point2D(3, 4)
    assert segment.centroid == Point2D(2, 3)
    assert segment.twin == Segment(Point2D(3, 4), Point2D(1, 2))
    assert segment.twin.min == Point2D(1, 2)
    assert segment.twin.max == Point2D(3, 4)
    assert segment.slope == 1
    assert Segment(Point2D(0, -1), Point2D(0, 1)).slope == INF
    assert Segment(Point2D(0, 1), Point2D(0, -1)).slope == -INF
    assert Segment(Point2D(0, 0), Point2D(1, 0)).bearing == 0
    assert Segment(Point2D(0, 0), Point2D(0, 1)).bearing == PI / 2
    assert Segment(Point2D(0, 0), Point2D(-1, 0)).bearing == PI
    assert Segment(Point2D(0, 0), Point2D(0, -1)).bearing == 3 * PI / 2
    assert Segment(Point2D(4, 3), Point2D(0, 0)).length == 5
    assert Segment(Point2D(0, 0), Point2D(1, 0)).normal == Vector2D(0, 1)
    assert Segment(Point2D(0, 0), Point2D(1, 0)).twin.normal == Vector2D(0, -1)
    assert Segment(Point2D(0, PI), Point2D(1, 2 * PI)).point_at(0).y == PI
    assert Segment(Point2D(0, PI), Point2D(1, 2 * PI)).point_at(1).y == 2 * PI
    assert str(segment) == 'Segment(Point2D(1, 2), Point2D(3, 4))'
    assert segment.intersect(Segment(Point2D(1, 3), Point2D(3, 5))) is None
    assert Segment(Point2D(1, 0), Point2D(1, 4)).intersect(segment) == Point2D(1, 2)
    # at most one point of intersection, include_end=True
    segments = [
        # vertical second segment
        (Segment(Point2D(0, 2), Point2D(0, 4)), (Point2D(0, 2), None)), # parallel, co-linear, end-end
        (Segment(Point2D(1, 2), Point2D(1, 4)), (None, None)), # parallel, not co-linear, not intersecting
        (Segment(Point2D(1, 1), Point2D(1, 3)), (None, None)), # parallel, not co-linear, not intersecting
        (Segment(Point2D(1, 0), Point2D(1, 2)), (None, None)), # parallel, not co-linear, not intersecting
        # horizontal second segment
        (Segment(Point2D(-1, 3), Point2D(1, 3)), (None, None)), # not parallel, not co-linear, not intersecting
        (Segment(Point2D(-1, 2), Point2D(1, 2)), (Point2D(0, 2), None)), # not parallel, co-linear, middle-end
        (Segment(Point2D(-1, 1), Point2D(1, 1)), (Point2D(0, 1), Point2D(0, 1))), # not parallel, not co-linear, middle-middle
        (Segment(Point2D(0, 3), Point2D(2, 3)), (None, None)), # not parallel, not co-linear, not intersecting
        (Segment(Point2D(0, 2), Point2D(2, 2)), (Point2D(0, 2), None)), # not parallel, co-linear, end-end
        (Segment(Point2D(0, 1), Point2D(2, 1)), (Point2D(0, 1), None)), # not parallel, co-linear, middle-end
    ]
    segment1 = Segment(Point2D(0, 0), Point2D(0, 2))
    for segment2, expecteds in segments:
        for expected, include_end in zip(expecteds, (True, False)):
            answer12 = segment1.intersect(segment2, include_end=include_end)
            answer21 = segment2.intersect(segment1, include_end=include_end)
            if expected is None:
                assert answer12 is None
                assert answer21 is None
            else:
                assert answer12 is not None
                assert answer21 is not None
                assert answer12 == expected
                assert answer21 == expected
    # more than one point of intersection
    segment2 = Segment(Point2D(0, 1), Point2D(0, 3))
    for answer in [segment1.intersect(segment2), segment2.intersect(segment1)]:
        assert answer.x == 0 and 1 <= answer.y <= 2
    segment2 = Segment(Point2D(0, 0), Point2D(0, 2))
    for answer in [segment1.intersect(segment2), segment2.intersect(segment1)]:
        assert answer.x == 0 and 0 <= answer.y <= 2
    # bounding box intersects but not segments
    segment1 = Segment(Point2D(0, 4), Point2D(4, 0))
    segment2 = Segment(Point2D(0, 0), Point2D(1, 1))
    assert segment1.intersect(segment2) is None
    assert segment2.intersect(segment1) is None
    # 2024-12-28
    segment1 = Segment(Point2D(3, 3), Point2D(4, 4))
    segment2 = Segment(Point2D(2, 2), Point2D(5, 5))
    assert segment1.is_overlapping(segment2) == segment2.is_overlapping(segment1) == True
    segment1 = Segment(Point2D(3, 4), Point2D(5, 2))
    segment2 = Segment(Point2D(2, 3), Point2D(4, 5))
    assert segment1.is_colinear(segment2) == segment2.is_colinear(segment1) == False
    assert segment1.is_overlapping(segment2) == segment2.is_overlapping(segment1) == False
    # 2025-03-26
    segment1 = Segment(Point2D(81, 17), Point2D(56, 23))
    segment2 = Segment(Point2D(68, 9), Point2D(43, 67))
    assert round(segment1.intersect(segment2), 3) == Point2D(62.654, 21.403)
    assert round(segment2.intersect(segment1), 3) == Point2D(62.654, 21.403)
    # 2025-03-30
    segment1 = Segment(Point2D(89, 30), Point2D(3, 30))
    segment2 = Segment(Point2D(77, 9), Point2D(84, 60))
    assert round(segment1.intersect(segment2), 3) == Point2D(79.882, 30.0)
    assert round(segment2.intersect(segment1), 3) == Point2D(79.882, 30.0)
    segment1 = Segment(Point2D(0, 0), Point2D(1, 1))
    segment2 = Segment(Point2D(0, 0), Point2D(-1, -1))
    segment3 = Segment(Point2D(0, 0), Point2D(2, 2))
    assert segment1.is_colinear(segment2)
    assert segment1.is_colinear(segment3)
    assert segment2.is_colinear(segment1)
    assert segment2.is_colinear(segment3)
    assert segment3.is_colinear(segment1)
    assert segment3.is_colinear(segment2)
    segment1 = Segment(Point2D(0, 0), Point2D(0, 2))
    segment2 = Segment(Point2D(0, -1), Point2D(0, 1))
    assert segment1.is_overlapping(segment2)
    assert segment2.is_overlapping(segment1)
    segment1 = Segment(Point2D(0, 0), Point2D(0, 1))
    segment2 = Segment(Point2D(0, 1), Point2D(0, 2))
    assert segment1.is_kissing(segment2)
    assert segment2.is_kissing(segment1)
    assert not segment1.is_overlapping(segment2)
    assert not segment2.is_overlapping(segment1)
    segment1 = Segment(Point2D(11, 33), Point2D(16, 68))
    segment2 = Segment(Point2D(12, 40), Point2D(16, 68))
    assert segment1.is_kissing(segment2)
    assert segment2.is_kissing(segment1)
    assert segment1.is_colinear(segment2)
    assert segment2.is_colinear(segment1)
    assert segment1.is_overlapping(segment2)
    assert segment2.is_overlapping(segment1)


def test_triangle():
    # type: () -> None
    """Test Triangle."""
    try:
        Triangle(Point2D(1, 2), Point2D(3, 4), Point2D(5, 6))
        assert False
    except ValueError:
        pass
    triangle = Triangle(Point2D(-4, -1), Point2D(1, -3), Point2D(3, 4))
    assert triangle == Triangle.from_segments(
        Segment(Point2D(-4, -1), Point2D(1, -3)),
        Segment(Point2D(1, -3), Point2D(3, 4)),
        Segment(Point2D(3, 4), Point2D(-4, -1)),
    )
    assert triangle.points == (Point2D(-4, -1), Point2D(1, -3), Point2D(3, 4))
    assert triangle.segments == (
        Segment(Point2D(-4, -1), Point2D(1, -3)),
        Segment(Point2D(1, -3), Point2D(3, 4)),
        Segment(Point2D(3, 4), Point2D(-4, -1)),
    )
    assert str(triangle) == 'Triangle(Point2D(-4, -1), Point2D(1, -3), Point2D(3, 4))'
    assert Triangle.from_matrix(triangle.matrix) == triangle
    assert triangle.area == 19.5
    assert triangle.centroid == Point2D()
    assert round(
        Transform(1, 3, PI / 2, 2)
        @ Triangle(
            Point2D(0, 2),
            Point2D(-2, -1),
            Point2D(2, -1),
        ),
        3,
    ) == Triangle(
        Point2D(-3, 3),
        Point2D(3, -1),
        Point2D(3, 7),
    )
    assert (
        floor(Triangle(Point2D(0.25, 1.25), Point2D(1.5, 0.5), Point2D(2.75, 3.75)))
        == Triangle(Point2D(0, 1), Point2D(1, 0), Point2D(2, 3))
    )
    assert (
        ceil(Triangle(Point2D(0.25, 1.25), Point2D(1.5, 0.5), Point2D(2.75, 3.75)))
        == Triangle(Point2D(1, 2), Point2D(2, 1), Point2D(3, 4))
    )
