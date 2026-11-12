"""Compile generated PNG glyphs into a TTF with a native sbix table."""

from __future__ import annotations

from pathlib import Path

from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable
from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
from fontTools.ttLib.tables.sbixStrike import Strike as SbixStrike
from PIL import Image

from font_generator import (
    ALL_CHARACTERS,
    CANVAS_SIZE,
    GLYPH_NAMES,
    VARIATION_COUNT,
)


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_WORKSPACE = PROJECT_ROOT / "font_workspace"
DEFAULT_FEATURE_FILE = DEFAULT_WORKSPACE / "randomize.fea"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "RandomRansom.ttf"
FALLBACK_ADVANCE_WIDTH = 200


def build_glyph_order() -> list[str]:
    """Return the complete ordered list of base and alternate glyph names."""
    base_glyph_names = [GLYPH_NAMES[character] for character in ALL_CHARACTERS]
    alternate_glyph_names = [
        f"{glyph_name}.v{variation_index}"
        for glyph_name in base_glyph_names
        for variation_index in range(1, VARIATION_COUNT + 1)
    ]
    return [".notdef", "space", *base_glyph_names, *alternate_glyph_names]


def build_character_map() -> dict[int, str]:
    """Map Unicode codepoints to the base glyphs, including whitespace."""
    character_map = {ord(" "): "space"}
    character_map.update(
        {ord(character): GLYPH_NAMES[character] for character in ALL_CHARACTERS}
    )
    return character_map


def _read_png(png_path: Path) -> tuple[int, bytes]:
    """Read a PNG and return its actual width and encoded image data."""
    if not png_path.is_file():
        raise FileNotFoundError(f"Missing glyph bitmap: {png_path}")
    with Image.open(png_path) as image:
        if image.format != "PNG":
            raise ValueError(f"Expected a PNG glyph bitmap: {png_path}")
        image_width = image.width
        image.verify()
    return image_width, png_path.read_bytes()


def add_sbix_table(font, workspace: Path, glyph_order: list[str]) -> dict[str, tuple[int, int]]:
    """Attach PNGs to sbix and derive each horizontal advance from image width."""
    strike = SbixStrike(ppem=CANVAS_SIZE, resolution=72)
    metrics: dict[str, tuple[int, int]] = {}

    for glyph_name in glyph_order:
        png_path = workspace / f"{glyph_name}.png"
        if not png_path.is_file():
            metrics[glyph_name] = (FALLBACK_ADVANCE_WIDTH, 0)
            continue

        image_width, image_data = _read_png(png_path)
        metrics[glyph_name] = (image_width, 0)
        strike.glyphs[glyph_name] = SbixGlyph(
            glyphName=glyph_name,
            originOffsetX=0,
            originOffsetY=0,
            graphicType="png",
            imageData=image_data,
        )

    sbix_table = newTable("sbix")
    sbix_table.version = 1
    sbix_table.flags = 1
    sbix_table.strikes = {CANVAS_SIZE: strike}
    font["sbix"] = sbix_table
    return metrics


def compile_font(
    workspace: Path = DEFAULT_WORKSPACE,
    feature_file: Path = DEFAULT_FEATURE_FILE,
    output_file: Path = DEFAULT_OUTPUT_FILE,
) -> Path:
    """Build and save a TrueType font with glyph outlines and sbix images."""
    if not feature_file.is_file():
        raise FileNotFoundError(f"Missing OpenType feature file: {feature_file}")

    glyph_order = build_glyph_order()
    character_map = build_character_map()
    font_builder = FontBuilder(CANVAS_SIZE, isTTF=True)
    font_builder.setupGlyphOrder(glyph_order)
    font_builder.setupCharacterMap(character_map)

    glyphs = {
        glyph_name: TTGlyphPen(None).glyph()
        for glyph_name in glyph_order
    }
    font_builder.setupGlyf(glyphs)
    metrics = add_sbix_table(font_builder.font, workspace, glyph_order)
    font_builder.setupHorizontalMetrics(metrics)
    font_builder.setupHorizontalHeader(ascent=CANVAS_SIZE, descent=0, lineGap=0)
    font_builder.setupNameTable(
        {
            "familyName": "RandomRansom",
            "styleName": "Regular",
            "uniqueFontIdentifier": "RandomRansomFont-1.0",
            "fullName": "RandomRansom Regular",
            "psName": "RandomRansom-Regular",
            "version": "Version 1.0",
            "manufacturer": "RandomRansom Font Generator",
            "description": "A cut-paper ransom-note color font.",
        }
    )
    font_builder.setupOS2(
        sTypoAscender=CANVAS_SIZE,
        sTypoDescender=0,
        sTypoLineGap=0,
        usWinAscent=CANVAS_SIZE,
        usWinDescent=0,
        usWeightClass=400,
        usWidthClass=5,
        sxHeight=CANVAS_SIZE // 2,
        sCapHeight=CANVAS_SIZE * 3 // 4,
    )
    font_builder.setupPost(keepGlyphNames=True)

    addOpenTypeFeatures(font_builder.font, str(feature_file))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    font_builder.save(str(output_file))
    return output_file


if __name__ == "__main__":
    compiled_path = compile_font()
    print(f"Built {compiled_path}")
