"""Generate cut-paper PNG glyphs and OpenType contextual alternates."""

from __future__ import annotations

import random
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


CANVAS_SIZE = 350
VARIATION_COUNT = 5
TURKISH_CHARACTERS = "çğıöşüÇĞİÖŞÜ"
ASCII_SYMBOLS = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
ALL_CHARACTERS = "".join(
    dict.fromkeys(
        string.ascii_lowercase
        + string.ascii_uppercase
        + TURKISH_CHARACTERS
        + string.digits
        + ASCII_SYMBOLS
    )
)
REQUIRED_CHARACTERS = ALL_CHARACTERS
FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc"}


GLYPH_NAMES = {character: character for character in string.ascii_letters}
GLYPH_NAMES.update(
    {
        "ç": "ccedilla",
        "ğ": "gbreve",
        "ı": "dotlessi",
        "ö": "odieresis",
        "ş": "scedilla",
        "ü": "udieresis",
        "Ç": "Ccedilla",
        "Ğ": "Gbreve",
        "İ": "Idotaccent",
        "Ö": "Odieresis",
        "Ş": "Scedilla",
        "Ü": "Udieresis",
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
        "!": "exclam",
        '"': "quotedbl",
        "#": "numbersign",
        "$": "dollar",
        "%": "percent",
        "&": "ampersand",
        "'": "quotesingle",
        "(": "parenleft",
        ")": "parenright",
        "*": "asterisk",
        "+": "plus",
        ",": "comma",
        "-": "hyphen",
        ".": "period",
        "/": "slash",
        ":": "colon",
        ";": "semicolon",
        "<": "less",
        "=": "equal",
        ">": "greater",
        "?": "question",
        "@": "at",
        "[": "bracketleft",
        "\\": "backslash",
        "]": "bracketright",
        "^": "asciicircum",
        "_": "underscore",
        "`": "grave",
        "{": "braceleft",
        "|": "bar",
        "}": "braceright",
        "~": "asciitilde",
    }
)


@dataclass(frozen=True)
class FontFace:
    """A font path and the face index for a TrueType collection."""

    path: Path
    index: int = 0


def _supports_required_characters(font: TTFont) -> bool:
    """Check that the font's Unicode cmap has every configured character."""
    character_map = font.getBestCmap() or {}
    return all(
        character_map.get(ord(character), ".notdef") != ".notdef"
        for character in REQUIRED_CHARACTERS
    )


