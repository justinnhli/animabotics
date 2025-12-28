"""A scene of objects."""

from collections import defaultdict
from functools import cached_property
from math import ceil, log2
from typing import Iterator, Iterable

from .simplex import Point2D, Vector2D
from .camera import Camera
from .game_object import GameObject

CollisionGroups = frozenset[str]
CollisionGroupPair = tuple[str, str]
CollisionGroupsPair = tuple[frozenset[str], frozenset[str]]


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

    def __init__(self, grid_size, hierarchy):
        # type: (int, HierarchicalHashGrid) -> None
        self.grid_size = grid_size
        self.hierarchy = hierarchy
        self.num_objects = 0
        self.cells = defaultdict(list) # type: dict[Point2D, list[GameObject]]
        self.populated_coords = set() # type: set[Point2D]

    def __len__(self):
        # type: () -> int
        return self.num_objects

    @property
    def objects(self):
        # type: () -> Iterator[GameObject]
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

    def add(self, game_object):
        # type: (GameObject) -> None
        """Add an object to the grid."""
        coord = self.to_cell_coord(game_object.position)
        self.cells[coord].append(game_object)
        self.num_objects += 1
        self.populated_coords.add(coord)

    def remove(self, game_object, position=None):
        # type: (GameObject) -> None
        """Remove an object to the grid."""
        if position is None:
            position = game_object.position
        coord = self.to_cell_coord(position)
        self.cells[coord].remove(game_object)
        self.num_objects -= 1
        if not self.cells[coord]:
            self.populated_coords.remove(coord)

    def get_collisions(self):
        # type: () -> Iterator[tuple[GameObject, GameObject]]
        """Get all collisions."""
        for coord in self.populated_coords:
            cell = self.cells[coord]
            for i, obj1 in enumerate(cell):
                # find collisions in the current cell
                for obj2 in cell[i + 1:]:
                    if not self.hierarchy.has_collision_group_pairs(obj1, obj2):
                        continue
                    if obj1.is_colliding(obj2):
                        yield (obj1, obj2)
                # find collisions in the adjacent cells
                yield from self.get_collisions_with(obj1, half_neighbors=True)

    def get_collisions_with(self, game_object, half_neighbors=False):
        # type: (GameObject, bool) -> Iterator[tuple[GameObject, GameObject]]
        """Get collisions with an object."""
        if self.num_objects == 0:
            return
        coord = self.to_cell_coord(game_object.position)
        if half_neighbors:
            offsets = HashGrid.HALF_OFFSETS
        else:
            offsets = HashGrid.FULL_OFFSETS
        for offset in offsets:
            neighbor_coord = coord + offset
            if neighbor_coord not in self.cells:
                continue
            for obj2 in self.cells[neighbor_coord]:
                if game_object == obj2:
                    continue
                if not self.hierarchy.has_collision_group_pairs(game_object, obj2):
                    continue
                if game_object.is_colliding(obj2):
                    yield (game_object, obj2)


class HierarchicalHashGrid:
    """A hierarchical hash grid."""

    def __init__(self, min_exponent=4, max_exponent=None):
        # type: (int, int) -> None
        """Initialize a hierarchical hash grid."""
        if max_exponent is None:
            max_exponent = min_exponent + 10
        self.min_exponent = min_exponent
        self.max_exponent = max_exponent
        self.grids = [] # type: list[HashGrid]
        for exponent in range(min_exponent):
            self.grids.append(None)
        for exponent in range(min_exponent, max_exponent + 1):
            self.grids.append(HashGrid(2 ** exponent, self))
        self.collision_group_pairs = set() # type: set[CollisionGroupPair]
        self.collision_groups_cache = {} # type: dict[CollisionGroupsPair, tuple[CollisionGroupPair, ...]]

    @cached_property
    def exponent_grids(self):
        # type: () -> list[tuple[int, HashGrid]]
        """Build a list of grids and their exponents."""
        return list(zip(
            range(self.min_exponent, self.max_exponent + 1),
            self.grids[self.min_exponent:],
        ))

    @property
    def all_collisions(self):
        # type: () -> Iterator[tuple[GameObject, GameObject]]
        """Yield all collisions."""
        for exponent, small_grid in self.exponent_grids:
            yield from small_grid.get_collisions()
            for game_object in small_grid.objects:
                for large_grid in self.grids[exponent + 1:]:
                    yield from large_grid.get_collisions_with(game_object)

    @property
    def collisions(self):
        # type: () -> Iterator[tuple[GameObject, GameObject, CollisionGroupPair]]
        """Yield all collisions of registered group pairs."""
        for obj1, obj2 in self.all_collisions:
            for pair in self.get_collision_group_pairs(obj1, obj2):
                yield obj1, obj2, pair
            for pair in self.get_collision_group_pairs(obj2, obj1): # pylint: disable = arguments-out-of-order
                yield obj2, obj1, pair

    def has_collision_group_pairs(self, obj1, obj2):
        # type: (GameObject, GameObject) -> bool
        """Determine if the two objects are part of a collision group pair."""
        return (
            bool(self._get_collision_group_pair(obj1.collision_groups, obj2.collision_groups))
            or bool(self._get_collision_group_pair(obj2.collision_groups, obj1.collision_groups))
        )

    def get_collision_group_pairs(self, obj1, obj2):
        # type: (GameObject, GameObject) -> tuple[CollisionGroupPair, ...]
        """Get the collision group pairs for the two objects."""
        return self._get_collision_group_pair(obj1.collision_groups, obj2.collision_groups)

    def _get_collision_group_pair(self, collision_groups1, collision_groups2):
        # type: (CollisionGroups, CollisionGroups) -> tuple[CollisionGroupPair, ...]
        """Get the collision group pairs for the two collision groups."""
        key = (collision_groups1, collision_groups2)
        if key not in self.collision_groups_cache:
            self.collision_groups_cache[key] = tuple(
                (group1, group2)
                for group1, group2 in self.collision_group_pairs
                if (
                    group1 in collision_groups1
                    and (
                        group2 is None
                        or group2 in collision_groups2
                    )
                )
            )
        return self.collision_groups_cache[key]

    def _get_exponent(self, game_object):
        return min(
            max(ceil(log2(game_object.collision_radius)), self.min_exponent),
            self.max_exponent,
        )

    def add(self, game_object):
        # type: (GameObject) -> None
        """Add an object to the grid."""
        exponent = self._get_exponent(game_object)
        self.grids[exponent].add(game_object)

    def remove(self, game_object, position=None):
        if position is None:
            position = game_object.position
        exponent = self._get_exponent(game_object)
        self.grids[exponent].remove(game_object, position)

    def set_collision_group_pairs(self, collision_pairs):
        # type: (Iterable[CollisionGroupPair]) -> None
        """Set collision group pairs to detect."""
        for group_pair in collision_pairs:
            self.collision_group_pairs.add(group_pair)
