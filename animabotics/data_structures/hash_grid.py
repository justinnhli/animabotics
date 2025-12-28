"""A spatial hashing container."""

from collections import defaultdict
from itertools import chain, groupby
from typing import Iterator

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
        # type: () -> Iterator[Transformable]
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
        # type: (Transformable) -> None
        """Add an object to the grid."""
        coord = self.to_cell_coord(obj.position)
        self.cells[coord].append(obj)
        self.num_objects += 1

    def remove(self, obj, position=None):
        # type: (Transformable, Point2D) -> None
        """Remove an object to the grid."""
        if position is None:
            position = obj.position
        coord = self.to_cell_coord(position)
        self.cells[coord].remove(obj)
        self.num_objects -= 1
        if not self.cells[coord]:
            del self.cells[coord]

    def nearest_neighbors(self, target, k=1):
        # type: (Point2D, int) -> Iterator[Transformable]
        """Get the k nearest objects to a target Point2D."""
        # special case if all objects are "nearest"
        if len(self) <= k:
            yield from sorted(
                chain(*self.cells.values()),
                key=(lambda obj: (obj.position - target).magnitude),
            )
            return
        # initialize variables
        target_coord = self.to_cell_coord(target)
        coord_dists = groupby(
            sorted(
                (self._min_squared_distance(coord - target_coord), coord)
                for coord in self.cells
            ),
            key=(lambda pair: pair[0]),
        )
        num_results = 0
        holding_area = [] # type: list[tuple[float, Transformable]]
        for min_dist, coords in coord_dists:
            for _, coord in coords:
                holding_area.extend(
                    ((obj.position - target).squared_magnitude, obj)
                    for obj in self.cells[coord]
                )
            holding_area = sorted(holding_area)
            while num_results < k and holding_area and holding_area[0][0] < min_dist:
                yield holding_area.pop(0)[-1]
                num_results += 1
        while num_results < k and holding_area:
            yield holding_area.pop(0)[-1]
            num_results += 1

    def _min_squared_distance(self, coord_diff):
        # type: (Vector2D) -> float
        coord_diff = abs(coord_diff)
        if coord_diff.x == 0 and coord_diff.y == 0:
            return 0
        elif coord_diff.x == 0 or coord_diff.y == 0:
            diff = max(coord_diff.x, coord_diff.y)
            return ((diff - 1) * self.grid_size) ** 2
        else:
            return (
                ((coord_diff.x - 1) * self.grid_size) ** 2
                + ((coord_diff.y - 1) * self.grid_size) ** 2
            )
