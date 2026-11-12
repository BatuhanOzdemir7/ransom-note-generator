# RandomRansom - Dynamic Ransom Note Font Generator

**RandomRansom** is a fully automated, pure Python pipeline that generates a dynamic, color-bitmap fanzine / ransom note font (.ttf). 

Instead of a static vector font, this generator cuts out letters from provided source fonts, applies paper textures, masks, drop shadows, and noise programmatically. It generates 5 unique variations for each character and compiles them into an Apple `sbix` color TrueType font. Thanks to the injected OpenType Contextual Alternates (`calt`), typing the same letter repeatedly cycles through different variations automatically, creating a true, chaotic ransom-note aesthetic.

## Features
* **100% Pure Python Pipeline:** Uses only `Pillow` for image generation and `fontTools` for binary TTF compilation. 
* **Zero External CLI Dependencies:** No `nanoemoji`, `ninja`, or shell scripts required. It builds natively on Windows, macOS, and Linux.
* **Dynamic Advance Widths:** Crops each letter dynamically to its exact non-transparent bounding box and sets realistic letter spacing.
* **Full Turkish Support:** Automatically filters fonts to ensure proper glyph rendering for `ç, ğ, ı, İ, ö, ş, ü`.

## ⚠️ Important Legal & Copyright Warning (Commercial Use)
This repository **only provides the generator code**. It does NOT contain or distribute any compiled fonts or proprietary typeface data. 

If you use this tool, **you are responsible for the fonts you feed into it.**
* Fonts located in your default system folder (e.g., `C:/Windows/Fonts`) such as Arial, Impact, or Times New Roman are **copyrighted commercial software**. Generating a `.ttf` file from these and sharing, selling, or distributing it is a violation of their End User License Agreements (EULA) and copyright laws.
* **For Commercial or Public Distribution:** You MUST use open-source, OFL (Open Font License) fonts (e.g., from Google Fonts). Create a separate directory, place your copyright-free `.ttf` files there, and point the generator to that specific folder.

## Prerequisites
* Python 3.10+
* `Pillow` and `fontTools`

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ransom-note-generator.git
   cd ransom-note-generator
   ```

2. **Install Dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Sourcing Your Fonts (Configuration)

You have two options for providing source fonts to the generator. You can change this in the Python script where the `font_folder` variable is defined:

**Option A: Custom Open-Source Directory (Recommended & Safe)**
1. Create a folder named `open_fonts` in the project root.
2. Download completely free, OFL-licensed fonts from Google Fonts and put them inside.
3. In the script, set: `font_folder = "open_fonts"`

**Option B: Windows System Fonts (Personal / Experimental Use Only)**
1. Let the script scan your entire system library to find the most chaotic mix of fonts.
2. In the script, set: `font_folder = "C:/Windows/Fonts"`
3. *Do not distribute the resulting font if you use this option.*

## Usage

Simply run the master build script. It will generate hundreds of letter assets in memory, construct the OpenType rules, and compile the final binary.

```bash
python build_font.py
```

* **Output:** A ready-to-install `RandomRansom.ttf` file will be generated in the root directory.

## How It Works (Architecture)

1. **Font Scanning:** The system scans the targeted directory and strictly validates if the font contains actual glyphs for specific language sets.
2. **Asset Generation:** A canvas is created. The letter is drawn, masked with an irregular dark polygon (paper cutout), rotated, and textured.
3. **Bounding Box Cropping:** To prevent awkward spacing, the canvas is cropped down to the exact pixel boundaries of the cutout, adding random padding.
4. **OpenType `calt` Features:** A `randomize.fea` script is dynamically written. It creates chained substitutions: if `A` is followed by another `A`, it swaps the second to `A.v1`, and so on.
5. **Native Compilation:** `fontBuilder` generates a blank TTF, writes the `hmtx` table based on the actual PNG widths, injects the images into the `sbix` table, adds the OpenType rules, and saves the binary.

---
*Built for fanzines, punk aesthetics, and digital ransom notes.*