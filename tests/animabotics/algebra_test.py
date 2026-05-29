from animabotics import AlgebraParser


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
        'abs()',
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
