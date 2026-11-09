// Render an SVG (or PNG) file with Chromium: node render.mjs IN OUT.png [SCALE] [X Y W H]
// The optional box is in source pixels and crops the output. Playwright is loaded from the
// module path in the environment variable PLAYWRIGHT (default: the "playwright" package).
import fs from 'node:fs';
import path from 'node:path';

const [input, output, scaleArg, ...box] = process.argv.slice(2);
const scale = Number(scaleArg || 1);
const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright');

// The view port is the image size, read from the SVG attributes or the PNG header
const file = path.resolve(input);
let width = 0;
let height = 0;
if (file.endsWith('.svg')) {
  const head = fs.readFileSync(file, 'utf8').slice(0, 2000);
  const vb = head.match(/viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"/);
  width = Number(head.match(/width="([\d.]+)"/)?.[1] || vb?.[1]);
  height = Number(head.match(/height="([\d.]+)"/)?.[1] || vb?.[2]);
} else {
  const png = fs.readFileSync(file);
  width = png.readUInt32BE(16);
  height = png.readUInt32BE(20);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Math.ceil(width), height: Math.ceil(height) }, deviceScaleFactor: scale });
await page.setContent(`<body style="margin:0"><img id="i" src="data:${file.endsWith('.svg') ? 'image/svg+xml' : 'image/png'};base64,${fs.readFileSync(file).toString('base64')}" style="display:block;width:${width}px;height:${height}px;image-rendering:${file.endsWith('.svg') ? 'auto' : 'pixelated'}"></body>`);
await page.waitForFunction(() => document.getElementById('i').complete);
const opts = { path: output };
if (box.length === 4) {
  const [x, y, w, h] = box.map(Number);
  const cx = Math.max(0, x);
  const cy = Math.max(0, y);
  opts.clip = { x: cx, y: cy, width: Math.min(w, width - cx), height: Math.min(h, height - cy) };
}
await page.screenshot(opts);
await browser.close();
