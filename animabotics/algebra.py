"""A computer algebra system.

Both Expressions and Patterns are parsed from S-expression, with the following grammar:

expression = number | variable | function_call_expression;
function_call_expression = "(" function ( expression_arg )* ")";
expression_arg = expression;

pattern = number | variable | function_call_pattern;
function_call_pattern = "(" function ( pattern_arg )* ")";
pattern_arg = pattern | list_variable;

function = identifier | operator;
operator = [+-*/^];
list_variable = "[" identifier "]";
variable = identifier;
number = -?[0-9]+;
identifier = [a-z][a-z0-9_]+;
"""

import re
from collections import namedtuple
from fractions import Fraction
from functools import reduce, lru_cache
from math import prod
from typing import Any, Union, Iterator, Callable
from typing import cast


BuiltInNumber = Union[int, float, Fraction]
ExpressionTuple = tuple['Expression', ...]
Bindings = dict[str, Union['Expression', ExpressionTuple]]


class Pattern:
    """A pattern."""

    def matches(self, expression, bindings):
        # type: (Expression, Bindings) -> Iterator[Bindings]
        """Match this pattern to the expression."""
        raise NotImplementedError()

    def substitute(self, bindings):
        # type: (Bindings) -> Expression
        """Substitute the bindings into this pattern."""
        raise NotImplementedError()


class Expression(Pattern):
    """An expression."""

    def __neg__(self):
        # type: (Any) -> Any
        return FunctionCallExpression(Function('-'), self)

    def __add__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCallExpression(Function('+'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCallExpression)):
            return FunctionCallExpression(Function('+'), self, other)
        if hasattr(other, '__radd__'):
            return other.__radd__(self)
        else:
            return FunctionCallExpression(Function('+'), self, other)

    def __radd__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) + self
        else:
            raise TypeError(f'unsupported operand type(s) for +: {type(other)} and {type(self)}')

    def __sub__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCallExpression(Function('-'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCallExpression)):
            return FunctionCallExpression(Function('-'), self, other)
        if hasattr(other, '__rsub__'):
            return other.__rsub__(self)
        else:
            return FunctionCallExpression(Function('-'), self, other)

    def __rsub__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) - self
        else:
            raise TypeError(f'unsupported operand type(s) for -: {type(other)} and {type(self)}')

    def __mul__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCallExpression(Function('*'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCallExpression)):
            return FunctionCallExpression(Function('*'), self, other)
        if hasattr(other, '__rmul__'):
            return other.__rmul__(self)
        else:
            return FunctionCallExpression(Function('*'), self, other)

    def __rmul__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) * self
        else:
            raise TypeError(f'unsupported operand type(s) for *: {type(other)} and {type(self)}')

    def __truediv__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCallExpression(Function('/'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCallExpression)):
            return FunctionCallExpression(Function('/'), self, other)
        if hasattr(other, '__rtruediv__'):
            return other.__rtruediv__(self)
        else:
            return FunctionCallExpression(Function('/'), self, other)

    def __rtruediv__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) / self
        else:
            raise TypeError(f'unsupported operand type(s) for /: {type(other)} and {type(self)}')

    def __pow__(self, other):
        # type: (Any) -> Any
        if isinstance(other, (int, float, Fraction)):
            return FunctionCallExpression(Function('^'), self, Number(other))
        if isinstance(other, (Number, Variable, FunctionCallExpression)):
            return FunctionCallExpression(Function('^'), self, other)
        if hasattr(other, '__rpow__'):
            return other.__rpow__(self)
        else:
            return FunctionCallExpression(Function('^'), self, other)

    def __rpow__(self, other):
        # type: (BuiltInNumber) -> Any
        if isinstance(other, (int, float, Fraction)):
            return Number(other) ** self
        else:
            raise TypeError(f'unsupported operand type(s) for **: {type(other)} and {type(self)}')

    def evaluate(self):
        # type: () -> Any
        """Evaluate this expression."""
        raise NotImplementedError()


