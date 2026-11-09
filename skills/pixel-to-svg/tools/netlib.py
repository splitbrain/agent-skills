"""Line networks: extract thin lines of one color from a raster image and snap rough polylines to them.

A network is a set of polylines (straight segments with rounded corners, one line width) and
filled dots in one line color on a plain background. Coordinates are source pixels.
"""
import cv2
import numpy as np
from scipy import ndimage
from skimage.morphology import skeletonize

# Supersampling factor for the skeleton of the line pixels
S = 4


def hex_rgb(color):
    """Return the RGB values of a #rrggbb color as a float array."""
    c = color.lstrip('#')
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float)


def load(path):
    """Return the RGB pixels of an image file as a float array."""
    from PIL import Image
    return np.array(Image.open(path).convert('RGB')).astype(float)


def strength(img, bg, line, tol=10):
    """Return the coverage of the line color per pixel (0..1).

    Pixels whose color is not a mix of the background and the line color get 0; so do
    colors on the same axis that are much darker than the line color.
    """
    axis = line - bg
    d = img - bg
    t = (d @ axis) / (axis @ axis)
    res = np.linalg.norm(d - t[..., None] * axis, axis=2)
    t[(res > tol) | (t > 1.3)] = 0
    return np.clip(t, 0, 1)


def find_dots(s, width):
    """Return the filled circles of the line color and a strength map without them."""
    k = int(round(width)) + 2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    core = cv2.morphologyEx((s > 0.5).astype(np.uint8), cv2.MORPH_OPEN, kernel)
    num, lab, stats, cent = cv2.connectedComponentsWithStats(core)
    dots = []
    s = s.copy()
    for i in range(1, num):
        x, y, w, h, a = stats[i]
        if w > 12 or h > 12 or abs(w - h) > 2:
            continue
        x0, y0 = max(x - 2, 0), max(y - 2, 0)
        x1, y1 = min(x + w + 2, s.shape[1]), min(y + h + 2, s.shape[0])
        win = s[y0:y1, x0:x1]
        yy, xx = np.mgrid[y0:y1, x0:x1]
        m = win.sum()
        cx, cy = (win * (xx + .5)).sum() / m, (win * (yy + .5)).sum() / m
        r = (w + h) / 4 + 0.5
        dots.append([round(cx, 2), round(cy, 2), round(r, 2)])
        s[y0:y1, x0:x1][np.hypot(xx + .5 - cx, yy + .5 - cy) < r + 1.2] = 0
    return dots, s


def chains(sk):
    """Split a skeleton image into pixel chains between endpoints and junctions."""
    h, w = sk.shape
    pts = set(zip(*np.nonzero(sk)))
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    def nbrs(p):
        return [(p[0] + a, p[1] + b) for a, b in nb if (p[0] + a, p[1] + b) in pts]

    deg = {p: len(nbrs(p)) for p in pts}
    nodes = {p for p in pts if deg[p] != 2}
    seen = set()
    out = []
    for n in nodes:
        for q in nbrs(n):
            if (n, q) in seen:
                continue
            path = [n, q]
            seen.add((n, q))
            prev, cur = n, q
            while cur not in nodes:
                nx = [r for r in nbrs(cur) if r != prev and r not in path[-3:]]
                if not nx:
                    break
                prev, cur = cur, nx[0]
                path.append(cur)
            seen.add((cur, prev))
            out.append(path)
    # loops without nodes
    rest = pts - {p for c in out for p in c}
    while rest:
        p = rest.pop()
        path = [p]
        cur = p
        while True:
            nx = [r for r in nbrs(cur) if r in rest]
            if not nx:
                break
            cur = nx[0]
            rest.discard(cur)
            path.append(cur)
        path.append(p)
        out.append(path)
    return out


