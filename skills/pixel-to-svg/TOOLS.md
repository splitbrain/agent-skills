# Tools

All tools are in the `tools` folder. Run the Python tools from that folder or add it to
`PYTHONPATH`, because they import each other. Images are PNG files; coordinates are source
pixels. Most tools work with any material; the line network tools are for backgrounds made of
thin lines.

## Look, measure and compare

| Tool | Use |
|---|---|
| `node render.mjs IN OUT.png [SCALE] [X Y W H]` | Render an SVG or PNG with Chromium at a scale, optionally cropped to a box. |
| `compare.sh SOURCE.png SVG X Y W H [SCALE] [OUT]` | Source crop on the left, SVG crop on the right. Default scale 4. |
| `tiles.sh SOURCE.png SVG [TILE] [SCALE] [OUTDIR]` | Comparison tiles that cover the whole image, with overlap. Default tile 96, scale 4. Use them for the full review. |
| `gridzoom.sh IMAGE X Y W H [SCALE] [OUT]` | Crop with a labeled 10 px grid, to read coordinates. |
| `palette.py IMAGE [N]` | The most frequent colors with pixel counts. |
| `regions.py IMAGE [COLORS] [MIN_AREA]` | Flat color regions with box, area and center, and groups of regions with a similar shape (candidates for repeated objects); writes `/tmp/regions.png`. |
| `polys.py IMAGE COLOR X0 Y0 X1 Y1 [EPS] [MIN_AREA]` | Corner points of the areas of one color in a box, to measure positions and sizes. Never use them as output. |

## Drawing and building

| Tool | Use |
|---|---|
| `draw.py` | Primitives (`path`, `poly`, `stroke`, `circle`, `ellipse`, `rect`, `group`), transforms (`tf`), polylines with rounded corners (`rounded`), smooth curves (`curve`), `Scene` (`define`, `use`, `add`, `svg`), path compaction and `count_nodes`. |
| `build.py IMAGE COMPOSITION.py OUT.svg [NET.py]` | Build one SVG from a composition module (`build(scene)`, optional `back(scene)` and `BG`) and an optional line network. |
| `fit.py` | `fit(src, dst, mirror)` gives a similarity transform, `affine(src, dst)` an SVG matrix. Use them to place a template onto measured points. |
| `curvefit.py IMAGE NODES.json COLOR [SCALE] [edge] [nofit]` | Fit the handles of a `curve` along a stroke of one color, or with `edge` along the border of a filled area of one color; writes `/tmp/curve.png`. |

`draw.curve` takes nodes `(x, y, angle, h_in, h_out)`: the point, the direction of travel in
degrees (0 = +x, 90 = +y) and the handle lengths before and after the point.

## Line networks

For backgrounds and diagrams made of thin lines of one color and width: straight segments,
rectangles with rounded corners, and filled dots.

| Tool | Use |
|---|---|
| `lines.py IMAGE BG LINE WIDTH > net.py` | First draft of the network file. |
| `netview.py IMAGE NET.py X Y W H [SCALE] [OUT]` | The snapped network in magenta over the source, with path ids and a grid. |
| `linecheck.py IMAGE NET.py` | Network alone against the source: `/tmp/linecheck.png` shows missed line pixels in red and lines over plain background in blue. |
| `linecheck.py IMAGE NET.py OUT.svg` | Source line pixels that the finished SVG shows as plain background. |

A network file is a Python file:

```python
BG = '#1ab6d6'      # background color
LINE = '#1e92aa'    # line color
WIDTH = 2           # line width
CORNER = 2          # corner radius of the polylines
NET = [             # rough polylines: 'x,y x,y ...' and closed
    ('20,10 120,10 120,80 20,80', True),
    ('130,5 130,60 170,60', False),
]
DOTS = [(140.5, 30, 4)]   # filled dots (x, y, r) in the line color
```

`netlib.py` holds the extraction and the snapping. `network.py` draws a network file into a
Scene.
