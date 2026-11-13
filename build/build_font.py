#!/usr/bin/env python3
"""Tribal Totem Display - reproducible font build.

    python3 build/build_font.py

Produces:
    glyphs/*.svg        per-glyph artwork (base, ss01-ss03, flat)
    dist/TribalTotemDisplay-Black.otf   CFF + SVG + COLRv0 + CPAL + GSUB
    dist/TribalTotemDisplay-Black.woff2
    specimen.html
    specimen.png        (if Playwright/Chromium is available)
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import geom
import letters
import motifs

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.ttLib.tables.S_V_G_ import SVGDocument

YELLOW = (242, 197, 17)      # #F2C511
RED = (165, 39, 20)          # #A52714
YELLOW_HEX = "#F2C511"
RED_HEX = "#A52714"

FAMILY = "Tribal Totem Display"
STYLE = "Black"
VERSION = "1.000"            # M5 release
PS_NAME = "TribalTotemDisplay-Black"
VARIANTS = ("", "ss01", "ss02", "ss03")


# --------------------------------------------------------------------------- #
def inset(box, amount):
    x0, y0, x1, y1 = box
    return (x0 + amount, y0 + amount, x1 - amount, y1 - amount)


def build_variant_art(letter, variant):
    """Return (red_path, yellow_path_or_None, svg_markup_body)."""
    red_strokes, red_solids = [], []
    yel_strokes, yel_solids = [], []

    for name, zone, params in letter.art[variant]:
        params = dict(params)
        color = params.pop("color", "red")
        zval = letter.zones[zone]
        if isinstance(zval[0], (tuple, list)):
            zval = zval[0]
        box = inset(zval, geom.ART_STROKE / 2.0 + 2.0)
        strokes, solids = motifs.MOTIFS[name](box, **params)
        if color == "yellow":
            yel_strokes.extend(strokes)
            yel_solids.extend(solids)
        else:
            red_strokes.extend(strokes)
            red_solids.extend(solids)

    red = None
    if red_strokes or red_solids:
        parts = []
        if red_strokes:
            parts.append(geom.strokes_to_fill(red_strokes))
        if red_solids:
            parts.append(geom.Path(red_solids))
        red = geom.union(parts)

    yel = None
    if yel_strokes or yel_solids:
        parts = []
        if yel_strokes:
            parts.append(geom.strokes_to_fill(yel_strokes))
        if yel_solids:
            parts.append(geom.Path(yel_solids))
        yel = geom.union(parts)

    return red, yel, (red_strokes, red_solids, yel_strokes, yel_solids)


def svg_document(gid, letter, variant, red, yel, raw):
    red_strokes, red_solids, yel_strokes, yel_solids = raw
    body = letter.body
    body.orient(outer_ccw=True)
    parts = [
        f'<path fill="{YELLOW_HEX}" fill-rule="evenodd" d="{body.to_svg_d()}"/>'
    ]
    if red_strokes:
        d = _open_paths_d(red_strokes)
        parts.append(
            f'<path fill="none" stroke="{RED_HEX}" stroke-width="20" '
            f'stroke-linecap="round" stroke-linejoin="round" d="{d}"/>')
    if red_solids:
        parts.append(f'<path fill="{RED_HEX}" fill-rule="evenodd" '
                     f'd="{geom.Path(red_solids).to_svg_d()}"/>')
    if yel_strokes:
        d = _open_paths_d(yel_strokes)
        parts.append(
            f'<path fill="none" stroke="{YELLOW_HEX}" stroke-width="20" '
            f'stroke-linecap="round" stroke-linejoin="round" d="{d}"/>')
    if yel_solids:
        parts.append(f'<path fill="{YELLOW_HEX}" fill-rule="evenodd" '
                     f'd="{geom.Path(yel_solids).to_svg_d()}"/>')
    inner = "".join(parts)
    return (f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg">'
            f'<g id="glyph{gid}">{inner}</g></svg>')


def _open_paths_d(polylines):
    out = []
    for pts in polylines:
        closed = len(pts) > 2 and pts[0] == pts[-1]
        d = []
        for i, (x, y) in enumerate(pts):
            d.append(f"{'M' if i == 0 else 'L'}{x:g} {-y:g}")
        if closed:
            d.append("Z")
        out.append("".join(d))
    return "".join(out)


def flat_svg(letter):
    body = letter.body
    body.orient(outer_ccw=True)
    return (f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg">'
            f'<path fill="{YELLOW_HEX}" fill-rule="evenodd" '
            f'd="{body.to_svg_d()}"/></svg>')


def charstring(path, advance):
    pen = T2CharStringPen(advance, None)
    path.draw(pen)
    return pen.getCharString()


# --------------------------------------------------------------------------- #
def build():
    glyphs_dir = os.path.join(ROOT, "glyphs")
    dist_dir = os.path.join(ROOT, "dist")
    os.makedirs(glyphs_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)

    letters_map = letters.all_letters()

    # ---- assemble glyph data -------------------------------------------- #
    glyph_order = [".notdef", "space"]
    charstrings = {}
    metrics = {}
    cmap = {}
    color_layers = {}     # base glyph -> [(layer glyph, palette index)]
    svg_docs = {}         # glyph name -> svg markup
    flat_svgs = {}        # path -> svg text

    # .notdef: hollow chamfered box in the house style
    outer = geom.poly(geom.chamfer_polygon(
        [(40, 0), (360, 0), (360, 600), (40, 600)], {0: 16, 1: 18, 2: 16, 3: 18}))
    inner = geom.poly([(140, 120), (260, 120), (260, 480), (140, 480)]).reversed()
    charstrings[".notdef"] = charstring(geom.Path([outer, inner]), 400)
    metrics[".notdef"] = (400, 40)

    # space / no-break space
    charstrings["space"] = charstring(geom.Path(), 300)
    metrics["space"] = (300, 0)
    cmap[0x20] = "space"
    charstrings["uni00A0"] = charstring(geom.Path(), 300)
    metrics["uni00A0"] = (300, 0)
    cmap[0x00A0] = "uni00A0"
    glyph_order.append("uni00A0")

    for ch in letters.CHARS:
        letter = letters_map[ch]
        base = letter.glyph_name
        flat_svgs[base] = flat_svg(letter)

        for variant in VARIANTS:
            name = base if not variant else f"{base}.{variant}"
            glyph_order.append(name)

            body = letter.body
            body.orient(outer_ccw=True)
            charstrings[name] = charstring(body, letter.adv)
            b = body.bounds()
            metrics[name] = (letter.adv, max(0, int(round(b[0]))))

            red, yel, raw = build_variant_art(letter, variant)
            layers = [(name, 0)]
            if red is not None:
                art_name = f"{name}.art"
                glyph_order.append(art_name)
                charstrings[art_name] = charstring(red, letter.adv)
                metrics[art_name] = (letter.adv, 0)
                layers.append((art_name, 1))
            if yel is not None:
                art_name = f"{name}.art2"
                glyph_order.append(art_name)
                charstrings[art_name] = charstring(yel, letter.adv)
                metrics[art_name] = (letter.adv, 0)
                layers.append((art_name, 0))
            color_layers[name] = layers

            if not variant:
                cmap[ord(ch)] = name
                for lower, upper in letters.LOWERCASE_MAP.items():
                    if upper == ch:
                        cmap[ord(lower)] = name

    # ---- assign glyph IDs, then build SVG documents --------------------- #
    gid = {name: i for i, name in enumerate(glyph_order)}
    for ch in letters.CHARS:
        letter = letters_map[ch]
        base = letter.glyph_name
        for variant in VARIANTS:
            name = base if not variant else f"{base}.{variant}"
            red, yel, raw = build_variant_art(letter, variant)
            svg_docs[name] = svg_document(gid[name], letter, variant, red, yel, raw)

    # ---- write per-glyph SVG files --------------------------------------- #
    for ch in letters.CHARS:
        letter = letters_map[ch]
        base = letter.glyph_name
        with open(os.path.join(glyphs_dir, f"{base}.flat.svg"), "w") as fh:
            fh.write(flat_svgs[base])
        for variant in VARIANTS:
            name = base if not variant else f"{base}.{variant}"
            fname = f"{base}.svg" if not variant else f"{base}.{variant}.svg"
            with open(os.path.join(glyphs_dir, fname), "w") as fh:
                fh.write(svg_docs[name])

    # ---- base font -------------------------------------------------------- #
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(
        PS_NAME,
        {"FullName": f"{FAMILY} {STYLE}",
         "FamilyName": FAMILY,
         "Weight": "Black",
         "version": VERSION},
        charstrings,
        {"BlueValues": [-20, 0, 700, 720], "StdHW": 20, "StdVW": 180},
    )
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200, lineGap=0)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": STYLE,
        "uniqueFontIdentifier": f"{VERSION};TTDF;{PS_NAME}",
        "fullName": f"{FAMILY} {STYLE}",
        "version": f"Version {VERSION}",
        "psName": PS_NAME,
        "typographicFamily": FAMILY,
        "typographicSubfamily": STYLE,
        "manufacturer": "Tribal Totem Display project",
        "copyright": "Copyright 2026 Tribal Totem Display project",
        "licenseDescription": "Commercial font licence. See LICENSE-EULA.txt.",
        "designer": "Tribal Totem Display project",
        "sampleText": "TOTEM TRIBAL",
    })
    fb.setupOS2(
        sTypoAscender=800, sTypoDescender=-200, sTypoLineGap=0,
        usWinAscent=800, usWinDescent=200,
        usWeightClass=900, usWidthClass=5, fsType=0,
        achVendID="TTDF",
        sxHeight=520, sCapHeight=720,
        panose=dict(bFamilyType=2, bSerifStyle=11, bWeight=10, bProportion=4,
                    bContrast=0, bStrokeVariation=0, bArmStyle=0,
                    bLetterForm=0, bMidline=0, bXHeight=0),
    )
    fb.setupPost(italicAngle=0, underlinePosition=-80, underlineThickness=40,
                 isFixedPitch=0)
    fb.setupMaxp()

    font = fb.font
    # Single-weight family: no linked Bold face, so keep the Regular bit.
    font["OS/2"].fsSelection |= 1 << 6
    font["OS/2"].fsSelection &= ~(1 << 5)
    font["head"].macStyle &= ~1
    font["OS/2"].ulCodePageRange1 = 1      # Latin 1
    font["OS/2"].ulCodePageRange2 = 0
    font["name"].names = [n for n in font["name"].names if n.platformID != 1]

    # ---- GSUB stylistic sets --------------------------------------------- #
    fea = []
    for i, variant in enumerate(VARIANTS[1:], 1):
        subs = " ".join(f"sub {letters_map[ch].glyph_name} by "
                        f"{letters_map[ch].glyph_name}.{variant};"
                        for ch in letters.CHARS)
        fea.append(f"feature {variant} {{ {subs} }} {variant};")

    # ---- spacing / kerning ------------------------------------------------ #
    def gn(ch):
        return letters_map[ch].glyph_name

    wide = letters.LETTER_CHARS + letters.ACCENT_CHARS
    diagonals = ["A", "V", "W", "Y"]
    pairs = []
    for left in diagonals:
        for right in diagonals:
            if left != right:
                pairs.append((left, right, -45))
    for left in ("T", "L", "P", "F"):
        for right in diagonals:
            pairs.append((left, right, -45))
    for left in diagonals:
        for right in ("T", "L"):
            pairs.append((left, right, -35))
    for right in (".", ",", ";", ":"):
        for left in wide:
            pairs.append((left, right, -70))
    for left in (".", ","):
        for right in wide:
            pairs.append((left, right, -50))
    for right in (")", "]", "}"):
        for left in wide:
            pairs.append((left, right, -30))
    for left in ("(", "["):
        for right in wide:
            pairs.append((left, right, -30))
    for left in ("'", '"'):
        for right in wide:
            pairs.append((left, right, -50))

    seen = set()
    kern = []
    for left, right, value in pairs:
        key = (gn(left), gn(right))
        if key in seen:
            continue
        seen.add(key)
        kern.append(f"pos {key[0]} {key[1]} {value};")
    fea.append("feature kern { " + " ".join(kern) + " } kern;")

    addOpenTypeFeaturesFromString(font, "\n".join(fea))

    # Stylistic-set UI descriptions.
    from fontTools.ttLib.tables.otTables import FeatureParamsStylisticSet
    ss_names = {
        "ss01": (256, "Alternate artwork set 1"),
        "ss02": (257, "Alternate artwork set 2"),
        "ss03": (258, "Alternate artwork set 3"),
    }
    for rec in font["GSUB"].table.FeatureList.FeatureRecord:
        if rec.FeatureTag in ss_names:
            nid, text = ss_names[rec.FeatureTag]
            params = FeatureParamsStylisticSet()
            params.Version = 0
            params.UINameID = nid
            rec.Feature.FeatureParams = params
            font["name"].setName(text, nid, 3, 1, 0x409)

    # ---- COLRv0 + CPAL ---------------------------------------------------- #
    palette = [tuple(c / 255.0 for c in YELLOW) + (1.0,),
               tuple(c / 255.0 for c in RED) + (1.0,)]
    font["CPAL"] = buildCPAL([palette])
    font["COLR"] = buildCOLR(color_layers, version=0,
                             glyphMap={n: gid[n] for n in glyph_order})

    # ---- SVG table -------------------------------------------------------- #
    from fontTools.ttLib import newTable
    svg_table = newTable("SVG ")
    svg_table.docList = [SVGDocument(svg_docs[name], gid[name], gid[name],
                                     compressed=True)
                         for name in svg_docs]
    svg_table.compressed = True
    font["SVG "] = svg_table

    # ---- save -------------------------------------------------------------- #
    otf_path = os.path.join(dist_dir, "TribalTotemDisplay-Black.otf")
    font.save(otf_path)
    font.flavor = "woff2"
    woff2_path = os.path.join(dist_dir, "TribalTotemDisplay-Black.woff2")
    font.save(woff2_path)

    flat_path = write_flat_font(otf_path)

    write_specimen(os.path.join(ROOT, "specimen.html"))
    print("built", otf_path)
    print("built", woff2_path)
    print("built", flat_path)
    print("glyphs:", len(glyph_order))
    return otf_path


def write_flat_font(otf_path):
    """A genuine one-colour companion: same outlines, no SVG/COLR/CPAL tables."""
    from fontTools.ttLib import TTFont

    font = TTFont(otf_path)
    for tag in ("SVG ", "COLR", "CPAL"):
        if tag in font:
            del font[tag]

    # Drop the now-unreachable colour art layers.
    from fontTools import subset
    options = subset.Options()
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.layout_features = ["*"]
    options.notdef_outline = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=list(font.getBestCmap().keys()))
    subsetter.subset(font)

    family = "Tribal Totem Display Flat"
    ps_name = "TribalTotemDisplayFlat-Black"
    for rec in font["name"].names:
        if rec.nameID == 1:
            rec.string = family
        elif rec.nameID == 2:
            rec.string = STYLE
        elif rec.nameID == 4:
            rec.string = f"{family} {STYLE}"
        elif rec.nameID == 6:
            rec.string = ps_name
        elif rec.nameID == 16:
            rec.string = family
        elif rec.nameID == 17:
            rec.string = STYLE
    try:
        font["CFF "].cff.fontNames[0] = ps_name
        font["CFF "].cff.topDictIndex[0].FontName = ps_name
    except Exception:
        pass

    out = os.path.join(os.path.dirname(otf_path),
                       "TribalTotemDisplayFlat-Black.otf")
    font.save(out)
    return out


# --------------------------------------------------------------------------- #
SPECIMEN = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Tribal Totem Display - specimen</title>
<style>
  @font-face {{
    font-family: "Tribal Totem Display";
    src: url("dist/TribalTotemDisplay-Black.otf") format("opentype");
  }}
  @font-face {{
    font-family: "Tribal Totem Display Flat";
    src: url("dist/TribalTotemDisplayFlat-Black.otf") format("opentype");
  }}
  html, body {{ margin: 0; padding: 0; }}
  body {{ background: #A52714; color: #F2C511; font-family: "Tribal Totem Display", sans-serif; }}
  .page {{ padding: 48px 56px 64px; }}
  .hero {{ font-size: {hero}px; line-height: 1.0; letter-spacing: -0.01em; }}
  .row {{ font-size: 56px; line-height: 1.2; margin-top: 24px; }}
  .small {{ font-size: 42px; line-height: 1.25; }}
  .label {{ font-family: ui-monospace, monospace; font-size: 13px; letter-spacing: .08em;
            text-transform: uppercase; color: #F2C511; opacity: .75; margin-bottom: 6px; }}
  .rule {{ height: 2px; background: #F2C511; opacity: .35; margin: 34px 0 22px; }}
  .flat {{ font-family: "Tribal Totem Display Flat", sans-serif;
           color: #1a1a1a; background: #F2C511; display: inline-block;
           padding: 8px 18px; }}
  .note {{ font-family: ui-monospace, monospace; font-size: 12px; color: #F2C511;
           opacity: .7; margin-top: 30px; max-width: 900px; line-height: 1.5; }}
</style>
</head>
<body>
<div class="page">
  <div class="hero">TOTEM</div>
  <div class="rule"></div>

  <div class="label">base</div>
  <div class="row">{alphabet}</div>

  <div class="label">stylistic set 01 &mdash; font-feature-settings: "ss01"</div>
  <div class="row" style='font-feature-settings: "ss01"'>{alphabet}</div>

  <div class="label">stylistic set 02 &mdash; font-feature-settings: "ss02"</div>
  <div class="row" style='font-feature-settings: "ss02"'>{alphabet}</div>

  <div class="label">stylistic set 03 &mdash; font-feature-settings: "ss03"</div>
  <div class="row" style='font-feature-settings: "ss03"'>{alphabet}</div>

  <div class="label">flat fallback (no colour tables)</div>
  <div class="row"><span class="flat">TOTEM</span></div>

  <div class="label">Latin-1 uppercase accents</div>
  <div class="row small">{accents}</div>

  <div class="label">kerning &mdash; AVATAR To. (A)</div>
  <div class="row" style="font-size:72px">AVATAR To. (A)</div>

  <div class="label">digits &amp; punctuation</div>
  <div class="row small">{extras}</div>

  <div class="note">
    Version {version} &mdash; {count} glyphs: A&ndash;Z, 0&ndash;9,
    punctuation and symbols, four artwork variants each.<br>
    Colour glyphs use the OpenType SVG table (stroked motifs, round caps) and a
    COLRv0 fallback. Display use only: minimum recommended size 48&nbsp;px.
  </div>
</div>
</body>
</html>
"""


