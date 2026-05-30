"""Symbolic algebra."""

import re
from collections import namedtuple
from fractions import Fraction
from functools import reduce
from typing import Any, Optional, Union, Callable


BuiltInNumber = Union[int, float, Fraction]


class SymbolicMath:

    def substitute(self, bindings):
        # type: (dict[Expression, Expression]) -> Expression
        raise NotImplementedError()


class Expression(SymbolicMath):

    def __neg__(self):
        # type: (Any) -> Any
        return FunctionCall(Function('-'), self)

    def __add__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall(Function('+'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall(Function('+'), self, other)
        if hasattr(other, '__radd__'):
            return other.__radd__(self)
        else:
            return FunctionCall(Function('+'), self, other)

    def __radd__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) + self
        else:
            raise TypeError(f'unsupported operand type(s) for +: {type(other)} and {type(self)}')

    def __sub__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall(Function('+'), self, Number(-other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall(Function('+'), self, FunctionCall(Function('-'), other))
        if hasattr(other, '__rsub__'):
            return other.__rsub__(self)
        else:
            return FunctionCall(Function('-'), self, other)

    def __rsub__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) - self
        else:
            raise TypeError(f'unsupported operand type(s) for -: {type(other)} and {type(self)}')

    def __mul__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall(Function('*'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall(Function('*'), self, other)
        if hasattr(other, '__rmul__'):
            return other.__rmul__(self)
        else:
            return FunctionCall(Function('*'), self, other)

    def __rmul__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) * self
        else:
            raise TypeError(f'unsupported operand type(s) for *: {type(other)} and {type(self)}')

    def __truediv__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall(Function('*'), self, FunctionCall(Function('/'), Number(other)))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall(Function('*'), self, FunctionCall(Function('/'), other))
        if hasattr(other, '__rtruediv__'):
            return other.__rtruediv__(self)
        else:
            return FunctionCall(Function('/'), self, other)

    def __rtruediv__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) / self
        else:
            raise TypeError(f'unsupported operand type(s) for /: {type(other)} and {type(self)}')

    def __pow__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall(Function('^'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall(Function('^'), self, other)
        if hasattr(other, '__rpow__'):
            return other.__rpow__(self)
        else:
            return FunctionCall(Function('^'), self, other)

    def __rpow__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) ** self
        else:
            raise TypeError(f'unsupported operand type(s) for **: {type(other)} and {type(self)}')

    def evaluate(self):
        # type: () -> BuiltInNumber
        raise NotImplementedError()


class Number(Expression):

    def __init__(self, value):
        # type: (BuiltInNumber) -> None
        if isinstance(value, Fraction):
            self.value = value
        else:
            self.value = Fraction(value)

    def __hash__(self):
        # type: () -> int
        return hash(self.value)

    def __eq__(self, other):
        # type: (Any) -> bool
        return isinstance(other, Number) and self.value == other.value

    def __lt__(self, other):
        # type: (Number) -> bool
        assert isinstance(other, Number)
        return self.value < other.value

    def __repr__(self): # pragma: no cover
        # type: () -> str
        if self.value.is_integer():
            return str(self.value.numerator)
        else:
            return f'{self.value.numerator}/{self.value.denominator}'

    def evaluate(self):
        # type: () -> BuiltInNumber
        return self.value


_FUNCTION_REGISTRY = {} # type: dict[str, Callable[[*tuple[Fraction, ...]], Fraction]]


def _register(func, extra_name=None):
    # type: (Callable[[*tuple[Fraction, ...]], Fraction], str) -> None
    names = []
    names.append(func.__name__.strip('_'))
    if extra_name is not None:
        names.append(extra_name)
    for name in names:
        assert name not in _FUNCTION_REGISTRY
        _FUNCTION_REGISTRY[name] = func


class Function(Expression):

    TAYLOR_TERMS = 10

    def __init__(self, name):
        # type: (str) -> None
        self.name = name

    def __hash__(self):
        # type: () -> int
        return hash(self.name)

    def __eq__(self, other):
        # type: (Any) -> bool
        return isinstance(other, Function) and self.name == other.name

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return self.name

    def evaluate(self):
        # type: () -> Callable[[*tuple[Fraction, ...]], Fraction]
        if self.name in _FUNCTION_REGISTRY:
            return _FUNCTION_REGISTRY[self.name]
        else:
            raise ValueError(f'unknown function "{self.name}()"')

    @_register
    @staticmethod
    def _e(*_):
        # type: (*Fraction) -> Fraction
        return Fraction(
            27182818284590452353602874713526,
            10000000000000000000000000000000,
        )

    @_register
    @staticmethod
    def _pi(*_):
        # type: (*Fraction) -> Fraction
        return Fraction(
            31415926535897932384626433832795,
            10000000000000000000000000000000,
        )

    @_register('+')
    @staticmethod
    def _sum(*terms):
        # type: (*Fraction) -> Fraction
        return reduce((lambda x, y: x + y), terms, initial=Fraction(0))

    @_register('-')
    @staticmethod
    def _negate(*terms):
        # type: (*Fraction) -> Fraction
        assert len(terms) == 1
        return -terms[0]

    @_register('*')
    @staticmethod
    def _product(*terms):
        # type: (*Fraction) -> Fraction
        return reduce((lambda x, y: x * y), terms, initial=Fraction(1))

    @_register('/')
    @staticmethod
    def _inverse(*terms):
        # type: (*Fraction) -> Fraction
        assert len(terms) == 1
        return Fraction(1, terms[0])

    @_register('^')
    @staticmethod
    def _exponentiate(*terms):
        # type: (*Fraction) -> Fraction
        assert len(terms) == 2
        return terms[0] ** terms[1]

    @_register()
    @staticmethod
    def _fact(*terms):
        # type: (*Fraction) -> Fraction
        assert len(terms) == 1
        n = terms[0]
        assert n.is_integer() and n >= 0
        if n == 0:
            return Fraction(1)
        else:
            return _FUNCTION_REGISTRY['*'](*range(1, int(n) + 1))

    @_register()
    @staticmethod
    def _sin(*terms):
        # type: (*Fraction) -> Fraction
        assert len(terms) == 1
        theta = terms[0]
        return sum(
            (
                Fraction(
                    ((-1) ** n) * theta**(2 * n + 1),
                    Function._fact(2 * n + 1),
                )
                for n in range(Function.TAYLOR_TERMS)
            ),
            start=Fraction(0),
        )

    @_register()
    @staticmethod
    def _cos(*terms):
        # type: (*Fraction) -> Fraction
        assert len(terms) == 1
        theta = terms[0]
        return sum(
            (
                Fraction(
                    ((-1) ** n) * theta**(2 * n),
                    Function._fact(2 * n ),
                )
                for n in range(Function.TAYLOR_TERMS)
            ),
            start=Fraction(0),
        )


class Variable(Expression):

    def __init__(self, name):
        # type: (str) -> None
        self.name = name

    def __hash__(self):
        # type: () -> int
        return hash(self.name)

    def __eq__(self, other):
        # type: (Any) -> bool
        return isinstance(other, Variable) and self.name == other.name

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return self.name

    def evaluate(self):
        # type: () -> BuiltInNumber
        raise ValueError(f'no value given for variable "{self.name}"')


class FunctionCall(Expression):

    OPPOSITES = {
        '+': '-',
        '-': '+',
        '*': '/',
        '/': '*',
    }

    def __init__(self, function, *args):
        # type: (Function, *Expression) -> None
        self.function = function
        self.args = args # type: tuple[Expression, ...]
        if self.function.name in '-/':
            assert len(self.args) == 1
        if self.function.name == 'sqrt':
            assert len(self.args) == 1
            self.function = Function('^')
            self.args = (self.args[0], Number(Fraction(1, 2)))

    def __hash__(self):
        # type: () -> int
        return hash((self.function, *self.args))

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, FunctionCall)
            and self.function == other.function
            and self.args == other.args
        )

    def __str__(self):
        # type: () -> str
        if self.function.name not in '+-*/^':
            return f'{self.function.name}(' + ', '.join(str(arg) for arg in self.args) + ')'
        if self.function.name == '-':
            # always unary
            return f'-{self.args[0]}'
        result = [str(self.args[0])]
        for arg in self.args[1:]:
            if isinstance(arg, FunctionCall) and arg.function.name == FunctionCall.OPPOSITES.get(self.function.name):
                result.append(f'{arg.function.name} {arg.args[0]}')
            else:
                result.append(f'{self.function.name} {arg}')
        return '(' + ' '.join(result) + ')'

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return f'({self.function}' + ''.join(f' {repr(arg)}' for arg in self.args) + ')'

    def evaluate(self):
        # type: () -> BuiltInNumber
        return self.function.evaluate()(*(
            arg.evaluate() for arg in self.args
        ))


class Equation(SymbolicMath):

    def __init__(self, lhs, rhs):
        # type: (Expression, Expression) -> None
        self.lhs = lhs
        self.rhs = rhs

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, Equation)
            and self.lhs == other.lhs
            and self.rhs == other.rhs
        )

    def __str__(self):
        # type: () -> str
        return f'{self.lhs} = {self.rhs}'

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return f'(= {repr(self.lhs)} {repr(self.rhs)})'

    def solve_for(self, variable):
        # type: (str) -> Expression
        raise NotImplementedError()


