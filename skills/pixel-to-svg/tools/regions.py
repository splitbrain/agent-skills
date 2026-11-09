#!/usr/bin/env python3
"""List the flat color regions of an image and group regions that look alike.

Usage: regions.py IMAGE [COLORS] [MIN_AREA]

Every pixel is set to the nearest of the COLORS most frequent colors (default 12), and the
connected regions of each color are measured (box, area, center). Regions of the same color
with a similar size and shape are printed as groups: they are candidates for one repeated
object (rotation and mirroring are allowed, scale changes up to about 15 %). The most frequent
color is taken as the background and is not grouped. Check each group at a zoom before you make
it one canonical form. Writes /tmp/regions.png (2x) with numbered boxes, grouped ones in red.
"""
import sys

import cv2
import numpy as np
from PIL import Image


def main():
    path = sys.argv[1]
    n_colors = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    min_area = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    img = np.array(Image.open(path).convert('RGB'))
    flat = img.reshape(-1, 3)
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    palette = colors[np.argsort(-counts)[:n_colors]].astype(float)
    nearest = np.argmin(((flat[:, None, :].astype(float) - palette[None]) ** 2).sum(2), axis=1).reshape(img.shape[:2])
    regions = []
    for ci in range(len(palette)):
        num, lab, st, cen = cv2.connectedComponentsWithStats((nearest == ci).astype(np.uint8))
        for i in range(1, num):
            x, y, w, h, a = st[i]
            if a < min_area or (w >= img.shape[1] - 1 and h >= img.shape[0] - 1):
                continue
            mask = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
            hu = cv2.HuMoments(cv2.moments(mask, True)).ravel()
            hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-30)
            regions.append(dict(color=ci, box=(int(x), int(y), int(w), int(h)), area=int(a),
                                center=(round(float(cen[i][0]), 1), round(float(cen[i][1]), 1)), hu=hu[:4]))
    print('colors:', ' '.join('%d=#%02x%02x%02x' % (i, *map(int, c)) for i, c in enumerate(palette)))
    for k, r in enumerate(regions):
        r['id'] = k
    # Group regions of one color with similar area and shape (Hu moments ignore rotation and mirroring)
    groups, used = [], set()
    for r in sorted(regions, key=lambda r: -r['area']):
        if r['id'] in used or r['color'] == 0:
            continue
        g = [q for q in regions if q['id'] not in used and q['color'] == r['color']
             and abs(q['area'] - r['area']) <= 0.3 * r['area'] and np.abs(q['hu'] - r['hu']).max() < 0.35]
        if len(g) > 1:
            groups.append(g)
            used.update(q['id'] for q in g)
    print(f'{len(regions)} regions')
    for g in groups:
        print(f'group of {len(g)} (color {g[0]["color"]}, area about {g[0]["area"]}):',
              ', '.join(f'#{q["id"]} at {q["center"]}' for q in g))
    vis = cv2.cvtColor((img * 0.6 + 100).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    vis = cv2.resize(vis, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    grouped = {q['id'] for g in groups for q in g}
    for r in regions:
        x, y, w, h = r['box']
        col = (0, 0, 255) if r['id'] in grouped else (0, 160, 0)
        cv2.rectangle(vis, (2 * x, 2 * y), (2 * (x + w), 2 * (y + h)), col, 1)
        cv2.putText(vis, str(r['id']), (2 * x + 2, 2 * y + 10), cv2.FONT_HERSHEY_PLAIN, 0.8, col, 1)
    cv2.imwrite('/tmp/regions.png', vis)


if __name__ == '__main__':
    main()
