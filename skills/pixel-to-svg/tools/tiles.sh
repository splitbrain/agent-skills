#!/bin/sh
# Side by side review tiles (source left, SVG right) that cover the whole image:
# tiles.sh SOURCE.png SVG [TILE] [SCALE] [OUTDIR]   (default tile 96, scale 4, out /tmp/tiles)
# Neighbor tiles overlap by a quarter tile, so no object is only seen cut at a tile border.
# Prints one line per tile: the file name and the box X Y W H in source pixels.
dir=$(dirname "$(realpath "$0")")
src=$1; svg=$2; t=${3:-96}; sc=${4:-4}; out=${5:-/tmp/tiles}
mkdir -p "$out"
size=$(magick identify -format '%w %h' "$src")
W=${size% *}; H=${size#* }
step=$((t * 3 / 4))
y=0
while :; do
  x=0
  while :; do
    f="$out/tile_${x}_${y}.png"
    sh "$dir/compare.sh" "$src" "$svg" "$x" "$y" "$t" "$t" "$sc" "$f" >/dev/null
    echo "$f $x $y $t $t"
    [ $((x + t)) -ge "$W" ] && break
    x=$((x + step))
  done
  [ $((y + t)) -ge "$H" ] && break
  y=$((y + step))
done
