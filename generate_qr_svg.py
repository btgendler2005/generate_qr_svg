#!/usr/bin/env python3
"""Generate a QR code as an SVG file suitable for 3D printing (extrusion)."""
import argparse
import sys

try:
    import qrcode
except ImportError:
    sys.exit("Missing dependency. Install with: pip install qrcode")


def build_svg(matrix, module_size_mm, border_modules, merge_rows):
    size = len(matrix)
    total_modules = size + 2 * border_modules
    total_mm = total_modules * module_size_mm

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

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_mm:.3f}mm" height="{total_mm:.3f}mm" '
        f'viewBox="0 0 {total_mm:.3f} {total_mm:.3f}">',
        '<g fill="black">',
    ]
    svg.extend(rects)
    svg.append("</g>")
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
    args = parser.parse_args()

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

    svg = build_svg(matrix, args.module_size, args.border, merge_rows=not args.no_merge)

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
