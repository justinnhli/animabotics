"""The Color class."""

from collections.abc import Iterator
from dataclasses import dataclass

from ._okhsv import RGB as _RGB, HSV as _HSV
from ._okhsv import okhsv_to_rgb as _okhsv_to_rgb, rgb_to_okhsv as _rgb_to_okhsv
from .metaprogramming import CachedMetaclass


@dataclass(frozen=True, order=True)
class Color(metaclass=CachedMetaclass):
    """A color, canonically represented as in OkHSVA."""
    # pylint: disable = invalid-name
    h: float = 0
    s: float = 0
    v: float = 0
    a: float = 1

    MAX_H = 360
    MAX_S = 100
    MAX_V = 100
    MAX_A = 256

    def __iter__(self):
        # type: () -> Iterator[float]
        yield from self.to_hsva_tuple()

    def to_hsva_tuple(self, integer=True):
        # type: (bool) -> tuple[float, float, float, float]
        """Convert the color to a HSVA tuple."""
        if integer:
            return (
                round(Color.MAX_H * self.h),
                round(Color.MAX_S * self.s),
                round(Color.MAX_V * self.v),
                round(Color.MAX_A * self.a),
            )
        else:
            return (self.h, self.s, self.v, self.a)

    def to_rgb_tuple(self, integer=True):
        # type: (bool) -> tuple[float, float, float]
        """Convert the color to a RGBA tuple."""
        return self.to_rgba_tuple(integer)[:3]

    def to_rgba_tuple(self, integer=True):
        # type: (bool) -> tuple[float, float, float, float]
        """Convert the color to a RGB tuple."""
        rgba = (*_okhsv_to_rgb(_HSV(self.h, self.s, self.v)), self.a)
        if integer:
            return (
                min(round(256 * rgba[0]), 255),
                min(round(256 * rgba[1]), 255),
                min(round(256 * rgba[2]), 255),
                min(round(256 * rgba[3]), 255),
            )
        else:
            return rgba

    def to_rgb_hex(self):
        # type: () -> str
        """Convert the color to a RGB hexcode."""
        return self.to_rgba_hex()[:7]

    def to_rgba_hex(self):
        # type: () -> str
        """Convert the color to a RGBA hexcode."""
        return '#' + ''.join(
            f'{n:02X}' for n in self.to_rgba_tuple(integer=True)
        )

    @staticmethod
    def from_rgba(r, g, b, a=1):
        # type: (float, float, float, float) -> Color
        """Create a color from RGB[A] values."""
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1
        assert 0 <= a <= 1
        h, s, v = _rgb_to_okhsv(_RGB(r, g, b))
        return Color(
            min(h, 1),
            min(s, 1),
            min(v, 1),
            min(a, 1),
        )

    @staticmethod
    def from_hex(hexcode):
        # type: (str) -> Color
        """Create a color from a RGB[A] hexcode."""
        return Color.from_rgba(*(
            int(hexcode[i:i+2], 16) / 256
            for i in range(1, len(hexcode) - 1, 2)
        ))
