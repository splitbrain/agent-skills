---
name: pixel-to-svg
description: Redraws raster graphics (game backgrounds and sprites, icons, logos, comics, diagrams, maps, UI mockups, low resolution illustrations) as clean SVG files that scale without loss. The SVG is built from shapes and shared objects, not from traced pixels. Use when asked to convert, vectorize, trace or redraw a raster image as SVG, or to review and fix such an SVG.
---

# Raster graphics to SVG

The result must look like the artwork at any size, with few nodes. Tracing the pixels gives
wobbly outlines, gaps and thousands of nodes, and users reject it. Read the image like the
artist drew it instead: find the layers and the objects, understand what each object is, and
draw it again from primitives. Objects that occur more than once get one canonical form that
every copy uses.

## Principles

- **Do not replicate pixels.** Use pixel measurements only to get coordinates and parameters.
  The output is rectangles, circles, ellipses, straight lines, smooth curves and polygons with
  few, logically placed nodes.
- **Understand what is depicted.** Decide from the meaning whether the drawing is right, not
  only from the pixels. Parts that connect must touch (a strap ends at its buckle, a branch
  grows out of its trunk, an arrow ends at its target). Geometry follows from the object
  (spokes meet the hub, a reflection mirrors its object, text sits on its baseline, a liquid
  surface is level).
- **Low resolution lies.** Anti aliased edges, halos, JPEG blocks, dithering and shading strips
  are not cracks, gaps or extra lines. Blobs of a few pixels can be small figures, sparks,
  splashes or letters. Zoom in at 10x and ask what the artist drew. When the meaning stays
  unclear, ask the user.
- **Layers.** Find the layers from back to front: the background, things behind other things,
  and the objects in front. A layer continues behind the layers in front of it, so draw it
  complete where it is hidden, with plausible shapes.
- **One canonical form per repeated object.** Copies differ only by a transform (move, rotate,
  scale, mirror) or by parameters, sometimes with extra decoration on top. Look at all copies,
  in all images of the set, before you fix the form.
- **Judge at 300 % or more.** The point of SVG is scaling. Problems hide at 1x.
- **Nothing invented, nothing missing.** Every detail of the SVG exists in the source (or in a
  content change the user decided), and every detail of the source exists in the SVG.

Node guide: a rectangle is one element; a circle or an ellipse is one element; a smooth curve
needs about one cubic segment per 90 degrees of turning; an organic outline needs about one
node per lobe, tip or notch; a repeated object costs one `<use>` per copy. The SVG is usually
smaller than a PNG of the same artwork.

## Kinds of source material

Decide with the user which result is wanted before you start.

- **Flat art with anti aliased edges** (most cartoon, game and icon art): the main case of this
  skill. Each flat color area becomes a shape.
- **True pixel art** (hard pixel edges, a small palette, the pixels are the style): either keep
  the pixel look (merge pixels of one color into rectangles or polygons with right angles) or
  reinterpret it as smooth shapes. Ask which one the user wants.
- **Shaded art** (gradients, soft shadows): use SVG gradients and a few flat shading shapes.
  Match the shading at the level of the style, not pixel by pixel.
- **Photos and painted textures**: they do not fit this method. Tell the user, and suggest a
  stylized redraw or keeping a raster image for those parts.
- **Text**: identify the font or use a similar font, and set the text as text or as glyph
  outlines. Do not trace letters.

## Setup

The tools are in the `tools` folder next to this file. `TOOLS.md` describes each tool. They
need python3 with numpy, scipy, scikit-image, opencv and pillow, node with Playwright and its
Chromium, and ImageMagick (`magick`). Set `PLAYWRIGHT` to the Playwright module path if
`import('playwright')` does not find it. Render with Chromium (or the target renderer of the
project), because other renderers differ in small ways.

Keep the work in a project folder: the source images, one composition module per image with
`build(scene)`, a `library` package with the canonical objects, a catalog file that lists each
object with its origin, orientation and the images that use it, and an `out` folder. Render a
sheet with every library object and check it after each change. Show results to the user as
images.

## Write your own tools

The tools here cover common jobs. Every source has its own structures, and specialized tools
pay off fast: write them in the project folder as soon as you measure the same kind of thing
twice. Good tools measure parameters of a known form and never output traced pixels. Examples
of tools that were worth writing:

- a fitter for a template object (all gears of an image share one design: fit center, size,
  angle and color of each copy, and test the draw order of overlapping copies)
- an ellipse or circle fit for rings, orbits, wheels and dials (`cv2.fitEllipse`, or a least
  squares fit of the pixels to several ellipses at once)
- a center line sampler for tubes and roads of one color, as input for a smooth curve
- a color class map that shows where a tinted layer (a light beam, a shadow, glass) changes
  the colors below it
- a checker that renders the SVG and compares it with the source for one color class

Build each tool on `draw.py` and `render.mjs`, so that it uses the same primitives and the
same renderer as the result.

## Process

### 1. Survey

