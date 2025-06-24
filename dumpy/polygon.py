"""The Polygon class."""

from functools import cached_property
from math import sin, cos, pi as PI
from typing import Sequence

from .algorithms import monotone_triangulation
from .matrix import Matrix
from .metaprogramming import CachedMetaclass
from .simplex import Geometry, Point2D, Vector2D, Triangle


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
        self._triangle_index = [] # type: list[tuple[int, int, int]]

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
        # type: () -> tuple[Geometry, ...]
        """Return a convex partition of the polygon."""
        if not self._triangle_index:
            triangles = tuple(monotone_triangulation(self.points))
            points_map = {point: index for index, point in enumerate(self.points)}
            for triangle in triangles:
                self._triangle_index.append((
                    points_map[triangle.point1],
                    points_map[triangle.point2],
                    points_map[triangle.point3],
                ))
        else:
            triangles = tuple(
                Triangle(self.points[i], self.points[j], self.points[k])
                for i, j, k in self._triangle_index
            )
        return triangles

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
        return Polygon(points)

    @staticmethod
    def ellipse(width_radius, height_radius, num_points=40):
        # type: (float, float, int) -> Polygon
        """Create a ellipse."""
        step = PI / (num_points / 2)
        return Polygon(tuple(
            Point2D(width_radius * cos(i * step), height_radius * sin(i * step))
            for i in range(num_points)
        ))
