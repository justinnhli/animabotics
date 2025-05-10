"""Symbolic algebra."""

import re
from fractions import Fraction
from typing import Any, Optional, Union


BuiltInNumber = Union[int, float, Fraction]


class SymbolicMath:
    pass


class Expression(SymbolicMath):

    def __neg__(self):
        # type: (Any) -> Any
        return FunctionCall('-', self)

    def __add__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall('+', self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall('+', self, other)
        if hasattr(other, '__radd__'):
            return other.__radd__(self)
        else:
            return FunctionCall('+', self, other)

    def __radd__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) + self
        else:
            raise TypeError(f'unsupported operand type(s) for +: {type(other)} and {type(self)}')

    def __sub__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall('+', self, Number(-other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall('+', self, FunctionCall('-', other))
        if hasattr(other, '__rsub__'):
            return other.__rsub__(self)
        else:
            return FunctionCall('-', self, other)

    def __rsub__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) - self
        else:
            raise TypeError(f'unsupported operand type(s) for -: {type(other)} and {type(self)}')

    def __mul__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall('*', self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall('*', self, other)
        if hasattr(other, '__rmul__'):
            return other.__rmul__(self)
        else:
            return FunctionCall('*', self, other)

    def __rmul__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) * self
        else:
            raise TypeError(f'unsupported operand type(s) for *: {type(other)} and {type(self)}')

    def __truediv__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall('*', self, FunctionCall('/', Number(other)))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall('*', self, FunctionCall('/', other))
        if hasattr(other, '__rtruediv__'):
            return other.__rtruediv__(self)
        else:
            return FunctionCall('/', self, other)

    def __rtruediv__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) / self
        else:
            raise TypeError(f'unsupported operand type(s) for /: {type(other)} and {type(self)}')

    def __pow__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCall('^', self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCall)):
            return FunctionCall('^', self, other)
        if hasattr(other, '__rpow__'):
            return other.__rpow__(self)
        else:
            return FunctionCall('^', self, other)

    def __rpow__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) ** self
        else:
            raise TypeError(f'unsupported operand type(s) for **: {type(other)} and {type(self)}')


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


class Function(Expression):

    def __init__(self, name):
        # type: (str) -> None
        self.name = name

    def __hash__(self):
        # type: () -> int
        return hash(self.name)

    def __eq__(self, other):
        # type: (Any) -> bool
        return isinstance(other, Function) and self.name == other.name

    def __str__(self):
        # type: () -> str
        return self.name

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return self.name


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


class FunctionCall(Expression):

    OPPOSITES = {
        '+': '-',
        '-': '+',
        '*': '/',
        '/': '*',
    }

    def __init__(self, function, *args):
        # type: (str, *Expression) -> None
        self.function = function
        self.args = args # type: tuple[Expression, ...]
        if self.function in '-/':
            assert len(self.args) == 1
        if self.function == 'sqrt':
            assert len(self.args) == 1
            self.function = '^'
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
        if self.function not in '+-*/':
            return f'{self.function}(' + ', '.join(str(arg) for arg in self.args) + ')'
        if self.function in '+*' and len(self.args) == 1:
            return str(self.args[0])
        if self.function == '-':
            # always unary
            return f'-{self.args[0]}'
        result = [str(self.args[0])]
        for arg in self.args[1:]:
            if isinstance(arg, FunctionCall) and arg.function == FunctionCall.OPPOSITES.get(self.function):
                result.append(f'{arg.function} {arg.args[0]}')
            else:
                result.append(f'{self.function} {arg}')
        return '(' + ' '.join(result) + ')'

    def __repr__(self): # pragma: no cover
        # type: () -> str
        return f'({self.function}' + ''.join(f' {repr(arg)}' for arg in self.args) + ')'


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


