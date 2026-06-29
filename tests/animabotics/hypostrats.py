"""Shared Hypothesis strategies and tests."""

from fractions import Fraction
from typing import TypeVar, Union

from hypothesis import strategies as strats
from hypothesis import example, given


def examples(*args_list):

    def wrapped(function):
        for args in args_list:
            function = example(*args)(function)
        return function

    return wrapped


finite_floats = strats.floats(
    min_value=-1e9,
    max_value=1e9,
    allow_nan=False,
    allow_infinity=False,
)


def rationals():
    # type: () -> Union[int, Fraction]
    """Generate rational numberss."""
    return strats.one_of(strats.integers(), strats.fractions())


def reals():
    # type: () -> Union[int, Fraction, float]
    """Generate real numbers."""
    return strats.one_of(strats.integers(), strats.fractions(), finite_floats)


S = TypeVar('S')
T = TypeVar('T')


def identity_metatest(strategy, identity, function):
    # type: (strats.SearchStrategy[T], T, Callable[[T, T], T]) -> None
    """Test that identity leaves a value unchanged."""
    # pylint: disable = no-value-for-parameter

    @given(strategy)
    def test(obj):
        # type: (T) -> None
        assert function(obj, identity) == obj

    test()


def inverse_metatest(strategy, identity, function, inverse):
    # type: (strats.SearchStrategy[T], T, Callable[[T, T], T], Callable[[T], T]) -> None
    """Test that inverse element undoes the function."""
    # pylint: disable = no-value-for-parameter

    @given(strategy)
    def test_inverse(obj):
        # type: (T) -> None
        assert function(obj, inverse(obj)) == identity

    @given(strategy)
    def test_double_inverse(obj):
        # type: (T) -> None
        assert obj == inverse(inverse(obj))

    test_inverse()
    test_double_inverse()


def involution_metatest(strategy, function):
    # type: (strats.SearchStrategy[T], Callable[[T], T]) -> None
    """Test that applying the function twice returns the original."""
    # pylint: disable = no-value-for-parameter

    @given(strategy)
    def test(obj):
        # type: (T) -> None
        assert obj == function(function(obj))

    test()


def associativity_metatest(strategy, function):
    # type: (strats.SearchStrategy[T], Callable[[T, T], T]) -> None
    """Test that the function is associative."""
    # pylint: disable = no-value-for-parameter

    @given(strategy, strategy, strategy)
    def test(obj1, obj2, obj3):
        # type: (T, T, T) -> None
        assert (
            function(function(obj1, obj2), obj3)
            == function(obj1, function(obj2, obj3))
        )

    test()


def commutativity_metatest(strategy, function):
    # type: (strats.SearchStrategy[T], Callable[[T, T], T]) -> None
    """Test that the function is commutative."""
    # pylint: disable = no-value-for-parameter

    @given(strategy, strategy)
    def test(obj1, obj2):
        # type: (T, T) -> None
        assert function(obj1, obj2) == function(obj2, obj1)

    test()


def affine_space_metatest(point_strategy, vector_strategy, vector_identity):
    # type: (strats.SearchStrategy[S], strats.SearchStrategy[T], T) -> None
    """Test that objects form an affine space and an associated vector space."""
    # pylint: disable = no-value-for-parameter

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

    identity_metatest(point_strategy, vector_identity, (lambda a, b: a + b))
    test_associative()
    test_subtraction()
    test_weyl()
    test_parallelogram()


def abelian_group_metatest(strategy, identity, function, inverse):
    # type: (strats.SearchStrategy[T], T) -> None
    """Test that objects form an abelian group."""
    # pylint: disable = no-value-for-parameter

    @given(strategy, strategy)
    def test_antisymmetric(obj1, obj2):
        # type: (T, T) -> None
        assert (
            function(obj1, inverse(obj2))
            == inverse(function(obj2, inverse(obj1)))
        )

    identity_metatest(strategy, identity, function)
    inverse_metatest(strategy, identity, function, inverse)
    associativity_metatest(strategy, function)
    commutativity_metatest(strategy, function)
    test_antisymmetric()


def field_metatest(strategy, additive_identity, multiplicative_identity):
    # type: (strats.SearchStrategy[T], T, T) -> None
    """Test that objects form a field."""
    # pylint: disable = no-value-for-parameter

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
