#!/bin/sh
# Crop of an image (PNG or SVG) with a labeled 10 px grid, to read coordinates:
# gridzoom.sh IMAGE X Y W H [SCALE] [OUT.png]   (default scale 6, default out /tmp/grid.png)
dir=$(dirname "$(realpath "$0")")
img=$(realpath "$1"); x=$2; y=$3; w=$4; h=$5; sc=${6:-6}; out=${7:-/tmp/grid.png}
tmp=$(mktemp -d)
node "$dir/render.mjs" "$img" "$tmp/full.png" 1
size=$(magick identify -format '%w %h' "$tmp/full.png")
W=${size% *}; H=${size#* }
case "$img" in *.svg) mime=image/svg+xml;; *) mime=image/png;; esac
{
  printf '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">' "$W" "$H" "$W" "$H"
  printf '<image href="data:%s;base64,%s" width="%s" height="%s" style="image-rendering:pixelated"/>' "$mime" "$(base64 -w0 "$img")" "$W" "$H"
  printf '<g stroke="#f00" stroke-width="0.12" opacity="0.7">'
  gx=0; while [ $gx -le "$W" ]; do printf '<line x1="%s" y1="0" x2="%s" y2="%s"/>' $gx $gx "$H"; gx=$((gx + 10)); done
  gy=0; while [ $gy -le "$H" ]; do printf '<line x1="0" y1="%s" x2="%s" y2="%s"/>' $gy "$W" $gy; gy=$((gy + 10)); done
  printf '</g><g font-size="2.5" fill="#f00" font-family="sans-serif">'
  gx=0; while [ $gx -lt "$W" ]; do gy=0; while [ $gy -lt "$H" ]; do printf '<text x="%s" y="%s" dx=".3">%s,%s</text>' $gx $((gy + 3)) $gx $gy; gy=$((gy + 20)); done; gx=$((gx + 10)); done
  printf '</g></svg>'
} > "$tmp/grid.svg"
node "$dir/render.mjs" "$tmp/grid.svg" "$out" "$sc" "$x" "$y" "$w" "$h"
rm -rf "$tmp"
echo "$out"
