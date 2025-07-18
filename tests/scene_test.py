"""Tests for scene.py."""

from collections import Counter

from animabotics.game_object import GameObject
from animabotics.polygon import Polygon
from animabotics.scene import HierarchicalHashGrid
from animabotics.simplex import Point2D


def test_hierarchical_hash_grid():
    # type: () -> None
    """Test HierarchicalHashGrid."""
    # initialize the HierarchicalHashGrid
    hhg = HierarchicalHashGrid()
    hhg.set_collision_group_pairs([('test', 'test')])
    # create and add the objects
    objects = []
    data = [
        (60, 110, 20, 5),
        (60, 120, 20, 5),
        (60, 65, 20, 5),
        (60, 170, 35, 6),
    ]
    for x, y, radius, _ in data:
        obj = GameObject()
        obj.collision_geometry = Polygon.ellipse(radius, radius)
        obj.move_to(Point2D(x, y))
        obj.collision_radius = radius
        obj.add_to_collision_group('test')
        hhg.add(obj)
        objects.append(obj)
    # test that the objects are in the appropriate grid
    for obj, (*_, exponent) in zip(objects, data):
        grid = hhg.grids[exponent]
        assert grid
        grid_objects = []
        for coord in grid.populated_coords:
            for grid_object in grid.cells[coord]:
                grid_objects.append(grid_object)
        assert obj in grid_objects
    collisions = list(hhg.collisions)
    assert len(collisions) == 4
    colliding_objects = Counter() # type: Counter[GameObject]
    for obj1, obj2, _ in collisions:
        colliding_objects.update([obj1])
        colliding_objects.update([obj2])
    assert len(colliding_objects) == 3
    # divide by two since each pair is added twice
    assert colliding_objects[objects[0]] // 2 == 1
    assert colliding_objects[objects[1]] // 2 == 2
    assert colliding_objects[objects[3]] // 2 == 1
