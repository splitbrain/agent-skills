#!/usr/bin/env python3
"""Fit a hand placed smooth curve to the pixels of the source image.

Usage: curvefit.py IMAGE NODES.json COLOR [SCALE] [edge] [nofit]

The curve is a draw.curve: NODES.json is {"nodes": [[x, y, angle] or [x, y, angle, h_in,
h_out], ...], "hidden": [[x0, y0, x1, y1], ...]}. Hidden boxes are where the curve runs behind
something. COLOR is the #rrggbb color of the drawn element.

Without "edge" the curve follows the center line of a thin stroke of that color (a cable, a
contour line, a hair, a letter stroke). With "edge" it follows the border of a filled region
of that color (one side of a blob, a hill, a cloud, a body). The nodes stay nearly where they
are placed; the handle lengths are fitted ("nofit" only fills in missing handles). Prints the
tuned nodes as JSON and writes /tmp/curve.png: the source crop with the curve in red and the
nodes in yellow.
"""
import base64
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage, optimize
from skimage.morphology import skeletonize

from draw import curve, num

HERE = os.path.dirname(os.path.abspath(__file__))
# Color distance at which a pixel stops counting as the element color
TOLERANCE = 60

SAMPLES = 24


def bezier(nodes):
    """Return sample points of the curve through the nodes (SAMPLES per segment)."""
    t = np.linspace(0, 1, SAMPLES)[:, None]
    out = []
    for a, b in zip(nodes, nodes[1:]):
        p0, p3 = np.array(a[:2]), np.array(b[:2])
        p1 = p0 + a[4] * np.array([math.cos(math.radians(a[2])), math.sin(math.radians(a[2]))])
        p2 = p3 - b[3] * np.array([math.cos(math.radians(b[2])), math.sin(math.radians(b[2]))])
        out.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)
    return np.vstack(out)


def auto_handles(nodes):
    """Return the nodes with handle lengths for round turns where they are missing."""
    out = [list(n) + [None] * (5 - len(n)) for n in nodes]
    for a, b in zip(out, out[1:]):
        chord = math.hypot(b[0] - a[0], b[1] - a[1])
        direction = math.atan2(b[1] - a[1], b[0] - a[0])
        for node, slot in ((a, 4), (b, 3)):
            if node[slot] is None:
                alpha = abs((math.radians(node[2]) - direction + math.pi) % (2 * math.pi) - math.pi)
                alpha = min(max(alpha, 1e-3), math.radians(150))
                node[slot] = chord * 4 / 3 * math.tan(alpha / 2) / (2 * math.sin(alpha))
    out[0][3] = out[-1][4] = 0
    return out


def main():
    path, nodes_path, color = sys.argv[1:4]
    scale = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4].isdigit() else '6'
    spec = json.load(open(nodes_path))
    nodes = auto_handles(spec['nodes'])
    hidden = spec.get('hidden', [])
    img = np.array(Image.open(path).convert('RGB')).astype(float)
    H, W = img.shape[:2]
    target = np.array([int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
    weight = np.clip(1 - np.linalg.norm(img - target, axis=2) / TOLERANCE, 0, 1)
    first = bezier(nodes)
    corridor = np.zeros(weight.shape, bool)
    for x, y in first:
        corridor[max(int(y) - 6, 0):int(y) + 7, max(int(x) - 6, 0):int(x) + 7] = True
    mask = weight > 0.5
    if 'edge' in sys.argv:
        # The border pixels of the region: inside the color, next to a pixel outside it
        skel = (mask & ~ndimage.binary_erosion(mask)) & corridor
    else:
        skel = skeletonize(mask & corridor)
    dist = ndimage.distance_transform_edt(~skel)
    sk_pts = np.argwhere(skel)[:, ::-1].astype(float) + 0.5

    def visible(p):
        return np.array([not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in hidden) for x, y in p])

    sk_pts = sk_pts[visible(sk_pts)]
    base = np.array([v for nd in nodes for v in nd], float)

    def unpack(v):
        return [list(v[i * 5:i * 5 + 5]) for i in range(len(nodes))]

    def residuals(v):
        nd = unpack(v)
        p = bezier(nd)
        d = ndimage.map_coordinates(dist, [p[:, 1] - 0.5, p[:, 0] - 0.5], order=1) * visible(p)
        cover = np.sqrt(((sk_pts[:, None, :] - p[None, :, :]) ** 2).sum(2)).min(1)
        reg = np.concatenate([(v - base).reshape(-1, 5)[:, :2].ravel() * 2.0,
                              (v - base).reshape(-1, 5)[:, 2] * 0.3,
                              np.minimum(v.reshape(-1, 5)[:, 3:], 0).ravel() * 10])
        return np.concatenate([d * 0.7, np.minimum(cover, 8), reg])

    if 'nofit' in sys.argv:
        res = optimize.OptimizeResult(x=base, cost=float((residuals(base) ** 2).sum() / 2))
    else:
        res = optimize.least_squares(residuals, base, diff_step=1e-3)
    tuned = [[round(x * 2) / 2, round(y * 2) / 2, round(a), round(hi, 1), round(ho, 1)] for x, y, a, hi, ho in unpack(res.x)]
    # The curve does not use the handle before the first node and after the last node
    tuned[0][3] = tuned[-1][4] = 0
    print(json.dumps({'nodes': tuned, 'hidden': hidden}))
    xs, ys = bezier(tuned)[:, 0], bezier(tuned)[:, 1]
    x0, y0 = int(xs.min()) - 6, int(ys.min()) - 6
    w, h = int(xs.max()) + 6 - x0, int(ys.max()) + 6 - y0
    dots = ''.join(f'<circle cx="{x}" cy="{y}" r="0.6" fill="#ff0"/>' for x, y, *_ in tuned)
    data = base64.b64encode(open(path, 'rb').read()).decode()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<image href="data:image/png;base64,{data}" width="{W}" height="{H}" style="image-rendering:pixelated"/>'
           f'<path d="{curve(tuned)}" fill="none" stroke="#f00" stroke-width="0.4" opacity="0.8"/>{dots}</svg>')
    tmp = os.path.join(tempfile.mkdtemp(), 'curve.svg')
    open(tmp, 'w').write(svg)
    subprocess.run(['node', os.path.join(HERE, 'render.mjs'), tmp, '/tmp/curve.png', scale,
                    str(x0), str(y0), str(w), str(h)], check=True)
    print(f'segments {len(tuned) - 1}, cost {res.cost:.1f}', file=sys.stderr)


if __name__ == '__main__':
    main()
