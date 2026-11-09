#!/bin/sh
# Side by side crop of the source image (left) and an SVG (right), both rendered by Chromium:
# compare.sh SOURCE.png SVG X Y W H [SCALE] [OUT.png]   (default scale 4, default out /tmp/compare.png)
dir=$(dirname "$(realpath "$0")")
src=$1; svg=$2; x=$3; y=$4; w=$5; h=$6; sc=${7:-4}; out=${8:-/tmp/compare.png}
tmp=$(mktemp -d)
node "$dir/render.mjs" "$src" "$tmp/a.png" "$sc" "$x" "$y" "$w" "$h" &&
node "$dir/render.mjs" "$svg" "$tmp/b.png" "$sc" "$x" "$y" "$w" "$h" &&
magick "$tmp/a.png" "$tmp/b.png" +append +repage "$out"
rm -rf "$tmp"
echo "$out"
