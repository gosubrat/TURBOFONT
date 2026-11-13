#!/usr/bin/env python3
"""Build the commercial release directory and zip.

    python3 build/package_release.py
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VERSION = "1.000"
NAME = f"TribalTotemDisplay-{VERSION}"
OUT = os.path.join(ROOT, "release")
PKG = os.path.join(OUT, NAME)

FONTS = [
    "TribalTotemDisplay-Black.otf",
    "TribalTotemDisplayFlat-Black.otf",
    "TribalTotemDisplay-Black.woff2",
]
IMAGES = [
    "specimen.png",
    "sheet.png",
    "sheet-accents.png",
    "sheet-symbols.png",
    "sheet-typographic.png",
    "proof-accents-sample.png",
    "proof-symbols-typographic.png",
    "proof-currency.png",
    "browser-chromium.png",
    "browser-firefox.png",
    "browser-webkit.png",
    "browser-woff2.png",
    "hello-subrat.png",
]

BUYER_README = """TRIBAL TOTEM DISPLAY 1.000
===========================

A heavy blocky slab-sans display face with illustrated negative-space line art,
built as an OpenType colour font.

CONTENTS
--------
fonts/TribalTotemDisplay-Black.otf        colour font (SVG + COLRv0)
fonts/TribalTotemDisplayFlat-Black.otf    one-colour companion
fonts/TribalTotemDisplay-Black.woff2      web font

specimen.html / specimen.png              specimen page
sheet*.png                                large QA sheets
proof-*.png                               glyph proofs
LICENSE-EULA.txt                          commercial licence
FONTLOG.txt                               version history

COVERAGE
--------
A-Z, 0-9, punctuation and ASCII symbols, Latin-1 uppercase accents (including
AE, OE, Eth, Thorn, Oslash), EUR/GBP/JPY/cent, ellipsis, bullet, degree,
plus-minus, multiply, divide, copyright, registered, trademark and smart quotes.
Lowercase input maps to the capital glyphs.

INSTALL
-------
Desktop: install fonts/TribalTotemDisplay-Black.otf. Use the flat OTF if your
application cannot display colour fonts.
Web: declare fonts/TribalTotemDisplay-Black.woff2 in @font-face.
Stylistic sets:
  font-feature-settings: "ss01";   alternate artwork set 1
  font-feature-settings: "ss02";   alternate artwork set 2
  font-feature-settings: "ss03";   alternate artwork set 3

COLOUR SUPPORT
--------------
Chrome, Edge, Firefox and Safari render the SVG colour table. Recent Adobe
apps may render colour via the SVG table. Word, PowerPoint and older apps use
the flat one-colour outlines.

LICENCE
-------
Commercial font licence. See LICENSE-EULA.txt. The font files may not be
redistributed or resold as font files.

SUPPORT
-------
Use the support channel provided with your purchase.
"""

FONTLOG = """FONTLOG for Tribal Totem Display
================================

2026-11-13 - Tribal Totem Display 1.000
- First commercial release.
- 120 mapped characters: A-Z, 0-9, punctuation, ASCII symbols, Latin-1
  uppercase accents, currency and typographic marks.
- Four artwork variants per glyph (ss01-ss03).
- Kerning feature, colour SVG + COLRv0 tables, flat companion, WOFF2 web font.
- Validated with internal checks, HarfBuzz, FontBakery, OTS, and Chromium,
  Firefox and WebKit.
"""

CHECKLIST = """SELLER CHECKLIST BEFORE PUBLISHING
==================================
[ ] Put your legal name/entity and support email/website into LICENSE-EULA.txt
    and your marketplace listing. The current licensor line is
    "Tribal Totem Display project".
[ ] Have a lawyer review LICENSE-EULA.txt for your jurisdiction.
[ ] Confirm you own the rights to the artwork and name.
[ ] Run a trademark search for "Tribal Totem Display".
[ ] Test install/rendering on your own macOS and Windows machines and in
    Adobe InDesign/Illustrator if you sell to those users.
[ ] Upload the zip and listing images, and set the price.
[ ] Archive the SHA256SUMS.txt file with the release.
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(PKG, "fonts"))
    os.makedirs(os.path.join(PKG, "proofs"))

    for name in FONTS:
        shutil.copy2(os.path.join(ROOT, "dist", name),
                     os.path.join(PKG, "fonts", name))
    shutil.copy2(os.path.join(ROOT, "LICENSE-EULA.txt"),
                 os.path.join(PKG, "LICENSE-EULA.txt"))
    with open(os.path.join(PKG, "README.txt"), "w") as fh:
        fh.write(BUYER_README)
    with open(os.path.join(PKG, "FONTLOG.txt"), "w") as fh:
        fh.write(FONTLOG)
    with open(os.path.join(PKG, "RELEASE-CHECKLIST.txt"), "w") as fh:
        fh.write(CHECKLIST)

    for name in IMAGES:
        src = os.path.join(ROOT, name)
        if os.path.exists(src):
            dst = os.path.join(PKG, "proofs" if name.startswith(("proof-", "browser-"))
                               else PKG, name)
            shutil.copy2(src, dst)

    hello = os.path.join(ROOT, "hello-subrat.html")
    if os.path.exists(hello):
        html = open(hello).read().replace("dist/", "fonts/")
        with open(os.path.join(PKG, "hello-subrat.html"), "w") as fh:
            fh.write(html)

    specimen = os.path.join(ROOT, "specimen.html")
    if os.path.exists(specimen):
        html = open(specimen).read()
        html = html.replace("dist/", "fonts/")
        with open(os.path.join(PKG, "specimen.html"), "w") as fh:
            fh.write(html)

    sums = []
    for base, _, files in os.walk(PKG):
        for name in sorted(files):
            if name == "SHA256SUMS.txt":
                continue
            path = os.path.join(base, name)
            rel = os.path.relpath(path, PKG)
            sums.append(f"{sha256(path)}  {rel}")
    with open(os.path.join(PKG, "SHA256SUMS.txt"), "w") as fh:
        fh.write("\n".join(sums) + "\n")

    archive = shutil.make_archive(os.path.join(OUT, NAME), "zip", OUT, NAME)
    print("release directory:", PKG)
    print("archive:", archive)
    print("files:", len(sums))


if __name__ == "__main__":
    sys.exit(main())