class AlgebraParser:

    '''
    equation = add_exp "=" add_exp;
    add_exp = mul_exp ( [+-] mul_exp )*;
    mul_exp = pow_exp ( [*/] pow_exp )*;
    pow_exp = term ( [^] term )*;
    term = number
         | variable
         | function
         | parenthesis;
    operator = [+-*/];
    number = [0-9]+;
    variable = [a-z][a-z0-9_]+;
    function = "(" [a-z][a-z0-9_]+ ( "," add_exp )* ")";
    parenthesis = "(" add_exp ")";
    '''

    def _parse_equation(self, string, index, depth):
        # type: (str, int, int) -> tuple[Optional[Equation], int]
        exp1_parse, exp1_index = self._parse_add_exp(string, index, depth + 1)
        if exp1_parse is None:
            return None, index
        if string[exp1_index] != '=':
            return None, index
        exp2_parse, exp2_index = self._parse_add_exp(string, exp1_index + 1, depth + 1)
        if exp2_parse is None:
            return None, index
        return Equation(exp1_parse, exp2_parse), exp2_index

    def _parse_add_exp(self, string, index, depth):
        # type: (str, int, int) -> tuple[Optional[Expression], int]
        result_parse, result_index = self._parse_mul_exp(string, index, depth + 1)
        if result_parse is None:
            return None, index
        while result_index < len(string):
            if string[result_index] not in '+-':
                break
            term_parse, term_index = self._parse_mul_exp(string, result_index + 1, depth + 1)
            if term_parse is None:
                break
            if string[result_index] == '-':
                term_parse = FunctionCall('-', term_parse)
            result_parse = FunctionCall('+', result_parse, term_parse)
            result_index = term_index
        return result_parse, result_index

    def _parse_mul_exp(self, string, index, depth):
        # type: (str, int, int) -> tuple[Optional[Expression], int]
        result_parse, result_index = self._parse_pow_exp(string, index, depth + 1)
        if result_parse is None:
            return None, index
        while result_index < len(string):
            if string[result_index] not in '*/':
                break
            term_parse, term_index = self._parse_pow_exp(string, result_index + 1, depth + 1)
            if term_parse is None:
                break
            if string[result_index] == '/':
                term_parse = FunctionCall('/', term_parse)
            result_parse = FunctionCall('*', result_parse, term_parse)
            result_index = term_index
        return result_parse, result_index

    def _parse_pow_exp(self, string, index, depth):
        # type: (str, int, int) -> tuple[Optional[Expression], int]
        result_parse, result_index = self._parse_term(string, index, depth + 1)
        if result_parse is None:
            return None, index
        while result_index < len(string):
            if string[result_index] != '^':
                break
            term_parse, term_index = self._parse_term(string, result_index + 1, depth + 1)
            if term_parse is None:
                break
            result_parse = FunctionCall(string[result_index], result_parse, term_parse)
            result_index = term_index
        return result_parse, result_index

    def _parse_term(self, string, index, depth):
        # type: (str, int, int) -> tuple[Optional[Expression], int]
        parse = None # type: Expression
        parse, new_index = self._parse_number(string, index, depth + 1)
        if parse is not None:
            return parse, new_index
        parse, new_index = self._parse_function(string, index, depth + 1)
        if parse is not None:
            return parse, new_index
        parse, new_index = self._parse_variable(string, index, depth + 1)
        if parse is not None:
            return parse, new_index
        parse, new_index = self._parse_parenthesis(string, index, depth + 1)
        if parse is not None:
            return parse, new_index
        return None, index

    def _parse_number(self, string, index, _):
        # type: (str, int, int) -> tuple[Optional[Number], int]
        regex_match = re.match(r'-?[0-9]*\.?[0-9]+', string[index:])
        if regex_match:
            return Number(Fraction(regex_match.group(0))), index + len(regex_match.group(0))
        else:
            return None, index

    def _parse_function(self, string, index, depth):
        # type: (str, int, int) -> tuple[Optional[Expression], int]
        regex_match = re.match('[A-Za-z][0-9A-Za-z_]+', string[index:])
        if not regex_match:
            return None, index
        function = regex_match.group(0)
        new_index = index + len(function)
        if string[new_index] != '(':
            return None, index
        arg_parse, new_index = self._parse_add_exp(string, new_index + 1, depth + 1)
        if arg_parse is None:
            return None, index
        args = [arg_parse]
        while new_index < len(string):
            if string[new_index] not in ',':
                break
            arg_parse, arg_index = self._parse_mul_exp(string, new_index + 1, depth + 1)
            if arg_parse is None:
                break
            args.append(arg_parse)
            new_index = arg_index
        if string[new_index] != ')':
            return None, index
        return FunctionCall(function, *args), new_index + 1

    def _parse_variable(self, string, index, _):
        # type: (str, int, int) -> tuple[Optional[Variable], int]
        regex_match = re.match('[A-Za-z][0-9A-Za-z_]+', string[index:])
        if regex_match:
            length = len(regex_match.group(0))
            return Variable(string[index:index + length]), index + length
        else:
            return None, index

    def _parse_parenthesis(self, string, index, depth):
        # type: (str, int, int) -> tuple[Optional[Expression], int]
        if string[index] != '(':
            return None, index
        parse, new_index = self._parse_add_exp(string, index + 1, depth + 1)
        if parse is None:
            return None, index
        if string[new_index] != ')':
            return None, index
        return parse, new_index + 1

    def parse_equation(self, string):
        # type: (str) -> Optional[Equation]
        string = string.replace(' ', '')
        parse, index = self._parse_equation(string, 0, 0)
        if index != len(string):
            return None
        else:
            return parse

    def parse_expression(self, string):
        # type: (str) -> Optional[Expression]
        string = string.replace(' ', '')
        parse, index = self._parse_add_exp(string, 0, 0)
        if index != len(string):
            return None
        else:
            return parse
