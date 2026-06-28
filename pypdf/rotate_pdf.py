"""Rotate all pages in a PDF by a fixed angle."""

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def rotate_pdf(input_path: Path, angle: int, output: Path) -> None:
    """Rotate every page in input_path by angle degrees and write to output."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page.rotate(angle))
    writer.write(output)


def main() -> None:
    """Parse CLI arguments and rotate all pages in a PDF."""
    parser = argparse.ArgumentParser(
        description="Rotate all pages in a PDF by a fixed angle.",
    )
    parser.add_argument("input", type=Path, help="Input PDF file")
    parser.add_argument(
        "angle",
        type=int,
        help="Clockwise rotation in degrees (multiple of 90)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output PDF file path",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"File not found: {args.input}")

    if args.angle % 90 != 0:
        parser.error("Rotation angle must be a multiple of 90")

    rotate_pdf(args.input, args.angle, args.output)


if __name__ == "__main__":
    main()
