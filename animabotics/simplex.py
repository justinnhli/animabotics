"""2D geometry primitives."""

# mypy: disable-error-code="override"

from dataclasses import dataclass
from functools import cached_property
from math import sqrt, atan2, pi as PI, inf as INF
from typing import TypeVar, Optional, Self

from .matrix import Matrix
from .metaprogramming import CachedMetaclass
from .transform import Transform


@dataclass(frozen=True, order=True)
class PointsMatrix:
    """Abstract class for a sequence of points."""
    matrix: Matrix

    def __abs__(self):
        # type: (int) -> Self
        return type(self).from_matrix(abs(self.matrix))

    def __round__(self, ndigits=0):
        # type: (int) -> Self
        return type(self).from_matrix(round(self.matrix, ndigits))

    def __floor__(self):
        # type: () -> Self
        return type(self).from_matrix(self.matrix.__floor__())

    def __ceil__(self):
        # type: () -> Self
        return type(self).from_matrix(self.matrix.__ceil__())

    def __rmatmul__(self, other):
        # type: (Transform) -> Self
        assert isinstance(other, Transform)
        return type(self).from_matrix(other.matrix @ self.matrix)

    @classmethod
    def from_matrix(cls, matrix):
        # type: (Matrix) -> Self
        """Create the class from a matrix."""
        return cls(matrix=matrix)


class Geometry(PointsMatrix):
    """A shape, broadly defined."""

    def __rmatmul__(self, other):
        # type: (Transform) -> Self
        result = super().__rmatmul__(other)
        # manually update cached_properties is cheaper than recalculating from scratch
        result.area = self.area
        result.centroid = Point2D.from_matrix(other.matrix @ self.centroid.matrix)
        return result

    @cached_property
    def min_x(self):
        # type: () -> float
        """The smallest x-coordinate."""
        return min(self.matrix.rows[0])

    @cached_property
    def min_y(self):
        # type: () -> float
        """The smallest y-coordinate."""
        return min(self.matrix.rows[1])

    @cached_property
    def max_x(self):
        # type: () -> float
        """The largest x-coordinate."""
        return max(self.matrix.rows[0])

    @cached_property
    def max_y(self):
        # type: () -> float
        """The largest y-coordinate."""
        return max(self.matrix.rows[1])

    @cached_property
    def points(self):
        # type: () -> tuple[Point2D, ...]
        """Return the points of the PointsMatrix."""
        return tuple(Point2D(col[0], col[1]) for col in self.matrix.cols)

    @cached_property
    def segments(self):
        # type: () -> tuple[Segment, ...]
        """Return the points of the PointsMatrix."""
        if self.matrix.width < 2:
            return ()
        points = self.points + (self.points[0],)
        return tuple(
            Segment(point1, point2)
            for point1, point2 in zip(points[:-1], points[1:])
        )

    @cached_property
    def area(self):
        # type: () -> float
        """Calculate the area of the PointsMatrix."""
        return 0

    @cached_property
    def centroid(self):
        # type: () -> Point2D
        """Calculate the centroid of the PointsMatrix."""
        raise NotImplementedError()

    @cached_property
    def convex_partitions(self):
        # type: () -> tuple[Geometry, ...]
        """Return a convex partition of the PointsMatrix."""
        return (self,)

    def get_projected_range(self, vector):
        # type: (Vector2D) -> tuple[float, float]
        """Return the min and max values when projected onto a vector."""
        denominator = (vector.x * vector.x + vector.y * vector.y) ** (1/2)
        projected = [
            (vector.x * point.x + vector.y * point.y) / denominator
            for point in self.points
        ]
        return min(projected), max(projected)


