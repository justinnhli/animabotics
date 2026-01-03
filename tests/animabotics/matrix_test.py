"""Tests for matrix.py."""

from math import floor, ceil
from fractions import Fraction

from animabotics.matrix import Matrix, identity


def test_matrix():
    # type: () -> None
    """Test Matrix."""
    # equality
    m1 = Matrix(((1, 2, 3, 4), (5, 6, 7, 8), (9, 8, 7, 6), (5, 4, 3, 2)))
    m2 = Matrix(((1, 2, 3, 4), (5, 6, 7, 8), (9, 8, 7, 6), (5, 4, 3, 2)))
    assert m1 == m2
    m1 = Matrix(((1, 2, 3, 4), (5, 6, 7, 8), (9, 8, 7, 6), (5, 4, 3, 2)))
    m2 = Matrix(((2, 3, 4, 5), (6, 7, 8, 9), (8, 7, 6, 5), (4, 3, 2, 1)))
    assert m1 != m2
    # indexing
    assert Matrix(((1, 2), (3, 4)))[0] == (1, 2)
    assert Matrix(((1, 2), (3, 4)))[1] == (3, 4)
    # identity
    assert identity(4) == Matrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    # element-wise arithmetic
    assert Matrix(((3, -2, 5, 1),)) + Matrix(((-2, 3, 1, 0),)) == Matrix(((1, 1, 6, 1),))
    assert Matrix(((3, 2, 1, 1),)) - Matrix(((5, 6, 7, 1),)) == Matrix(((-2, -4, -6, 0),))
    assert Matrix(((3, 2, 1, 1),)) - Matrix(((5, 6, 7, 0),)) == Matrix(((-2, -4, -6, 1),))
    assert Matrix(((3, 2, 1, 0),)) - Matrix(((5, 6, 7, 0),)) == Matrix(((-2, -4, -6, 0),))
    assert Matrix(((1, -2, 3, -4),)) * 3.5 == Matrix(((3.5, -7, 10.5, -14),))
    assert 0.5 * Matrix(((1, -2, 3, -4),)) == Matrix(((0.5, -1, 1.5, -2),))
    assert Matrix(((1, -2, 3, -4),)) / 2 == Matrix(((0.5, -1, 1.5, -2),))
    assert Matrix(((1, -2, 3, -4),)) // 2 == Matrix(((0, -1, 1, -2),))
    assert -Matrix(((1, 2), (3, 4))) == Matrix(((-1, -2), (-3, -4)))
    # rounding
    assert round(Matrix(((0.25, 0.5), (1.5, 1.75)))) == Matrix(((0, 0), (2, 2)))
    assert floor(Matrix(((0.25, 0.5), (1.5, 1.75)))) == Matrix(((0, 0), (1, 1)))
    assert ceil(Matrix(((0.25, 0.5), (1.5, 1.75)))) == Matrix(((1, 1), (2, 2)))
    # reflection
    assert Matrix(((1, 2, 3, 4),)).transpose.x_reflection == Matrix(((-1, 2, 3, 4),)).transpose
    assert Matrix(((1, 2, 3, 4),)).transpose.y_reflection == Matrix(((1, -2, 3, 4),)).transpose
    assert Matrix(((1, 2, 3, 4),)).transpose.z_reflection == Matrix(((1, 2, -3, 4),)).transpose
    # magnitude and normalization
    assert Matrix(((1, 0, 0, 0),)).transpose.magnitude == 1
    assert Matrix(((0, 1, 0, 0),)).transpose.magnitude == 1
    assert Matrix(((0, 0, 1, 0),)).transpose.magnitude == 1
    assert Matrix(((2, 3, 6, 0),)).transpose.magnitude == 7
    assert Matrix(((-2, -3, -6, 0),)).transpose.magnitude == 7
    assert Matrix(((4, 0, 0, 0),)).transpose.normalized == Matrix(((1, 0, 0, 0),)).transpose
    assert Matrix(((1, 2, 3, 0),)).transpose.normalized.magnitude == 1
    # dot and cross product
    assert Matrix(((1, 2, 3, 0),)).transpose.dot(Matrix(((2, 3, 4, 0),)).transpose) == 20
    assert Matrix(((1, 2, 3, 0),)).transpose.cross(Matrix(((2, 3, 4, 0),)).transpose) == Matrix(((-1, 2, -1, 0),)).transpose
    assert Matrix(((2, 3, 4, 0),)).transpose.cross(Matrix(((1, 2, 3, 0),)).transpose) == Matrix(((1, -2, 1, 0),)).transpose
    # matrix multiplication
    m1 = Matrix(((1, 2, 3, 4), (5, 6, 7, 8), (9, 8, 7, 6), (5, 4, 3, 2)))
    m2 = Matrix(((-2, 1, 2, 3), (3, 2, 1, -1), (4, 3, 6, 5), (1, 2, 7, 8)))
    m3 = Matrix(((20, 22, 50, 48), (44, 54, 114, 108), (40, 58, 110, 102), (16, 26, 46, 42)))
    assert m1 @ m2 == m3
    m1 = Matrix(((1, 2, 3, 4), (2, 4, 4, 2), (8, 6, 4, 1), (0, 0, 0, 1)))
    try:
        print(m1 @ Matrix(((1, 2, 3, 1),)))
        assert False
    except AssertionError:
        pass
    assert m1 @ Matrix(((1, 2, 3, 1),)).transpose == Matrix(((18, 24, 33, 1),)).transpose
    m1 = Matrix(((0, 1, 2, 4), (1, 2, 4, 8), (2, 4, 8, 16), (4, 8, 16, 32)))
    assert m1 @ identity(4) == m1
    # transposition
    m1 = Matrix(((0, 9, 3, 0), (9, 8, 0, 8), (1, 8, 5, 3), (0, 0, 5, 8)))
    m2 = Matrix(((0, 9, 1, 0), (9, 8, 8, 0), (3, 0, 5, 5), (0, 8, 3, 8)))
    assert m1.transpose == m2
    assert m1.transpose.transpose == m1
    assert identity(4).transpose == identity(4)
    # determinant
    assert Matrix(((1, 5), (-3, 2))).determinant == 17
    assert Matrix(((1, 5, 0), (-3, 2, 7), (0, 6, -3))).submatrix(0, 2) == Matrix(((-3, 2), (0, 6)))
    assert Matrix(((-6, 1, 1, 6), (-8, 5, 8, 6), (-1, 0, 8, 2), (-7, 1, -1, 1))).submatrix(2, 1) == Matrix(((-6, 1, 6), (-8, 8, 6), (-7, -1, 1)))
    assert Matrix(((3, 5, 0), (2, -1, -7), (6, -1, 5))).minor(1, 0) == 25
    m = Matrix(((3, 5, 0), (2, -1, -7), (6, -1, 5)))
    assert m.cofactor(0, 0) == -12
    assert m.cofactor(1, 0) == -25
    assert Matrix(((1, 2, 6), (-5, 8, -4), (2, 6, 4))).determinant == -196
    assert Matrix(((-2, -8, 3, 5), (-3, 1, 7, 3), (1, 2, -9, 6), (-6, 7, 7, -9))).determinant == -4071
    # inverse
    m1 = Matrix(((3, -9, 7, 3), (3, -8, 2, -9), (-4, 4, 4, 1), (-6, 5, -1, 1)))
    m2 = Matrix(((8, 2, 2, 2), (3, -1, 7, 0), (7, 0, 5, 4), (6, -2, 0, 5)))
    assert m2.invertible
    assert not Matrix(((2, 4), (2, 4))).invertible
    assert round(m1 @ m2 @ m2.inverse, 3) == round(m1, 3)
    # translation and scaling
    assert identity(4).translate(5, -3, 2) @ Matrix(((-3, 4, 5, 1),)).transpose == Matrix(((2, 1, 7, 1),)).transpose
    assert identity(4).translate(5, -3, 2).inverse @ Matrix(((-3, 4, 5, 1),)).transpose == Matrix(((-8, 7, 3, 1),)).transpose
    assert identity(4).translate(5, -3, 2) @ Matrix(((-3, 4, 5, 0),)).transpose == Matrix(((-3, 4, 5, 0),)).transpose
    assert identity(4).scale(2, 3, 4) @ Matrix(((-4, 6, 8, 1),)).transpose == Matrix(((-8, 18, 32, 1),)).transpose
    assert identity(4).scale(2, 3, 4) @ Matrix(((-4, 6, 8, 0),)).transpose == Matrix(((-8, 18, 32, 0),)).transpose
    assert identity(4).scale(2, 3, 4).inverse @ Matrix(((-4, 6, 8, 1),)).transpose == Matrix(((-2, 2, 2, 1),)).transpose
    # shear
    assert identity(4).shear(1, 0, 0, 0, 0, 0) @ Matrix(((2, 3, 4, 1),)).transpose == Matrix(((5, 3, 4, 1),)).transpose
    assert identity(4).shear(0, 1, 0, 0, 0, 0) @ Matrix(((2, 3, 4, 1),)).transpose == Matrix(((6, 3, 4, 1),)).transpose
    assert identity(4).shear(0, 0, 1, 0, 0, 0) @ Matrix(((2, 3, 4, 1),)).transpose == Matrix(((2, 5, 4, 1),)).transpose
    assert identity(4).shear(0, 0, 0, 1, 0, 0) @ Matrix(((2, 3, 4, 1),)).transpose == Matrix(((2, 7, 4, 1),)).transpose
    assert identity(4).shear(0, 0, 0, 0, 1, 0) @ Matrix(((2, 3, 4, 1),)).transpose == Matrix(((2, 3, 6, 1),)).transpose
    assert identity(4).shear(0, 0, 0, 0, 0, 1) @ Matrix(((2, 3, 4, 1),)).transpose == Matrix(((2, 3, 7, 1),)).transpose

