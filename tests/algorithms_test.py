"""Tests for algorithms.py."""

from collections.abc import Sequence
from itertools import product
from math import pi as PI
from typing import Iterator

from animabotics.algorithms import bentley_ottmann, triangulate_polygon, convex_partition
from animabotics.simplex import Point2D, Segment
from animabotics.polygon import ConvexPolygon


def _no_duplicates_coord_segments(num_segments):
    # type: (int) -> Iterator[tuple[Segment, ...]]
    """Generate segments with no duplicate x or y coordinates."""

    def _generate_segments(xs, ys, segments):
        # type: (list[int], list[int], list[Segment]) -> Iterator[tuple[Segment, ...]]
        if not xs:
            yield ()
            return
        x1 = xs[0]
        for y1 in ys:
            point1 = Point2D(x1, y1)
            xs_ = xs[1:]
            ys_ = [y for y in ys if y != y1]
            for x2, y2 in product(xs_, ys_):
                segment = Segment(point1, Point2D(x2, y2))
                if any(segment.is_overlapping(existing) for existing in segments):
                    continue
                recursed = _generate_segments(
                    [x for x in xs_ if x != x2],
                    [y for y in ys_ if y != y2],
                    segments + [segment],
                )
                for results in recursed:
                    yield (segment, *results)

    yield from _generate_segments(
        list(range(2 * num_segments)),
        list(range(2 * num_segments)),
        [],
    )


def _naive_all_intersects(segments, include_end=False):
    # type: (Sequence[Segment], bool) -> list[Point2D]
    """Calculate all intersects naively (in O(n^2) time)."""
    results = []
    for i, segment1 in enumerate(segments):
        for segment2 in segments[i + 1:]:
            intersect = segment1.intersect(segment2, include_end=include_end)
            if intersect is not None:
                results.append(intersect)
    return results


def test_bentley_ottmann():
    # type: () -> None
    """Testing entry point."""

    def test_segments(segments, include_end):
        # type: (Sequence[Segment], bool) -> None
        expected = sorted(set(
            round(intersect, 3) for intersect
            in _naive_all_intersects(segments, include_end=include_end)
        ))
        actual = sorted(
            round(intersect, 3) for intersect
            in bentley_ottmann(segments, include_end=include_end)
        )
        assert expected == actual, (segments, expected, actual)

    # no duplicate x or y, including three-segment intersects
    num_segments = 3
    for segments in _no_duplicates_coord_segments(num_segments):
        for include_end in (False, True):
            test_segments(segments, include_end)
    # vertical segment with one horizontal segment
    assert bentley_ottmann([
        Segment(Point2D(-2, 1), Point2D(2, 1)),
        Segment(Point2D(1, -2), Point2D(1, 2)),
    ]) == [Point2D(1, 1)]
    # vertical segment with multiple horizontal segments
    assert bentley_ottmann([
        Segment(Point2D(0, -3), Point2D(0, 3)),
        *(
            Segment(Point2D(-3, i), Point2D(3, i))
            for i in range(-2, 3)
        )
    ]) == [Point2D(0, i) for i in range(-2, 3)]
    # vertical segment that "kisses" a horizontal segment
    for include_end, expected in zip((False, True), ([], [Point2D(0, 0)])):
        assert bentley_ottmann(
            [
                Segment(Point2D(-2, 0), Point2D(0, 0)),
                Segment(Point2D(0, -2), Point2D(0, 2)),
            ],
            include_end=include_end,
        ) == expected
    # non-vertical co-linear segments that "kiss"
    for include_end, expected in zip((False, True), ([], [Point2D(0, 0)])):
        assert bentley_ottmann(
            [
                Segment(Point2D(-2, -2), Point2D(0, 0)),
                Segment(Point2D(0, 0), Point2D(2, 2)),
            ],
            include_end=include_end,
        ) == expected
    # vertical co-linear segments that "kiss"
    for include_end, expected in zip((False, True), ([], [Point2D(0, 0)])):
        assert bentley_ottmann(
            [
                Segment(Point2D(0, -2), Point2D(0, 0)),
                Segment(Point2D(0, 0), Point2D(0, 2)),
            ],
            include_end=include_end,
        ) == expected
    # 2025-02-08
    assert bentley_ottmann(
        [
            Segment(Point2D(0, 0), Point2D(-2, -2)),
            Segment(Point2D(0, 0), Point2D(2, 2)),
        ],
        include_end=True,
    ) == [Point2D(0, 0)]
    # 2025-03-30
    assert bentley_ottmann(
        [
            Segment(Point2D(93, 87), Point2D(54, 8)),
            Segment(Point2D(54, 8), Point2D(40, 37)),
        ],
        include_end=True,
    ) == [Point2D(54, 8)]


