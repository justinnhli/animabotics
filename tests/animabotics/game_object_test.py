"""Tests for game_object.py."""

from math import pi as PI

from animabotics import Collidable
from animabotics import Point2D, Polygon, Geometry


class CollidingGameObject(Collidable):
    """A dummy game object to hold a static geometry."""

    def __init__(self, physics_geometry):
        # type: (Geometry) -> None
        """Initialize the CollidingGameObject."""
        super().__init__(physics_geometry=physics_geometry)


def colliding_and_commutes(obj1, obj2):
    # type: (CollidingGameObject, CollidingGameObject) -> bool
    """Check that two objects are colliding from both directions."""
    result = obj1.is_colliding(obj2)
    assert result == obj2.is_colliding(obj1)
    return result


def test_collision():
    # type: () -> None
    """Test collisions."""
    # rectangles
    obj1 = CollidingGameObject(Polygon.rectangle(100, 100))
    obj2 = CollidingGameObject(Polygon.rectangle(100, 100))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(150, 0))
    assert not colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(75, 75))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(100, 0))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(112.5, 0))
    assert not colliding_and_commutes(obj1, obj2)
    obj2.rotate_by(0.25 * PI)
    assert colliding_and_commutes(obj1, obj2)
    obj2.rotate_by(0.25 * PI)
    assert not colliding_and_commutes(obj1, obj2)
    # hexagons
    obj1 = CollidingGameObject(Polygon.ellipse(100, 100, 6))
    obj2 = CollidingGameObject(Polygon.ellipse(100, 100, 6))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(150, 150))
    assert not colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(150, 0))
    assert colliding_and_commutes(obj1, obj2)
    # taco
    obj1 = CollidingGameObject(Polygon.rectangle(100, 100))
    obj2 = CollidingGameObject(Polygon((
        Point2D(-100, 100),
        Point2D(-100, -100),
        Point2D(100, -100),
        Point2D(100, 100),
        Point2D(75, 100),
        Point2D(75, -75),
        Point2D(-75, -75),
        Point2D(-75, 100),
    )))
    assert not colliding_and_commutes(obj1, obj2)
    # sushi
    obj1 = CollidingGameObject(Polygon.rectangle(100, 100))
    obj2 = CollidingGameObject(Polygon((
        Point2D(-100, 100),
        Point2D(-100, -100),
        Point2D(100, -100),
        Point2D(100, 100),
        Point2D(-100, 100),
        Point2D(-75, 75),
        Point2D(75, 75),
        Point2D(75, -75),
        Point2D(-75, -75),
        Point2D(-75, 75),
    )))
    assert not colliding_and_commutes(obj1, obj2)
