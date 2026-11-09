#!/usr/bin/env python3
"""Show the snapped network over the source image with path ids and a 10 px grid.

Usage: netview.py IMAGE NET.py X Y W H [SCALE] [OUT.png]   (default scale 5, out /tmp/netview.png)
"""
import base64
import os
import subprocess
import sys
import tempfile

import netlib
from network import load_net
from draw import circle, rounded

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    path, netpath = sys.argv[1], sys.argv[2]
    x, y, w, h = sys.argv[3:7]
    sc = sys.argv[7] if len(sys.argv) > 7 else '5'
    out = sys.argv[8] if len(sys.argv) > 8 else '/tmp/netview.png'
    img = netlib.load(path)
    H, W = img.shape[:2]
    net = load_net(netpath)
    snapped = netlib.snap_all(img, net)
    data = base64.b64encode(open(path, 'rb').read()).decode()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<image href="data:image/png;base64,{data}" width="{W}" height="{H}" style="image-rendering:pixelated"/>',
           '<g stroke="#f00" stroke-width="0.15" opacity="0.6">']
    svg += [f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H}"/>' for gx in range(0, W, 10)]
    svg += [f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}"/>' for gy in range(0, H, 10)]
    svg.append('</g><g font-size="3" fill="#f00">')
    svg += [f'<text x="{gx + .3}" y="{gy + 3}">{gx},{gy}</text>' for gx in range(0, W, 10) for gy in range(0, H, 20)]
    svg.append('</g><g fill="none" stroke="#f0f" stroke-width="0.5">')
    svg += [f'<path d="{rounded(p, getattr(net, "CORNER", 2), c)}"/>' for p, c in snapped]
    svg += [circle(cx, cy, r, 'none') for cx, cy, r in net.DOTS]
    svg.append('</g><g font-size="4" fill="#ff0" stroke="#000" stroke-width="0.15" font-weight="bold">')
    for i, (p, c) in enumerate(snapped):
        (ax, ay), (bx, by) = p[0], p[1]
        svg.append(f'<text x="{(ax + bx) / 2:.1f}" y="{(ay + by) / 2:.1f}">{i}</text>')
    svg.append('</g></svg>')
    tmp = os.path.join(tempfile.mkdtemp(), 'netview.svg')
    open(tmp, 'w').write('\n'.join(svg))
    subprocess.run(['node', os.path.join(HERE, 'render.mjs'), tmp, out, sc, x, y, w, h], check=True)
    print(out)


if __name__ == '__main__':
    main()