def refine(seg, s, width):
    """Fit a line to the strength pixels near a segment; return the refined end points."""
    (x1, y1), (x2, y2) = seg
    d = np.array([x2 - x1, y2 - y1])
    L = np.linalg.norm(d)
    d /= L
    nrm = np.array([-d[1], d[0]])
    x0, x1b = int(min(x1, x2)) - 3, int(max(x1, x2)) + 4
    y0, y1b = int(min(y1, y2)) - 3, int(max(y1, y2)) + 4
    x0, y0 = max(x0, 0), max(y0, 0)
    x1b, y1b = min(x1b, s.shape[1]), min(y1b, s.shape[0])
    win = s[y0:y1b, x0:x1b]
    yy, xx = np.mgrid[y0:y1b, x0:x1b] + .5
    rel = np.stack([xx - x1, yy - y1], -1)
    t = rel @ d
    o = rel @ nrm
    m = (t > 1.5) & (t < L - 1.5) & (np.abs(o) < width / 2 + 1.5) & (win > 0)
    if m.sum() < 4:
        return seg
    wgt = win[m]
    P = np.stack([xx[m], yy[m]], -1)
    c = (P * wgt[:, None]).sum(0) / wgt.sum()
    Q = P - c
    cov = (Q * wgt[:, None]).T @ Q
    ev, evec = np.linalg.eigh(cov)
    dd = evec[:, 1]
    if dd @ d < 0:
        dd = -dd
    a = c + dd * ((np.array([x1, y1]) - c) @ dd)
    b = c + dd * ((np.array([x2, y2]) - c) @ dd)
    return [tuple(a), tuple(b)]


def _meet_segments(a, b):
    """Return the intersection of the lines through segments a and b, or None."""
    p, r = np.array(a[0]), np.array(a[1]) - np.array(a[0])
    q, t = np.array(b[0]), np.array(b[1]) - np.array(b[0])
    den = r[0] * t[1] - r[1] * t[0]
    if den == 0 or abs(den) < 1e-6 * np.linalg.norm(r) * np.linalg.norm(t):
        return None
    u = ((q - p)[0] * t[1] - (q - p)[1] * t[0]) / den
    return tuple(p + u * r)


def polyline(chain, s, width, eps):
    """Turn a skeleton chain into a refined polyline with sharp corners."""
    pts = np.array([[c[1], c[0]] for c in chain], np.float32) / S + 0.5 / S
    closed = len(chain) > 2 and chain[0] == chain[-1]
    ap = cv2.approxPolyDP(pts.reshape(-1, 1, 2), eps, closed)[:, 0]
    if closed and len(ap) > 1 and np.allclose(ap[0], ap[-1]):
        ap = ap[:-1]
    v = [tuple(p) for p in ap]
    n = len(v)
    segs = [(v[i], v[(i + 1) % n]) for i in range(n if closed else n - 1)]
    if not segs:
        return None
    # drop short corner chamfers between long segments
    def length(sg):
        return np.hypot(sg[1][0] - sg[0][0], sg[1][1] - sg[0][1])
    long = [sg for sg in segs if length(sg) >= 5]
    if not long:
        long = [max(segs, key=length)]
    long = [refine(sg, s, width) for sg in long]
    out = []
    for i, sg in enumerate(long):
        out.append(sg)
    verts = []
    m = len(out)
    for i in range(m):
        if not closed and i == 0:
            verts.append(out[0][0])
        if closed or i < m - 1:
            nxt = out[(i + 1) % m]
            p = _meet_segments(out[i], nxt)
            if p is None or np.hypot(p[0] - out[i][1][0], p[1] - out[i][1][1]) > 8:
                verts.append(out[i][1])
                verts.append(nxt[0])
            else:
                verts.append(p)
    if not closed:
        verts.append(out[-1][1])
    return {'closed': bool(closed), 'v': [[round(float(x), 2), round(float(y), 2)] for x, y in verts]}


