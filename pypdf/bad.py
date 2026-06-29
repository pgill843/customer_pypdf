"""Merge two PDFs into one using pypdf."""

import argparse
from pathlib import Path

from pypdf import PdfWriter


def merge_pdfs(pdf_a: Path, pdf_b: Path, output: Path) -> None:
    """Append every page of pdf_b after pdf_a and write to output."""
    writer = PdfWriter()
    writer.append(pdf_a)
    writer.append(pdf_b)
    writer.write(output)


def main() -> None:
    """Parse CLI arguments and merge two PDF files."""
    parser = argparse.ArgumentParser(description="Merge two PDFs into one.")
    parser.add_argument("pdf_a", type=Path, help="First PDF (pages come first)")
    parser.add_argument("pdf_b", type=Path, help="Second PDF (pages appended after)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output PDF file path",
    )
    args = parser.parse_args()

    for path in (args.pdf_a, args.pdf_b):
        if not path.is_file():
            parser.error(f"File not found: {path}")

    merge_pdfs(args.pdf_a, args.pdf_b, args.output)


if __name__ == "__main__":
    main()