class Number(Expression):
    """A number."""

    def __init__(self, value):
        # type: (BuiltInNumber) -> None
        super().__init__()
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

    def __str__(self):
        # type: () -> str
        if self.value.is_integer():
            return str(self.value.numerator)
        else:
            return f'(/ {self.value.numerator} {self.value.denominator})'

    def __repr__(self):
        # type: () -> str
        return f'Number({self.value})'

    def evaluate(self):
        # type: () -> BuiltInNumber
        return self.value

    def matches(self, expression, bindings):
        # type: (Expression, Bindings) -> Iterator[Bindings]
        if isinstance(expression, Number) and expression.value == self.value:
            yield bindings

    def substitute(self, _):
        # type: (Bindings) -> Number
        return self


class Variable(Expression):
    """A variable."""

    def __init__(self, name):
        # type: (str) -> None
        super().__init__()
        self.name = name

    def __hash__(self):
        # type: () -> int
        return hash(self.name)

    def __eq__(self, other):
        # type: (Any) -> bool
        return isinstance(other, Variable) and self.name == other.name

    def __str__(self):
        # type: () -> str
        return self.name

    def evaluate(self):
        # type: () -> Any
        raise ValueError(f'Unbound variable {self.name}.')

    def matches(self, expression, bindings):
        # type: (Expression, Bindings) -> Iterator[Bindings]
        if self.name not in bindings:
            yield {**bindings, self.name: expression}
        elif bindings[self.name] == expression:
            yield bindings

    def substitute(self, bindings):
        # type: (Bindings) -> Expression
        if self.name in bindings:
            value = bindings[self.name]
            if isinstance(value, (int, Fraction)):
                return Number(value)
            if not isinstance(value, Expression):
                raise ValueError(' '.join([
                    f'expected variable {self.name} to be an Expression,',
                    f'but got a {type(value).__name__}: {value}',
                ]))
            return value
        else:
            return self


class ListVariable(Pattern):
    """A list variable."""

    def __init__(self, name):
        # type: (str) -> None
        super().__init__()
        self.name = name

    def __hash__(self):
        # type: () -> int
        return hash(self.name)

    def __eq__(self, other):
        # type: (Any) -> bool
        return isinstance(other, ListVariable) and self.name == other.name

    def __str__(self):
        # type: () -> str
        return f'[{self.name}]'

    def matches(self, expression, bindings):
        # type: (Expression, Bindings) -> Iterator[Bindings]
        assert False

    def substitute(self, bindings):
        # type: (Bindings) -> Expression
        assert False


EvaluatableFunction = Callable[[*tuple[BuiltInNumber, ...]], BuiltInNumber]
_FUNCTION_REGISTRY = {} # type: dict[str, EvaluatableFunction]


def _register(*extra_names):
    # type: (*str) -> Callable[[EvaluatableFunction], EvaluatableFunction]

    def wrapped(func: EvaluatableFunction) -> EvaluatableFunction:
        names = [func.__name__.strip('_'), *extra_names]
        for name in names:
            assert name not in _FUNCTION_REGISTRY
            _FUNCTION_REGISTRY[name] = func
        return func

    return wrapped