class Seg:
    """A straight line: point c, unit direction d, extent t0..t1 along d."""

    def __init__(self, a, b):
        a, b = np.array(a, float), np.array(b, float)
        d = b - a
        L = np.linalg.norm(d)
        self.d = d / L
        self.c = a
        self.t0, self.t1 = 0.0, L
        self.links = [None, None]

    def end(self, k):
        return self.c + self.d * (self.t0 if k == 0 else self.t1)

    def set_end(self, k, p):
        t = (np.array(p) - self.c) @ self.d
        if k == 0:
            self.t0 = t
        else:
            self.t1 = t

    @property
    def length(self):
        return self.t1 - self.t0

    def off(self, p):
        """Perpendicular distance of point p from the line."""
        q = np.array(p) - self.c
        return abs(q[0] * self.d[1] - q[1] * self.d[0])

    def proj(self, p):
        return (np.array(p) - self.c) @ self.d


def foreground(img, s, bg):
    """Mask of pixels that belong to neither the background nor the line network."""
    fg = (np.linalg.norm(img - bg, axis=2) > 12) & (s == 0)
    return fg


def object_mask(fg, close=5, maxhole=1500):
    """Mask of the foreground objects with their holes filled (line pixels inside count)."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close))
    m = cv2.morphologyEx(fg.astype(np.uint8), cv2.MORPH_CLOSE, k) > 0
    holes = ndimage.binary_fill_holes(m) & ~m
    lab, n = ndimage.label(holes)
    sizes = ndimage.sum(holes, lab, range(1, n + 1))
    small = np.isin(lab, 1 + np.nonzero(sizes < maxhole)[0])
    return m | small


def covered(fg, a, b):
    """Fraction of the sample points between a and b that lie on foreground pixels."""
    n = max(int(np.linalg.norm(b - a)), 1)
    hits = 0
    for i in range(n + 1):
        p = a + (b - a) * i / n
        x, y = int(p[0]), int(p[1])
        if 0 <= x < fg.shape[1] and 0 <= y < fg.shape[0] and fg[y, x]:
            hits += 1
    return hits / (n + 1)


def merge_collinear(segs, fg, s, angle=3.0, offset=1.2, gap=8.0):
    """Join segments on the same line whose gap is short or hidden by foreground."""
    cosmax = np.cos(np.radians(angle))
    changed = True
    while changed:
        changed = False
        segs.sort(key=lambda g: -g.length)
        for i, a in enumerate(segs):
            for j in range(i + 1, len(segs)):
                b = segs[j]
                if abs(a.d @ b.d) < cosmax:
                    continue
                if a.off(b.end(0)) > offset or a.off(b.end(1)) > offset:
                    continue
                u0, u1 = sorted([a.proj(b.end(0)), a.proj(b.end(1))])
                if u0 > a.t1:
                    g = (a.end(1), a.c + a.d * u0)
                elif u1 < a.t0:
                    g = (a.c + a.d * u1, a.end(0))
                else:
                    g = None
                if g is not None:
                    dist = np.linalg.norm(g[1] - g[0])
                    if dist > gap and covered(fg | (s > 0.3), g[0], g[1]) < 0.9:
                        continue
                # weighted refit through both
                la, lb = a.length, b.length
                pts = [a.end(0), a.end(1), b.end(0), b.end(1)]
                w = [la, la, lb, lb]
                c = sum(p * wi for p, wi in zip(pts, w)) / sum(w)
                d = a.d if (a.d @ b.d) > 0 else a.d
                ts = [(p - c) @ d for p in pts]
                new = Seg(c + d * min(ts), c + d * max(ts))
                segs[i] = new
                del segs[j]
                changed = True
                break
            if changed:
                break
    return segs


def intersect(a, b):
    den = a.d[0] * b.d[1] - a.d[1] * b.d[0]
    if abs(den) < 0.2:
        return None
    q = b.c - a.c
    u = (q[0] * b.d[1] - q[1] * b.d[0]) / den
    return a.c + a.d * u


def snap(segs, s, corner=5.0, far=10.0, tee=4.0):
    """Join segment ends into corners and snap ends onto other lines (T-junctions)."""
    ends = [(i, k) for i in range(len(segs)) for k in (0, 1)]
    cands = []
    for x in range(len(ends)):
        i, k = ends[x]
        for y in range(x + 1, len(ends)):
            j, m = ends[y]
            if i == j:
                continue
            a, b = segs[i], segs[j]
            p = intersect(a, b)
            if p is None:
                continue
            da = np.linalg.norm(a.end(k) - p)
            db = np.linalg.norm(b.end(m) - p)
            # the intersection must lie beyond or near the end, not deep inside
            ta, tb = a.proj(p), b.proj(p)
            ina = (a.t0 + 2 < ta < a.t1 - 2)
            inb = (b.t0 + 2 < tb < b.t1 - 2)
            near = da < corner and db < corner
            if not near and da < far and db < far:
                ink = np.minimum(covered(s > 0.2, a.end(k), p), covered(s > 0.2, p, b.end(m)))
                near = ink > 0.6
            if near and not ina and not inb:
                cands.append((da + db, i, k, j, m, p))
    cands.sort(key=lambda c: c[0])
    for _, i, k, j, m, p in cands:
        if segs[i].links[k] is None and segs[j].links[m] is None:
            segs[i].set_end(k, p)
            segs[j].set_end(m, p)
            segs[i].links[k] = (j, m)
            segs[j].links[m] = (i, k)
    for i, a in enumerate(segs):
        for k in (0, 1):
            if a.links[k] is not None:
                continue
            best = None
            for j, b in enumerate(segs):
                if j == i:
                    continue
                p = intersect(a, b)
                if p is None:
                    continue
                tb = b.proj(p)
                if not (b.t0 - 1 < tb < b.t1 + 1):
                    continue
                da = np.linalg.norm(a.end(k) - p)
                ta = a.proj(p)
                beyond = ta <= a.t0 + 1 if k == 0 else ta >= a.t1 - 1
                if da < tee and beyond and (best is None or da < best[0]):
                    best = (da, p)
            if best:
                a.set_end(k, best[1])
                a.links[k] = 'tee'
    return segs


def extend_hidden(segs, fg, s, maxlen=200):
    """Extend loose ends that run into a foreground object to the far side of it."""
    for a in segs:
        for k in (0, 1):
            if a.links[k] is not None:
                continue
            sign = -1 if k == 0 else 1
            p = a.end(k)
            steps = 0
            for st in range(1, maxlen):
                q = p + a.d * sign * st
                x, y = int(q[0]), int(q[1])
                if not (0 <= x < fg.shape[1] and 0 <= y < fg.shape[0]):
                    steps = st
                    break
                if not fg[y, x]:
                    break
                steps = st
            if steps >= 2:
                a.set_end(k, p + a.d * sign * steps)
                a.links[k] = 'hidden'
    return segs


def polylines(segs):
    """Chain linked segments into polylines (lists of vertices, closed flag)."""
    used = set()
    out = []

    def walk(i, k):
        """Walk from segment i, leaving through end k; return vertices and closed flag."""
        verts = [segs[i].end(1 - k), segs[i].end(k)]
        used.add(i)
        cur, ck = i, k
        while True:
            ln = segs[cur].links[ck]
            if not isinstance(ln, tuple):
                return verts, False
            j, m = ln
            if j == i:
                return verts[:-1], True
            if j in used:
                return verts, False
            used.add(j)
            verts.append(segs[j].end(1 - m))
            cur, ck = j, 1 - m

    for i, a in enumerate(segs):
        if i in used:
            continue
        # start from a free end if there is one
        start = i
        k = 1
        cur, ck = i, 0
        seen = {i}
        while isinstance(segs[cur].links[ck], tuple):
            j, m = segs[cur].links[ck]
            if j in seen:
                break
            seen.add(j)
            cur, ck = j, 1 - m
        start, k = cur, 1 - ck
        if start in used:
            continue
        v, closed = walk(start, k)
        out.append({'closed': closed, 'v': [[round(float(x), 2), round(float(y), 2)] for x, y in v]})
    return out
def extract(img, bg, line, width, eps=0.7, minlen=4):
    """Return the automatic draft of a network: polylines {'closed', 'v'} and dots [x, y, r].

    The draft contains pieces of objects drawn in the line color and misses lines hidden
    behind objects; curate it by hand.
    """
    s = strength(img, bg, line)
    fg0 = foreground(img, s, bg)
    obj = object_mask(fg0)
    s = s * ~cv2.dilate(obj.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    dots, s2 = find_dots(s, width)
    big = cv2.resize(s2, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
    sk = skeletonize(big > 0.45)
    segs = []
    for c in chains(sk):
        if len(c) < minlen * S:
            continue
        p = polyline(c, s2, width, eps)
        if not p:
            continue
        v = p['v'] + ([p['v'][0]] if p['closed'] else [])
        for a, b in zip(v, v[1:]):
            if np.hypot(b[0] - a[0], b[1] - a[1]) >= minlen:
                segs.append(Seg(a, b))
    fg = obj | fg0
    segs = merge_collinear(segs, fg, s2)
    segs = snap(segs, s2)
    segs = extend_hidden(segs, fg, s2)
    return polylines(segs), dots


def fit(a, b, s, width, band=2.0):
    """Refit segment a-b to the strength pixels within a band; return (point, dir, support)."""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    L = np.linalg.norm(d)
    if L < 1e-6:
        return a, np.array([1.0, 0.0]), 0
    d /= L
    nrm = np.array([-d[1], d[0]])
    x0 = max(int(min(a[0], b[0]) - band - 2), 0)
    x1 = min(int(max(a[0], b[0]) + band + 3), s.shape[1])
    y0 = max(int(min(a[1], b[1]) - band - 2), 0)
    y1 = min(int(max(a[1], b[1]) + band + 3), s.shape[0])
    win = s[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1] + .5
    rel = np.stack([xx - a[0], yy - a[1]], -1)
    t = rel @ d
    o = rel @ nrm
    m = (t > 2.5) & (t < L - 2.5) & (np.abs(o) < width / 2 + band) & (win > 0.05)
    support = win[m].sum() / max(width, 1) / max(L - 5, 1)
    if m.sum() < 6 or support < 0.3:
        return a, d, support
    wgt = win[m]
    P = np.stack([xx[m], yy[m]], -1)
    c = (P * wgt[:, None]).sum(0) / wgt.sum()
    Q = P - c
    cov = (Q * wgt[:, None]).T @ Q
    _, evec = np.linalg.eigh(cov)
    dd = evec[:, 1]
    if dd @ d < 0:
        dd = -dd
    # keep near-axis lines from tilting on short supports
    return c, dd, support


def meet(p, d, q, e):
    """Intersection of the lines p + t d and q + u e, or None for parallel lines."""
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 0.05:
        return None
    w = q - p
    t = (w[0] * e[1] - w[1] * e[0]) / den
    return p + t * d


def snap_polyline(poly, closed, s, width):
    """Return the snapped vertices of one rough polyline."""
    v = [np.array(p, float) for p in poly]
    n = len(v)
    segs = [(v[i], v[(i + 1) % n]) for i in range(n if closed else n - 1)]
    lines = [fit(a, b, s, width) for a, b in segs]
    out = []
    m = len(lines)
    for i in range(n):
        if not closed and i == 0:
            p, d, _ = lines[0]
            out.append(p + d * ((v[0] - p) @ d))
        elif not closed and i == n - 1:
            p, d, _ = lines[-1]
            out.append(p + d * ((v[-1] - p) @ d))
        else:
            p, d, _ = lines[i - 1]
            q, e, _ = lines[i % m]
            x = meet(p, d, q, e)
            out.append(x if x is not None and np.linalg.norm(x - v[i]) < 6 else v[i])
    return [[round(float(x), 2), round(float(y), 2)] for x, y in out]


def parse(net):
    """Return the polylines of a network file's NET list as (points, closed) pairs."""
    return [([tuple(map(float, q.split(','))) for q in p.split()], c) for p, c in net]


def snap_all(img, net):
    """Return the snapped vertex lists of a network module (NET, WIDTH, LINE, BG) as (points, closed)."""
    s = strength(img, hex_rgb(net.BG), hex_rgb(net.LINE))
    return [(snap_polyline(p, c, s, net.WIDTH), c) for p, c in parse(net.NET)]