def test_rref():
    testcases = [
        (
            Matrix(((2, 0, 0), (0, 3, 0),)),
            Matrix(((1, 0, 0), (0, 1, 0),)),
        ),
        (
            Matrix(((2, 4), (1, 2), (3, 6),)),
            Matrix(((1, 2), (0, 0), (0, 0),)),
        ),
        (
            Matrix(((1, 0), (1, 0), (0, 1),)),
            Matrix(((1, 0), (0, 1), (0, 0),)),
        ),
        (
            Matrix(((2, 6, 3, 6), (0, 0, 1, 2), (0, 0, 0, 0),)),
            Matrix(((1, 3, 0, 0), (0, 0, 1, 2), (0, 0, 0, 0),)),
        ),
        (
            Matrix(((1, 1, 1), (0, 0, 1), (0, 0, 1), (0, 1, 0))),
            Matrix(((1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0))),
        ),
        (
            # from https://kirkmcdonald.github.io/posts/calculation.html
            Matrix((
                (Fraction(-40),  Fraction(0),    Fraction(30),    Fraction(10),    Fraction(0),  Fraction(0),  Fraction(10)),
                (Fraction(30),   Fraction(-30),  Fraction(30),    Fraction(45),    Fraction(0),  Fraction(0),  Fraction(0)),
                (Fraction(0),    Fraction(20),   Fraction(40),    Fraction(55),    Fraction(0),  Fraction(0),  Fraction(45)),
                (Fraction(-30),  Fraction(-30),  Fraction(0),     Fraction(-50),   Fraction(1),  Fraction(0),  Fraction(0)),
                (Fraction(0),    Fraction(0),    Fraction(-100),  Fraction(-100),  Fraction(0),  Fraction(1),  Fraction(0)),
            )),
            Matrix((
                (Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(-13, 400), Fraction(-23, 12)),
                (Fraction(0), Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(-7, 400), Fraction(-1, 4)),
                (Fraction(0), Fraction(0), Fraction(1), Fraction(0), Fraction(0), Fraction(-3, 50), Fraction(-10, 3)),
                (Fraction(0), Fraction(0), Fraction(0), Fraction(1), Fraction(0), Fraction(1, 20), Fraction(10, 3)),
                (Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(1), Fraction(1), Fraction(305, 3)),
            )),
        ),
    ]
    for matrix, expect in testcases:
        actual = matrix.rref
        assert expect == actual
