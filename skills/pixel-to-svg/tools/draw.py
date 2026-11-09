"""SVG primitives, path compaction and the Scene that collects a drawing.

Coordinates are in the pixel space of the source image. A Scene holds shared definitions
(canonical objects, placed with <use> and a transform) and the drawing in back to front order.
"""
import math
import re


def num(v):
    """Format a number with at most two decimal places and no trailing zeros."""
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s == '-0' else s


def attrs(**kw):
    """Return the SVG attribute string for the keyword arguments; underscores become dashes."""
    return ''.join(f' {k.replace("_", "-")}="{num(v) if isinstance(v, (int, float)) else v}"'
                   for k, v in kw.items() if v is not None)


def pts(points):
    """Return the points as path coordinates."""
    return 'L'.join(f'{num(x)} {num(y)}' for x, y in points)


def path(d, fill='none', **kw):
    """Return a path element."""
    return f'<path d="{d}"{attrs(fill=fill, **kw)}/>'


def poly(points, fill, **kw):
    """Return a closed polygon through the points."""
    return path('M' + pts(points) + 'Z', fill, **kw)


def stroke(d, color, width, **kw):
    """Return an open stroked path with round caps and joins."""
    opts = dict(stroke=color, stroke_width=width, stroke_linecap='round', stroke_linejoin='round')
    opts.update(kw)
    return path(d, 'none', **opts)


def circle(cx, cy, r, fill, **kw):
    """Return a circle element."""
    return f'<circle{attrs(cx=cx, cy=cy, r=r, fill=fill, **kw)}/>'


def ellipse(cx, cy, rx, ry, fill, **kw):
    """Return an ellipse element."""
    return f'<ellipse{attrs(cx=cx, cy=cy, rx=rx, ry=ry, fill=fill, **kw)}/>'


def rect(x, y, w, h, fill, rx=None, **kw):
    """Return a rect element."""
    return f'<rect{attrs(x=x, y=y, width=w, height=h, rx=rx, fill=fill, **kw)}/>'


def group(body, **kw):
    """Return a group element around body."""
    return f'<g{attrs(**kw)}>{body}</g>'


def tf(x=0, y=0, angle=0, sx=1, sy=None):
    """Return a transform attribute value: translate, rotate (degrees), then scale."""
    sy = sx if sy is None else sy
    out = []
    if x or y:
        out.append(f'translate({num(x)} {num(y)})')
    if angle:
        out.append(f'rotate({num(angle)})')
    if sx != 1 or sy != 1:
        out.append(f'scale({num(sx)})' if sx == sy else f'scale({num(sx)} {num(sy)})')
    return ' '.join(out) or None


def rounded(points, r, closed=True):
    """Return path data of a polygon (or polyline) with all corners rounded by radius r.

    r may be one number or a list with one radius per vertex.
    """
    n = len(points)
    rs = r if isinstance(r, (list, tuple)) else [r] * n

    def d(a, b):
        return math.hypot(b[0] - a[0], b[1] - a[1])

    def toward(a, b, t):
        k = t / d(a, b)
        return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)

    idx = range(n) if closed else range(1, n - 1)
    corners = {}
    for i in idx:
        a, b, c = points[i - 1], points[i], points[(i + 1) % n]
        rr = min(rs[i], d(a, b) / 2, d(b, c) / 2)
        corners[i] = (toward(b, a, rr), b, toward(b, c, rr))
    if closed:
        out = 'M' + pts([corners[0][2]])
        order = list(range(1, n)) + [0]
    else:
        out = 'M' + pts([points[0]])
        order = list(range(1, n - 1))
    for i in order:
        p0, b, p1 = corners[i]
        if rs[i] > 0:
            out += 'L' + pts([p0]) + 'Q' + pts([b]) + ' ' + pts([p1])
        else:
            out += 'L' + pts([b])
    out += 'Z' if closed else 'L' + pts([points[-1]])
    return out


def curve(nodes):
    """Return path data of a smooth curve with one cubic Bezier segment between two nodes.

    Each node is (x, y, angle, h_in, h_out): the point, the direction of travel in degrees
    (0 = +x, 90 = +y) and the lengths of the handles before and after the point.
    """
    def handle(node, length):
        a = math.radians(node[2])
        return (node[0] + length * math.cos(a), node[1] + length * math.sin(a))
    out = 'M' + pts([nodes[0][:2]])
    for a, b in zip(nodes, nodes[1:]):
        out += 'C' + ' '.join(pts([p]) for p in (handle(a, a[4]), handle(b, -b[3]), b[:2]))
    return out