class Function(Expression):
    """A function."""

    TAYLOR_TERMS = 10

    def __init__(self, name):
        # type: (str) -> None
        super().__init__()
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

    def __repr__(self):
        # type: () -> str
        return f'Function({self.name})'

    def evaluate(self):
        # type: () -> EvaluatableFunction
        if self.name in _FUNCTION_REGISTRY:
            return _FUNCTION_REGISTRY[self.name]
        else:
            raise ValueError(f'unknown function "{self.name}()"')

    def matches(self, expression, bindings):
        # type: (Expression, Bindings) -> Iterator[Bindings]
        if isinstance(expression, Function) and expression.name == self.name:
            yield bindings

    def substitute(self, _):
        # type: (Bindings) -> Function
        return self

    @_register()
    @staticmethod
    def _e(*_):
        # type: (*BuiltInNumber) -> BuiltInNumber
        return Fraction(
            27182818284590452353602874713526,
            10000000000000000000000000000000,
        )

    @_register()
    @staticmethod
    def _pi(*_):
        # type: (*BuiltInNumber) -> BuiltInNumber
        return Fraction(
            31415926535897932384626433832795,
            10000000000000000000000000000000,
        )

    @_register('+')
    @staticmethod
    def _sum(*terms):
        # type: (*BuiltInNumber) -> BuiltInNumber
        if len(terms) == 0:
            raise ValueError('operator + must have at least one argument; got zero')
        if len(terms) == 1:
            return terms[0]
        return reduce((lambda x, y: x + y), terms)

    @_register('-')
    @staticmethod
    def _negate(*terms):
        # type: (*BuiltInNumber) -> BuiltInNumber
        if len(terms) == 0:
            raise ValueError('operator - must have at least one argument; got zero')
        if len(terms) == 1:
            return -terms[0]
        return reduce((lambda x, y: x - y), terms)

    @_register('*')
    @staticmethod
    def _product(*terms):
        # type: (*BuiltInNumber) -> BuiltInNumber
        if len(terms) == 0:
            raise ValueError('operator * must have at least one argument; got zero')
        if len(terms) == 1:
            return terms[0]
        return reduce((lambda x, y: x * y), terms)

    @_register('/')
    @staticmethod
    def _inverse(*terms):
        # type: (*BuiltInNumber) -> BuiltInNumber
        if len(terms) == 0:
            raise ValueError('operator / must have at least one argument; got zero')
        if len(terms) == 1:
            if isinstance(terms[0], int):
                return Fraction(1, terms[0])
            else:
                return 1 / terms[0]
        return reduce((lambda x, y: x / y), terms)

    @_register('^')
    @staticmethod
    def _exponentiate(*terms):
        # type: (*BuiltInNumber) -> BuiltInNumber
        if len(terms) < 2:
            raise ValueError('operator ^ must have at least two arguments; got zero')
        return reduce((lambda x, y: x ** y), terms)

    @_register()
    @staticmethod
    def _fact(*terms):
        # type: (*BuiltInNumber) -> BuiltInNumber
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
        # type: (*BuiltInNumber) -> BuiltInNumber
        assert len(terms) == 1
        theta = terms[0]
        return sum(
            (
                Fraction(
                    ((-1) ** n) * theta**(2 * n + 1),
                    int(Function._fact(2 * n + 1)),
                )
                for n in range(Function.TAYLOR_TERMS)
            ),
            start=Fraction(0),
        )

    @_register()
    @staticmethod
    def _cos(*terms):
        # type: (*BuiltInNumber) -> BuiltInNumber
        assert len(terms) == 1
        theta = terms[0]
        return sum(
            (
                Fraction(
                    ((-1) ** n) * theta**(2 * n),
                    int(Function._fact(2 * n )),
                )
                for n in range(Function.TAYLOR_TERMS)
            ),
            start=Fraction(0),
        )


