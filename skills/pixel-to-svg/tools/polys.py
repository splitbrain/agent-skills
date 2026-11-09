#!/usr/bin/env python3
"""Print the polygons of one color inside a box of an image, as python lists.

Usage: py polys.py IN.png COLOR X0 Y0 X1 Y1 [EPS] [MIN_AREA]

The pixels near the color (distance below 30) are scaled up four times, their contours are
simplified with the tolerance EPS pixels (default 1.0), and the polygons are printed with one
decimal place. Holes are printed as separate polygons marked "hole".
"""
import sys

import cv2
import numpy as np
from PIL import Image


def main():
    src, color, *rest = sys.argv[1:]
    x0, y0, x1, y1 = [int(v) for v in rest[:4]]
    eps = float(rest[4]) if len(rest) > 4 else 1.0
    min_area = float(rest[5]) if len(rest) > 5 else 12
    rgb = np.array([int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)])
    img = np.array(Image.open(src).convert('RGB')).astype(int)
    mask = np.zeros(img.shape[:2], np.uint8)
    mask[y0:y1, x0:x1] = (np.linalg.norm(img - rgb, axis=2) < 30)[y0:y1, x0:x1]
    big = cv2.resize(mask, (mask.shape[1] * 4, mask.shape[0] * 4), interpolation=cv2.INTER_LINEAR)
    big = (big > 0).astype(np.uint8)
    contours, hier = cv2.findContours(big, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for i, c in enumerate(contours):
        area = cv2.contourArea(c) / 16
        if area < min_area:
            continue
        poly = cv2.approxPolyDP(c, eps * 4, True).reshape(-1, 2) / 4
        kind = 'hole' if hier[0][i][3] >= 0 else 'poly'
        pts = ', '.join(f'({x:.1f}, {y:.1f})'.replace('.0,', ',').replace('.0)', ')') for x, y in poly)
        print(f'{kind} area {area:.0f}: [{pts}]')


if __name__ == '__main__':
    main()
