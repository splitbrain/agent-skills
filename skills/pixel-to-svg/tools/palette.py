#!/usr/bin/env python3
"""Print the most frequent colors of an image with their pixel counts: palette.py IMAGE [N]

Mixed colors of anti aliased edges show up with small counts; the flat colors of the artwork
are the large ones.
"""
import sys

import numpy as np
from PIL import Image

img = np.array(Image.open(sys.argv[1]).convert('RGB')).reshape(-1, 3)
n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
colors, counts = np.unique(img, axis=0, return_counts=True)
for i in np.argsort(-counts)[:n]:
    print('#%02x%02x%02x' % tuple(colors[i]), counts[i])