Print the palette (`palette.py`) and use these exact colors. Run `regions.py` to list the flat
color regions and the groups of regions that look alike, which are candidates for repeated
objects. Look at the whole image at 2x to 3x and at each region at 4x to 6x. Write an
inventory: the layers, every object, what it is, what it connects to, and which objects repeat.
With a set of images, survey all of them first, because objects repeat across images.

Ask the user about content that must change (people, logos, copyrighted characters). Agree on
replacements before you draw them, and show a design image of any new object first.

### 2. Background

Choose the technique by the kind of background:

- **Plain color or gradient**: one rectangle, with an SVG gradient if needed.
- **Repeating pattern or tiles**: draw one tile and repeat it with `<use>` or an SVG
  `<pattern>`. Measure the period exactly.
- **Line structures** (circuit or blueprint lines, map grids, diagram connectors): use the line
  network tools, see below.
- **Scenery** (sky, hills, walls, floors): large shapes per color area with smooth outlines and
  few nodes (`curvefit.py edge`), continued under the objects in front.

Line networks: run `lines.py` for a first draft of the network file. The draft is wrong in
typical ways. It holds pieces of objects drawn in the line color, it misses lines behind
objects, and it can put dots on line crossings. Curate it by hand with `netview.py` and
`gridzoom.sh`, region by region at scale 5 or more. Delete pieces of objects, join lines that
continue behind objects (as a straight continuation, a corner or a T onto another line, with
the hidden end under the object), and keep only real dots. The rough polylines need only about
2 px accuracy, because the build refits every segment to the line pixels. Lines seen through a
tinted layer have another color and must be placed by hand. Run `linecheck.py` until nothing
is blue and every red place is an object.

### 3. Objects

For each object, write a library function with a docstring that states the origin and the
orientation of its local coordinates. Draw the form once (`scene.define`) and place every copy
with `scene.use` and a transform. Fit transforms to measured points with `fit.py`: a similarity
fit (with mirroring) for clean copies, an affine fit for hand drawn copies that are slightly
skewed. Use parameters instead of non-uniform scaling when a form must be flatter or longer,
because a squashed template distorts circles and line widths.

- **Connections.** When objects plug into each other, let the object that receives the other
  one return its connection point and direction, and make the other object end exactly there.
- **Curves.** Use `draw.curve` (cubic segments with a direction and handle lengths per node)
  for every smooth line and outline, and fit the handles with `curvefit.py`: along a stroke
  (wires, hair, contour lines) or along the edge of a filled area (blobs, hills, bodies). A loop
  in the source is a closed loop in the SVG.
- **Order.** Draw back to front as the source shows what covers what. A composition can draw
  things behind the line network in `back(scene)`.
- **Transparency.** Draw overlapping translucent shapes as opaque shapes inside one group with
  the opacity, so overlaps do not get brighter. Where a tinted layer changes the colors below
  it, draw the covered drawing a second time in the tinted colors, clipped to the layer
  (`network.draw_network` defines the network without a color for this).
- **Organic shapes** need both round lobes and sharp tips or notches. Place one node per lobe,
  tip or notch.

### 4. Review

Go through the image region by region with `compare.sh` at scale 4 or more. Check every item
and write the result down:

- Connections: every part that should touch another part touches it, without gap or overshoot.
- Concept: each object reads as what it is; geometric relations hold (shared centers,
  alignment, symmetry, identical copies).
- Draw order, and nothing invented or missing.
- Anti aliasing, halos and compression artifacts were not drawn as features.
- Node economy: no traced outlines, no leftover or duplicate drawing.
- For line networks, `linecheck.py IMAGE NET.py OUT.svg`: every listed place is an object edge
  or removed content, or it is fixed.

### 5. Work with the user

Show comparison images (source left, SVG right) at 3x, one image for each question. Offer
options as rendered images when the user must decide on new content. Apply review notes in the
project files and rebuild every image that uses a changed library object.

## Sub-agents

A set of images is a long job. Write a brief for sub-agents in the project folder: the user's
standards, the content decisions, the tools, the file layout, the review checklist and the
report format. Then give each image fresh agents for its steps, strictly one at a time, for
example one for the background, one for the objects and one that only reviews and fixes.
After each agent, look at its previews yourself and send back what is wrong. Typical faults:
traced shapes with dozens of points, wrong concepts (leaves instead of splashes, a blob instead
of an animal), invented details, and library changes that break earlier images.

## Pitfalls

- Edges of dark objects mix to a lighter color and look like thin lines of that color. Mask
  the objects before you extract lines.
- A fit of a short piece tilts toward neighbor pixels of a similar color. Add a node where the
  piece is hidden, or split it.
- Path compaction with relative coordinates must round the absolute coordinates first.
  Otherwise the rounding errors add up and closed shapes do not close.
- Fixed temporary file names collide when two renders run at the same time.
- A library change must leave the other images byte-identical unless the change is meant for
  them. Rebuild and compare after every library change.
