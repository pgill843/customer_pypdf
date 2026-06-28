"""Tests for pypdf.rotate_pdf."""

import sys
from unittest.mock import patch

import pytest

from pypdf import PdfReader
from pypdf.rotate_pdf import main, rotate_pdf

from . import RESOURCE_ROOT


def test_rotate_pdf_sets_page_rotation(tmp_path):
    """Rotated output stores the requested rotation on every page."""
    source = RESOURCE_ROOT / "toy.pdf"
    output = tmp_path / "rotated.pdf"
    angle = 90

    rotate_pdf(source, angle, output)

    original = PdfReader(source)
    rotated = PdfReader(output)
    assert len(rotated.pages) == len(original.pages)
    for page in rotated.pages:
        assert page.rotation == angle
    assert output.is_file()


def test_main_writes_rotated_pdf(tmp_path):
    """CLI entry point rotates a PDF to the requested output path."""
    source = RESOURCE_ROOT / "toy.pdf"
    output = tmp_path / "cli-rotated.pdf"
    argv = [
        "rotate_pdf",
        str(source),
        "180",
        "-o",
        str(output),
    ]

    with patch.object(sys, "argv", argv):
        main()

    assert output.is_file()
    assert PdfReader(output).pages[0].rotation == 180


def test_main_missing_input_file_exits_with_error():
    """CLI reports missing inputs before attempting a rotation."""
    argv = [
        "rotate_pdf",
        "does-not-exist.pdf",
        "90",
        "-o",
        "out.pdf",
    ]

    with patch.object(sys, "argv", argv), pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2


def test_main_invalid_angle_exits_with_error():
    """CLI rejects rotation angles that are not multiples of 90."""
    argv = [
        "rotate_pdf",
        str(RESOURCE_ROOT / "toy.pdf"),
        "45",
        "-o",
        "out.pdf",
    ]

    with patch.object(sys, "argv", argv), pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code == 2
