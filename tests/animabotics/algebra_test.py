from fractions import Fraction

from animabotics import AlgebraParser
from animabotics.algebra import FunctionCall, Function, Number


def test_parser_good():
    # type: () -> None
    parser = AlgebraParser()
    equations = [
        'x=2',
        '1+1 = 2',
        '(1+1) = 2',
        '1 + 1 + 1 = 3',
        '1 + 1 + 1 - 1 + 1 = 3',
        '(9 * c) / 5 = f - 32',
        'y = (9 + x) / (5 * x)',
        '(9 * c) / 5 = 85 - 32',
        '9 * c / 5 + 32 - 85 = 0',
        'x = 0',
        '(2 * x + 8) / 2 = (8 * x + 2) / 8',
        'y = cos(x)',
        'a^2 + b^2 = c^2',
        '1 / x = x^-1',
        'undef = -1 / 0',
        'long_variable_name = long + variable + name',
        'z = func(x, y)',
        'y = relu(sum(xs)) + b',
        'const = pi()',
    ]
    for equation in equations:
        sides = equation.split('=')
        assert len(sides) == 2
        for side in sides:
            parse = parser.parse_expression(side)
            assert parse is not None, side
            assert parser.parse_expression(str(parse)) == parse, (
                side,
                parse,
                str(parse),
                parser.parse_expression(str(parse)),
            )
        parse = parser.parse_equation(equation)
        assert parse is not None, equation
        assert parser.parse_equation(str(parse)) == parse, (
            equation,
            parse,
            str(parse),
            parser.parse_equation(str(parse)),
        )


def test_parser_bad():
    # type: () -> None
    parser = AlgebraParser()
    expressions = [
        '_a',
        '0a',
        '1 + 2 +',
        '1 * 2 *',
        '1 ^ 2 ^',
        '1 = 1', # expressions should not have equal signs
        '+1',
        '+',
        'sin(x',
        'sin(+',
        'sin(x, +)',
        '(-',
        '(0',
        'c++',
        '1 2',
        'x y',
        '0^-',
        '/ 2',
    ]
    for expression in expressions:
        parse = parser.parse_expression(expression)
        assert parse is None, (expression, parse)
    equations = [
        'x',
        '1 = 1 = 1',
        '1 + = 2',
        '+ 1 = 2',
        '2 = + 1',
        '0 = _',
    ]
    for equation in equations:
        parse = parser.parse_equation(equation)
        assert parse is None, (equation, parse)


def test_sexp_parser_good():
    parser = AlgebraParser()
    sexps = [
        '0',
        'b',
        ' ( + 1 1 ) ',
        ' ( + 1 (+ 1 1) ) ',
        '(/ a)',
        '(* [a] 0 [b])',
        '(+ [a] 0 [b])',
        '(* [a] 1 [b])',
        '(* [a] [b])',
        '(+ [a] [b])',
        '(+ [a] [b] [c])',
        '(+ [a] (- x) [b] x [c])',
        '(+ [a] x [b] (- x) [c])',
        '(op [a] [b] [c])',
        '(op [a] [b] [c] z)',
        '(op [a] (op [b]) [c])',
        '(op [a] x [b] y [c])',
        '(+ (^ ("cos" theta) 2) (^ ("sin" theta) 2))',
    ]
    for sexp in sexps:
        parse = parser.parse_s_expression(sexp)
        assert parse is not None, sexp
        assert parser.parse_s_expression(str(parse)) == parse, (
            sexp,
            parse,
            str(parse),
            parser.parse_s_expression(str(parse)),
        )


def test_sexp_parser_bad():
    parser = AlgebraParser()
    sexps = [
        '+',
        '(+ +)',
        '"123 abc"',
        '"abc123]',
        '[123 abc]',
        '[abc123"',
        '[abc123"',
        '(0)',
        '(cos)',
    ]
    for sexp in sexps:
        parse = parser.parse_s_expression(sexp)
        assert parse is None, (sexp, parse)


def test_evaluate():
    parser = AlgebraParser()
    assert parser.parse_expression('1').evaluate() == 1
    assert parser.parse_expression('2 + 3').evaluate() == 5
    assert parser.parse_expression('2 - 3').evaluate() == -1
    assert parser.parse_expression('2 * 3').evaluate() == 6
    assert parser.parse_expression('2 / 3').evaluate() == Fraction(2, 3)
    assert parser.parse_expression('2 ^ 3').evaluate() == 8
    assert parser.parse_expression('2^(-1 + -1)').evaluate() == Fraction(1, 4)
    assert parser.parse_expression('(2 / 3)^2').evaluate() == Fraction(4, 9)
    try:
        print(parser.parse_expression('a').evaluate())
        assert False
    except ValueError:
        pass
    try:
        print(parser.parse_expression('asdf(0)').evaluate())
        assert False
    except ValueError:
        pass
