"""Run the complete native Python ransom-note font build."""

from __future__ import annotations

from pathlib import Path

from cleanup import cleanup_workspace
from font_generator import (
    VARIATION_COUNT,
    find_supported_fonts,
    generate_glyph_pngs,
    generate_randomize_feature,
)
from native_compiler import compile_font


PROJECT_ROOT = Path(__file__).resolve().parent
FONT_WORKSPACE = PROJECT_ROOT / "font_workspace"
FEATURE_FILE = FONT_WORKSPACE / "randomize.fea"
OUTPUT_FILE = PROJECT_ROOT / "Ransom.ttf"


def main() -> None:
    """Clean old output, create glyph artwork and compile the final TTF."""
    print("Cleaning previous generated folders...")
    cleanup_workspace(PROJECT_ROOT)

    print("Scanning C:/Windows/Fonts for compatible font faces...")
    font_pool = find_supported_fonts("C:/Windows/Fonts")
    print(f"Found {len(font_pool)} compatible font faces.")
    if len(font_pool) < VARIATION_COUNT:
        raise RuntimeError(
            f"At least {VARIATION_COUNT} supported font faces are required; "
            f"found {len(font_pool)}."
        )

    generated_pngs = generate_glyph_pngs(
        font_pool,
        FONT_WORKSPACE,
        variations=VARIATION_COUNT,
    )
    generate_randomize_feature(FEATURE_FILE, variations=VARIATION_COUNT)
    print(f"Generated {len(generated_pngs)} PNG glyph images.")

    compiled_path = compile_font(FONT_WORKSPACE, FEATURE_FILE, OUTPUT_FILE)
    print(f"Font build completed: {compiled_path}")


if __name__ == "__main__":
    main()
