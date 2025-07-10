"""Tests for algorithms.py."""

from collections.abc import Sequence
from itertools import product
from typing import Iterator

from dumpy.algorithms import bentley_ottmann, triangulate_polygon
from dumpy.simplex import Point2D, Segment


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


def _test_triangulation(points):
    # type: (Sequence[Point2D]) -> None
    triangles = triangulate_polygon(points)
    # initialize the segments with the _clockwise_ perimeter
    # which will be "canceled out" during the verification
    segments = set(
        Segment(points[i], points[i - 1])
        for i in range(len(points))
    )
    # verify each triangle
    for triangle in triangles:
        # verify triangle is counter-clockwise
        assert all(
            Segment.orientation(
                triangle.points[i - 1],
                triangle.points[i],
                triangle.points[i + 1],
            ) == -1
            for i in range(-1, 2)
        )
        # verify triangle has non-zero area
        assert triangle.area > 0
        # verify that all triangle edges either:
        # * have a twin that belongs to another triangle, or
        # * is part of the perimeter of the polygon
        for segment in triangle.segments:
            assert segment not in segments, segment
            if segment.twin in segments:
                segments.remove(segment.twin)
            else:
                segments.add(segment)
    assert not segments, segments


def test_monotone_triangulation():
    # type: () -> None
    """Test monotone triangulation."""
    shapes = (
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
            Point2D(-1, 1), Point2D(-0, 0), Point2D(-1, -1),
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
    )
    for index, polygon in enumerate(shapes):
        print(f'POLYGON {index}')
        _test_triangulation(polygon)
        print(f'POLYGON {index}y')
        _test_triangulation(list(reversed([
            Point2D.from_matrix(point.matrix.y_reflection) for point in polygon
        ])))
        print(f'POLYGON {index}x')
        _test_triangulation(list(reversed([
            Point2D.from_matrix(point.matrix.x_reflection) for point in polygon
        ])))
        print(f'POLYGON {index}xy')
        _test_triangulation([
            Point2D.from_matrix(point.matrix.x_reflection.y_reflection) for point in polygon
        ])