def write_specimen(path):
    lets = letters.LETTER_CHARS
    half = (len(lets) + 1) // 2
    alphabet = " ".join(lets[:half]) + "<br>" + " ".join(lets[half:])
    extras = (" ".join(letters.DIGIT_CHARS) + "<br>" +
              ". , : ; ! ? ' &quot; - \u2013 \u2014 ( )<br>" +
              "[ ] / \\ # + = _ |<br>" +
              "&amp; @ $ % * &lt; &gt; ^ ~ ` { }<br>" +
              "\u20ac \u00a3 \u00a5 \u00a2 \u2026 \u2022 \u00b0 \u00b1 "
              "\u00d7 \u00f7 \u00a9 \u00ae \u2122 "
              "\u2018 \u2019 \u201c \u201d")
    accents = " ".join(letters.ACCENT_CHARS)
    html = SPECIMEN.format(hero=160, alphabet=alphabet,
                           count=len(letters.CHARS) + 1, extras=extras,
                           accents=accents, version=VERSION)
    with open(path, "w") as fh:
        fh.write(html)


def screenshot():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        print("screenshot skipped:", exc)
        return None
    url = "file://" + os.path.join(ROOT, "specimen.html")
    out = os.path.join(ROOT, "specimen.png")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1200},
                                device_scale_factor=2)
        page.goto(url)
        page.wait_for_timeout(300)
        try:
            page.evaluate("document.fonts.ready")
        except Exception:
            pass
        page.wait_for_timeout(600)
        page.screenshot(path=out, full_page=True)
        browser.close()
    print("screenshot", out)
    return out


if __name__ == "__main__":
    build()
    if "--no-shot" not in sys.argv:
        screenshot()
