#!/usr/bin/env python3
"""Verification suite - turns the brief's checklist into hard assertions.

    python3 build/verify.py
"""
from __future__ import annotations

import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import geom
import letters
import build_font as B

from fontTools.ttLib import TTFont

TOL = 0.6
MARGIN = 25.0

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))
    return ok


def main():
    font_path = os.path.join(ROOT, "dist", "TribalTotemDisplay-Black.otf")
    flat_path = os.path.join(ROOT, "dist", "TribalTotemDisplayFlat-Black.otf")
    font = TTFont(font_path)
    flat = TTFont(flat_path)

    # 1. required tables ---------------------------------------------------- #
    tags = set(font.keys())
    need = {"CFF ", "SVG ", "COLR", "CPAL", "GSUB", "GPOS", "cmap", "hmtx",
            "name", "OS/2"}
    check("required tables present", need <= tags, f"missing={sorted(need - tags)}")

    # 2. character coverage -------------------------------------------------- #
    cmap = font.getBestCmap()
    chars = letters.CHARS
    missing = [c for c in chars if ord(c) not in cmap]
    check("every character has a glyph + flat glyph",
          not missing and all(ord(c) in flat.getBestCmap() for c in chars),
          f"missing={missing}")
    check("no-break space is mapped",
          cmap.get(0x00A0) == "uni00A0" and flat.getBestCmap().get(0x00A0) == "uni00A0")

    letters_map = letters.all_letters()
    names = {ch: letters_map[ch].glyph_name for ch in chars}
    bad_lower = [lower for lower, upper in letters.LOWERCASE_MAP.items()
                 if cmap.get(ord(lower)) != names[upper]]
    check("lowercase input maps to capital glyphs", not bad_lower,
          f"{bad_lower[:8]}")

    # 3. stylistic sets ------------------------------------------------------ #
    gsub = font["GSUB"].table
    feats = {fr.FeatureTag for fr in gsub.FeatureList.FeatureRecord}
    have = {"ss01", "ss02", "ss03"}
    check("ss01-ss03 registered", have <= feats, f"features={sorted(feats)}")
    for variant in ("ss01", "ss02", "ss03"):
        ok = all(f"{names[c]}.{variant}" in font.getGlyphOrder() for c in chars)
        check(f"{variant} variants exist", ok)

    gp = font["GPOS"].table
    kern_feats = [fr for fr in gp.FeatureList.FeatureRecord
                  if fr.FeatureTag == "kern"]
    kern_lookups = (sum(len(lk.SubTable) for lk in gp.LookupList.Lookup)
                    if gp.LookupList and gp.LookupList.Lookup else 0)
    check("kern feature registered", bool(kern_feats))
    check("kerning lookups built", kern_lookups > 0, f"subtables={kern_lookups}")

    # 4. colours ------------------------------------------------------------- #
    svg_table = font["SVG "]
    docs = [d.data for d in svg_table.docList]
    blob = "\n".join(docs)
    allowed = {"#F2C511", "#A52714"}
    import re
    hexes = set(h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}", blob))
    check("SVG art uses only the two spec colours", hexes <= allowed, f"found={sorted(hexes)}")
    banned = [w for w in ("gradient", "filter", "opacity", "rgba(", "<style", "mask=")
              if w in blob.lower()]
    check("no gradients / filters / opacity tricks", not banned, f"found={banned}")

    cpal = font["CPAL"]
    pal = cpal.palettes[0]
    got = [(c.red, c.green, c.blue) for c in pal]
    want = [(242, 197, 17), (165, 39, 20)]
    check("CPAL palette matches hex colours exactly",
          got == want, f"got={got} want={want}")

    # 5. metrics ------------------------------------------------------------- #
    hmtx = font["hmtx"].metrics
    wide = (letters.LETTER_CHARS + letters.ACCENT_CHARS +
            letters.DIGIT_CHARS)
    bad_adv = {c: hmtx[names[c]][0] for c in wide
               if not (800 <= hmtx[names[c]][0] <= 1000)}
    check("letter/digit advances within 800-1000", not bad_adv, f"offenders={bad_adv}")
    bad_punct = {c: hmtx[names[c]][0] for c in letters.PUNCT_CHARS
                 if not (380 <= hmtx[names[c]][0] <= 560)}
    check("punctuation advances within 380-560", not bad_punct,
          f"offenders={bad_punct}")

    from fontTools.pens.boundsPen import BoundsPen
    gs = font.getGlyphSet()
    bad_box = {}
    for c in letters.LETTER_CHARS + letters.DIGIT_CHARS:
        bp = BoundsPen(gs)
        gs[names[c]].draw(bp)
        if bp.bounds is None:
            bad_box[c] = None
            continue
        x0, y0, x1, y1 = bp.bounds
        if abs(y0) > TOL or abs(y1 - 720) > TOL:
            bad_box[c] = (round(y0, 1), round(y1, 1))
    check("letters and digits sit on baseline and reach cap height 720",
          not bad_box, f"{bad_box}")

    bad_abox = {}
    for c in letters.ACCENT_CHARS:
        bp = BoundsPen(gs)
        gs[names[c]].draw(bp)
        if bp.bounds is None:
            bad_abox[c] = None
            continue
        x0, y0, x1, y1 = bp.bounds
        if y0 < -140 or y1 > 800 or y0 > 0.6 or y1 < 719.4:
            bad_abox[c] = tuple(round(v, 1) for v in bp.bounds)
    check("accented letters keep the baseline and stay under the ascender",
          not bad_abox, f"{bad_abox}")

    bad_sbox = {}
    for c in letters.SYMBOL_CHARS:
        bp = BoundsPen(gs)
        gs[names[c]].draw(bp)
        if bp.bounds is None:
            bad_sbox[c] = None
            continue
        x0, y0, x1, y1 = bp.bounds
        if y0 < -160 or y1 > 800 or x0 < -1 or x1 > hmtx[names[c]][0] + 1:
            bad_sbox[c] = tuple(round(v, 1) for v in bp.bounds)
    check("symbols fit the em box and their advances", not bad_sbox,
          f"{bad_sbox}")

    bad_symadv = {c: hmtx[names[c]][0] for c in letters.SYMBOL_CHARS
                  if not (300 <= hmtx[names[c]][0] <= 1000)}
    check("symbol advances within 300-1000", not bad_symadv,
          f"offenders={bad_symadv}")

    bad_pbox = {}
    for c in letters.PUNCT_CHARS:
        bp = BoundsPen(gs)
        gs[names[c]].draw(bp)
        if bp.bounds is None:
            bad_pbox[c] = None
            continue
        x0, y0, x1, y1 = bp.bounds
        if not (-160 <= y0 and y1 <= 800 and x0 >= -1 and x1 <= hmtx[names[c]][0] + 1):
            bad_pbox[c] = tuple(round(v, 1) for v in bp.bounds)
    check("punctuation stays inside descender/ascender and its advance",
          not bad_pbox, f"{bad_pbox}")

    # 6. art margin (>= 25 units of yellow) ---------------------------------- #
    offenders = []
    for ch in chars:
        letter = letters_map[ch]
        body = letter.body
        body.orient(outer_ccw=True)
        for variant in B.VARIANTS:
            red, yel, _ = B.build_variant_art(letter, variant)
            for art in (red, yel):
                if art is None:
                    continue
                for cont in art.contours:
                    for p in cont.sampled(steps=16):
                        d = geom.distance_to_path(p, body)
                        if d < MARGIN - 0.5:
                            offenders.append((ch, variant, round(d, 1)))
                            break
    check("25-unit yellow margin respected", not offenders,
          f"{len(offenders)} offenders: {offenders[:6]}")

    # 7. variants change art, never the letter shape ------------------------- #
    from fontTools.pens.recordingPen import RecordingPen

    def outline(name):
        pen = RecordingPen()
        gs[name].draw(pen)
        return pen.value

    shape_ok = True
    for ch in chars:
        base = outline(names[ch])
        for variant in ("ss01", "ss02", "ss03"):
            if outline(f"{names[ch]}.{variant}") != base:
                shape_ok = False
    check("ss01-ss03 keep the identical letter outline", shape_ok)

    doc_by_name = {font.getGlyphOrder()[d.startGlyphID]: d.data
                   for d in svg_table.docList}
    art_differs = True
    for ch in chars:
        docs_for = [doc_by_name.get(n) for n in
                    (names[ch],) + tuple(f"{names[ch]}.{v}"
                                        for v in ("ss01", "ss02", "ss03"))]
        if None in docs_for or len(set(docs_for)) < len(B.VARIANTS):
            art_differs = False
    check("every variant has different artwork", art_differs)

    # 8. flat companion ------------------------------------------------------ #
    flat_tags = set(flat.keys())
    check("flat font has no colour tables",
          not ({"SVG ", "COLR", "CPAL"} & flat_tags))
    check("flat font covers the same characters",
          all(ord(c) in flat.getBestCmap() for c in chars))

    # 9. artefacts ----------------------------------------------------------- #
    for rel in ("specimen.html", "specimen.png",
                "dist/TribalTotemDisplay-Black.woff2"):
        check(f"artefact exists: {rel}", os.path.exists(os.path.join(ROOT, rel)))
    for ch in chars:
        for suffix in ("", ".ss01", ".ss02", ".ss03", ".flat"):
            rel = f"glyphs/{names[ch]}{suffix}.svg"
            check(f"artefact exists: {rel}", os.path.exists(os.path.join(ROOT, rel)))

    # 10. special glyphs and release metadata -------------------------------- #
    nd = RecordingPen()
    gs[".notdef"].draw(nd)
    check(".notdef is a hollow chamfered box",
          sum(1 for op in nd.value if op[0] == "moveTo") == 2)
    sp = RecordingPen()
    gs["space"].draw(sp)
    check("space is empty", not sp.value)
    nbsp = RecordingPen()
    gs["uni00A0"].draw(nbsp)
    check("no-break space is empty",
          not nbsp.value and hmtx["uni00A0"][0] == hmtx["space"][0])

    os2 = font["OS/2"]
    check("style name matches the 900 weight",
          font["name"].getDebugName(2) == "Black" and os2.usWeightClass == 900)
    check("single Black weight uses the Regular style bit",
          bool(os2.fsSelection & (1 << 6)) and not bool(os2.fsSelection & (1 << 5)))
    lic = font["name"].getDebugName(13) or ""
    check("commercial licence embedded",
          "Commercial" in lic and os.path.exists(
              os.path.join(ROOT, "LICENSE-EULA.txt")), lic)
    check("font embedding permission is installable", os2.fsType == 0)

    # summary ---------------------------------------------------------------- #
    failed = [r for r in results if not r[1]]
    print()
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED:", ", ".join(r[0] for r in failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