class Scene:
    """One SVG drawing: shared definitions and the body in back to front order."""

    def __init__(self, width, height, background=None):
        """Create an empty scene of the source image size, optionally filled with a background color."""
        self.width, self.height, self.background = width, height, background
        self.defs = {}
        self.body = []

    def define(self, ident, svg):
        """Add a definition once; svg must carry id=ident."""
        if ident not in self.defs:
            self.defs[ident] = svg

    def add(self, svg):
        """Append drawing to the scene."""
        self.body.append(svg)

    def use(self, ident, transform=None, **kw):
        """Append a use of the definition ident."""
        self.body.append(f'<use href="#{ident}"{attrs(transform=transform, **kw)}/>')

    def svg(self):
        """Return the complete, compacted SVG document."""
        w, h = self.width, self.height
        defs = '<defs>' + ''.join(self.defs.values()) + '</defs>' if self.defs else ''
        bg = rect(0, 0, w, h, self.background) if self.background else ''
        text = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
                + defs + bg + ''.join(self.body) + '</svg>\n')
        return compact_svg(text)


def count_nodes(text):
    """Return the number of path commands and basic shapes in the SVG text."""
    nodes = len(re.findall(r'[MLCQAZHVSTmlcqazhvst]', ''.join(re.findall(r' d="([^"]+)"', text))))
    shapes = len(re.findall(r'<(?:circle|ellipse|rect|use|line)\b', text))
    return nodes + shapes


def compact_path(d):
    """Return the path data d with relative coordinates where that is shorter.

    Handles M, L, H, V, C, Q, A and Z (absolute or relative input); the output keeps the
    shapes exactly (up to rounding to one decimal place).
    """
    tokens = re.findall(r'[MLHVCQAZmlhvcqaz]|-?\d*\.?\d+(?:e-?\d+)?', d)
    sizes = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'Q': 4, 'A': 7, 'Z': 0}
    out = []
    x = y = sx = sy = 0.0
    i = 0
    cmd = None
    prev_out = None

    def fmt(v):
        s = f'{v:.1f}'.rstrip('0').rstrip('.')
        if s == '-0':
            s = '0'
        return s.replace('0.', '.', 1) if s.startswith('0.') else s.replace('-0.', '-.', 1)

    def join(vals):
        txt = ''
        for v in vals:
            f = fmt(v)
            txt += f if (not txt or f.startswith('-') or (f.startswith('.') and '.' in txt.split(' ')[-1].split('-')[-1])) else ' ' + f
        return txt
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in 'Zz':
                out.append('z')
                x, y = sx, sy
                prev_out = None
                continue
        up = cmd.upper()
        n = sizes[up]
        vals = [float(v) for v in tokens[i:i + n]]
        i += n
        rel = cmd.islower()
        # absolute values
        if up == 'H':
            ax = vals[0] + (x if rel else 0)
            absv, relv = [ax], [ax - x]
            nx, ny = ax, y
        elif up == 'V':
            ay = vals[0] + (y if rel else 0)
            absv, relv = [ay], [ay - y]
            nx, ny = x, ay
        elif up == 'A':
            ex, ey = vals[5] + (x if rel else 0), vals[6] + (y if rel else 0)
            absv = vals[:5] + [ex, ey]
            relv = vals[:5] + [ex - x, ey - y]
            nx, ny = ex, ey
        else:
            absv = [vals[k] + ((x if k % 2 == 0 else y) if rel else 0) for k in range(n)]
            relv = [absv[k] - (x if k % 2 == 0 else y) for k in range(n)]
            nx, ny = absv[-2], absv[-1]
        # Round the absolute coordinates first, so the relative steps add up to them exactly
        absv = [round(v, 1) for v in absv]
        if up == 'H':
            relv, nx = [absv[0] - x], absv[0]
        elif up == 'V':
            relv, ny = [absv[0] - y], absv[0]
        elif up == 'A':
            relv = absv[:5] + [absv[5] - x, absv[6] - y]
            nx, ny = absv[5], absv[6]
        else:
            relv = [absv[k] - (x if k % 2 == 0 else y) for k in range(n)]
            nx, ny = absv[-2], absv[-1]
        a_txt, r_txt = join(absv), join(relv)
        if up == 'M':
            use_rel = len(r_txt) < len(a_txt) and out
            letter = 'm' if use_rel else 'M'
            sx, sy = nx, ny
            cmd = 'l' if cmd == 'm' else 'L'
        else:
            use_rel = len(r_txt) < len(a_txt)
            letter = up.lower() if use_rel else up
        body = r_txt if use_rel else a_txt
        if prev_out == letter and letter not in 'Mm':
            out.append(body if body.startswith('-') else ' ' + body)
        else:
            out.append(letter + body)
        prev_out = letter if letter not in 'Mm' else ('l' if letter == 'm' else 'L')
        x, y = nx, ny
    return ''.join(out)


def compact_svg(text):
    """Return the SVG text with all path data compacted (see compact_path)."""
    return re.sub(r' d="([^"]+)"', lambda m: ' d="' + compact_path(m.group(1)) + '"', text)