class FunctionCallPattern(Pattern):
    """A function call."""

    def __init__(self, head, *args):
        # type: (Function, *Pattern) -> None
        self.head = head
        self.args = args

    def __hash__(self):
        # type: () -> int
        return hash((self.head, *self.args))

    def __eq__(self, other):
        # type: (Any) -> bool
        return (
            isinstance(other, type(self))
            and self.head == other.head
            and self.args == other.args
        )

    def __str__(self):
        # type: () -> str
        return f'({self.head} {" ".join(str(arg) for arg in self.args)})'

    def __repr__(self):
        # type: () -> str
        return f'FunctionCallPattern({self.head}, {", ".join(repr(arg) for arg in self.args)})'

    def matches(self, expression, bindings):
        # type: (Expression, Bindings) -> Iterator[Bindings]
        if not isinstance(expression, FunctionCallExpression):
            return
        assert isinstance(expression, FunctionCallExpression)
        bindings_list = list(self.head.matches(expression.head, bindings))
        if not bindings_list:
            return
        assert len(bindings_list) == 1
        yield from self._matches(self.args, expression.args, bindings_list[0])

    def _matches(self, patterns, expressions, bindings):
        # type: (tuple[Pattern, ...], tuple[Expression, ...], Bindings) -> Iterator[Bindings]
        if not patterns and expressions:
            # base case: no more patterns to match, but expressions remaining
            return
        elif not patterns and not expressions:
            # base case: both patterns and expressions are exhausted
            yield bindings
        elif isinstance(patterns[0], ListVariable):
            # recursive case: first pattern is a ListVariable
            for i in range(len(expressions) + 1):
                yield from self._matches(
                    patterns[1:],
                    expressions[i:],
                    {
                        patterns[0].name: expressions[:i],
                        **bindings,
                    },
                )
        else:
            # recursive case: first pattern is not a ListVariable
            if not expressions:
                return
            for new_bindings in patterns[0].matches(expressions[0], bindings):
                yield from self._matches(patterns[1:], expressions[1:], new_bindings)

    def substitute(self, bindings):
        # type: (Bindings) -> Expression
        new_head = self.head.substitute(bindings)
        new_args = [] # type: list[Expression]
        for arg in self.args:
            if isinstance(arg, ListVariable):
                if arg.name not in bindings:
                    # unbound list variables are not allowed, in order to return an Expression
                    # FIXME note discrepancy with non-list variables
                    raise ValueError(f'variable {arg.name} not bound')
                values = bindings[arg.name]
                if not isinstance(values, tuple): # FIXME deeper type check
                    raise ValueError(' '.join([
                        f'expected variable {arg.name} to be a tuple of Expressions,',
                        f'but got a {type(values).__name__}: {values}',
                    ]))
                # FIXME allow for int and Fraction in the tuple
                new_args.extend(value for value in values)
            else:
                new_args.append(arg.substitute(bindings))
        return FunctionCallExpression(new_head, *new_args)


class FunctionCallExpression(FunctionCallPattern, Expression):
    """A function call (expression)."""

    def __init__(self, head, *args):
        # type: (Function, *Expression) -> None
        super().__init__(head, *args)
        self.args = args # type: tuple[Expression, ...]

    def __repr__(self):
        # type: () -> str
        return f'FunctionCallExpression({self.head}, {", ".join(repr(arg) for arg in self.args)})'

    def evaluate(self):
        # type: () -> BuiltInNumber
        return self.head.evaluate()(*(arg.evaluate() for arg in self.args))



_TOKEN_REGEXES = {
    'space': re.compile(' +'),
    'number': re.compile('-?[0-9]+'),
    'identifier': re.compile('[A-Za-z][0-9A-Za-z_]*'),
    'operator': re.compile('[+*/^-]'),
    'equal': re.compile('='),
    'paren_left': re.compile(r'\('),
    'paren_right': re.compile(r'\)'),
    'bracket_left': re.compile(r'\['),
    'bracket_right': re.compile(r'\]'),
}


Token = namedtuple('Token', 'token_class, string, index')


def _tokenize(string):
    # type: (str) -> list[Token]
    tokens = []
    index = 0
    while index < len(string):
        match = None
        for token_class, regex in _TOKEN_REGEXES.items():
            if match := regex.match(string, pos=index):
                tokens.append(Token(token_class, match.group(), index))
                break
        if match is None:
            return None
        index += len(match.group())
    assert index == len(string)
    return tokens


def _token_is(tokens, index, token_class):
    # type: (list[Token], int, str) -> bool
    return index < len(tokens) and tokens[index].token_class == token_class


def _parse_number(tokens, index):
    # type: (list[Token], int) -> tuple[Number, int]
    if _token_is(tokens, index, 'number'):
        return Number(Fraction(tokens[index].string)), index + 1
    else:
        return None, index


def _parse_variable(tokens, index):
    # type: (list[Token], int) -> tuple[Variable, int]
    if _token_is(tokens, index, 'identifier'):
        return Variable(tokens[index].string), index + 1
    else:
        return None, index


