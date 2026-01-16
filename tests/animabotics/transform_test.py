"""Tests for transform.py."""

from math import pi as PI

from animabotics.matrix import Matrix, identity
from animabotics.transform import Transform


def test_transform():
    # type: () -> None
    """Test Transform."""
    t1 = Transform(3, 2, PI / 2, 0.25)
    t2 = Transform(1, 1, PI / 2, 2)
    assert t1.x == 3
    assert t1.y == 2
    assert t1.theta == PI / 2
    assert t1.scale == 0.25
    assert t1.inverse == Transform(-8, 12, -PI / 2, 4)
    assert round(t1.matrix, 3) == Matrix((
        (0, -0.25, 0, 3),
        (0.25, 0, 0, 2),
        (0, 0, 0.25, 0),
        (0, 0, 0, 1),
    ))
    assert round(t2 @ t1, 3) == round(Transform(-3, 7, PI, 0.5), 3)
    assert round((t2 @ t1).matrix, 3) == round(Transform(-3, 7, PI, 0.5).matrix, 3)
    assert round(t1 @ t2, 3) == round(Transform(2.75, 2.25, PI, 0.5), 3)
    assert round((t1 @ t2).matrix, 3) == round(Transform(2.75, 2.25, PI, 0.5).matrix, 3)
    assert round((t1.inverse @ t1).matrix, 3) == identity()
    assert round((t1 @ t1.inverse).matrix, 3) == identity()
