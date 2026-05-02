"""Shared Hypothesis strategies and tests."""

from fractions import Fraction
from typing import TypeVar, Any, Union

from hypothesis import strategies as strats, given


finite_floats = strats.floats(
    min_value=-1e9,
    max_value=1e9,
    allow_nan=False,
    allow_infinity=False,
)


def rationals():
    # type: () -> Union[int, Fraction]
    return strats.one_of(strats.integers(), strats.fractions())


def reals():
    # type: () -> Union[int, Fraction, float]
    return strats.one_of(strats.integers(), strats.fractions(), finite_floats)


S = TypeVar('S')
T = TypeVar('T')


def affine_space_metatest(point_strategy, vector_strategy, vector_identity):
    # type: (strats.SearchStrategy[S], strats.SearchStrategy[T], T) -> None

    @given(point_strategy)
    def test_identity(point):
        # type: (S) -> None
        assert point + vector_identity == point

    @given(point_strategy, vector_strategy, vector_strategy)
    def test_associative(point, vector1, vector2):
        # type: (S, T, T) -> None
        assert (point + vector1) + vector2 == point + (vector1 + vector2)

    @given(point_strategy, point_strategy)
    def test_subtraction(point1, point2):
        # type: (S, S) -> None
        assert point1 + (point2 - point1) == point2

    @given(point_strategy, point_strategy, point_strategy)
    def test_weyl(point1, point2, point3):
        # type: (S, S, S) -> None
        assert (point1 - point2) + (point2 - point3) == point1 - point3

    @given(point_strategy, point_strategy, point_strategy, point_strategy)
    def test_parallelogram(point1, point2, point3, point4):
        # type: (S, S, S, S) -> None
        assert (
            point1 - point4
            == (point1 - point2) + (point2 - point4)
            == (point1 - point3) + (point3 - point4)
        )

    test_identity()
    test_associative()
    test_subtraction()
    test_weyl()
    test_parallelogram()


def abelian_group_metatest(strategy, identity):
    # type: (strats.SearchStrategy[T], T) -> None

    @given(strategy)
    def test_double_inverse(obj):
        # type: (T) -> None
        assert obj == -(-obj)

    @given(strategy)
    def test_identity(obj):
        # type: (T) -> None
        assert obj + identity == obj
        assert obj - identity == obj

    @given(strategy)
    def test_inverse_self(obj):
        # type: (T) -> None
        assert obj + (-obj) == identity

    @given(strategy, strategy)
    def test_antisymmetric(obj1, obj2):
        # type: (T, T) -> None
        assert obj1 - obj2 == -(obj2 - obj1)

    @given(strategy, strategy)
    def test_add_sub_roundtrip(obj1, obj2):
        # type: (T, T) -> None
        assert (obj1 + obj2) - obj2 == obj1
        assert (obj1 - obj2) + obj2 == obj1

    @given(strategy, strategy, strategy)
    def test_associative(obj1, obj2, obj3):
        # type: (T, T, T) -> None
        assert (obj1 + obj2) + obj3 == obj1 + (obj2 + obj3)

    @given(strategy, strategy)
    def test_commutative(obj1, obj2):
        # type: (T, T) -> None
        assert obj1 + obj2 == obj2 + obj1

    test_double_inverse()
    test_identity()
    test_inverse_self()
    test_antisymmetric()
    test_add_sub_roundtrip()
    test_associative()
    test_commutative()


def field_metatest(strategy, additive_identity, multiplicative_identity):
    # type: (strats.SearchStrategy[T], T, T) -> None

    @given(strategy, strategy, strategy)
    def test_additive_associativity(element1, element2, element3):
        # type: (T, T, T) -> None
        """Test associativity of addition.

        a + (b + c) = (a + b) + c
        """
        assert (element1 + element2) + element3 == element1 + (element2 + element3)

    @given(strategy, strategy, strategy)
    def test_multiplicative_associativity(element1, element2, element3):
        # type: (T, T, T) -> None
        """Test associativity of multiplication.

        a * (b * c) = (a * b) * c
        """
        assert (element1 * element2) * element3 == element1 * (element2 * element3)

    @given(strategy, strategy)
    def test_additive_commutivity(element1, element2):
        # type: (T, T) -> None
        """Test commutativity of addition.

        a + b = b + a
        """
        assert element1 + element2 == element2 + element1

    @given(strategy, strategy)
    def test_multiplicative_commutivity(element1, element2):
        # type: (T, T) -> None
        """Test commutativity of multiplication.

        a * b = b * a
        """
        assert element1 * element2 == element2 * element1

    @given(strategy)
    def test_additive_identity(element):
        # type: (T) -> None
        """Test additive identity.

        a + 0 = a
        """
        assert element + additive_identity == element

    @given(strategy)
    def test_multiplicative_identity(element):
        # type: (T) -> None
        """Test multiplicative identity.

        a * 1 = a
        """
        assert element * multiplicative_identity == element

    @given(strategy)
    def test_additive_inverse(element):
        # type: (T) -> None
        """Test additive inverses.

        a - a = 0 and a + (−a) = 0
        """
        assert element - element == additive_identity
        assert element + (-element) == additive_identity

    @given(strategy.filter(lambda n: n != 0))
    def test_multiplicative_inverse(element):
        # type: (T) -> None
        """Test multiplicative inverses.

        a / a = 1 and a * (1/a) = 1 (if a != 0)

        The second version is skipped to avoid the floating point weirdness of 1/a.
        """
        assert element / element == multiplicative_identity

    @given(strategy, strategy, strategy)
    def test_distributivity(element1, element2, element3):
        # type: (T, T, T) -> None
        """Test distributivity of multiplication over addition.

        a * (b + c) = (a * b) + (a * c)
        """
        assert element1 * (element2 + element3) == element1 * element2 + element1 * element3

    test_additive_associativity()
    test_multiplicative_associativity()
    test_additive_commutivity()
    test_multiplicative_commutivity()
    test_additive_identity()
    test_multiplicative_identity()
    test_additive_inverse()
    test_multiplicative_inverse()
    test_distributivity()
