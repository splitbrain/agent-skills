"""Fit a similarity transform (with optional mirror) from template points to measured points.

fit(src, dst, mirror) returns (x, y, angle, scale, rms) for translate(x y) rotate(angle) scale(+-s, s).
"""
import math

import numpy as np


def fit(src, dst, mirror=False):
    """Return the translate, rotation, scale and rms error that map src onto dst."""
    S = np.array(src, float)
    if mirror:
        S[:, 0] = -S[:, 0]
    D = np.array(dst, float)
    sc, dc = S.mean(0), D.mean(0)
    A, B = S - sc, D - dc
    # complex least squares: B = z A
    za = A[:, 0] + 1j * A[:, 1]
    zb = B[:, 0] + 1j * B[:, 1]
    z = (np.conj(za) @ zb) / (np.conj(za) @ za)
    s, ang = abs(z), math.degrees(np.angle(z))
    t = dc - np.array([(z * (sc[0] + 1j * sc[1])).real, (z * (sc[0] + 1j * sc[1])).imag])
    pred = np.stack([(z * za).real, (z * za).imag], 1) + dc
    rms = float(np.sqrt(((pred - D) ** 2).sum(1).mean()))
    return round(float(t[0]), 2), round(float(t[1]), 2), round(ang, 2), round(s, 4), round(rms, 2)


def affine(src, dst):
    """Return the least squares affine map src -> dst as an SVG matrix(...) string and the rms."""
    S = np.array(src, float)
    D = np.array(dst, float)
    A = np.hstack([S, np.ones((len(S), 1))])
    M, *_ = np.linalg.lstsq(A, D, rcond=None)
    rms = float(np.sqrt(((A @ M - D) ** 2).sum(1).mean()))
    a, c, e = M[:, 0]
    b, d, f = M[:, 1]
    vals = ' '.join(f'{v:.4f}'.rstrip('0').rstrip('.') for v in (a, b, c, d, e, f))
    return f'matrix({vals})', round(rms, 2)
