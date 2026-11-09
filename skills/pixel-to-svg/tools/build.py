#!/usr/bin/env python3
"""Build one SVG from a source image and its composition module.

Usage: build.py IMAGE COMPOSITION.py OUT.svg [NET.py]

COMPOSITION.py defines build(scene) and may define back(scene) for drawing that lies behind
the line network, and BG for a plain background fill. NET.py is an optional line network
file (see lines.py); it is drawn between back and build, and its BG is the default fill.
Prints the node count and the file size.
"""
import os
import runpy
import sys

import netlib
from draw import Scene, count_nodes
from network import draw_network, load_net


def main():
    path, comppath, out = sys.argv[1:4]
    img = netlib.load(path)
    net = load_net(sys.argv[4]) if len(sys.argv) > 4 else None
    sys.path.insert(0, os.path.dirname(os.path.abspath(comppath)))
    comp = runpy.run_path(comppath)
    background = comp.get('BG', getattr(net, 'BG', None))
    scene = Scene(img.shape[1], img.shape[0], background)
    if 'back' in comp:
        comp['back'](scene)
    if net:
        draw_network(scene, img, net)
    comp['build'](scene)
    text = scene.svg()
    with open(out, 'w') as f:
        f.write(text)
    print(f'{out}: {count_nodes(text)} nodes, {len(text) / 1024:.1f} KB')


if __name__ == '__main__':
    main()