class TokenizationError(Exception):
    """Tokenization Error."""
    pass


Token = namedtuple('Token', 'token_class, string, index')

class AlgebraParser:
    """A parser for algebraic expression and equations.

    equation = add_exp "=" add_exp;
    add_exp = mul_exp ( [+-] mul_exp )*;
    mul_exp = pow_exp ( [*/] pow_exp )*;
    pow_exp = term ( [^] term )?;
    term = parenthesis
         | number
         | function
         | variable;
    identifier = [a-z][a-z0-9_]+;
    variable = identifier;
    function = identifier "(" add_exp ( "," add_exp )* ")";
    parenthesis = "(" add_exp ")";
    operator = [+-*/^];
    number = -?[0-9]+;
    """

    REGEXES = {
        'space': re.compile(' +'),
        'number': re.compile('-?[0-9]+'),
        'identifier': re.compile('[A-Za-z][0-9A-Za-z_]*'),
        'add_op': re.compile('[+-]'),
        'mul_op': re.compile('[*/]'),
        'pow_op': re.compile('\\^'),
        'equal': re.compile('='),
        'comma': re.compile(','),
        'paren_left': re.compile(r'\('),
        'paren_right': re.compile(r'\)'),
    }

    def _tokenize(self, string):
        # type: (str) -> list[Token]
        tokens = []
        index = 0
        while index < len(string):
            match = None
            for token_class, regex in AlgebraParser.REGEXES.items():
                if match := regex.match(string, pos=index):
                    tokens.append(Token(token_class, match.group(), index))
                    break
            if match is None:
                raise TokenizationError(string, index, tokens)
            index += len(match.group())
        assert index == len(string)
        return tokens

    def _token_is(self, tokens, index, token_class):
        # type: (list[Token], int, str) -> bool
        return index < len(tokens) and tokens[index].token_class == token_class

    def _parse_equation(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[Equation], int]
        exp1_parse, exp1_index = self._parse_expression(tokens, index, depth + 1)
        if exp1_parse is None:
            return None, index
        if not self._token_is(tokens, exp1_index, 'equal'):
            return None, index
        exp2_parse, exp2_index = self._parse_expression(tokens, exp1_index + 1, depth + 1)
        if exp2_parse is None:
            return None, index
        return Equation(exp1_parse, exp2_parse), exp2_index

    def _parse_expression(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[Expression], int]
        #print(depth * '  ' + f'expression@{index}')
        return self._parse_add_exp(tokens, index, depth)

    def _parse_add_exp(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[Expression], int]
        #print(depth * '  ' + f'add_exp@{index}')
        args = []
        arg_parse, arg_index = self._parse_mul_exp(tokens, index, depth + 1)
        if arg_parse is None:
            return None, index
        args.append(arg_parse)
        while arg_index < len(tokens):
            if not self._token_is(tokens, arg_index, 'add_op'):
                break
            op = tokens[arg_index].string
            arg_parse, arg_index = self._parse_expression(tokens, arg_index + 1, depth + 1)
            if arg_parse is None:
                return None, index
            if op == '-':
                arg_parse = FunctionCall(Function('-'), arg_parse)
            args.append(arg_parse)
        if len(args) == 1:
            return args[0], arg_index
        else:
            return FunctionCall(Function('+'), *args), arg_index

    def _parse_mul_exp(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[Expression], int]
        #print(depth * '  ' + f'mul_exp@{index}')
        args = []
        arg_parse, arg_index = self._parse_pow_exp(tokens, index, depth + 1)
        if arg_parse is None:
            return None, index
        args.append(arg_parse)
        while arg_index < len(tokens):
            if not self._token_is(tokens, arg_index, 'mul_op'):
                break
            op = tokens[arg_index].string
            arg_parse, arg_index = self._parse_expression(tokens, arg_index + 1, depth + 1)
            if arg_parse is None:
                return None, index
            if op == '/':
                arg_parse = FunctionCall(Function('/'), arg_parse)
            args.append(arg_parse)
        if len(args) == 1:
            return args[0], arg_index
        else:
            return FunctionCall(Function('*'), *args), arg_index

    def _parse_pow_exp(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[Expression], int]
        #print(depth * '  ' + f'pow_exp@{index}')
        base_parse, base_index = self._parse_term(tokens, index, depth + 1)
        if base_parse is None:
            return None, index
        if not self._token_is(tokens, base_index, 'pow_op'):
            return base_parse, base_index
        exp_parse, exp_index = self._parse_term(tokens, base_index + 1, depth + 1)
        if exp_parse is None:
            return None, index
        return FunctionCall(Function('^'), base_parse, exp_parse), exp_index

    def _parse_term(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[Expression], int]
        #print(depth * '  ' + f'term@{index}')
        parse = None # type: Expression
        parse, new_index = self._parse_parenthesis(tokens, index, depth + 1)
        if parse is not None:
            return parse, new_index
        parse, new_index = self._parse_number(tokens, index, depth + 1)
        if parse is not None:
            return parse, new_index
        parse, new_index = self._parse_function_call(tokens, index, depth + 1)
        if parse is not None:
            return parse, new_index
        parse, new_index = self._parse_variable(tokens, index, depth + 1)
        if parse is not None:
            return parse, new_index
        return None, index

    def _parse_parenthesis(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[Expression], int]
        #print(depth * '  ' + f'parenthesis@{index}')
        if not self._token_is(tokens, index, 'paren_left'):
            return None, index
        parse, new_index = self._parse_expression(tokens, index + 1, depth + 1)
        if parse is None:
            return None, index
        if not self._token_is(tokens, new_index, 'paren_right'):
            return None, index
        return parse, new_index + 1

    def _parse_number(self, tokens, index, depth): # pylint: disable = unused-argument
        # type: (list[Token], int, int) -> tuple[Optional[Number], int]
        #print(depth * '  ' + f'number@{index}')
        if self._token_is(tokens, index, 'number'):
            if tokens[index].string.startswith('-'):
                return (
                    FunctionCall(
                        Function('-'),
                        Number(Fraction(tokens[index].string[1:])),
                    ),
                    index + 1
                )
            else:
                return Number(Fraction(tokens[index].string)), index + 1
        else:
            return None, index

    def _parse_function_call(self, tokens, index, depth):
        # type: (list[Token], int, int) -> tuple[Optional[FunctionCall], int]
        #print(depth * '  ' + f'function@{index}')
        if not self._token_is(tokens, index, 'identifier'):
            return None, index
        function = Function(tokens[index].string)
        if not self._token_is(tokens, index + 1, 'paren_left'):
            return None, index
        args = []
        arg_parse, arg_index = self._parse_expression(tokens, index + 2, depth + 1)
        if arg_parse is not None:
            args.append(arg_parse)
            while arg_index < len(tokens):
                if not self._token_is(tokens, arg_index, 'comma'):
                    break
                arg_parse, arg_index = self._parse_expression(tokens, arg_index + 1, depth + 1)
                if arg_parse is None:
                    return None, index
                args.append(arg_parse)
        if not self._token_is(tokens, arg_index, 'paren_right'):
            return None, index
        return FunctionCall(function, *args), arg_index + 1

    def _parse_variable(self, tokens, index, depth): # pylint: disable = unused-argument
        # type: (list[Token], int, int) -> tuple[Optional[Variable], int]
        #print(depth * '  ' + f'variable@{index}')
        if self._token_is(tokens, index, 'identifier'):
            return Variable(tokens[index].string), index + 1
        else:
            return None, index

    def parse_equation(self, string):
        # type: (str) -> Optional[Equation]
        try:
            tokens = self._tokenize(string)
        except TokenizationError:
            return None
        tokens = [token for token in tokens if token.token_class != 'space']
        parse, index = self._parse_equation(tokens, 0, 0)
        if index != len(tokens):
            return None
        else:
            return parse

    def parse_expression(self, string):
        # type: (str) -> Optional[Expression]
        try:
            tokens = self._tokenize(string)
        except TokenizationError:
            return None
        tokens = [token for token in tokens if token.token_class != 'space']
        parse, index = self._parse_expression(tokens, 0, 0)
        if index != len(tokens):
            return None
        else:
            return parse