def _parse_function(tokens, index):
    # type: (list[Token], int) -> tuple[Function, int]
    if _token_is(tokens, index, 'identifier'):
        return Function(tokens[index].string), index + 1
    if _token_is(tokens, index, 'operator'):
        return Function(tokens[index].string), index + 1
    else:
        return None, index


def _parse_list_variable(tokens, index):
    # type: (list[Token], int) -> tuple[ListVariable, int]
    if not _token_is(tokens, index, 'bracket_left'):
        return None, index
    parse, new_index = _parse_variable(tokens, index + 1)
    if parse is None:
        return None, index
    if not _token_is(tokens, new_index, 'bracket_right'):
        return None, index
    return ListVariable(parse.name), new_index + 1


def _parse_function_call_expression(tokens, index):
    # type: (list[Token], int) -> tuple[FunctionCallExpression, int]
    if not _token_is(tokens, index, 'paren_left'):
        return None, index
    head, arg_index = _parse_function(tokens, index + 1)
    if head is None:
        return None, index
    args = []
    while arg_index < len(tokens):
        arg_parse, arg_index = _parse_expression(tokens, arg_index)
        if arg_parse is None:
            break
        args.append(arg_parse)
    if not _token_is(tokens, arg_index, 'paren_right'):
        return None, index
    return FunctionCallExpression(head, *args), arg_index + 1


def _parse_expression(tokens, index):
    # type: (list[Token], int) -> tuple[Expression, int]
    parse = None # type: Expression
    parse, new_index = _parse_function_call_expression(tokens, index)
    if parse is not None:
        return parse, new_index
    parse, new_index = _parse_variable(tokens, index)
    if parse is not None:
        return parse, new_index
    parse, new_index = _parse_number(tokens, index)
    if parse is not None:
        return parse, new_index
    return None, index


def _parse_function_call_pattern(tokens, index):
    # type: (list[Token], int) -> tuple[FunctionCallPattern, int]
    if not _token_is(tokens, index, 'paren_left'):
        return None, index
    head, arg_index = _parse_function(tokens, index + 1)
    if head is None:
        return None, index
    args = []
    while arg_index < len(tokens):
        arg_parse, arg_index = _parse_pattern(tokens, arg_index, listvar=True)
        if arg_parse is None:
            break
        args.append(arg_parse)
    if not _token_is(tokens, arg_index, 'paren_right'):
        return None, index
    return FunctionCallPattern(head, *args), arg_index + 1


def _parse_pattern(tokens, index, listvar=False):
    # type: (list[Token], int, bool) -> tuple[Pattern, int]
    parse = None # type: Pattern
    parse, new_index = _parse_function_call_pattern(tokens, index)
    if parse is not None:
        return parse, new_index
    parse, new_index = _parse_variable(tokens, index)
    if parse is not None:
        return parse, new_index
    parse, new_index = _parse_number(tokens, index)
    if parse is not None:
        return parse, new_index
    if listvar:
        parse, new_index = _parse_list_variable(tokens, index)
        if parse is not None:
            return parse, new_index
    return None, index


def parse_expression(string):
    # type: (str) -> Expression
    """Parse an S-expression as an expression."""
    tokens = _tokenize(string)
    if tokens is None:
        raise ValueError(f'tokenization error: {string}')
    tokens = [token for token in tokens if token.token_class != 'space']
    parse, index = _parse_expression(tokens, 0)
    if parse is None or index != len(tokens):
        raise ValueError(f'parsing error: {string}')
    return parse


def parse_pattern(string):
    # type: (str) -> Pattern
    """Parse an S-expression as a pattern."""
    tokens = _tokenize(string)
    if tokens is None:
        raise ValueError(f'tokenization error: {string}')
    tokens = [token for token in tokens if token.token_class != 'space']
    parse, index = _parse_pattern(tokens, 0)
    if parse is None or index != len(tokens):
        raise ValueError(f'parsing error: {string}')
    return parse