def find_supported_fonts(font_folder: Path | str = "C:/Windows/Fonts") -> list[FontFace]:
    """Find installed font faces supporting Turkish and the output character set."""
    folder = Path(font_folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Font folder does not exist: {folder}")

    supported_faces: list[FontFace] = []
    font_paths = sorted(
        (
            font_path
            for font_path in folder.iterdir()
            if font_path.is_file() and font_path.suffix.lower() in FONT_EXTENSIONS
        ),
        key=lambda font_path: font_path.name.casefold(),
    )

    for font_path in font_paths:
        try:
            if font_path.suffix.lower() in {".ttc", ".otc"}:
                collection = TTCollection(str(font_path), lazy=True)
                try:
                    for face_index, font in enumerate(collection.fonts):
                        if _supports_required_characters(font):
                            supported_faces.append(FontFace(font_path, face_index))
                finally:
                    for font in collection.fonts:
                        font.close()
            else:
                font = TTFont(str(font_path), lazy=True)
                try:
                    if _supports_required_characters(font):
                        supported_faces.append(FontFace(font_path))
                finally:
                    font.close()
        except Exception:
            continue

    return supported_faces


def _make_cutout_points(
    bounds: tuple[int, int, int, int],
    rng: random.Random,
) -> list[tuple[int, int]]:
    """Build an irregular paper polygon around the glyph bounds."""
    left, top, right, bottom = bounds
    middle_x = (left + right) // 2
    middle_y = (top + bottom) // 2

    def margin() -> int:
        return rng.randint(16, 27)

    return [
        (left - margin(), top - margin()),
        (middle_x + rng.randint(-9, 9), top - margin()),
        (right + margin(), top - margin()),
        (right + margin(), middle_y + rng.randint(-9, 9)),
        (right + margin(), bottom + margin()),
        (middle_x + rng.randint(-9, 9), bottom + margin()),
        (left - margin(), bottom + margin()),
        (left - margin(), middle_y + rng.randint(-9, 9)),
    ]


def generate_rough_cut_letter(
    character: str,
    font_face: FontFace,
    rng: random.Random | None = None,
) -> Image.Image:
    """Draw a cut-paper glyph with light lettering, shadow, and generated grain."""
    rng = rng or random.Random()
    center = CANVAS_SIZE // 2
    font_size = rng.randint(150, 190)
    font = ImageFont.truetype(
        str(font_face.path), font_size, index=font_face.index
    )
    measure = ImageDraw.Draw(Image.new("L", (CANVAS_SIZE, CANVAS_SIZE)))
    bounds = measure.textbbox((center, center), character, font=font, anchor="mm")

    while (bounds[2] - bounds[0] > 205 or bounds[3] - bounds[1] > 205) and font_size > 80:
        font_size -= 5
        font = ImageFont.truetype(
            str(font_face.path), font_size, index=font_face.index
        )
        bounds = measure.textbbox((center, center), character, font=font, anchor="mm")

    cutout_points = _make_cutout_points(bounds, rng)
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))

    shadow_layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_x = rng.randint(4, 8)
    shadow_y = rng.randint(5, 9)
    shadow_draw.polygon(
        [(x + shadow_x, y + shadow_y) for x, y in cutout_points],
        fill=(0, 0, 0, 145),
    )
    canvas.alpha_composite(shadow_layer.filter(ImageFilter.GaussianBlur(radius=5)))

    tone = rng.randint(18, 42)
    paper_color = (tone, max(14, tone - rng.randint(0, 5)), min(52, tone + 5), 255)
    paper_layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    paper_mask = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    ImageDraw.Draw(paper_mask).polygon(cutout_points, fill=255)
    ImageDraw.Draw(paper_layer).polygon(
        cutout_points,
        fill=paper_color,
        outline=(rng.randint(150, 205), rng.randint(150, 205), rng.randint(150, 205), 255),
        width=1,
    )

    noise = Image.effect_noise((CANVAS_SIZE, CANVAS_SIZE), 42).convert("L")
    noise_alpha = noise.point(lambda value: min(30, max(0, (value - 78) // 5)))
    noise_alpha = ImageChops.multiply(noise_alpha, paper_mask)
    noise_layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (220, 220, 220, 0))
    noise_layer.putalpha(noise_alpha)
    paper_layer.alpha_composite(noise_layer)
    canvas.alpha_composite(paper_layer)

    text_color = (
        rng.randint(236, 255),
        rng.randint(236, 255),
        rng.randint(232, 250),
        255,
    )
    ImageDraw.Draw(canvas).text(
        (center + rng.randint(-3, 3), center + rng.randint(-3, 3)),
        character,
        font=font,
        fill=text_color,
        anchor="mm",
    )

    rotated_image = canvas.rotate(
        rng.uniform(-8.0, 8.0),
        resample=Image.Resampling.BICUBIC,
        expand=False,
    )
    if rotated_image.getbbox() is None:
        raise ValueError(f"The generated glyph has no visible pixels: {character!r}")

    cropped_image = rotated_image.crop(rotated_image.getbbox())
    left_padding = rng.randint(2, 8)
    right_padding = rng.randint(2, 8)
    padded_image = Image.new(
        "RGBA",
        (cropped_image.width + left_padding + right_padding, cropped_image.height),
        (0, 0, 0, 0),
    )
    padded_image.paste(cropped_image, (left_padding, 0))
    return padded_image


def generate_glyph_pngs(
    font_pool: Sequence[FontFace],
    output_folder: Path,
    variations: int = VARIATION_COUNT,
    characters: str = ALL_CHARACTERS,
) -> list[Path]:
    """Write base PNGs and numbered alternate PNGs to a flat folder."""
    if variations < 1:
        raise ValueError("At least one glyph variation is required.")
    if len(font_pool) < variations:
        raise ValueError(
            f"At least {variations} supported font faces are required; "
            f"found {len(font_pool)}."
        )

    output_folder.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []

    for character in characters:
        glyph_name = GLYPH_NAMES[character]
        selected_fonts = random.sample(list(font_pool), variations)

        base_path = output_folder / f"{glyph_name}.png"
        base_image = generate_rough_cut_letter(character, selected_fonts[0])
        base_image.save(base_path, format="PNG", optimize=True)
        output_paths.append(base_path)

        for variation_index, font_face in enumerate(selected_fonts, start=1):
            variation_path = output_folder / f"{glyph_name}.v{variation_index}.png"
            variation_image = generate_rough_cut_letter(character, font_face)
            variation_image.save(variation_path, format="PNG", optimize=True)
            output_paths.append(variation_path)

    return output_paths


def generate_randomize_feature(
    output_path: Path,
    variations: int = VARIATION_COUNT,
) -> None:
    """Write calt rules that cycle variants for consecutive copies of a glyph."""
    if variations < 1:
        raise ValueError("At least one glyph variation is required.")

    lines = [
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "languagesystem latn TRK;",
        "",
        "feature calt {",
    ]

    for glyph_name in GLYPH_NAMES.values():
        lines.append(f"    sub {glyph_name} {glyph_name}' by {glyph_name}.v1;")
        for variation_index in range(1, variations):
            previous_glyph = f"{glyph_name}.v{variation_index}"
            next_glyph = f"{glyph_name}.v{variation_index + 1}"
            lines.append(f"    sub {previous_glyph} {glyph_name}' by {next_glyph};")
        lines.append(
            f"    sub {glyph_name}.v{variations} {glyph_name}' by {glyph_name};"
        )

    lines.append("} calt;")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
