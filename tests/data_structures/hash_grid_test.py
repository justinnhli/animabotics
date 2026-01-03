"""Tests for data_structures/hash_grid.py."""

from collections import defaultdict
from random import Random

from animabotics.transformable import Transformable
from animabotics.simplex import Point2D
from animabotics.data_structures import HashGrid


class TransformablePoint(Transformable):
    """A wrapper around Point2D to make it Transformable."""

    def __init__(self, position):
        # type: (Point2D) -> None
        super().__init__(position=position)

    def __lt__(self, other):
        # type: (TransformablePoint) -> bool
        assert isinstance(other, TransformablePoint)
        return self.position < other.position

    def __str__(self):
        # type: () -> str
        return str(self.position)

    def __repr__(self):
        # type: () -> str
        return str(self)


def test_hash_grid_nearest_neighbor():
    # type: () -> None
    """Test HashGrid."""
    # set test constants
    num_points = 2000
    grid_size = 50
    target = TransformablePoint(Point2D(41, 60))
    # create random number generator
    rng = Random(8675309)
    # populate hash grid
    hash_grid = HashGrid(grid_size)
    points = []
    for _ in range(num_points):
        point = TransformablePoint(Point2D(
            rng.randrange(-500, 501),
            rng.randrange(-500, 501),
        ))
        points.append(point)
        hash_grid.add(point)
    # test hash grid size
    assert len(hash_grid) == num_points
    # general check that points are in increasing distance from target
    prev_distance = 0.0
    for point in hash_grid.nearest_neighbors(target.position, num_points):
        distance = (point.position - target.position).magnitude
        assert distance >= prev_distance
        prev_distance = distance
    # calculate the ground truth; use sets to avoid non-determinism for equidistant points
    groundtruth = defaultdict(set) # type: dict[float, set[TransformablePoint]]
    for point in points:
        groundtruth[(point.position - target.position).magnitude].add(point)
    # remove the max to avoid the generator finishing
    groundtruth.pop(max(groundtruth))
    # get points in sorted order
    generator = hash_grid.nearest_neighbors(target.position, num_points - 1)
    for distance, expect in sorted(groundtruth.items()):
        actual = set()
        for _ in range(len(expect)):
            actual.add(next(generator))
        assert actual == expect
