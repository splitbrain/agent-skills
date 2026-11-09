"""Draw a network file into a Scene, and render it alone for checks."""
import runpy

import netlib
from draw import circle, group, rounded, stroke


def load_net(path):
    """Return the network file at path as a simple namespace."""
    return type('Net', (), runpy.run_path(path))


def network_svg(img, net, color=None):
    """Return the snapped network (lines and dots) as SVG drawing; color None leaves it to the parent."""
    corner = getattr(net, 'CORNER', 2)
    d = ''.join(rounded(p, corner, c) for p, c in netlib.snap_all(img, net))
    dots = ''.join(circle(x, y, r, color) for x, y, r in net.DOTS)
    return stroke(d, color, net.WIDTH, stroke_linecap='butt') + group(dots, stroke='none')


def draw_network(scene, img, net, ident='network'):
    """Define the network once without a color and use it in the line color.

    A later <use href="#network"> with another stroke and fill draws it again, for example in
    another color clipped to a tinted layer such as a light beam.
    """
    scene.define(ident, group(network_svg(img, net), id=ident))
    scene.use(ident, stroke=net.LINE, fill=net.LINE)