class Point2D(Geometry, metaclass=CachedMetaclass):
    """A 2D point."""

    def __init__(self, x=0, y=0, matrix=None):
        # type: (float, float, Matrix) -> None
        if matrix is None:
            matrix = Matrix(((x,), (y,), (0,), (1,)))
        super().__init__(matrix)

    def __neg__(self):
        # type: () -> Point2D
        return Point2D(-self.x, -self.y)

    def __add__(self, other):
        # type: (Vector2D) -> Point2D
        assert isinstance(other, Vector2D)
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        # type: (Point2D) -> Vector2D
        if isinstance(other, Point2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        else:
            # allow other classes to implement the reciprocal dunder method
            return NotImplemented

    def __repr__(self):
        # type: () -> str
        return f'Point2D({self.x}, {self.y})'

    @property
    def x(self):
        # type: () -> float
        """Return the x component of the point."""
        return self.matrix.x

    @property
    def y(self):
        # type: () -> float
        """Return the y component of the point."""
        return self.matrix.y

    @cached_property
    def centroid(self):
        # type: () -> Point2D
        """Calculate the centroid of the PointsMatrix."""
        return self

    def distance(self, other):
        # type: (Point2D) -> float
        """Calculate the distance to another point."""
        return sqrt(self.squared_distance(other))

    def squared_distance(self, other):
        # type: (Point2D) -> float
        """Calculate the squared distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def to_vector(self):
        # type: () -> Vector2D
        """Convert to a Vector2D."""
        return Vector2D(self.x, self.y)


class Vector2D(PointsMatrix, metaclass=CachedMetaclass):
    """A 2D Vector."""

    RT = TypeVar('RT', Point2D, 'Vector2D')

    def __init__(self, x=0, y=0, matrix=None):
        # type: (float, float, Matrix) -> None
        if matrix is None:
            matrix = Matrix(((x,), (y,), (0,), (0,)))
        super().__init__(matrix)

    def __bool__(self):
        # type: () -> bool
        return self.x != 0 or self.y != 0

    def __neg__(self):
        # type: () -> Vector2D
        return Vector2D(-self.x, -self.y)

    def __add__(self, other):
        # type: (Vector2D.RT) -> Vector2D.RT
        return type(other)(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        # type: (Point2D | Vector2D) -> Vector2D
        assert isinstance(other, type(self))
        return Vector2D(self.x - other.x, self.y - other.y)

    def __rsub__(self, other):
        # type: (Vector2D.RT) -> Vector2D.RT
        return type(other)(other.x - self.x, other.y - self.y)

    def __mul__(self, other):
        # type: (float) -> Self
        return type(self)(
            self.x * other,
            self.y * other,
        )

    def __rmul__(self, other):
        # type: (float) -> Self
        return type(self)(
            self.x * other,
            self.y * other,
        )

    def __truediv__(self, other):
        # type: (float) -> Self
        return type(self)(
            self.x / other,
            self.y / other,
        )

    def __floordiv__(self, other):
        # type: (float) -> Self
        return type(self)(
            self.x // other,
            self.y // other,
        )

    def __repr__(self):
        # type: () -> str
        return f'Vector2D({self.x}, {self.y})'

    @cached_property
    def x(self):
        # type: () -> float
        """Return the x component of the vector."""
        return self.matrix.x

    @cached_property
    def y(self):
        # type: () -> float
        """Return the y component of the vector."""
        return self.matrix.y

    @cached_property
    def magnitude(self):
        # type: () -> float
        """The magnitude of the vector."""
        return sqrt(self.squared_magnitude)

    @cached_property
    def squared_magnitude(self):
        # type: () -> float
        """The squared magnitude of the vector."""
        return self.x * self.x + self.y * self.y

    @cached_property
    def normalized(self):
        # type: () -> Vector2D
        """The normalized vector."""
        if self.magnitude == 0:
            return self
        else:
            return self / self.magnitude

    def to_point(self):
        # type: () -> Point2D
        """Convert to a Point2D."""
        return Point2D(self.x, self.y)


class Segment(Geometry, metaclass=CachedMetaclass):
    """A line segment."""

    def __init__(self, point1=None, point2=None, matrix=None):
        # type: (Point2D, Point2D, Matrix) -> None
        if matrix is None:
            assert point1 != point2
            matrix = Matrix((
                (point1.x, point2.x),
                (point1.y, point2.y),
                (0, 0),
                (1, 1),
            ))
        super().__init__(matrix)

    def __repr__(self):
        # type: () -> str
        return f'Segment({self.point1}, {self.point2})'

    @cached_property
    def point1(self):
        # type: () -> Point2D
        """The source point."""
        return Point2D(self.matrix.rows[0][0], self.matrix.rows[1][0])

    @cached_property
    def point2(self):
        # type: () -> Point2D
        """The destination point."""
        return Point2D(self.matrix.rows[0][1], self.matrix.rows[1][1])

    @cached_property
    def min(self):
        # type: () -> Point2D
        """The "smaller" point."""
        if self.point1 <= self.point2:
            return self.point1
        else:
            return self.point2

    @cached_property
    def max(self):
        # type: () -> Point2D
        """The "larger" point."""
        if self.point1 <= self.point2:
            return self.point2
        else:
            return self.point1

    @cached_property
    def centroid(self):
        # type: () -> Point2D
        """Calculate the centroid of the Segment."""
        return Point2D(
            (self.point1.x + self.point2.x) / 2,
            (self.point1.y + self.point2.y) / 2,
        )

    @cached_property
    def twin(self):
        # type: () -> Segment
        """The twin segment."""
        return Segment(self.point2, self.point1)

    @cached_property
    def slope(self):
        # type: () -> float
        """The slope of the segment."""
        denominator = self.point2.x - self.point1.x
        if denominator != 0:
            return (self.point2.y - self.point1.y) / denominator
        elif self.point2.y > self.point1.y:
            return INF
        else:
            return -INF

    @cached_property
    def bearing(self):
        # type: () -> float
        """The bearing of the segment.

        Calculated as the angle counterclockwise angle from the positive x-axis.
        """
        dx = self.point2.x - self.point1.x
        dy = self.point2.y - self.point1.y
        result = atan2(dy, dx)
        if result < 0:
            result += 2 * PI
        return result

    @cached_property
    def length(self):
        # type: () -> float
        """The length of the segment."""
        return self.point2.distance(self.point1)

    @cached_property
    def normal(self):
        # type: () -> Vector2D
        """A normal unit vector to the segment.

        The normal vector will point into the positive rotation direction.
        """
        return Vector2D(
            -(self.point2.y - self.point1.y),
            (self.point2.x - self.point1.x),
        ).normalized

    def is_parallel(self, other):
        # type: (Segment) -> bool
        """Return whether the other segment is parallel."""
        crossmul1 = (self.point2.x - self.point1.x) * (other.point2.y - other.point1.y)
        crossmul2 = (other.point2.x - other.point1.x) * (self.point2.y - self.point1.y)
        return crossmul1 == crossmul2

    def is_colinear(self, other):
        # type: (Segment) -> bool
        """Return whether the other segment is colinear."""
        if not self.is_parallel(other):
            return False
        if self.point1 == other.point1:
            third_segment = Segment(self.point1, other.point2)
        else:
            third_segment = Segment(self.point1, other.point1)
        return self.is_parallel(third_segment)

    def is_kissing(self, other):
        # type: (Segment) -> bool
        """Return whether the other segment intersects at an endpoint."""
        return (
            self.point1 in (other.point1, other.point2)
            or self.point2 in (other.point1, other.point2)
        )

    def is_overlapping(self, other):
        # type: (Segment) -> bool
        """Return whether the other segment overlaps at more than one point."""
        return (
            self.is_colinear(other)
            and (
                self.contains(other.point1, include_end=False)
                or self.contains(other.point2, include_end=False)
                or other.contains(self.point1, include_end=False)
                or other.contains(self.point2, include_end=False)
            )
        )

    def contains(self, point, include_end=True):
        # type: (Point2D, bool) -> bool
        """Return True if the point is on the segment."""
        if include_end:
            return (
                self.min_x <= point.x <= self.max_x
                and self.min_y <= point.y <= self.max_y
            )
        else:
            return (
                (
                    self.point1.x == self.point2.x
                    or self.min_x < point.x < self.max_x
                ) and (
                    self.point1.y == self.point2.y
                    or self.min_y < point.y < self.max_y
                )
            )

    def point_at(self, x):
        # type: (float) -> Point2D
        """Find the point at x."""
        assert self.min_x != self.max_x
        assert self.min_x <= x <= self.max_x, (self.min_x, x, self.max_x)
        if x == self.min_x:
            return self.min
        elif x == self.max_x:
            return self.max
        else:
            numerator = self.point2.y - self.point1.y
            denominator = self.point2.x - self.point1.x
            return Point2D(
                x,
                self.point1.y + (x - self.point1.x) * numerator / denominator,
            )

    def intersect(self, other, include_end=True):
        # type: (Segment, bool) -> Optional[Point2D]
        """Find the intersection with another segment, if any."""
        bounding_box_overlaps = (
            (
                self.min_x <= other.min_x <= self.max_x
                or other.min_x <= self.min_x <= other.max_x
            ) and (
                self.min_y <= other.min_y <= self.max_y
                or other.min_y <= self.min_y <= other.max_y
            )
        )
        if not bounding_box_overlaps:
            return None
        o1 = Segment.orientation(self.point1, other.point1, other.point2)
        o2 = Segment.orientation(self.point2, other.point1, other.point2)
        o3 = Segment.orientation(other.point1, self.point1, self.point2)
        o4 = Segment.orientation(other.point2, self.point1, self.point2)
        # general case: no co-linearity
        if 0 not in (o1, o2, o3, o4):
            if self.is_parallel(other):
                return None
            if self > other:
                return other.intersect(self)
            # calculate y=mx+b for both segments to solve for the intersection
            # avoid Segment.slope for better numeric stability
            diff1x = self.point2.x - self.point1.x
            diff1y = self.point2.y - self.point1.y
            diff2x = other.point2.x - other.point1.x
            diff2y = other.point2.y - other.point1.y
            x = (
                (
                    (other.point1.y - self.point1.y) * (diff1x * diff2x)
                    + (self.point1.x * diff1y * diff2x - other.point1.x * diff1x * diff2y)
                )
                / (diff1y * diff2x - diff2y * diff1x)
            )
            if not (self.min_x <= x <= self.max_x and other.min_x <= x <= other.max_x):
                return None
            # preferentially select the line to calculate the intersection from
            if diff1y == 0:
                result = self.point_at(x)
            elif diff2y == 0:
                result = other.point_at(x)
            elif diff1x != 0:
                result = self.point_at(x)
            else:
                result = other.point_at(x)
            if not (self.min_y <= result.y <= self.max_y and other.min_y <= result.y <= other.max_y):
                return None
            if not include_end and result in (self.point1, self.point2, other.point1, other.point2):
                return None
            else:
                return result
        if not include_end:
            return None
        if o1 == 0 and other.contains(self.point1, include_end=True):
            # p1, q1 and p2 are collinear and p2 lies on segment p1q1
            return self.point1
        elif o2 == 0 and other.contains(self.point2, include_end=True):
            # p1, q1 and q2 are collinear and q2 lies on segment p1q1
            return self.point2
        elif o3 == 0 and self.contains(other.point1, include_end=True):
            # p2, q2 and p1 are collinear and p1 lies on segment p2q2
            return other.point1
        elif o4 == 0 and self.contains(other.point2, include_end=True):
            # p2, q2 and q1 are collinear and q1 lies on segment p2q2
            return other.point2
        else:
            return None

    @staticmethod
    def angle(p1, p2, p3):
        # type: (Point2D, Point2D, Point2D) -> float
        """Determine the counterclockwise angle going from p1 to p2 to p3."""
        result = atan2(p3.y - p2.y, p3.x - p2.x) - atan2(p1.y - p2.y, p1.x - p2.x)
        if result < 0:
            result += 2 * PI
        return result

    @staticmethod
    def orientation(p1, p2, p3):
        # type: (Point2D, Point2D, Point2D) -> int
        """Determine the orientation going from p1 to p2 to p3."""
        val = (
            ((p2.y - p1.y) * (p3.x - p2.x))
            - ((p2.x - p1.x) * (p3.y - p2.y))
        )
        if val < 0: # counterclockwise
            return -1
        elif val > 0: # clockwise
            return 1
        else: # co-linear
            return 0


class Triangle(Geometry, metaclass=CachedMetaclass):
    """A triangle."""

    def __init__(self, point1=None, point2=None, point3=None, matrix=None):
        # type: (Point2D, Point2D, Point2D, Matrix) -> None
        if matrix is None:
            points_list = [point1, point2, point3]
            if Segment.orientation(point1, point2, point3) != -1:
                raise ValueError(f'triangle is not counterclockwise: {points_list}')
            matrix = Matrix((
                (point1.x, point2.x, point3.x),
                (point1.y, point2.y, point3.y),
                (0, 0, 0),
                (1, 1, 1),
            ))
        super().__init__(matrix)

    def __repr__(self):
        # type: () -> str
        return f'Triangle({self.point1}, {self.point2}, {self.point3})'

    @cached_property
    def point1(self):
        # type: () -> Point2D
        """Return the "first" point of the triangle."""
        return Point2D(self.matrix.rows[0][0], self.matrix.rows[1][0])

    @cached_property
    def point2(self):
        # type: () -> Point2D
        """Return the "second" point of the triangle."""
        return Point2D(self.matrix.rows[0][1], self.matrix.rows[1][1])

    @cached_property
    def point3(self):
        # type: () -> Point2D
        """Return the "third" point of the triangle."""
        return Point2D(self.matrix.rows[0][2], self.matrix.rows[1][2])

    @cached_property
    def area(self):
        # type: () -> float
        """The area of the Triangle."""
        point1, point2, point3 = self.points
        return abs(
            point1.x * (point2.y - point3.y)
            + point2.x * (point3.y - point1.y)
            + point3.x * (point1.y - point2.y)
        ) / 2

    @cached_property
    def centroid(self):
        # type: () -> Point2D
        """The centroid of the Triangle."""
        return Point2D(
            (self.point1.x + self.point2.x + self.point3.x) / 3,
            (self.point1.y + self.point2.y + self.point3.y) / 3,
        )

    @staticmethod
    def from_segments(segment1, segment2, segment3):
        # type: (Segment, Segment, Segment) -> Triangle
        """Create a Triangle from segments."""
        return Triangle(
            segment1.point1,
            segment2.point1,
            segment3.point1,
        )