ConditionsFunction = Callable[['RewriteRule', Expression, Bindings], bool]
ResultsFunction = Callable[['RewriteRule', Expression, Bindings], Bindings]


def _true(_1, _2, _3):
    # type: (RewriteRule, Expression, Bindings) -> bool
    return True


def _identity(_1, _2, bindings):
    # type: (RewriteRule, Expression, Bindings) -> Bindings
    return bindings


class RewriteRule:
    """A rewrite rule."""

    def __init__(self, before, after, condition=None, results=None):
        # type: (str|Pattern, str|Pattern, ConditionsFunction, ResultsFunction) -> None
        if isinstance(before, str):
            self.before = parse_pattern(before)
        else:
            self.before = before
        if isinstance(after, str):
            self.after = parse_pattern(after)
        else:
            self.after = after
        if condition is None:
            self.condition = _true # type: ConditionsFunction
        else:
            self.condition = condition
        if results is None:
            self.results = _identity # type: ResultsFunction
        else:
            self.results = results

    def apply_all_no_recur(self, expression):
        # type: (Expression) -> Expression
        """Apply the rule at the top level exhaustively."""
        while True:
            bindings = None
            for new_bindings in self.before.matches(expression, {}):
                if self.condition(self, expression, new_bindings):
                    bindings = new_bindings
                    break
            if bindings is None:
                break
            expression = self.after.substitute({
                **bindings,
                **self.results(self, expression, bindings),
            })
        return expression

    def apply_all(self, expression):
        # type: (Expression) -> Expression
        """Apply the rule exhaustively and recursively."""
        # apply first to prune applications later
        expression = self.apply_all_no_recur(expression)
        # apply recursively
        if isinstance(expression, FunctionCallExpression):
            expression = FunctionCallExpression(
                expression.head,
                *(
                    self.apply_all(subexpression)
                    for subexpression in expression.args
                ),
            )
        # apply again
        return self.apply_all_no_recur(expression)


def abelian_rules(operation, inverse, identity):
    # type: (str, str, str) -> tuple[RewriteRule, ...]
    """Generate rewrite rules for abelian groups."""
    return (
        # unwrap
        RewriteRule(f'({operation})', identity),
        RewriteRule(f'({operation} x)', 'x'),
        RewriteRule(f'({inverse} x {identity})', 'x'),
        # remove identity
        RewriteRule(f'({operation} [a] {identity} [b])', f'({operation} [a] [b])'),
        # force inverse to have arity 2
        RewriteRule(
            f'({inverse} x)',
            f'({inverse} {identity} x)',
        ),
        RewriteRule(
            f'({inverse} a b c [d])',
            f'({inverse} a ({operation} b c [d]))',
        ),
        # flatten/disassociate
        RewriteRule(
            f'({operation} [a] ({operation} [b]) [c])',
            f'({operation} [a] [b] [c])',
        ),
        RewriteRule(
            f'({operation} [a] ({inverse} b c) [d])',
            f'({inverse} ({operation} [a] b [d]) c)',
        ),
        RewriteRule(
            f'({inverse} a ({inverse} b c))',
            f'({inverse} ({operation} a c) b)',
        ),
        RewriteRule(
            f'({inverse} ({inverse} a b) c)',
            f'({inverse} a ({operation} b c))',
        ),
        # cancellation
        RewriteRule(
            f'({inverse} x x)',
            identity,
        ),
        RewriteRule(
            f'({inverse} ({operation} [a] x [b]) x)',
            f'({operation} [a] [b])',
        ),
        RewriteRule(
            f'({inverse} x ({operation} [a] x [b]))',
            f'({inverse} {identity} ({operation} [a] [b]))',
        ),
        RewriteRule(
            f'({inverse} ({operation} [a] x [b]) ({operation} [c] x [d]))',
            f'({inverse} ({operation} [a] [b]) ({operation} [c] [d]))',
        ),
    )


