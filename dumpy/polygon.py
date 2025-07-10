"""The Polygon class."""

from functools import cached_property
from math import sin, cos, pi as PI
from typing import Self, Sequence

from .algorithms import triangulate_polygon
from .matrix import Matrix
from .metaprogramming import CachedMetaclass
from .simplex import Geometry, Point2D, Vector2D, Segment, Triangle
from .transform import Transform


class ConvexPolygon(Geometry, metaclass=CachedMetaclass):
    """A convex polygon."""

    def __init__(self, points=None, matrix=None):
        # type: (Sequence[Point2D], Matrix) -> None
        if matrix is None:
            matrix = Matrix(tuple(
                (point.x, point.y, 0, 1)
                for point in points
            )).transpose
        super().__init__(matrix)

    @cached_property
    def area(self):
        # type: () -> float
        """Calculate the area of the polygon.

        Uses the shoelace formula.
        """
        result = 0 # type: float
        for i, point2 in enumerate(self.points):
            point1 = self.points[i - 1]
            point2 = self.points[i]
            result += point1.x * point2.y - point2.x * point1.y
        return result / 2

    @cached_property
    def centroid(self):
        # type: () -> Point2D
        """Calculate the centroid of the polygon.

        Uses the shoelace formula.
        """
        result = Vector2D()
        for i, point2 in enumerate(self.points):
            point1 = self.points[i - 1]
            point2 = self.points[i]
            factor = point1.x * point2.y - point2.x * point1.y
            result += Vector2D(
                (point1.x + point2.x) * factor,
                (point1.y + point2.y) * factor,
            )
        return (result / (6 * self.area)).to_point()


class Polygon(Geometry, metaclass=CachedMetaclass):
    """A (potentially non-convex) polygon."""

    def __init__(self, points=None, matrix=None):
        # type: (Sequence[Point2D], Matrix) -> None
        if matrix is None:
            matrix = Matrix(tuple(
                (point.x, point.y, 0, 1)
                for point in points
            )).transpose
        super().__init__(matrix)
        self._convex_index = tuple() # type: tuple[tuple[int, ...], ...]

    def __rmatmul__(self, other):
        # type: (Transform) -> Self
        result = super().__rmatmul__(other)
        result._convex_index = self._convex_index
        return result

    @cached_property
    def area(self):
        # type: () -> float
        """Calculate the area of the polygon."""
        return sum(partition.area for partition in self.convex_partitions)

    @cached_property
    def centroid(self):
        # type: () -> Point2D
        """Calculate the centroid of the polygon."""
        total_area = 0 # type: float
        centroid = Vector2D()
        for partition in self.convex_partitions:
            total_area += partition.area
            centroid += partition.area * partition.centroid.to_vector()
        return (centroid / total_area).to_point()

    @cached_property
    def convex_partitions(self):
        # type: () -> tuple[ConvexPolygon, ...]
        """Return a convex partition of the polygon."""
        if not self._convex_index:
            self._convex_index = triangulate_polygon(self.points)
        return tuple(
            ConvexPolygon(tuple(self.points[i] for i in indices))
            for indices in self._convex_index
        )

    def union(self, *polygons):
        # type: (*Polygon) -> Polygon
        """Create the union of polygons."""
        raise NotImplementedError()

    def intersection(self, *polygons):
        # type: (*Polygon) -> Polygon
        """Create the intersection of polygons."""
        raise NotImplementedError()

    def difference(self, *polygons):
        # type: (*Polygon) -> Polygon
        """Create the difference of polygons."""
        raise NotImplementedError()

    @staticmethod
    def rectangle(width, height):
        # type: (float, float) -> Polygon
        """Create a rectangle."""
        half_width = width / 2
        half_height = height / 2
        points = (
            Point2D(-half_width, half_height),
            Point2D(-half_width, -half_height),
            Point2D(half_width, -half_height),
            Point2D(half_width, half_height),
        )
        result = Polygon(points)
        result._convex_index = ( # pylint: disable = protected-access
            (0, 1, 3),
            (1, 2, 3),
        )
        return result

    @staticmethod
    def ellipse(width_radius, height_radius, num_points=40):
        # type: (float, float, int) -> Polygon
        """Create a ellipse."""
        step = PI / (num_points / 2)
        result = Polygon(tuple(
            Point2D(width_radius * cos(i * step), height_radius * sin(i * step))
            for i in range(num_points)
        ))
        result._convex_index = (tuple(range(num_points)),) # pylint: disable = protected-access
        return result


def make_geometry(points):
    # type: (Sequence[Point2D]) -> Geometry
    """Create the appropriate Geometry."""
    if len(points) == 1:
        return points[0]
    elif len(points) == 2:
        return Segment(points[0], points[1])
    elif len(points) == 2:
        return Triangle(points[0], points[1], points[2])
    elif len(points) == 3:
        return Polygon(points)
    else:
        assert False
