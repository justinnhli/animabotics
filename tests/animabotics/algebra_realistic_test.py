"""Test symbolic algebra in realistic conditions."""

# pylint: disable = import-outside-toplevel

import math
from contextlib import contextmanager
from functools import partial
from importlib import import_module
from os import environ
from pathlib import Path
from subprocess import run, CalledProcessError


VENV = 'animabotics'


def run_test(test_name):
    # type: (str) -> None
    """Run a test via a subprocess.

    This gets around Python import weirdness.
    """
    venv_python = Path(environ['PYTHON_VENV_HOME'], VENV, 'bin', 'python3').expanduser()
    if not venv_python.exists():
        raise FileNotFoundError(f'could not find venv "{VENV}" executable {venv_python}')
    try:
        run(
            [
                str(venv_python),
                '-c', 
                ' '.join([
                    f'from tests.animabotics.algebra_realistic_test import {test_name};',
                    f'{test_name}();',
                ]),
            ],
            check=True,
        )
    except CalledProcessError:
        assert False, f'failed to run {__name__}::{test_name}'


@contextmanager
def symbolic_math_builtins(*functions):
    # type: (*str) -> None
    """Create a context where math functions are replaced with symbolic versions.

    NOTE: this context must be used _before_ the math module is imported.
    """

    def wrap(name, x):
        is_symbolic = (
            ('animabotics.algebra', 'Expression')
            in ((t.__module__, t.__name__) for t in type(x).mro())
        )
        if is_symbolic:
            return import_module('animabotics').algebra.parse_expression(f'({name} {x})')
        else:
            return x

    if not functions:
        functions = ('sqrt', 'sin', 'cos')
    originals = {}
    for name in functions:
        originals[name] = getattr(math, name)
        setattr(
            math,
            name,
            partial(wrap, name),
        )
    try:
        yield
    finally:
        for name, original in originals.items():
            setattr(math, name, original)


def _test_project_point_to_vector():
    # type: () -> None
    """Test algebra with point to vector projection."""
    with symbolic_math_builtins():
        from animabotics.algebra import Variable, simplify, parse_expression
        from animabotics import Point2D, Vector2D

        origin = Point2D(0, 0)
        vector = Vector2D(Variable('Vx'), Variable('Vy'))
        point = Point2D(Variable('Px'), Variable('Py'))

        angled = point - origin
        scale = vector.matrix.dot(angled.matrix) / vector.matrix.dot(vector.matrix)
        magnitude = scale * vector.magnitude

        # note: since sqrt(x)/x == 1/sqrt(x), the answer could be further simplified as
        # (Vx * Px + Vy * Py) / ((Vx^2 + Vy^2) ^ (1/2))
        expect = '''
            (/
                (+
                    (* Px Vx (sqrt (+ (* Vx Vx) (* Vy Vy))))
                    (* Py Vy (sqrt (+ (* Vx Vx) (* Vy Vy)))))
                (+ (* Vx Vx) (* Vy Vy)))
        '''.strip().replace('\n', ' ')

        actual = simplify(magnitude)
        assert actual == parse_expression(expect), str(actual)


def test_project_point_to_vector():
    """Wrapper around _test_project_point_to_vector()."""
    run_test('_test_project_point_to_vector')
