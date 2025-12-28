"""A spatial hashing container."""

from collections import defaultdict
from typing import Any, Iterator

from ..simplex import Point2D, Vector2D
from ..transformable import Transformable


class HashGrid:
    """A hash grid."""

    HALF_OFFSETS = [
        Vector2D(-1, -1),
        Vector2D(-1, 0),
        Vector2D(-1, 1),
        Vector2D(0, -1),
    ]
    FULL_OFFSETS = [
        *HALF_OFFSETS,
        Vector2D(0, 0),
        Vector2D(0, 1),
        Vector2D(1, -1),
        Vector2D(1, 0),
        Vector2D(1, 1),
    ]

    def __init__(self, grid_size):
        # type: (int) -> None
        self.grid_size = grid_size
        self.num_objects = 0
        self.cells = defaultdict(list) # type: dict[Point2D, list[Transformable]]

    def __len__(self):
        # type: () -> int
        return self.num_objects

    @property
    def objects(self):
        # type: () -> Iterator[Any]
        """Get all objects in the grid."""
        for cell in self.cells.values():
            yield from cell

    def to_cell_coord(self, position):
        # type: (Point2D) -> Point2D
        """Calculate the cell for an object."""
        return Point2D(
            position.x // self.grid_size,
            position.y // self.grid_size,
        )

    def add(self, obj):
        # type: (Any) -> None
        """Add an object to the grid."""
        coord = self.to_cell_coord(obj.position)
        self.cells[coord].append(obj)
        self.num_objects += 1

    def remove(self, obj, position=None):
        # type: (Any, Point2D) -> None
        """Remove an object to the grid."""
        if position is None:
            position = obj.position
        coord = self.to_cell_coord(position)
        self.cells[coord].remove(obj)
        self.num_objects -= 1
        if not self.cells[coord]:
            del self.cells[coord]