POLYGON_PARTITION_DATASET = (
    # start, add, end
    (
        Point2D(4, 1), Point2D(2, 2), Point2D(-1, 2), Point2D(-3, 1),
        Point2D(-4, -1), Point2D(-2, -2), Point2D(1, -2), Point2D(3, -1),
    ),
    (
        Point2D(-8, 0), Point2D(-5, -1), Point2D(-3, -2),
        Point2D(-2, -3), Point2D(-1, -5), Point2D(0, -8),
        Point2D(1, 1),
    ),
    (
        Point2D(-8, 0), Point2D(-5, -1), Point2D(-3, -2),
        Point2D(-2, -3), Point2D(-1, -5), Point2D(0, -8),
        Point2D(1, -4), Point2D(3, 0),
    ),
    (
        Point2D(8, -4), Point2D(7, 4), Point2D(5, 4), Point2D(4, 1), Point2D(3, -1),
        Point2D(2, -2), Point2D(0, -3), Point2D(-1, 4), Point2D(-8, 4), Point2D(-8, 1),
        Point2D(-6, 2), Point2D(-5, 2), Point2D(-4, 1), Point2D(-3, -1), Point2D(-2, -4),
    ),
    (
        Point2D(-2, 2), Point2D(-2, -2), Point2D(2, -2), Point2D(2, 2),
    ),
    (
        Point2D(-2, 2), Point2D(-2, 0), Point2D(-2, -2), Point2D(0, -2),
        Point2D(2, -2), Point2D(2, 0), Point2D(2, 2), Point2D(0, 2),
    ),
    # merge or split
    (
        Point2D(-1, 1), Point2D(0, 0), Point2D(-1, -1),
        Point2D(2, -1), Point2D(1, 1),
    ),
    (
        Point2D(-1, 1), Point2D(0, 0), Point2D(-1, -1),
        Point2D(2, -1),
    ),
    (
        Point2D(-1, 5), Point2D(0, 4), Point2D(-1, 3), Point2D(1, 2), Point2D(-1, 1), Point2D(0, 0),
        Point2D(-1, -1), Point2D(1, -2), Point2D(-1, -3), Point2D(0, -4), Point2D(-1, -5), Point2D(8, 0),
    ),
    (
        Point2D(-1, 2), Point2D(0, 0), Point2D(-2, 1),
        Point2D(1, -2), Point2D(2, -1),
    ),
    (
        Point2D(-1, 2), Point2D(0, 0), Point2D(-2, 1),
        Point2D(2, -2), Point2D(1, 3),
    ),
    (
        Point2D(-1, 3), Point2D(-2, 2), Point2D(0, 0),
        Point2D(-2, 1), Point2D(1, -1),
    ),
    (
        Point2D(0, 3), Point2D(-1, 2), Point2D(0, 1),
        Point2D(0, -1), Point2D(-1, -2), Point2D(0, -3),
        Point2D(2, 0),
    ),
    (
        Point2D(1, 3), Point2D(-2, 2), Point2D(-1, 1), Point2D(0, 1),
        Point2D(0, -1), Point2D(-1, -2), Point2D(1, -3), Point2D(2, 0),
    ),
    (
        Point2D(3, 0), Point2D(2, 4), Point2D(-3, 4), Point2D(1, -1), Point2D(-1, 1),
        Point2D(-3, 1), Point2D(-2, 0), Point2D(-3, -1), Point2D(-3, -4), Point2D(2, -4),
    ),
    (
        Point2D(3, 0), Point2D(2, 4), Point2D(-3, 4), Point2D(1, -1), Point2D(-1, 1),
        Point2D(-3, 1), Point2D(-2, 0), Point2D(-6, -4), Point2D(2, -4),
    ),
    (
        Point2D(-2, 2),
        Point2D(0, -1),
        Point2D(-2, -2),
        Point2D(1, -2),
        Point2D(1, 1),
        Point2D(2, 2),
    ),
    (
        Point2D(-2, 2),
        Point2D(0, -1),
        Point2D(-2, -2),
        Point2D(0, -2),
        Point2D(1, 1),
        Point2D(2, 2),
    ),
    (
        Point2D(0, 0), Point2D(8, 2), Point2D(7, 4),
        Point2D(8, 6), Point2D(7, 5), Point2D(6, 3), Point2D(5, 2), Point2D(3, 1),
    ),
    # merge and split
    (
        Point2D(0, 2), Point2D(-2, 1), Point2D(-1, 0), Point2D(-2, -1),
        Point2D(0, -2), Point2D(2, -1), Point2D(1, 0), Point2D(2, 1),
    ),
    (
        Point2D(-2, 1), Point2D(-1, 0), Point2D(-2, -1),
        Point2D(2, -1), Point2D(1, 0), Point2D(2, 1),
    ),
    (
        Point2D(-2, 4), Point2D(0, 3), Point2D(-2, 2), Point2D(0, 1),
        Point2D(-2, -1), Point2D(0, -2), Point2D(-2, -3), Point2D(-1, -4),
        Point2D(2, -4), Point2D(0, -3), Point2D(2, -2), Point2D(0, -1),
        Point2D(2, 1), Point2D(0, 2), Point2D(2, 3), Point2D(1, 4),
    ),
    (
        Point2D(3, 0),
        Point2D(1, 2), Point2D(3, 4),
        Point2D(-2, 4), Point2D(-1, 3), Point2D(-2, 2), Point2D(-1, 1),
        Point2D(-2, 0),
        Point2D(-1, -1), Point2D(-2, -2), Point2D(-1, -3), Point2D(-2, -4),
        Point2D(3, -4), Point2D(1, -2),
    ),
    (
        Point2D(3, 0),
        Point2D(1, 2), Point2D(3, 4),
        Point2D(-4, 4), Point2D(-1, 3), Point2D(-2, 2), Point2D(-1, 1),
        Point2D(-2, 0),
        Point2D(-1, -1), Point2D(-2, -2), Point2D(-1, -3), Point2D(-4, -4),
        Point2D(3, -4), Point2D(1, -2),
    ),
    (
        Point2D(1, 0), Point2D(2, 5), Point2D(-4, 1), Point2D(-2, 2), Point2D(-1, 2),
        Point2D(0, 0), Point2D(-1, -2), Point2D(-2, -2), Point2D(-4, -1), Point2D(2, -5),
    ),
    (
        Point2D(1, 0), Point2D(2, 5), Point2D(-4, 1), Point2D(-2, 2), Point2D(-1, 2),
        Point2D(-1, -2), Point2D(-2, -2), Point2D(-4, -1), Point2D(2, -5),
    ),
    (
        Point2D(-2, 2),
        Point2D(-1, 1),
        Point2D(-2, -2),
        Point2D(2, -2),
        Point2D(0, -1),
        Point2D(2, 2),
    ),
    (
        Point2D(0, -5), Point2D(10, -3), Point2D(9, 0), Point2D(10, 3),
        Point2D(0, 5), Point2D(3, 4), Point2D(5, 3), Point2D(6, 2),
        Point2D(7, 0), Point2D(6, -2), Point2D(5, -3), Point2D(3, -4),
    ),
    (
        Point2D(-2, 4),
        Point2D(-2, -4),
        Point2D(0, -1),
        Point2D(2, -4),
        Point2D(2, -3),
        Point2D(-1, 2),
        Point2D(2, -2),
        Point2D(2, 4),
        Point2D(0, 1),
    ),
    # repeated points and opposite colinear segments
    (
        Point2D(0, 0), Point2D(1, 1), Point2D(2, 0), Point2D(1, -1),
        Point2D(0, 0), Point2D(2, -3), Point2D(4, 0), Point2D(2, 3),
    ),
    (
        Point2D(2, 0), Point2D(0, 2), Point2D(-2, 0), Point2D(0, -2), Point2D(2, 0),
        Point2D(1, 0), Point2D(0, -1), Point2D(-1, 0), Point2D(0, 1), Point2D(1, 0),
    ),
    (
        Point2D(0, 0), Point2D(2, -3), Point2D(1, -1), Point2D(4, -3), Point2D(4, -1),
        Point2D(1, 0), Point2D(4, 1), Point2D(4, 3), Point2D(1, 1), Point2D(2, 3),
        Point2D(0, 0), Point2D(3, 2), Point2D(3, 1),
        Point2D(0, 0), Point2D(3, -1), Point2D(3, -2),
    ),
    (
        Point2D(0, -4), Point2D(4, -4), Point2D(4, 4), Point2D(-4, 4), Point2D(-4, -4), Point2D(0, -4), Point2D(0, 0),
        Point2D(-1, -2), Point2D(-2, -1), Point2D(0, 0),
        Point2D(-3, -1), Point2D(-3, 1), Point2D(0, 0),
        Point2D(-2, 1), Point2D(-1, 2), Point2D(0, 0),
        Point2D(-1, 3), Point2D(1, 3), Point2D(0, 0),
        Point2D(1, 2), Point2D(2, 1), Point2D(0, 0),
        Point2D(3, 1), Point2D(3, -1), Point2D(0, 0),
        Point2D(2, -1), Point2D(1, -2), Point2D(0, 0),
    ),
)


