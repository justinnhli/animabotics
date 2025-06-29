#!/usr/bin/env python3

"""Conversions between the RGB and OkHSV color spaces.

Adapted from https://bottosson.github.io/posts/colorpicker/#source-code
"""

# pylint: disable = invalid-name

from math import sqrt, cbrt, sin, cos, atan2, pi as PI
from collections import namedtuple

RGB = namedtuple('RGB', 'r, g, b')
HSV = namedtuple('HSV', 'h, s, v')

_Lab = namedtuple('_Lab', 'l, a, b')
_LC = namedtuple('_LC', 'l, c')
_ST = namedtuple('_ST', 's, t')

_K1 = 0.206
_K2 = 0.03
_K3 = (1 + _K1) / (1 + _K2)


def _rgb_transfer(a):
    # type: (float) -> float
    if .0031308 >= a:
        return 12.92 * a
    else:
        return 1.055 * pow(a, 1 / 2.4) - .055


def _rgb_transfer_inv(a):
    # type: (float) -> float
    if .04045 < a:
        return pow((a + .055) / 1.055, 2.4)
    else:
        return a / 12.92


def _rgb_to_oklab(rgb):
    # type: (RGB) -> _Lab
    l = 0.4122214708 * rgb.r + 0.5363325363 * rgb.g + 0.0514459929 * rgb.b
    m = 0.2119034982 * rgb.r + 0.6806995451 * rgb.g + 0.1073969566 * rgb.b
    s = 0.0883024619 * rgb.r + 0.2817188376 * rgb.g + 0.6299787005 * rgb.b
    l_ = cbrt(l)
    m_ = cbrt(m)
    s_ = cbrt(s)
    return _Lab(
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def _oklab_to_rgb(lab):
    # type: (_Lab) -> RGB
    l_ = lab.l + 0.3963377774 * lab.a + 0.2158037573 * lab.b
    m_ = lab.l - 0.1055613458 * lab.a - 0.0638541728 * lab.b
    s_ = lab.l - 0.0894841775 * lab.a - 1.2914855480 * lab.b
    l = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_
    return RGB(
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def _max_saturation(a, b):
    # type: (float, float) -> float
    # max saturation will be when one of r, g or b goes below zero.
    # select different coefficients depending on which component goes below zero first
    if -1.88170328 * a - 0.80936493 * b > 1:
        # red component
        k0 = +1.19086277
        _k1 = +1.76576728
        _k2 = +0.59662641
        _k3 = +0.75515197
        k4 = +0.56771245
        wl = +4.0767416621
        wm = -3.3077115913
        ws = +0.2309699292
    elif 1.81444104 * a - 1.19445276 * b > 1:
        # green component
        k0 = +0.73956515
        _k1 = -0.45954404
        _k2 = +0.08285427
        _k3 = +0.12541070
        k4 = +0.14503204
        wl = -1.2684380046
        wm = +2.6097574011
        ws = -0.3413193965
    else:
        # blue component
        k0 = +1.35733652
        _k1 = -0.00915799
        _k2 = -1.15130210
        _k3 = -0.50559606
        k4 = +0.00692167
        wl = -0.0041960863
        wm = -0.7034186147
        ws = +1.7076147010
    # approximate max saturation using a polynomial
    S = k0 + _k1 * a + _k2 * b + _k3 * a * a + k4 * a * b
    # do one step Halley's method to get closer
    # this gives an error less than 10e6, except for some blue hues where the dS/dh is close to infinite
    # this should be sufficient for most applications, otherwise do two/three steps
    k_l = +0.3963377774 * a + 0.2158037573 * b
    k_m = -0.1055613458 * a - 0.0638541728 * b
    k_s = -0.0894841775 * a - 1.2914855480 * b

    l_ = 1 + S * k_l
    m_ = 1 + S * k_m
    s_ = 1 + S * k_s

    l = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    l_dS = 3 * k_l * l_ * l_
    m_dS = 3 * k_m * m_ * m_
    s_dS = 3 * k_s * s_ * s_

    l_dS2 = 6 * k_l * k_l * l_
    m_dS2 = 6 * k_m * k_m * m_
    s_dS2 = 6 * k_s * k_s * s_

    f = wl * l + wm * m + ws * s
    f1 = wl * l_dS + wm * m_dS + ws * s_dS
    f2 = wl * l_dS2 + wm * m_dS2 + ws * s_dS2

    return S - f * f1 / (f1 * f1 - 0.5 * f * f2)


def _find_cusp(a, b):
    # type: (float, float) -> _LC
    # first, find the maximum saturation (saturation S = C/L)
    S_cusp = _max_saturation(a, b)
    # convert to linear sRGB to find the first point where at least one of r,g or b >= 1
    rgb_at_max = _oklab_to_rgb(_Lab(1, S_cusp * a, S_cusp * b))
    L_cusp = cbrt(1 / max(rgb_at_max.r, rgb_at_max.g, rgb_at_max.b))
    C_cusp = L_cusp * S_cusp
    return _LC(L_cusp , C_cusp)


def _toe(x):
    # type: (float) -> float
    return 0.5 * (_K3 * x - _K1 + sqrt((_K3 * x - _K1) * (_K3 * x - _K1) + 4 * _K2 * _K3 * x))


def _toe_inv(x):
    # type: (float) -> float
    return (x * x + _K1 * x) / (_K3 * (x + _K2))


def _to_st(lc):
    # type: (_LC) -> _ST
    return _ST(lc.c / lc.l, lc.c / (1 - lc.l))


def okhsv_to_rgb(hsv):
    # type: (HSV) -> RGB
    """Convert OkHSV to RGB."""
    h = hsv.h
    s = hsv.s
    v = hsv.v

    if v == 0:
        return RGB(0, 0, 0)

    a_ = cos(2 * PI * h)
    b_ = sin(2 * PI * h)

    cusp = _find_cusp(a_, b_)
    ST_max = _to_st(cusp)
    S_max = ST_max.s
    T_max = ST_max.t
    S_0 = 0.5
    k = 1 - S_0 / S_max

    # first we compute L and V as if the gamut is a perfect triangle

    # L, C when v == 1
    L_v = 1 - s * S_0 / (S_0 + T_max - T_max * k * s)
    C_v = s * T_max * S_0 / (S_0 + T_max - T_max * k * s)

    L = v * L_v
    C = v * C_v

    # then we compensate for both _toe and the curved top part of the triangle
    L_vt = _toe_inv(L_v)
    C_vt = C_v * L_vt / L_v

    L_new = _toe_inv(L)
    C = C * L_new / L
    L = L_new

    rgb_scale = _oklab_to_rgb(_Lab(L_vt, a_ * C_vt, b_ * C_vt))
    scale_L = cbrt(1 / max(rgb_scale.r, rgb_scale.g, rgb_scale.b, 0))

    L = L * scale_L
    C = C * scale_L

    rgb = _oklab_to_rgb(_Lab(L, C * a_, C * b_))
    return RGB(
	_rgb_transfer(rgb.r),
	_rgb_transfer(rgb.g),
	_rgb_transfer(rgb.b),
    )


def rgb_to_okhsv(rgb):
    # type: (RGB) -> HSV
    """Convert RGB to OkHSV.

    >>> rgb = okhsv_to_rgb(HSV(314 / 360, 50 / 100, 75 / 100))
    >>> '#' + ''.join(f'{round(v*255):2x}'.upper() for v in rgb)
    '#A372BB'

    >>> rgb = okhsv_to_rgb(HSV(314 / 360, 50 / 100, 75 / 100))
    >>> '#' + ''.join(f'{round(v*255):2x}'.upper() for v in rgb)
    '#A372BB'
    """
    lab = _rgb_to_oklab(RGB(
	_rgb_transfer_inv(rgb.r),
	_rgb_transfer_inv(rgb.g),
	_rgb_transfer_inv(rgb.b),
    ))

    C = sqrt(lab.a * lab.a + lab.b * lab.b)
    if C == 0:
        return HSV(0, 0, 0)

    a_ = lab.a / C
    b_ = lab.b / C

    L = lab.l
    h = 0.5 + 0.5 * atan2(-lab.b, -lab.a) / PI

    cusp = _find_cusp(a_, b_)
    ST_max = _to_st(cusp)
    S_max = ST_max.s
    T_max = ST_max.t
    S_0 = 0.5
    k = 1 - S_0 / S_max

    # first we find L_v, C_v, L_vt and C_vt
    t = T_max / (C + L * T_max)
    L_v = t * L
    C_v = t * C

    L_vt = _toe_inv(L_v)
    C_vt = C_v * L_vt / L_v

    # we can then use these to invert the step that compensates for the _toe
    # and the curved top part of the triangle
    rgb_scale = _oklab_to_rgb(_Lab(L_vt, a_ * C_vt, b_ * C_vt))
    scale_L = cbrt(1 / max(rgb_scale.r, rgb_scale.g, rgb_scale.b, 0))

    L = L / scale_L
    C = C / scale_L

    C = C * _toe(L) / L
    L = _toe(L)

    # we can now compute v and s
    v = L / L_v
    s = (S_0 + T_max) * C_v / ((T_max * S_0) + T_max * k * C_v)
    return HSV(h, s, v)
