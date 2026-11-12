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

The user expects an acceptable result in one pass, without having to point out faults. Review
your own work as strictly as the user would, and fix every fault you find before you report.

## Principles

- **Do not replicate pixels.** Use pixel measurements only to get coordinates and parameters.
  The output is rectangles, circles, ellipses, straight lines, smooth curves and polygons with
  few, logically placed nodes.
- **Understand what is depicted.** Decide from the meaning whether the drawing is right, not
  only from the pixels. Parts that connect must touch (a strap ends at its buckle, a branch
  grows out of its trunk, an arrow ends at its target). Geometry follows from the object
  (spokes meet the hub, a reflection mirrors its object, text sits on its baseline, a liquid
  surface is level).
- **Identify before you draw.** Find out what each object is and what form the artist gave it,
  and draw that form. Do not draw what such an object usually looks like. A flask can be one
  glass outline that flares from the neck into the bulb, not a neck set on a circle.
- **Shapes before shading.** Users judge the objects: their outlines, the number of parts, how
  the parts join and from which side they are seen. Get these right first. Shading only has to
  match the style of the source.
- **Related measurements agree.** Parts of one object share their geometry. A disc inside a
  gear has the center of the gear, rings of a dial share one center, the ends of a pipe meet
  their fittings. Fit related parts together and check the relation by numbers.
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

Choose the result from the kind of source. Ask the user only when the source leaves a real
choice (true pixel art) or when this method does not fit (photos).

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

Then look at each object at 6x to 8x with `gridzoom.sh` and write an object record in the
project folder (`objects.md`). For each object, write down:

- What it is and from which side it is seen. A round part seen at an angle is an ellipse, and
  a tube seen at an angle shows its depth as a crescent.
- Its parts, and for each part whether it is one closed outline or several. One physical piece
  is one outline, also when it has a narrow and a wide section.
- Each joint: which part touches which part, where, and which one is in front.
- Shared geometry with other parts and objects: centers, axes, alignment.
- The small parts on it: rivets, seams, screws, knobs, collars, clamps, caps.
- The coordinates of its outline points and centers, read from the grid.

Draw from this record, and correct the record when the source shows that it is wrong.

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
  At a joint, let the part in front overlap the part behind by a few pixels, so that the
  background cannot show through.
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

The review decides whether the result is acceptable. Do all of it before you report anything.

1. Render tiles of the whole image with `tiles.sh` at scale 4 or more, and look at every tile.
   A region that looks right at 2x can still be wrong.
2. In each tile, take the objects of the record one by one and compare the source with the SVG:
   - Outline: the same form and the same number of pieces. One piece in the source is one
     piece in the SVG, without a line across it. No seam of the source is missing.
   - Joints: every part that touches another part in the source touches it in the SVG. Look at
     each joint alone at 6x or more (`compare.sh` on a small box). No background shows through.
   - View: the same side and angle. Ellipses where the source has ellipses, and the depth of
     tubes and cylinders where the source shows it.
   - Geometry: shared centers, alignment, symmetry, identical copies. Measure them.
   - Parts: nothing invented (a slab, a bar or a ring that the source does not have), nothing
     missing (knobs, collars, caps, small fittings, seams), and no two parts merged into one.
   - Draw order at each crossing and overlap.
   - Anti aliasing, halos and compression artifacts were not drawn as features.
   - Node economy: no traced outlines, no leftover or duplicate drawing.
   - For line networks, `linecheck.py IMAGE NET.py OUT.svg`: every listed place is an object
     edge or removed content, or it is fixed.
3. Write each fault into a review log (`review.md`): the tile, the object and the fault. Fix
   all of them.
4. After each fix, render the whole tile again, not only the fixed part. A fix often shows
   the next fault nearby, or moves a joint apart.
5. Do the full pass over all tiles again. Stop only when a complete pass finds no fault in
   outlines, joints, view, geometry or parts.

Differences in shading do not keep the review going. Differences in shapes and objects do.

These faults passed weak reviews and the user found them:

- An upper arm that ended above the forearm, with background in the gap.
- A flask drawn as a neck shape on top of a circle, with a line where they meet, where the
  source has one glass outline.
- A goggle drawn from the front, where the source shows it from the side.
- A light disc in a gear that was not centered on the gear.
- A dark slab under a flask that the source does not have, and one long bar where the source
  has a rod with a knob, a collar and a separate clamp arm.

### 5. Report

Report only after a review pass without faults. Show the full comparison image (source left,
SVG right) at 2x or 3x, and list the differences that remain, such as simplified shading or
hidden parts that you completed. Do not give an unreviewed draft to the user, and do not ask
the user to find faults. Ask the user only about decisions that are theirs: content changes,
and the kind of result when the source leaves a real choice. Offer options as rendered images
when the user must decide on new content. When the user sends review notes, apply them in the
project files, rebuild every image that uses a changed library object, and do the full review
again.

## Sub-agents

A set of images is a long job. Write a brief for sub-agents in the project folder: the user's
standards, the content decisions, the tools, the file layout, the review checklist and the
report format. Then give each image fresh agents for its steps, strictly one at a time, for
example one for the background, one for the objects and one that only reviews and fixes.
After each agent, do the full review of step 4 yourself and send back what is wrong. Typical
faults:
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
- Two fits of related parts that are made one by one give different centers. Fit them together,
  or fit the main object first and derive the other parts from it.
- A library change must leave the other images byte-identical unless the change is meant for
  them. Rebuild and compare after every library change.
