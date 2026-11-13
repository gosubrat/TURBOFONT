#!/usr/bin/env python3
"""HarfBuzz shaping checks: GSUB stylistic sets and GPOS kerning.

    python3 build/shaping_test.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import uharfbuzz as hb
from fontTools.ttLib import TTFont

PATH = os.path.join(ROOT, "dist", "TribalTotemDisplay-Black.otf")
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))


def shaper():
    blob = hb.Blob.from_file_path(PATH)
    face = hb.Face(blob)
    return hb.Font(face)


def shape(text, features=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(shaper(), buf, features or {})
    return buf


def main():
    font = TTFont(PATH)
    order = font.getGlyphOrder()

    def names(text, features=None):
        return [order[i.codepoint] for i in shape(text, features).glyph_infos]

    base_t = names("T")
    ss01_t = names("T", {"ss01": True})
    check("ss01 reaches the alternate glyph in HarfBuzz",
          base_t == ["T"] and ss01_t == ["T.ss01"], f"{base_t} -> {ss01_t}")
    ss03_a = names("A", {"ss03": True})
    check("ss03 reaches the alternate glyph in HarfBuzz",
          ss03_a == ["A.ss03"], f"{ss03_a}")

    buf = shape("AV")
    kerned = sum(p.x_advance for p in buf.glyph_positions)
    buf = shape("AV", {"kern": False})
    plain = sum(p.x_advance for p in buf.glyph_positions)
    check("kern feature tightens AV", kerned < plain, f"{plain} -> {kerned}")

    buf = shape("To.")
    seq = [order[i.codepoint] for i in buf.glyph_infos]
    check("punctuation shapes as expected",
          seq == ["T", "O", "period"], f"{seq}")

    missing = []
    for ch in "AÀÇÆŒØÞ€£¥©®™‘’“”":
        buf = shape(ch)
        if not buf.glyph_infos or buf.glyph_infos[0].codepoint == 0:
            missing.append(ch)
    check("all extended characters shape to real glyphs", not missing,
          f"missing={missing}")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} shaping checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
