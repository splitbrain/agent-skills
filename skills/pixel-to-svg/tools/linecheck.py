#!/usr/bin/env python3
"""Compare a network (or a finished SVG) with the line pixels of the source image.

Usage: linecheck.py IMAGE NET.py [BUILT.svg]

Without BUILT.svg: renders the network alone and writes /tmp/linecheck.png (3x) where red
marks line pixels the network misses and blue marks network lines over plain background.
With BUILT.svg: lists source line pixels that the finished SVG shows as plain background
(lines that end too early, gaps behind objects that were not closed).
Prints the boxes (x, y, w, h, pixels) of all marked places, largest first.
"""
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
from PIL import Image

import netlib
from network import load_net, network_svg

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = tempfile.mkdtemp()


def render(svg_path, out):
    """Render an SVG at 1x and return its RGB pixels."""
    subprocess.run(['node', os.path.join(HERE, 'render.mjs'), svg_path, out, '1'], check=True)
    return np.array(Image.open(out).convert('RGB')).astype(float)


def boxes(mask):
    """Return the boxes of the connected areas of a mask, largest first."""
    num, _, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    return sorted([tuple(int(v) for v in st[i]) for i in range(1, num) if st[i][4] >= 2], key=lambda b: -b[4])


def main():
    path, netpath = sys.argv[1], sys.argv[2]
    img = netlib.load(path)
    H, W = img.shape[:2]
    net = load_net(netpath)
    bg, line = netlib.hex_rgb(net.BG), netlib.hex_rgb(net.LINE)
    s = netlib.strength(img, bg, line)
    k = np.ones((3, 3), np.uint8)
    if len(sys.argv) > 3:
        built = render(os.path.abspath(sys.argv[3]), os.path.join(TMP, 'built.png'))
        plain = cv2.erode((np.linalg.norm(built - bg, axis=2) < 6).astype(np.uint8), k).astype(bool)
        for b in boxes((s > 0.5) & plain):
            print(b)
        return
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<rect width="{W}" height="{H}" fill="{net.BG}"/>' + network_svg(img, net, net.LINE) + '</svg>')
    open(os.path.join(TMP, 'net.svg'), 'w').write(svg)
    r = netlib.strength(render(os.path.join(TMP, 'net.svg'), os.path.join(TMP, 'net.png')), bg, line)
    fg = netlib.object_mask(netlib.foreground(img, s, bg))
    fg = cv2.dilate(fg.astype(np.uint8), k) > 0
    near_r = cv2.dilate((r > 0.2).astype(np.uint8), k) > 0
    near_s = cv2.dilate((s > 0.2).astype(np.uint8), k) > 0
    miss = (s > 0.5) & ~near_r & ~fg
    extra = (r > 0.5) & ~near_s & ~fg
    vis = (img * 0.6 + 255 * 0.4).astype(np.uint8)
    vis[miss] = [255, 0, 0]
    vis[extra] = [0, 0, 255]
    Image.fromarray(cv2.resize(vis, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)).save('/tmp/linecheck.png')
    print('missing', boxes(miss)[:30])
    print('extra', boxes(extra)[:30])


if __name__ == '__main__':
    main()
