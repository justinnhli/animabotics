"""Tests for data_structures/hash_grid.py."""

from collections import defaultdict
from random import Random

from animabotics.transformable import Transformable
from animabotics.simplex import Point2D
from animabotics.data_structures import HashGrid


class TransformablePoint(Transformable):

    def __init__(self, position):
        super().__init__(position=position)

    def __lt__(self, other):
        assert isinstance(other, TransformablePoint)
        return self.position < other.position

    def __str__(self):
        return str(self.position)

    def __repr__(self):
        return str(self)


def test_hash_grid_nearest_neighbor():
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
    # calculate the ground truth
    groundtruth = defaultdict(set) # type: dict[float, set[TransformablePoint]]
    for point in points:
        groundtruth[(point.position - target.position).magnitude].add(point)
    # get points in sorted order
    expect = set()
    for distance, points in sorted(groundtruth.items()):
        expect |= points
        actual = hash_grid.nearest_neighbors(
            target.position,
            k=len(expect),
        )
        assert set(actual) == expect