def _validate_partition(points, partition_indices):
    # type: (Sequence[Point2D], tuple[tuple[int, ...], ...]) -> None
    components = (
        ConvexPolygon(points=tuple(points[i] for i in index))
        for index in partition_indices
    )
    # initialize the segments with the _clockwise_ perimeter
    # which will be "canceled out" during the verification
    boundary_segments = set(
        Segment(points[i], points[i - 1])
        for i in range(len(points))
    )
    internal_segments = set() # type: set[Segment]
    # verify each component
    for component in components:
        # verify component goes does not go clockwise
        assert all(
            Segment.orientation(
                component.points[i - 1],
                component.points[i],
                component.points[i + 1],
            ) != 1
            for i in range(-2, len(component.points) - 2)
        )
        # verify component angles are convex
        assert all(
            Segment.angle(
                component.points[i - 1],
                component.points[i],
                component.points[i + 1],
            ) <= 2 * PI
            for i in range(-2, len(component.points) - 2)
        )
        # verify component has non-zero area
        assert component.area > 0
        # verify that all component edges either:
        # * have a twin that belongs to another component, or
        # * is part of the perimeter of the polygon
        for segment in component.segments:
            if segment.twin in boundary_segments:
                boundary_segments.remove(segment.twin)
            elif segment.twin in internal_segments:
                internal_segments.remove(segment.twin)
            else:
                assert segment not in internal_segments
                internal_segments.add(segment)
    assert not boundary_segments, boundary_segments
    assert not internal_segments, internal_segments


