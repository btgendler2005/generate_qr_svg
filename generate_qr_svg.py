#!/usr/bin/env python3
"""Generate a QR code as an SVG file suitable for 3D printing (extrusion)."""
import argparse
import base64
import mimetypes
import re
import sys

try:
    import qrcode
except ImportError:
    sys.exit("Missing dependency. Install with: pip install qrcode")

MAX_RECOMMENDED_LOGO_SCALE = 0.30


def clear_logo_area(matrix, module_size_mm, border_modules, clear_zone_mm):
    """Blank out modules whose center falls inside clear_zone_mm (x0, y0, x1, y1)."""
    if clear_zone_mm is None:
        return matrix
    cx0, cy0, cx1, cy1 = clear_zone_mm
    size = len(matrix)
    cleared = [list(row) for row in matrix]
    for y in range(size):
        my = (y + border_modules + 0.5) * module_size_mm
        if my < cy0 or my > cy1:
            continue
        for x in range(size):
            mx = (x + border_modules + 0.5) * module_size_mm
            if cx0 <= mx <= cx1:
                cleared[y][x] = False
    return cleared


def build_qr_rects(matrix, module_size_mm, border_modules, merge_rows):
    size = len(matrix)
    rects = []
    for y, row in enumerate(matrix):
        x = 0
        while x < size:
            if row[x]:
                start = x
                if merge_rows:
                    while x < size and row[x]:
                        x += 1
                else:
                    x += 1
                width = x - start
                rx = (start + border_modules) * module_size_mm
                ry = (y + border_modules) * module_size_mm
                rw = width * module_size_mm
                rects.append(
                    f'<rect x="{rx:.3f}" y="{ry:.3f}" width="{rw:.3f}" height="{module_size_mm:.3f}"/>'
                )
            else:
                x += 1
    return rects


def parse_svg_dimensions(svg_text):
    m = re.search(r'<svg\b[^>]*\bviewBox="([^"]+)"', svg_text)
    if m:
        parts = re.split(r"[\s,]+", m.group(1).strip())
        if len(parts) == 4:
            return float(parts[2]), float(parts[3])
    m_w = re.search(r'<svg\b[^>]*\bwidth="([\d.]+)', svg_text)
    m_h = re.search(r'<svg\b[^>]*\bheight="([\d.]+)', svg_text)
    if m_w and m_h:
        return float(m_w.group(1)), float(m_h.group(1))
    sys.exit("Could not determine logo dimensions: SVG has no viewBox or width/height")


def extract_svg_inner(svg_text):
    m = re.search(r"<svg\b[^>]*>(.*)</svg>", svg_text, re.DOTALL)
    if not m:
        sys.exit("Could not parse logo SVG: no <svg>...</svg> content found")
    return m.group(1)


def build_logo_element(logo_path, box_x0, box_y0, box_w, box_h):
    """Return an SVG snippet that fits logo_path's artwork into the given box, centered."""
    if logo_path.lower().endswith(".svg"):
        with open(logo_path, "r") as f:
            svg_text = f.read()
        inner_w, inner_h = parse_svg_dimensions(svg_text)
        inner = extract_svg_inner(svg_text)
        scale = min(box_w / inner_w, box_h / inner_h)
        scaled_w = inner_w * scale
        scaled_h = inner_h * scale
        tx = box_x0 + (box_w - scaled_w) / 2
        ty = box_y0 + (box_h - scaled_h) / 2
        return f'<g transform="translate({tx:.3f},{ty:.3f}) scale({scale:.5f})">{inner}</g>'
    else:
        with open(logo_path, "rb") as f:
            data = f.read()
        mime = mimetypes.guess_type(logo_path)[0] or "image/png"
        b64 = base64.b64encode(data).decode("ascii")
        return (
            f'<image x="{box_x0:.3f}" y="{box_y0:.3f}" width="{box_w:.3f}" height="{box_h:.3f}" '
            f'preserveAspectRatio="xMidYMid meet" '
            f'href="data:{mime};base64,{b64}"/>'
        )


def build_svg(matrix, module_size_mm, border_modules, merge_rows, logo_path=None, logo_scale=0.22):
    size = len(matrix)
    total_modules = size + 2 * border_modules
    total_mm = total_modules * module_size_mm

    clear_zone_mm = None
    if logo_path:
        box_size = total_mm * min(logo_scale, MAX_RECOMMENDED_LOGO_SCALE)
        box_x0 = (total_mm - box_size) / 2
        box_y0 = box_x0
        clear_zone_mm = (box_x0, box_y0, box_x0 + box_size, box_y0 + box_size)
        matrix = clear_logo_area(matrix, module_size_mm, border_modules, clear_zone_mm)

    rects = build_qr_rects(matrix, module_size_mm, border_modules, merge_rows)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_mm:.3f}mm" height="{total_mm:.3f}mm" '
        f'viewBox="0 0 {total_mm:.3f} {total_mm:.3f}">',
        '<g fill="black">',
    ]
    svg.extend(rects)
    svg.append("</g>")

    if logo_path:
        x0, y0, x1, y1 = clear_zone_mm
        svg.append(build_logo_element(logo_path, x0, y0, x1 - x0, y1 - y0))

    svg.append("</svg>")
    return "\n".join(svg)


def main():
    parser = argparse.ArgumentParser(description="Generate a QR code SVG for 3D printing.")
    parser.add_argument("data", help="Text/URL to encode")
    parser.add_argument("-o", "--output", default="qrcode.svg", help="Output SVG path")
    parser.add_argument(
        "--module-size", type=float, default=2.0, help="Size of one QR module in mm (default 2.0)"
    )
    parser.add_argument(
        "--border", type=int, default=4, help="Quiet zone width in modules (default 4)"
    )
    parser.add_argument(
        "--ec",
        choices=["L", "M", "Q", "H"],
        default="H",
        help="Error correction level (default H, most robust for embossed/engraved codes)",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Emit one rect per module instead of merging adjacent modules in a row (more shapes, simpler geometry per shape)",
    )
    parser.add_argument(
        "--logo",
        help="Path to a logo file (SVG recommended, PNG/JPG also supported) to overlay centered on the QR code",
    )
    parser.add_argument(
        "--logo-scale",
        type=float,
        default=0.22,
        help="Logo size as a fraction of the total QR code width (default 0.22, capped at 0.30)",
    )
    args = parser.parse_args()

    if args.logo:
        if args.logo_scale > MAX_RECOMMENDED_LOGO_SCALE:
            print(
                f"Warning: --logo-scale {args.logo_scale} exceeds the max of "
                f"{MAX_RECOMMENDED_LOGO_SCALE}; capping at {MAX_RECOMMENDED_LOGO_SCALE} "
                "to avoid an unscannable code.",
                file=sys.stderr,
            )
        if args.ec != "H":
            print(
                "Warning: --logo works best with high error correction; forcing --ec H.",
                file=sys.stderr,
            )
            args.ec = "H"

    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }

    qr = qrcode.QRCode(error_correction=ec_map[args.ec], box_size=1, border=0)
    qr.add_data(args.data)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    svg = build_svg(
        matrix,
        args.module_size,
        args.border,
        merge_rows=not args.no_merge,
        logo_path=args.logo,
        logo_scale=args.logo_scale,
    )

    with open(args.output, "w") as f:
        f.write(svg)

    size = len(matrix) + 2 * args.border
    print(
        f"Wrote {args.output}: {size}x{size} modules, "
        f"{size * args.module_size:.1f}mm x {size * args.module_size:.1f}mm "
        f"(module size {args.module_size}mm, EC level {args.ec})"
    )


if __name__ == "__main__":
    main()
