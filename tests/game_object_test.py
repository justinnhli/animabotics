"""Tests for game_object.py."""

from animabotics import Point2D, Polygon
from animabotics.basic_window import DummyGameObject


def colliding_and_commutes(obj1, obj2):
    # type: (DummyGameObject, DummyGameObject) -> bool
    result = obj1.is_colliding(obj2)
    assert result == obj2.is_colliding(obj1)
    return result


def test_collision():
    # type: () -> None
    # rectangles
    obj1 = DummyGameObject(Polygon.rectangle(100, 100))
    obj2 = DummyGameObject(Polygon.rectangle(100, 100))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(150, 0))
    assert not colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(75, 75))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(100, 0))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(112.5, 0))
    assert not colliding_and_commutes(obj1, obj2)
    obj2.rotate_by(0.25)
    assert colliding_and_commutes(obj1, obj2)
    obj2.rotate_by(0.25)
    assert not colliding_and_commutes(obj1, obj2)
    # hexagons
    obj1 = DummyGameObject(Polygon.ellipse(100, 100, 6))
    obj2 = DummyGameObject(Polygon.ellipse(100, 100, 6))
    assert colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(150, 150))
    assert not colliding_and_commutes(obj1, obj2)
    obj2.move_to(Point2D(150, 0))
    assert colliding_and_commutes(obj1, obj2)
    # taco
    obj1 = DummyGameObject(Polygon.rectangle(100, 100))
    obj2 = DummyGameObject(Polygon((
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
    obj1 = DummyGameObject(Polygon.rectangle(100, 100))
    obj2 = DummyGameObject(Polygon((
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
