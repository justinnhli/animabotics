"""A Matrix class."""

# pylint: disable = too-many-lines

from dataclasses import dataclass
from functools import lru_cache as cache, cached_property
from math import floor, ceil, sqrt, sin, cos

from .metaprogramming import CachedMetaclass


EPSILON = 0.00001


@dataclass(frozen=True, order=True)
class Matrix(metaclass=CachedMetaclass): # pylint: disable = too-many-public-methods
    """A matrix."""
    rows: tuple[tuple[float, ...], ...]

    def __getitem__(self, index):
        # type: (int) -> tuple[float, ...]
        return self.rows[index]

    def __round__(self, ndigits=None):
        # type: (int) -> Matrix
        return Matrix(tuple(
            tuple(round(val, ndigits) for val in row)
            for row in self.rows
        ))

    def __floor__(self):
        # type: () -> Matrix
        return Matrix(tuple(
            tuple(floor(val) for val in row)
            for row in self.rows
        ))

    def __ceil__(self):
        # type: () -> Matrix
        return Matrix(tuple(
            tuple(ceil(val) for val in row)
            for row in self.rows
        ))

    def __neg__(self):
        # type: () -> Matrix
        return Matrix(tuple(
            tuple(-val for val in row)
            for row in self.rows
        ))

    def __add__(self, other):
        # type: (Matrix) -> Matrix
        return Matrix(tuple(
            tuple(val1 + val2 for val1, val2 in zip(row1, row2))
            for row1, row2 in zip(self.rows, other.rows)
        ))

    def __sub__(self, other):
        # type: (Matrix) -> Matrix
        return Matrix(tuple(
            tuple(val1 - val2 for val1, val2 in zip(row1, row2))
            for row1, row2 in zip(self.rows, other.rows)
        ))

    def __mul__(self, other):
        # type: (float) -> Matrix
        return Matrix(tuple(
            tuple(val * other for val in row)
            for row in self.rows
        ))

    def __rmul__(self, other):
        # type: (float) -> Matrix
        return self * other

    def __truediv__(self, other):
        # type: (float) -> Matrix
        return Matrix(tuple(
            tuple(val / other for val in row)
            for row in self.rows
        ))

    def __floordiv__(self, other):
        # type: (float) -> Matrix
        return Matrix(tuple(
            tuple(val // other for val in row)
            for row in self.rows
        ))

    def __matmul__(self, other):
        # type: (Matrix) -> Matrix
        assert self.width == other.height, f'({self.height}, {self.width}) x ({other.height}, {other.width})'
        result = []
        for r in range(self.height):
            row = self.rows[r]
            result_row = []
            for c in range(other.width):
                col = other.cols[c]
                result_row.append(sum(a * b for a, b in zip(row, col)))
            result.append(tuple(result_row))
        return Matrix(tuple(result))

    @cached_property
    def height(self):
        # type: () -> int
        """Return the height of the matrix."""
        return len(self.rows)

    @cached_property
    def width(self):
        # type: () -> int
        """Return the width of the matrix."""
        return len(self.rows[0])

    @cached_property
    def cols(self):
        # type: () -> tuple[tuple[float, ...], ...]
        """Get the columns of the matrix."""
        return tuple(
            tuple(self.rows[r][c] for r in range(self.height))
            for c in range(self.width)
        )

    @cached_property
    def x(self):
        # type: () -> float
        """Return the x value of a 4-tuple."""
        return self.rows[0][0]

    @cached_property
    def y(self):
        # type: () -> float
        """Return the y value of a 4-tuple."""
        return self.rows[1][0]

    @cached_property
    def z(self):
        # type: () -> float
        """Return the z value of a 4-tuple."""
        return self.rows[2][0]

    @cached_property
    def w(self): # pylint: disable = invalid-name
        # type: () -> float
        """Return the w value of a 4-tuple."""
        return self.rows[3][0]

    @cached_property
    def magnitude(self):
        # type: () -> float
        """Return the magnitude of a 4-tuple."""
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    @cached_property
    def normalized(self):
        # type: () -> Matrix
        """Normalize a graphics point/vector."""
        magnitude = self.magnitude
        return Matrix((
            (self.x / magnitude,),
            (self.y / magnitude,),
            (self.z / magnitude,),
            (self.w,),
        ))

    @cached_property
    def transpose(self):
        # type: () -> Matrix
        """Transpose the matrix."""
        return Matrix(self.cols)

    @cached_property
    def x_reflection(self):
        # type: () -> Matrix
        """Reflect across the x-axis."""
        return Matrix((
            (-1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        )) @ self

    @cached_property
    def y_reflection(self):
        # type: () -> Matrix
        """Reflect across the y-axis."""
        return Matrix((
            (1, 0, 0, 0),
            (0, -1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        )) @ self

    @cached_property
    def z_reflection(self):
        # type: () -> Matrix
        """Reflect across the z-axis."""
        return Matrix((
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, -1, 0),
            (0, 0, 0, 1),
        )) @ self

    @cached_property
    def determinant(self):
        # type: () -> float
        """Calculate the determinant."""
        if self.height == 2 and self.width == 2:
            return self.rows[0][0] * self.rows[1][1] - self.rows[0][1] * self.rows[1][0]
        else:
            return sum(self.rows[0][i] * self.cofactor(0, i) for i in range(self.width))

    @cached_property
    def invertible(self):
        # type: () -> bool
        """Return True if the matrix is invertible."""
        return self.determinant != 0

    @cached_property
    def inverse(self):
        # type: () -> Matrix
        """Inverse the matrix."""
        result = []
        for r in range(self.height):
            result.append(tuple(self.cofactor(r, c) for c in range(self.width)))
        return Matrix(tuple(result)).transpose / self.determinant

    def dot(self, other):
        # type: (Matrix) -> float
        """Take the dot product with another 4-tuple."""
        return (other.transpose @ self).rows[0][0]

    def cross(self, other):
        # type: (Matrix) -> Matrix
        """Take the cross product with another matrix."""
        return Matrix((
            (self.y * other.z - self.z * other.y,),
            (self.z * other.x - self.x * other.z,),
            (self.x * other.y - self.y * other.x,),
            (0,),
        ))

    def submatrix(self, dr, dc): # pylint: disable = invalid-name
        # type: (int, int) -> Matrix
        """Slice out a submatrix."""
        return Matrix(tuple(
            row[:dc] + row[dc + 1:]
            for r, row in enumerate(self.rows)
            if r != dr
        ))

    def minor(self, dr, dc): # pylint: disable = invalid-name
        # type: (int, int) -> float
        """Calculate a minor."""
        return self.submatrix(dr, dc).determinant

    def cofactor(self, dr, dc): # pylint: disable = invalid-name
        # type: (int, int) -> float
        """Calculate a cofactor."""
        if (dr + dc) % 2 == 0:
            return self.minor(dr, dc)
        else:
            return -self.minor(dr, dc) # pylint: disable = invalid-unary-operand-type

    def translate(self, x, y, z):
        # type: (float, float, float) -> Matrix
        """Translate the matrix."""
        return Matrix((
            (1, 0, 0, x),
            (0, 1, 0, y),
            (0, 0, 1, z),
            (0, 0, 0, 1),
        )) @ self

    def scale(self, x, y, z):
        # type: (float, float, float) -> Matrix
        """Scale the matrix."""
        return Matrix((
            (x, 0, 0, 0),
            (0, y, 0, 0),
            (0, 0, z, 0),
            (0, 0, 0, 1),
        )) @ self

    def rotate_x(self, r):
        # type: (float) -> Matrix
        """Rotate the matrix along the x-axis."""
        return Matrix((
            (1, 0, 0, 0),
            (0, cos(r), -sin(r), 0),
            (0, sin(r), cos(r), 0),
            (0, 0, 0, 1),
        )) @ self

    def rotate_y(self, r):
        # type: (float) -> Matrix
        """Rotate the matrix along the y-axis."""
        return Matrix((
            (cos(r), 0, sin(r), 0),
            (0, 1, 0, 0),
            (-sin(r), 0, cos(r), 0),
            (0, 0, 0, 1),
        )) @ self

    def rotate_z(self, r):
        # type: (float) -> Matrix
        """Rotate the matrix along the z-axis."""
        return Matrix((
            (cos(r), -sin(r), 0, 0),
            (sin(r), cos(r), 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        )) @ self

    def shear(self, x_y, x_z, y_x, y_z, z_x, z_y):
        # pylint: disable = too-many-positional-arguments
        # type: (float, float, float, float, float, float) -> Matrix
        """Shear the matrix."""
        return Matrix((
            (1, x_y, x_z, 0),
            (y_x, 1, y_z, 0),
            (z_x, z_y, 1, 0),
            (0, 0, 0, 1),
        )) @ self


@cache
def identity(size=4):
    # type: (int) -> Matrix
    """Create an identity matrix."""
    return Matrix(tuple(
        (i * (0.0,)) + (1.0,) + (size - i - 1) * (0.0,)
        for i in range(size)
    ))
