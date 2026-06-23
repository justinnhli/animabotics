"""Tests for algebra.py."""

from animabotics.algebra import FunctionCallExpression, Function, Number
from animabotics.algebra import parse_expression, parse_pattern



def test_interoperability():
    # type: () -> None
    """Test Expression interoperability with regular Python operators."""
    assert (
        1 + Number(2)
        == Number(1) + 2
        == Number(1) + Number(2)
        == FunctionCallExpression(Function('+'), Number(1), Number(2))
    )
    assert (
        1 - Number(2)
        == Number(1) - 2
        == Number(1) - Number(2)
        == FunctionCallExpression(Function('-'), Number(1), Number(2))
    )
    assert (
        1 * Number(2)
        == Number(1) * 2
        == Number(1) * Number(2)
        == FunctionCallExpression(Function('*'), Number(1), Number(2))
    )
    assert (
        1 / Number(2)
        == Number(1) / 2
        == Number(1) / Number(2)
        == FunctionCallExpression(Function('/'), Number(1), Number(2))
    )
    assert (
        2 ** Number(3)
        == Number(2) ** 3
        == Number(2) ** Number(3)
        == FunctionCallExpression(Function('^'), Number(2), Number(3))
    )


def test_parser_expression_good():
    # type: () -> None
    """Test the Expression and Pattern parser on good (parsable) strings."""
    tests = (
        '1',
        '-1',
        'x',
        '(+ 1 1)',
        '(+ 1 1 1 1)',
        '(cos x)',
        '(pi)',
        '(sqrt (+ (^ a 2) (^ b 2)))',
        '(/)',
        '(temp_)',
        'temp_',
    )
    for test in tests:
        expression = parse_expression(test)
        assert expression is not None, (test, expression)
        assert parse_expression(str(expression)) == expression, (test, expression)
        pattern = parse_pattern(test)
        assert pattern is not None, (test, pattern)
        assert parse_pattern(str(pattern)) == pattern, (test, pattern)


def test_parser_pattern_good():
    # type: () -> None
    """Test the Pattern parser on good (parsable) strings."""
    tests = (
        '(+ [a] 0 [b])',
    )
    for test in tests:
        pattern = parse_pattern(test)
        assert pattern is not None, (test, pattern)
        assert parse_pattern(str(pattern)) == pattern, (test, pattern)
        try:
            print(parse_expression(test))
        except ValueError:
            pass


def test_parser_bad():
    # type: () -> None
    """Test the Expression and Pattern parser on bad (unparsable) strings."""
    tests = (
        '(0 1 2)',
        '((+ 1 2) 1 2)',
        '((pi) 1 2)',
        '1.5',
        '-x',
        '(_temp)',
        '_temp',
        '(cos a',
        '(cos a',
        '(cos [a)',
        '(cos [0',
    )
    for test in tests:
        try:
            print(parse_expression(test))
        except ValueError:
            pass
        try:
            print(parse_pattern(test))
        except ValueError:
            pass
