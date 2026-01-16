"""A 2D camera."""

from functools import lru_cache

from .animation import Sprite, Shape
from .canvas import Canvas
from .color import Color
from .matrix import Matrix
from .polygon import Polygon
from .simplex import Geometry, Point2D
from .transform import Transform
from .transformable import Collidable


@lru_cache
def projection_matrix(width, height, x, y, rotation, zoom): # pylint: disable = too-many-positional-arguments
    # type: (int, int, float, float, float, float) -> Matrix
    """Create the projection matrix."""
    return (
        Transform(width // 2, height // 2).matrix
        @ Transform(x, y, rotation, 1 / zoom).matrix.inverse.y_reflection
    )


class Camera(Collidable):
    """A 2D camera."""

    def __init__(self, canvas, zoom_level=0):
        # type: (Canvas, int) -> None
        """Initialize the Camera."""
        super().__init__()
        self.canvas = canvas
        self._zoom_level = zoom_level
        self.origin_transform = Transform(
            self.canvas.width // 2,
            self.canvas.height // 2,
        )
        self._set_collision_geometry()

    @property
    def zoom(self):
        # type: () -> float
        """Get the zoom factor."""
        return 1.25 ** self.zoom_level

    @property
    def zoom_level(self):
        # type: () -> int
        """Get the zoom level."""
        return self._zoom_level

    @zoom_level.setter
    def zoom_level(self, value):
        # type: (int) -> None
        """Set the zoom level."""
        self._zoom_level = value
        self._set_collision_geometry()

    @property
    def projection_matrix(self):
        # type: () -> Matrix
        """Create the projection matrix.

        Because this project involves flipping the y-axis, it cannot be
        represented as a Transform, and the underlying matrix must be used
        instead. The creation of the matrix is put in a separate function to
        take advantage of caching."""
        return projection_matrix(
            self.canvas.width,
            self.canvas.height,
            self.position.x,
            self.position.y,
            self.rotation,
            self.zoom,
        )

    @property
    def inverse_projection_matrix(self):
        # type: () -> Matrix
        """Create the inverse of the projection matrix."""
        return self.projection_matrix.inverse

    def _set_collision_geometry(self):
        # type: () -> None
        corner = Point2D.from_matrix(
            self.projection_matrix.inverse @ Point2D(0, 0).matrix
        )
        min_x = corner.x
        max_y = corner.y
        corner = Point2D.from_matrix(
            self.projection_matrix.inverse
            @ Point2D(self.canvas.width, self.canvas.height).matrix
        )
        max_x = corner.x
        min_y = corner.y
        self.collision_geometry = Polygon((
            Point2D(min_x, max_y),
            Point2D(min_x, min_y),
            Point2D(max_x, min_y),
            Point2D(max_x, max_y),
        ))

    def _project(self, matrix):
        # type: (Matrix) -> Matrix
        """Project to screen coordinates."""
        return self.projection_matrix @ matrix

    def draw_sprite(self, sprite):
        # type: (Sprite) -> None
        """Draw a Sprite."""
        for shape in sprite:
            self.draw_shape(shape)

    def draw_shape(self, shape):
        # type: (Shape) -> None
        """Draw a Shape."""
        self.draw_geometry(
            geometry=shape.polygon,
            fill_color=shape.fill_color,
            line_color=shape.line_color,
        )

    def draw_geometry(self, geometry, fill_color=None, line_color=None):
        # type: (Geometry, Color, Color) -> None
        """Draw a Geometry."""
        matrix = self._project(geometry.matrix)
        if matrix.width == 1:
            self.canvas.draw_pixel(
                (matrix[0][0], matrix[1][0]),
                fill_color=fill_color,
            )
        elif matrix.width == 2:
            self.canvas.draw_line(
                (matrix[0][0], matrix[1][0]),
                (matrix[0][1], matrix[1][1]),
                line_color=line_color,
            )
        else:
            self.canvas.draw_poly(
                tuple(
                    (matrix[0][i], matrix[1][i])
                    for i in range(matrix.width)
                ),
                fill_color=fill_color,
                line_color=line_color,
            )