SIMPLIFICATION_RULESET = (
    # remove negatives
    RewriteRule(
        'a',
        ('(- 0 b)'),
        condition=(lambda rule, expression, bindings:
            isinstance(bindings['a'], Number)
            and bindings['a'].value < 0
        ),
        results=(lambda rule, expression, bindings: {
            'b': Number(abs(cast(Number, bindings['a']).value)),
        }),
    ),
    # fold constants
    RewriteRule(
        '(+ [terms])',
        '(+ number [non_numbers])',
        condition=(lambda rule, expression, bindings:
            sum(1 for term in cast(ExpressionTuple, bindings['terms']) if isinstance(term, Number)) > 1
        ),
        results=(lambda rule, expression, bindings: {
            'number': Number(sum(
                term.value for term in cast(ExpressionTuple, bindings['terms'])
                if isinstance(term, Number)
            )),
            'non_numbers': tuple(
                term for term in cast(ExpressionTuple, bindings['terms'])
                if not isinstance(term, Number)
            ),
        }),
    ),
    RewriteRule(
        '(* [terms])',
        '(* number [non_numbers])',
        condition=(lambda rule, expression, bindings:
            sum(1 for term in cast(ExpressionTuple, bindings['terms']) if isinstance(term, Number)) > 1
        ),
        results=(lambda rule, expression, bindings: {
            'number': Number(prod(
                term.value for term in cast(ExpressionTuple, bindings['terms'])
                if isinstance(term, Number)
            )),
            'non_numbers': tuple(
                term for term in cast(ExpressionTuple, bindings['terms'])
                if not isinstance(term, Number)
            ),
        }),
    ),
    # reduce the zero product
    RewriteRule('(* [a] 0 [b])', '0'),
    RewriteRule('(/ 0 [a])', '0'),
    # double negatives
    RewriteRule(
        '(* [a] (- 0 x) [b] (- 0 y) [c])',
        '(* [a] x [b] y [c])',
    ),
    RewriteRule(
        '(/ (- 0 x) (- 0 y))',
        '(/ x y)',
    ),
    # share denominators
    RewriteRule(
        '(+ [a] (/ b c) [d] (/ e c) [f])',
        '(+ (/ (+ b e) c) [a] [d] [f])',
    ),
    RewriteRule(
        '(- (/ a b) (/ c b))',
        '(/ (- a c) b)',
    ),
    # distribute
    RewriteRule(
        '(* [a] (+ [b]) [c])',
        '(+ [d])',
        results=(lambda rule, expression, bindings: {
            'd': tuple(
                FunctionCallExpression(
                    Function('*'),
                    *cast(ExpressionTuple, bindings['a']),
                    expression,
                    *cast(ExpressionTuple, bindings['c']),
                )
                for expression in cast(ExpressionTuple, bindings['b'])
            ),
        }),
    ),
    RewriteRule(
        '(* [a] (- b c) [d])',
        '(- (* [a] b [d]) (* [a] c [d]))',
    ),
    RewriteRule(
        '(/ (- 0 a) b)',
        '(- 0 (/ a b))',
    ),
    RewriteRule(
        '(/ a (- 0 b))',
        '(- 0 (/ a b))',
    ),
    # FIXME these should be part of a search instead
    RewriteRule(
        '(/ (* [a] b [c]) (+ (* [d] b [e]) (* [f] b [g])))',
        '(/ (* [a] [c]) (+ (* [d] [e]) (* [f] [g])))',
    ),
    # generic abelian group rules
    *abelian_rules('+', '-', '0'),
    *abelian_rules('*', '/', '1'),
)


@lru_cache(maxsize=2**20)
def simplify(expression):
    # type: (Expression) -> Expression
    """Simplify an algebraic expression."""
    for rule in SIMPLIFICATION_RULESET:
        expression = rule.apply_all_no_recur(expression)
    if isinstance(expression, FunctionCallExpression):
        expression = FunctionCallExpression(
            expression.head,
            *(simplify(term) for term in expression.args),
        )
    old_expression = None
    while old_expression != expression:
        old_expression = expression
        for rule in SIMPLIFICATION_RULESET:
            expression = rule.apply_all(expression)
    return expression
