#!/usr/bin/env python3
"""Write the automatic draft of a line network (thin lines of one color on a plain background) as a network file.

Usage: lines.py IMAGE BG LINE WIDTH > net.py
  BG and LINE are #rrggbb colors, WIDTH is the line width in pixels.

The network file holds rough polylines ('x,y x,y ...', closed) that are snapped to the line
pixels at build time, so they can be edited by hand with about 2 px accuracy.
"""
import sys

import netlib


def main():
    path, bg, line, width = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    img = netlib.load(path)
    paths, dots = netlib.extract(img, netlib.hex_rgb(bg), netlib.hex_rgb(line), width)
    print('"""Line network (rough polylines, snapped to the line pixels at build time)."""')
    print(f'BG = {bg!r}')
    print(f'LINE = {line!r}')
    print(f'WIDTH = {width:g}')
    print('CORNER = 2')
    print('NET = [')
    for i, p in enumerate(paths):
        print(f"    ('{' '.join(f'{x:.0f},{y:.0f}' for x, y in p['v'])}', {p['closed']}),  # {i}")
    print(']')
    print('DOTS = [')
    for x, y, r in dots:
        print(f'    ({x:.1f}, {y:.1f}, {r:.1f}),')
    print(']')


if __name__ == '__main__':
    main()