def test_polygon_triangulation_good():
    # type: () -> None
    """Test successful polygon triangulations."""
    for index, points in enumerate(POLYGON_PARTITION_DATASET):
        variants = (
            ('', points),
            (
                'y',
                list(reversed([
                    Point2D.from_matrix(point.matrix.y_reflection) for point in points
                ])),
            ),
            (
                'x',
                list(reversed([
                    Point2D.from_matrix(point.matrix.x_reflection) for point in points
                ])),
            ),
            (
                'xy',
                [
                    Point2D.from_matrix(point.matrix.x_reflection.y_reflection) for point in points
                ],
            ),
        )
        for marker, variant_points in variants:
            print(f'POLYGON {index}{marker}')
            _validate_partition(variant_points, triangulate_polygon(variant_points))


def test_polygon_triangulation_bad():
    # type: () -> None
    shapes = (
        # shrink to a point
        (
            Point2D(-1, 1), Point2D(-1, -1), Point2D(0, 0),
            Point2D(1, -1), Point2D(1, 1), Point2D(0, 0),
        ),
        (
            Point2D(1, 1), Point2D(-1, 1), Point2D(0, 0),
            Point2D(-1, -1), Point2D(1, -1), Point2D(0, 0),
        ),
        # squeezed to a line
        (
            Point2D(-2, 1), Point2D(-2, -1), Point2D(-1, 0), Point2D(1, 0),
            Point2D(2, -1), Point2D(2, 1), Point2D(1, 0),  Point2D(-1, 0),
        ),
        (
            Point2D(1, 2), Point2D(-1, 2), Point2D(0, 1), Point2D(0, -1),
            Point2D(-1, -2), Point2D(1, -2), Point2D(0, -1),  Point2D(0, 1),
        ),
        (
            Point2D(-3, 1), Point2D(-3, -1), Point2D(-2, 0), Point2D(2, 0),
            Point2D(3, -1), Point2D(3, 1), Point2D(1, 0), Point2D(-1, 0),
        ),
    )
    for index, polygon in enumerate(shapes):
        try:
            print(f'POLYGON {index}')
            triangulate_polygon(polygon)
            assert False
        except (ValueError, AssertionError):
            pass


def test_convex_partition():
    # type: () -> None
    """Test successful polygon convex partitions."""
    for index, points in enumerate(POLYGON_PARTITION_DATASET):
        variants = (
            ('', points),
            (
                'y',
                list(reversed([
                    Point2D.from_matrix(point.matrix.y_reflection) for point in points
                ])),
            ),
            (
                'x',
                list(reversed([
                    Point2D.from_matrix(point.matrix.x_reflection) for point in points
                ])),
            ),
            (
                'xy',
                [
                    Point2D.from_matrix(point.matrix.x_reflection.y_reflection) for point in points
                ],
            ),
        )
        for marker, variant_points in variants:
            print(f'POLYGON {index}{marker}')
            _validate_partition(variant_points, convex_partition(variant_points))
