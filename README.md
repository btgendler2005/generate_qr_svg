# generate_qr_svg

Generate a QR code as a clean, transparent SVG made of solid rectangles — no
anti-aliasing, no background fill — so it can be imported into a slicer or
CAD tool (e.g. Blender) and extruded into a 3D-printable model.

## Requirements

- Python 3.7+
- [`qrcode`](https://pypi.org/project/qrcode/) package

## Install

```bash
git clone https://github.com/btgendler2005/generate_qr_svg.git
cd generate_qr_svg
pip install -r requirements.txt
```

## Usage

```bash
python3 generate_qr_svg.py "https://example.com" -o qrcode.svg
```

The first argument is the text or URL to encode. Output defaults to
`qrcode.svg` in the current directory.

### Options

| Flag | Default | Description |
|---|---|---|
| `-o`, `--output` | `qrcode.svg` | Output SVG file path |
| `--module-size` | `2.0` | Size of one QR "pixel" in mm. Keep this ≥1.5–2mm on FDM printers so modules don't fuse together |
| `--border` | `4` | Quiet-zone width in modules (per the QR spec, don't go below this or some scanners will fail) |
| `--ec` | `H` | Error-correction level: `L`, `M`, `Q`, or `H`. Defaults to `H` (highest), since embossed/engraved codes lose contrast |
| `--no-merge` | off | Emit one rect per module instead of merging adjacent same-row modules into wider rects |
| `--logo` | none | Path to a logo file (SVG recommended; PNG/JPG also works) to overlay centered on the QR code |
| `--logo-scale` | `0.22` | Logo size as a fraction of the total QR code width. Hard-capped at `0.30` — anything larger risks an unscannable code |

### Examples

Bigger, chunkier modules for a large sign:

```bash
python3 generate_qr_svg.py "https://example.com" -o sign.svg --module-size 4 --border 4
```

One rect per module (uniform squares, useful if your downstream tool needs it):

```bash
python3 generate_qr_svg.py "https://example.com" -o qrcode.svg --no-merge
```

Overlay a logo in the center (e.g. to brand a QR code for your Instagram,
Etsy, or Hotplate profile):

```bash
python3 generate_qr_svg.py "https://instagram.com/yourhandle" -o qrcode.svg --logo instagram-logo.svg
```

## Adding a platform logo (Facebook, Instagram, Etsy, Hotplate, etc.)

`--logo` overlays any SVG (or PNG/JPG) you point it at, centered on the QR
code, with the modules underneath automatically cleared and error correction
forced to `H` so the code stays scannable.

This tool does **not** ship with Facebook/Instagram/Etsy/etc. logos bundled
in — those are trademarked assets, and each platform requires you to use
their logo unmodified and sourced from their own official brand/press
resources (not a copy someone else made). Grab the SVG from the platform's
official brand page, then run:

```bash
python3 generate_qr_svg.py "https://etsy.com/shop/yourshop" -o qrcode.svg --logo etsy-logo.svg
```

If a platform only distributes PNG logos, `--logo` will accept that too, but
note that a raster image won't extrude as 3D geometry in Blender — for
printing, either trace it to vector first (e.g. Inkscape's "Trace Bitmap")
or use it only for a non-printed digital SVG.

### Why this doesn't break scanning

QR codes carry redundant data (error correction), so covering part of the
center is recoverable as long as it stays away from the three corner
"finder" squares and the covered area is a modest fraction of the total
code. `--logo-scale` is capped at `0.30` (30% of the code's width) and forces
`--ec H` (30% error correction budget) for this reason — tested up through
0.30 the code still decodes reliably; pushing past that starts to fail.

## Output

The SVG has real-world dimensions — `width`/`height` and `viewBox` are both in
millimeters — so importing it into Blender or any CAD tool at 1 SVG unit =
1mm gives you correct physical dimensions with no extra scaling. There is no
background rectangle; only the black QR modules are drawn, so the shape is
ready to extrude directly.

## 3D printing tips

- Use `--ec H` (default) — physical processes (engraving, embossing, low
  print resolution) reduce effective contrast, and high error correction
  keeps the code scannable.
- Keep `--module-size` at least 1.5–2mm for FDM printers; smaller modules
  risk merging together or not resolving at all.
- Don't shrink `--border` below the default of 4 modules — scanners rely on
  the quiet zone to detect the code's edges.
- After generating the SVG, import it into Blender (or your slicer/CAD tool
  of choice) and extrude it to your desired height.
