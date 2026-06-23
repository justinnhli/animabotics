"""Tests for algebra.py."""

from fractions import Fraction

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


def test_evaluate():
    # type: () -> None
    """Test the evaluation of Expressions."""
    assert parse_expression('1').evaluate() == 1
    assert parse_expression('(+ 2 3)').evaluate() == 5
    assert parse_expression('(- 2 3)').evaluate() == -1
    assert parse_expression('(* 2 3)').evaluate() == 6
    assert parse_expression('(/ 2 3)').evaluate() == Fraction(2, 3)
    assert parse_expression('(^ 2 3)').evaluate() == 8
    assert parse_expression('(+ 5)').evaluate() == 5
    assert parse_expression('(- 5)').evaluate() == -5
    assert parse_expression('(* 5)').evaluate() == 5
    assert parse_expression('(/ 5)').evaluate() == Fraction(1, 5)
    assert parse_expression('(^ 2 (+ -1 -1))').evaluate() == Fraction(1, 4)
    assert parse_expression('(^ (/ 2 3) 2)').evaluate() == Fraction(4, 9)
    assert parse_expression('(fact 0)').evaluate() == 1
    assert parse_expression('(fact 5)').evaluate() == 120
    assert round(parse_expression('(* (pi) 100)').evaluate()) == 314
    assert round(parse_expression('(* (e) 100)').evaluate()) == 272
    for op in '+-*/^':
        try:
            print(parse_expression(f'({op})').evaluate())
            assert False
        except ValueError:
            pass

    try:
        print(parse_expression('a').evaluate())
        assert False
    except ValueError:
        pass
    try:
        print(parse_expression('(asdf 0)').evaluate())
        assert False
    except ValueError:
        pass


def test_pattern_matching():
    tests = [
        ('1', '1', [{}]),
        ('1', '0', []),
        ('x', '1', [{'x': '1'}]),
        ('x', 'y', [{'x': 'y'}]),
        ('x', '(+ 1 1)', [{'x': '(+ 1 1)'}]),
        ('(x)', '(+ 1 1)', []),
        ('(x)', '1', []),
        ('(+ 0 1)', '(* 0 1)', []),
        ('(+ x y)', '(+ 1 1)', [{'x': '1', 'y': '1'}]),
        ('(+ x y)', '(+ 1 2)', [{'x': '1', 'y': '2'}]),
        ('(+ x x)', '(+ 1 1)', [{'x': '1'}]),
        ('(+ x x)', '(+ 1 2)', []),
        ('(+ x (+ x x))', '(+ 1 (+ 1 1))', [{'x': '1'}]),
        ('(+ x (+ y y))', '(+ 1 (+ 1 1))', [{'x': '1', 'y': '1'}]),
        ('(+ x (+ x y))', '(+ 1 (+ 1 1))', [{'x': '1', 'y': '1'}]),
        ('(+ x (+ y y))', '(+ 1 (+ 2 2))', [{'x': '1', 'y': '2'}]),
        ('(+ x (+ x y))', '(+ 1 (+ 2 1))', []),
        ('(+ x x x)', '(+ 1 1 1)', [{'x': '1'}]),
        (
            '(+ [a] [b])',
            '(+ 0)',
            [
                {'a': (), 'b': ('0',)},
                {'a': ('0',), 'b': ()},
            ],
        ),
        (
            '(+ [a] [b])',
            '(+ 0 1)',
            [
                {'a': (), 'b': ('0', '1')},
                {'a': ('0',), 'b': ('1',)},
                {'a': ('0', '1'), 'b': ()},
            ],
        ),
        (
            '(+ [a] [b])',
            '(+ 0 1 2)',
            [
                {'a': (), 'b': ('0', '1', '2')},
                {'a': ('0',), 'b': ('1', '2')},
                {'a': ('0', '1'), 'b': ('2',)},
                {'a': ('0', '1', '2'), 'b': ()},
            ],
        ),
        (
            '(+ [a] [b] [c])',
            '(+ 0 1)',
            [
                {'a': (), 'b': (), 'c': ('0', '1')},
                {'a': (), 'b': ('0',), 'c': ('1',)},
                {'a': (), 'b': ('0', '1'), 'c': ()},
                {'a': ('0',), 'b': (), 'c': ('1',)},
                {'a': ('0',), 'b': ('1',), 'c': ()},
                {'a': ('0', '1'), 'b': (), 'c': ()},
            ],
        ),
        (
            '(+ [a] x [b])',
            '(+ 0 1)',
            [
                {'a': (), 'b': ('1',), 'x': '0'},
                {'a': ('0',), 'b': (), 'x': '1'},
            ],
        ),
        (
            '(+ [a] 1 [b])',
            '(+ 0 1)',
            [{'a': ('0',), 'b': ()}],
        ),
    ]
    for pattern_str, expression_str, expect_matches_list in tests:
        pattern = parse_pattern(pattern_str)
        assert pattern is not None, (pattern_str, pattern)
        expression = parse_expression(expression_str)
        assert expression is not None, (expression_str, expression)
        expect_matches = set()
        for bindings in expect_matches_list:
            expression_bindings = {}
            for variable, value in bindings.items():
                if isinstance(value, str):
                    expression_bindings[variable] = parse_expression(value)
                elif isinstance(value, tuple):
                    expression_bindings[variable] = tuple(parse_expression(val) for val in value)
                else:
                    raise ValueError()
            expect_matches.add(tuple(sorted(expression_bindings.items())))
        actual_matches = set(
            tuple(sorted(bindings.items()))
            for bindings in pattern.matches(expression, {})
        )
        assert actual_matches == expect_matches, (pattern_str, expression_str, actual_matches)
