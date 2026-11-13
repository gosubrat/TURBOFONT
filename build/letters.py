"""Letter bodies, art zones and the motif composition table.

Body outlines are identical across every stylistic set: only the art changes.
Letters built from overlapping blocks are merged with a boolean union so the
body stays a single, clean outline with correctly wound counters.
"""
from __future__ import annotations

from dataclasses import dataclass

import math

import geom

CAP = 720
VARIANTS = ("", "ss01", "ss02", "ss03")


@dataclass
class Letter:
    char: str
    adv: int
    contours: list
    zones: dict
    art: dict           # variant -> list[(motif, zone, params)]
    label: str = ""
    name: str = ""      # safe PostScript/CFF glyph name (defaults to char)

    @property
    def glyph_name(self) -> str:
        return self.name or self.char

    @property
    def body(self) -> geom.Path:
        return geom.Path([c for c in self.contours])


# --------------------------------------------------------------------------- #
# Block helpers
# --------------------------------------------------------------------------- #
def _contour(points, cuts=None) -> geom.Contour:
    return geom.poly(geom.chamfer_polygon(points, cuts or {}))


def _rect(x0, y0, x1, y1, cuts=None) -> geom.Contour:
    return _contour([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], cuts)


def _merge(*contours) -> list:
    """Boolean-union block contours into one body outline.

    Every block is normalized to CCW first: pathops assumes matching winding
    when unioning and a mirrored block (negative area) otherwise punches a
    hole instead of adding a limb.
    """
    paths = []
    for c in contours:
        if c.signed_area() < 0:
            c = c.reversed()
        paths.append(geom.Path([c]))
    path = geom.union(paths)
    return path.contours


# --------------------------------------------------------------------------- #
# Automatic motif rotation for letters without hand-picked artwork
# --------------------------------------------------------------------------- #
def _motif_cycle(box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if w > h * 1.6:                                    # horizontal band
        return [
            ("zigzag", {"n": max(2, round(w / 105))}),
            ("greek_key", {}),
            ("diamonds", {"n": max(2, round(w / 130)), "vertical": False}),
            ("hatch", {"n": max(2, round(w / 130))}),
            ("dots", {"n": max(2, round(w / 90)), "vertical": False}),
        ]
    if h > w * 1.6:                                    # vertical stem
        return [
            ("dots", {"n": max(2, round(h / 105))}),
            ("chevrons", {"n": max(2, round(h / 115)), "vertical": True}),
            ("zigzag", {"n": max(2, round(h / 80)), "vertical": True}),
            ("hatch", {"n": max(2, round(h / 120)), "vertical": True}),
            ("diamonds", {"n": max(2, round(h / 130))}),
        ]
    if min(w, h) < 110:                                # small square pocket
        return [("star", {}), ("sun", {}), ("shield", {}), ("mask", {})]
    return [("star", {}), ("mask", {}), ("sun", {}),
            ("drum", {}), ("shield", {}), ("maraca", {})]


def _auto_art(zones) -> dict:
    """Rotate the motif library through the zones, one step per variant."""
    art = {}
    for vi, variant in enumerate(VARIANTS):
        items = []
        for zi, (zname, zval) in enumerate(zones.items()):
            if isinstance(zval[0], (tuple, list)):
                box, color = zval
            else:
                box, color = zval, "red"
            cycle = _motif_cycle(box)
            name, params = cycle[(vi + zi) % len(cycle)]
            params = dict(params)
            if color == "yellow":
                params["color"] = "yellow"
            items.append((name, zname, params))
        art[variant] = items
    return art


# --------------------------------------------------------------------------- #
# Hand-tuned proof-of-concept letters
# --------------------------------------------------------------------------- #
def _t() -> Letter:
    pts = [(0, 720), (760, 720), (760, 560), (470, 560),
           (470, 0), (290, 0), (290, 560), (0, 560)]
    pts = geom.chamfer_polygon(pts, {0: 16, 1: 20, 2: 18, 4: 14, 5: 12, 7: 15})
    zones = {
        "bar": (25, 585, 735, 695),
        "stem": (315, 25, 445, 535),
    }
    art = {
        "": [("zigzag", "bar", {"n": 6}), ("spear", "stem", {})],
        "ss01": [("diamonds", "bar", {"n": 5, "vertical": False}),
                 ("maraca", "stem", {})],
        "ss02": [("greek_key", "bar", {}), ("chevrons", "stem", {"n": 5, "vertical": True})],
        "ss03": [("dots", "bar", {"n": 7, "vertical": False}),
                 ("star", "stem", {})],
    }
    return Letter("T", 820, [geom.poly(pts)], zones, art, "spear / zigzag")


def _o() -> Letter:
    outer = geom.rounded_rect(0, 0, 780, 720, 140)
    inner = geom.rounded_rect(160, 160, 620, 560, 0).reversed()
    zones = {
        "wall_l": (25, 185, 135, 535),
        "wall_r": (645, 185, 755, 535),
        "counter": (185, 185, 595, 535),
    }
    art = {
        "": [("dots", "wall_l", {"n": 4}), ("dots", "wall_r", {"n": 4}),
             ("mask", "counter", {"color": "yellow"})],
        "ss01": [("chevrons", "wall_l", {"n": 4, "vertical": True}),
                 ("chevrons", "wall_r", {"n": 4, "vertical": True}),
                 ("sun", "counter", {"color": "yellow"})],
        "ss02": [("hatch", "wall_l", {"n": 3, "vertical": True}),
                 ("hatch", "wall_r", {"n": 3, "vertical": True}),
                 ("star", "counter", {"color": "yellow"})],
        "ss03": [("diamonds", "wall_l", {"n": 3}), ("diamonds", "wall_r", {"n": 3}),
                 ("shield", "counter", {"color": "yellow"})],
    }
    return Letter("O", 840, [outer, inner], zones, art, "mask / dots")


def _e() -> Letter:
    pts = [(0, 720), (700, 720), (700, 531), (200, 531), (200, 450),
           (640, 450), (640, 265), (200, 265), (200, 189), (700, 189),
           (700, 0), (0, 0)]
    pts = geom.chamfer_polygon(pts, {0: 18, 1: 22, 2: 12, 5: 10, 6: 10,
                                     9: 12, 10: 20, 11: 16})
    zones = {
        "stem": (25, 25, 175, 695),
        "top": (225, 556, 675, 695),
        "mid": (225, 290, 615, 425),
        "bot": (225, 25, 675, 164),
    }
    art = {
        "": [("greek_key", "stem", {"vertical": True}),
             ("hatch", "top", {"n": 4}), ("hatch", "mid", {"n": 3}),
             ("hatch", "bot", {"n": 4})],
        "ss01": [("dots", "stem", {"n": 5}),
                 ("zigzag", "top", {"n": 4}), ("zigzag", "mid", {"n": 3}),
                 ("zigzag", "bot", {"n": 4})],
        "ss02": [("spear", "stem", {}), ("star", "top", {}),
                 ("diamonds", "mid", {"n": 3, "vertical": False}),
                 ("star", "bot", {})],
        "ss03": [("chevrons", "stem", {"n": 5, "vertical": True}),
                 ("chevrons", "top", {"n": 2}), ("chevrons", "mid", {"n": 2}),
                 ("chevrons", "bot", {"n": 2})],
    }
    return Letter("E", 820, [geom.poly(pts)], zones, art, "Greek key / hatch")


def _m() -> Letter:
    # Stems + a chevron band in the upper middle. The inner V sits BELOW the
    # outer V, otherwise the outline self-intersects and even-odd fill eats
    # the middle of the letter.
    pts = [(0, 720), (190, 720), (470, 547), (750, 720), (940, 720),
           (940, 0), (750, 0), (750, 520), (470, 297), (190, 520), (190, 0), (0, 0)]
    pts = geom.chamfer_polygon(pts, {0: 16, 1: 12, 2: 14, 3: 14, 4: 22,
                                     5: 18, 6: 14, 10: 18, 11: 16})
    zones = {
        "stem_l": (25, 25, 165, 695),
        "stem_r": (775, 25, 915, 695),
        "center": (400, 360, 540, 500),
    }
    art = {
        "": [("chevrons", "stem_l", {"n": 5, "vertical": True}),
             ("chevrons", "stem_r", {"n": 5, "vertical": True}),
             ("star", "center", {})],
        "ss01": [("zigzag", "stem_l", {"n": 6, "vertical": True}),
                 ("zigzag", "stem_r", {"n": 6, "vertical": True}),
                 ("mask", "center", {})],
        "ss02": [("diamonds", "stem_l", {"n": 4}), ("diamonds", "stem_r", {"n": 4}),
                 ("sun", "center", {})],
        "ss03": [("hatch", "stem_l", {"n": 4, "vertical": True}),
                 ("hatch", "stem_r", {"n": 4, "vertical": True}),
                 ("dots", "center", {"n": 3})],
    }
    return Letter("M", 1000, [geom.poly(pts)], zones, art, "chevrons / star")


# --------------------------------------------------------------------------- #
# M2 letters (block-built, auto-rotated art)
# --------------------------------------------------------------------------- #
def _a() -> Letter:
    # Two splayed legs and a crossbar. The legs overlap at the apex so the
    # top closes into a flat slab instead of a fragile point.
    left = _contour([(0, 0), (180, 0), (420, 720), (240, 720)],
                    {0: 14, 3: 16})
    right = _contour([(780, 0), (600, 0), (360, 720), (540, 720)],
                     {0: 16, 1: 10, 3: 12})
    cross = _rect(160, 300, 620, 430, {0: 10, 1: 10, 2: 10, 3: 10})
    zones = {
        "leg_l": (250, 585, 345, 650),
        "leg_r": (435, 585, 530, 650),
        "bar": (200, 325, 580, 405),
    }
    return Letter("A", 840, _merge(left, right, cross), zones,
                  _auto_art(zones), "apex / crossbar")


def _b() -> Letter:
    stem = _rect(0, 0, 160, 720)
    top = _rect(0, 560, 760, 720, {2: 20, 3: 18})
    mid = _rect(0, 300, 720, 430, {1: 10, 2: 10})
    bot = _rect(0, 0, 760, 160, {0: 20, 1: 20})
    right_top = _rect(600, 430, 760, 720, {2: 14})
    right_bot = _rect(600, 160, 760, 300)
    zones = {
        "stem_lo": (25, 25, 135, 275),
        "stem_hi": (25, 455, 135, 695),
        "top": (185, 585, 735, 695),
        "mid": (200, 325, 560, 405),
        "bot": (185, 25, 735, 135),
    }
    return Letter("B", 820, _merge(stem, top, mid, bot, right_top, right_bot),
                  zones, _auto_art(zones), "double bowl")


def _c() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    stem = _rect(0, 0, 160, 720)
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20, 2: 12})
    zones = {
        "top": (185, 585, 735, 695),
        "stem": (25, 185, 135, 535),
        "bot": (185, 25, 735, 135),
    }
    return Letter("C", 820, _merge(top, stem, bot), zones,
                  _auto_art(zones), "open bowl")


def _d() -> Letter:
    stem = _rect(0, 0, 160, 720)
    top = _rect(0, 560, 760, 720, {2: 20, 3: 18})
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20})
    right = _rect(600, 160, 760, 560)
    zones = {
        "stem": (25, 185, 135, 535),
        "top": (185, 585, 735, 695),
        "bot": (185, 25, 735, 135),
        "right": (625, 185, 735, 535),
    }
    return Letter("D", 820, _merge(stem, top, bot, right), zones,
                  _auto_art(zones), "stem / bowl")


def _f() -> Letter:
    stem = _rect(0, 0, 160, 720)
    top = _rect(0, 560, 720, 720, {1: 12, 2: 20, 3: 18})
    mid = _rect(0, 300, 680, 430, {1: 10, 2: 10})
    zones = {
        "stem_lo": (25, 25, 135, 275),
        "stem_hi": (25, 455, 135, 695),
        "top": (185, 585, 695, 695),
        "mid": (200, 325, 655, 405),
    }
    return Letter("F", 800, _merge(stem, top, mid), zones,
                  _auto_art(zones), "two arms")


def _g() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    stem = _rect(0, 0, 160, 720)
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20, 2: 12})
    right = _rect(600, 160, 760, 420, {2: 10})
    spur = _rect(380, 300, 760, 420, {3: 10})
    zones = {
        "top": (185, 585, 735, 695),
        "stem": (25, 185, 135, 535),
        "mid": (405, 325, 575, 395),
        "right": (625, 185, 735, 275),
        "bot": (185, 25, 735, 135),
    }
    return Letter("G", 820, _merge(top, stem, bot, right, spur), zones,
                  _auto_art(zones), "spurred bowl")


def _h() -> Letter:
    left = _rect(0, 0, 160, 720, {2: 14, 3: 14})
    right = _rect(600, 0, 760, 720, {0: 14, 1: 14})
    cross = _rect(0, 280, 760, 440)
    zones = {
        "stem_l": (25, 25, 135, 695),
        "stem_r": (625, 25, 735, 695),
        "cross": (185, 305, 575, 415),
    }
    return Letter("H", 820, _merge(left, right, cross), zones,
                  _auto_art(zones), "ladder")


def _i() -> Letter:
    top = _rect(0, 560, 760, 720, {2: 20, 3: 18})
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20})
    stem = _rect(300, 160, 460, 560)
    zones = {
        "top": (25, 585, 735, 695),
        "bot": (25, 25, 735, 135),
        "stem": (325, 185, 435, 535),
    }
    return Letter("I", 820, _merge(top, bot, stem), zones,
                  _auto_art(zones), "slab pillar")


def _j() -> Letter:
    pts = [(0, 720), (760, 720), (760, 0), (180, 0), (0, 180),
           (0, 300), (220, 300), (220, 160), (600, 160), (600, 560),
           (0, 560)]
    pts = geom.chamfer_polygon(pts, {0: 16, 1: 20, 2: 16, 5: 12, 6: 10,
                                     10: 14})
    zones = {
        "top": (25, 585, 735, 695),
        "stem": (625, 185, 735, 535),
        "bot": (205, 25, 735, 135),
        "hook": (65, 195, 190, 275),
    }
    return Letter("J", 820, [geom.poly(pts)], zones,
                  _auto_art(zones), "hooked pillar")


def _k() -> Letter:
    stem = _rect(0, 0, 160, 720)
    upper = _contour([(140, 300), (140, 460), (760, 720), (760, 560)],
                     {2: 20, 3: 16})
    lower = _contour([(140, 260), (140, 420), (760, 160), (760, 0)],
                     {2: 20, 3: 16})
    zones = {
        "stem": (25, 25, 135, 695),
        "upper": (625, 570, 705, 635),
        "lower": (625, 85, 705, 150),
    }
    return Letter("K", 820, _merge(stem, upper, lower), zones,
                  _auto_art(zones), "split arms")


def _l() -> Letter:
    stem = _rect(0, 0, 160, 720, {2: 14})
    foot = _rect(0, 0, 720, 160, {0: 18, 1: 20})
    zones = {
        "stem": (25, 185, 135, 695),
        "foot": (185, 25, 695, 135),
    }
    return Letter("L", 800, _merge(stem, foot), zones,
                  _auto_art(zones), "stem / foot")


def _n() -> Letter:
    left = _rect(0, 0, 160, 720, {2: 14, 3: 14})
    right = _rect(600, 0, 760, 720, {0: 14, 1: 14})
    diag = _contour([(0, 560), (0, 720), (760, 160), (760, 0)],
                    {1: 18, 2: 16})
    zones = {
        "stem_l": (25, 185, 135, 535),
        "stem_r": (625, 185, 735, 535),
        "diag": (375, 320, 425, 370),
    }
    return Letter("N", 820, _merge(left, right, diag), zones,
                  _auto_art(zones), "diagonal")


def _p() -> Letter:
    stem = _rect(0, 0, 160, 720)
    top = _rect(0, 560, 720, 720, {2: 20, 3: 18})
    mid = _rect(0, 360, 720, 480, {1: 10, 2: 10})
    right = _rect(560, 360, 720, 720, {2: 12})
    zones = {
        "stem": (25, 25, 135, 335),
        "top": (185, 585, 695, 695),
        "mid": (185, 385, 695, 455),
    }
    return Letter("P", 800, _merge(stem, top, mid, right), zones,
                  _auto_art(zones), "bowl")


def _q() -> Letter:
    outer = geom.rounded_rect(0, 0, 780, 720, 140)
    inner = geom.rounded_rect(160, 160, 620, 560, 0).reversed()
    tail = _contour([(600, 160), (720, 160), (820, 0), (700, 0)],
                    {2: 16, 3: 16})
    zones = {
        "wall_l": (25, 185, 135, 535),
        "wall_r": (645, 185, 755, 535),
        "counter": (185, 185, 595, 535),
    }
    art = {
        "": [("dots", "wall_l", {"n": 4}), ("dots", "wall_r", {"n": 4}),
             ("mask", "counter", {"color": "yellow"})],
        "ss01": [("chevrons", "wall_l", {"n": 4, "vertical": True}),
                 ("chevrons", "wall_r", {"n": 4, "vertical": True}),
                 ("sun", "counter", {"color": "yellow"})],
        "ss02": [("hatch", "wall_l", {"n": 3, "vertical": True}),
                 ("hatch", "wall_r", {"n": 3, "vertical": True}),
                 ("star", "counter", {"color": "yellow"})],
        "ss03": [("diamonds", "wall_l", {"n": 3}), ("diamonds", "wall_r", {"n": 3}),
                 ("shield", "counter", {"color": "yellow"})],
    }
    return Letter("Q", 860, _merge(outer, tail) + [inner], zones, art,
                  "mask / tail")


def _r() -> Letter:
    stem = _rect(0, 0, 160, 720)
    top = _rect(0, 560, 740, 720, {2: 20, 3: 18})
    mid = _rect(0, 360, 740, 480, {1: 10, 2: 10})
    right = _rect(580, 360, 740, 720, {2: 12})
    leg = _contour([(560, 420), (720, 420), (820, 0), (660, 0)],
                   {2: 16, 3: 16})
    zones = {
        "stem": (25, 25, 135, 335),
        "top": (185, 585, 715, 695),
        "mid": (185, 385, 715, 455),
        "leg": (655, 170, 735, 245),
    }
    return Letter("R", 860, _merge(stem, top, mid, right, leg), zones,
                  _auto_art(zones), "bowl / leg")


def _s() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    upper = _rect(0, 340, 160, 620)
    mid = _rect(0, 280, 760, 460, {0: 12, 1: 10, 2: 10, 3: 12})
    lower = _rect(600, 100, 760, 380)
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20, 2: 12})
    zones = {
        "top": (185, 585, 735, 695),
        "upper": (25, 380, 135, 590),
        "mid": (200, 305, 560, 435),
        "lower": (625, 120, 735, 255),
        "bot": (185, 25, 735, 135),
    }
    return Letter("S", 820, _merge(top, upper, mid, lower, bot), zones,
                  _auto_art(zones), "double curve")


def _u() -> Letter:
    left = _rect(0, 0, 160, 720, {2: 14})
    right = _rect(600, 0, 760, 720, {3: 14})
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20})
    zones = {
        "stem_l": (25, 185, 135, 695),
        "stem_r": (625, 185, 735, 695),
        "bot": (185, 25, 735, 135),
    }
    return Letter("U", 820, _merge(left, right, bot), zones,
                  _auto_art(zones), "open bowl")


def _v() -> Letter:
    left = _contour([(0, 720), (160, 720), (480, 0), (320, 0)],
                    {0: 16, 3: 10})
    right = _contour([(600, 720), (760, 720), (440, 0), (280, 0)],
                     {1: 16, 2: 10})
    zones = {
        "arm_l_hi": (117, 520, 186, 600),
        "arm_l_lo": (215, 300, 285, 380),
        "arm_r_hi": (574, 520, 643, 600),
        "arm_r_lo": (475, 300, 545, 380),
        "bot": (325, 40, 435, 120),
    }
    return Letter("V", 820, _merge(left, right), zones,
                  _auto_art(zones), "converging arms")


def _w() -> Letter:
    a1 = _contour([(0, 720), (160, 720), (340, 0), (180, 0)],
                  {0: 16, 1: 10})
    a2 = _contour([(180, 0), (340, 0), (480, 720), (320, 720)],
                  {2: 12, 3: 12})
    a3 = _contour([(320, 720), (480, 720), (660, 0), (500, 0)],
                  {0: 12, 1: 12})
    a4 = _contour([(500, 0), (660, 0), (800, 720), (640, 720)],
                  {2: 16, 3: 10})
    zones = {
        "top_l": (70, 555, 140, 685),
        "top_m": (340, 555, 420, 685),
        "top_r": (660, 555, 730, 685),
        "valley_l": (200, 40, 320, 120),
        "valley_r": (520, 45, 640, 115),
    }
    return Letter("W", 860, _merge(a1, a2, a3, a4), zones,
                  _auto_art(zones), "double valley")


def _x() -> Letter:
    down = _contour([(0, 720), (160, 720), (760, 0), (600, 0)],
                    {0: 16, 1: 12, 2: 16, 3: 12})
    up = _contour([(600, 720), (760, 720), (160, 0), (0, 0)],
                  {0: 12, 1: 16, 2: 12, 3: 16})
    zones = {
        "ul": (141, 590, 194, 640),
        "ur": (566, 590, 619, 640),
        "ll": (590, 55, 642, 105),
        "lr": (118, 55, 170, 105),
        "center": (330, 320, 430, 420),
    }
    return Letter("X", 820, _merge(down, up), zones,
                  _auto_art(zones), "crossed bands")


def _y() -> Letter:
    left = _contour([(0, 720), (160, 720), (460, 360), (300, 360)],
                    {0: 16, 3: 10})
    right = _contour([(600, 720), (760, 720), (460, 360), (300, 360)],
                     {1: 16, 2: 10})
    stem = _rect(300, 0, 460, 400)
    zones = {
        "upper_l": (118, 620, 167, 668),
        "upper_r": (593, 620, 642, 668),
        "knot": (335, 385, 425, 428),
        "stem": (325, 25, 435, 335),
    }
    return Letter("Y", 820, _merge(left, right, stem), zones,
                  _auto_art(zones), "fork / stem")


def _z() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20, 2: 12})
    diag = _contour([(580, 620), (760, 620), (340, 80), (160, 80)],
                    {1: 14, 2: 14})
    zones = {
        "top": (185, 585, 735, 695),
        "bot": (185, 25, 735, 135),
        "diag": (432, 315, 490, 385),
    }
    return Letter("Z", 820, _merge(top, bot, diag), zones,
                  _auto_art(zones), "zig diagonal")


# --------------------------------------------------------------------------- #
# Digits
# --------------------------------------------------------------------------- #
def _zero() -> Letter:
    outer = geom.rounded_rect(0, 0, 760, 720, 120)
    inner = geom.rounded_rect(160, 160, 600, 560, 0).reversed()
    zones = {
        "wall_l": (25, 185, 135, 535),
        "wall_r": (625, 185, 735, 535),
        "counter": (185, 185, 575, 535),
    }
    art = {
        "": [("dots", "wall_l", {"n": 4}), ("dots", "wall_r", {"n": 4}),
             ("mask", "counter", {"color": "yellow"})],
        "ss01": [("chevrons", "wall_l", {"n": 4, "vertical": True}),
                 ("chevrons", "wall_r", {"n": 4, "vertical": True}),
                 ("sun", "counter", {"color": "yellow"})],
        "ss02": [("hatch", "wall_l", {"n": 3, "vertical": True}),
                 ("hatch", "wall_r", {"n": 3, "vertical": True}),
                 ("star", "counter", {"color": "yellow"})],
        "ss03": [("diamonds", "wall_l", {"n": 3}), ("diamonds", "wall_r", {"n": 3}),
                 ("shield", "counter", {"color": "yellow"})],
    }
    return Letter("0", 820, [outer, inner], zones, art, "ring", "zero")


def _one() -> Letter:
    flag = _rect(0, 560, 460, 720, {2: 20, 3: 18})
    stem = _rect(300, 0, 460, 720)
    foot = _rect(0, 0, 760, 160, {0: 18, 1: 20})
    zones = {
        "flag": (25, 585, 435, 695),
        "stem": (325, 185, 435, 535),
        "foot_l": (25, 25, 275, 135),
        "foot_r": (485, 25, 735, 135),
    }
    return Letter("1", 820, _merge(flag, stem, foot), zones,
                  _auto_art(zones), "flagged pillar", "one")


def _two() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    upper = _rect(600, 420, 760, 620, {2: 10})
    mid = _rect(0, 400, 760, 520, {1: 10, 2: 10})
    lower = _rect(0, 100, 160, 440)
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20, 2: 12})
    zones = {
        "top": (185, 585, 735, 695),
        "mid": (185, 425, 575, 495),
        "lower": (25, 185, 135, 415),
        "bot": (185, 25, 735, 135),
    }
    return Letter("2", 820, _merge(top, upper, mid, lower, bot), zones,
                  _auto_art(zones), "two-form", "two")


def _three() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    right = _rect(600, 400, 760, 620, {2: 10})
    mid = _rect(0, 400, 760, 520, {1: 10, 2: 10})
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20, 2: 12})
    zones = {
        "top": (185, 585, 735, 695),
        "mid": (185, 425, 575, 495),
        "bot": (185, 25, 735, 135),
    }
    return Letter("3", 820, _merge(top, right, mid, bot), zones,
                  _auto_art(zones), "two bowls", "three")


def _four() -> Letter:
    left = _rect(240, 300, 400, 720, {2: 14})
    right = _rect(600, 0, 760, 720, {0: 14, 1: 14})
    cross = _rect(0, 280, 760, 430)
    zones = {
        "left": (265, 455, 375, 695),
        "right_hi": (625, 455, 735, 695),
        "cross": (185, 305, 575, 405),
        "right_lo": (625, 25, 735, 255),
    }
    return Letter("4", 820, _merge(left, right, cross), zones,
                  _auto_art(zones), "broken cross", "four")


def _five() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    upper = _rect(0, 340, 160, 620)
    mid = _rect(0, 280, 760, 460, {0: 12, 1: 10, 2: 10, 3: 12})
    lower = _rect(600, 100, 760, 380)
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20, 2: 12})
    zones = {
        "top": (185, 585, 735, 695),
        "upper": (25, 380, 135, 590),
        "mid": (200, 305, 560, 435),
        "lower": (625, 120, 735, 255),
        "bot": (185, 25, 735, 135),
    }
    return Letter("5", 820, _merge(top, upper, mid, lower, bot), zones,
                  _auto_art(zones), "S-form", "five")


def _six() -> Letter:
    stem = _rect(0, 0, 160, 720)
    top = _rect(0, 540, 620, 720, {2: 18})
    mid = _rect(0, 420, 760, 560, {1: 10, 2: 10})
    right = _rect(600, 160, 760, 540)
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20})
    zones = {
        "top": (185, 585, 595, 695),
        "left": (25, 185, 135, 395),
        "mid": (185, 445, 575, 535),
        "right": (625, 185, 735, 395),
        "bot": (185, 25, 575, 135),
    }
    return Letter("6", 820, _merge(stem, top, mid, right, bot), zones,
                  _auto_art(zones), "lower bowl", "six")


def _seven() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    diag = _contour([(560, 560), (760, 560), (520, 0), (340, 0)],
                    {2: 16, 3: 16})
    zones = {
        "top": (185, 585, 735, 695),
        "diag_hi": (552, 400, 664, 470),
        "diag_lo": (485, 220, 587, 300),
    }
    return Letter("7", 820, _merge(top, diag), zones,
                  _auto_art(zones), "diagonal", "seven")


def _eight() -> Letter:
    top = _rect(0, 560, 760, 720, {2: 20, 3: 18})
    mid = _rect(0, 300, 760, 440)
    bot = _rect(0, 0, 760, 160, {0: 18, 1: 20})
    left = _rect(0, 0, 160, 720)
    right_top = _rect(600, 440, 760, 720, {2: 14})
    right_bot = _rect(600, 0, 760, 320)
    zones = {
        "stem_lo": (25, 25, 135, 275),
        "stem_hi": (25, 455, 135, 695),
        "top": (185, 585, 735, 695),
        "mid": (185, 325, 575, 415),
        "bot": (185, 25, 735, 135),
    }
    return Letter("8", 820, _merge(left, right_top, right_bot, top, mid, bot),
                  zones, _auto_art(zones), "double ring", "eight")


def _nine() -> Letter:
    top = _rect(0, 560, 760, 720, {1: 12, 2: 20, 3: 18})
    left = _rect(0, 180, 160, 580)
    mid = _rect(0, 160, 760, 300)
    right = _rect(600, 0, 760, 720, {0: 14, 1: 14})
    foot = _rect(140, 0, 760, 180, {0: 18})
    zones = {
        "top": (185, 585, 735, 695),
        "left": (25, 325, 135, 535),
        "mid": (185, 185, 575, 275),
        "right": (625, 325, 735, 535),
        "foot": (165, 25, 735, 135),
    }
    return Letter("9", 820, _merge(top, left, mid, right, foot), zones,
                  _auto_art(zones), "upper bowl", "nine")


# --------------------------------------------------------------------------- #
# Punctuation
# --------------------------------------------------------------------------- #
def _punct(char, name, adv, contours, zones, label) -> Letter:
    return Letter(char, adv, contours, zones, _auto_art(zones), label, name)


def _period() -> Letter:
    body = _merge(_rect(110, 0, 310, 200, {0: 20, 1: 20, 2: 18, 3: 18}))
    zones = {"dot": (135, 25, 285, 175)}
    return _punct(".", "period", 420, body, zones, "dot")


def _comma() -> Letter:
    square = _rect(110, 0, 310, 200, {2: 18, 3: 18})
    tail = _contour([(210, 0), (310, 0), (230, -130), (130, -70)], {2: 14, 3: 14})
    body = _merge(square, tail)
    zones = {"dot": (135, 25, 285, 175)}
    return _punct(",", "comma", 420, body, zones, "tailed dot")


def _colon() -> Letter:
    top = _rect(130, 360, 290, 520, {2: 16, 3: 16})
    bot = _rect(130, 40, 290, 200, {0: 16, 1: 16})
    zones = {
        "dot_top": (155, 385, 265, 495),
        "dot_bot": (155, 65, 265, 175),
    }
    return _punct(":", "colon", 420, _merge(top, bot), zones, "two dots")


def _semicolon() -> Letter:
    top = _rect(130, 360, 290, 520, {2: 16, 3: 16})
    bot = _rect(130, 40, 290, 200, {2: 16, 3: 16})
    tail = _contour([(230, 40), (290, 40), (210, -100), (120, -50)], {2: 14})
    zones = {
        "dot_top": (155, 385, 265, 495),
        "dot_bot": (155, 65, 265, 175),
    }
    return _punct(";", "semicolon", 420, _merge(top, bot, tail), zones,
                  "dot + tail")


def _exclam() -> Letter:
    stem = _rect(170, 220, 310, 720, {2: 18, 3: 18})
    dot = _rect(170, 0, 310, 160, {0: 18, 1: 18})
    zones = {
        "stem": (195, 245, 285, 695),
        "dot": (195, 25, 285, 135),
    }
    return _punct("!", "exclam", 440, _merge(stem, dot), zones, "stem + dot")


def _question() -> Letter:
    top = _rect(60, 560, 460, 720, {1: 16, 2: 20, 3: 18})
    right = _rect(320, 420, 460, 620, {2: 10})
    mid = _rect(60, 400, 460, 520, {1: 10})
    stem = _rect(200, 180, 320, 440)
    dot = _rect(200, 0, 320, 120, {0: 16, 1: 16})
    zones = {
        "top": (85, 585, 435, 695),
        "mid": (85, 425, 435, 495),
        "stem": (225, 205, 295, 415),
        "dot": (225, 25, 295, 95),
    }
    return _punct("?", "question", 520, _merge(top, right, mid, stem, dot),
                  zones, "hook + dot")


def _quotesingle() -> Letter:
    body = _merge(_rect(160, 440, 320, 720, {2: 16, 3: 16}))
    zones = {"quote": (185, 465, 295, 695)}
    return _punct("'", "quotesingle", 400, body, zones, "single")


def _quotedbl() -> Letter:
    left = _rect(100, 440, 240, 720, {2: 16, 3: 16})
    right = _rect(300, 440, 440, 720, {2: 16, 3: 16})
    zones = {
        "quote_l": (125, 465, 215, 695),
        "quote_r": (325, 465, 415, 695),
    }
    return _punct('"', "quotedbl", 540, _merge(left, right), zones, "double")


def _hyphen() -> Letter:
    body = _merge(_rect(60, 320, 460, 440, {0: 12, 1: 12, 2: 12, 3: 12}))
    zones = {"bar": (85, 345, 435, 415)}
    return _punct("-", "hyphen", 520, body, zones, "short dash")


def _endash() -> Letter:
    body = _merge(_rect(20, 320, 540, 440, {0: 12, 1: 12, 2: 12, 3: 12}))
    zones = {"bar": (45, 345, 515, 415)}
    return _punct("\u2013", "endash", 560, body, zones, "en dash")


def _emdash() -> Letter:
    body = _merge(_rect(0, 320, 560, 440, {0: 12, 1: 12, 2: 12, 3: 12}))
    zones = {"bar": (25, 345, 535, 415)}
    return _punct("\u2014", "emdash", 560, body, zones, "em dash")


def _parenleft() -> Letter:
    top = _rect(140, 560, 480, 720, {1: 14, 2: 20, 3: 18})
    stem = _rect(140, 160, 300, 720)
    bot = _rect(140, 0, 480, 160, {0: 18, 1: 20, 2: 14})
    zones = {
        "top": (165, 585, 455, 695),
        "stem": (165, 185, 275, 535),
        "bot": (165, 25, 455, 135),
    }
    return _punct("(", "parenleft", 520, _merge(top, stem, bot), zones, "round")


def _parenright() -> Letter:
    top = _rect(0, 560, 340, 720, {0: 18, 1: 14, 2: 20, 3: 20})
    stem = _rect(180, 160, 340, 720)
    bot = _rect(0, 0, 340, 160, {0: 20, 1: 18, 2: 14})
    zones = {
        "top": (25, 585, 315, 695),
        "stem": (205, 185, 315, 535),
        "bot": (25, 25, 315, 135),
    }
    return _punct(")", "parenright", 520, _merge(top, stem, bot), zones, "round")


def _bracketleft() -> Letter:
    top = _rect(100, 560, 480, 720, {1: 14, 2: 20, 3: 18})
    stem = _rect(100, 0, 260, 720)
    bot = _rect(100, 0, 480, 160, {0: 18, 1: 20, 2: 14})
    zones = {
        "top": (125, 585, 455, 695),
        "stem": (125, 185, 235, 535),
        "bot": (125, 25, 455, 135),
    }
    return _punct("[", "bracketleft", 520, _merge(top, stem, bot), zones, "square")


def _bracketright() -> Letter:
    top = _rect(0, 560, 380, 720, {0: 18, 1: 14, 2: 20, 3: 20})
    stem = _rect(220, 0, 380, 720)
    bot = _rect(0, 0, 380, 160, {0: 20, 1: 18, 2: 14})
    zones = {
        "top": (25, 585, 355, 695),
        "stem": (245, 185, 355, 535),
        "bot": (25, 25, 355, 135),
    }
    return _punct("]", "bracketright", 520, _merge(top, stem, bot), zones, "square")


def _slash() -> Letter:
    body = _merge(_contour([(60, 0), (220, 0), (500, 720), (340, 720)],
                           {2: 16, 3: 16}))
    zones = {"diag": (243, 300, 309, 400)}
    return _punct("/", "slash", 560, body, zones, "diagonal")


def _backslash() -> Letter:
    body = _merge(_contour([(340, 0), (500, 0), (220, 720), (60, 720)],
                           {2: 16, 3: 16}))
    zones = {"diag": (251, 300, 317, 400)}
    return _punct("\\", "backslash", 560, body, zones, "diagonal")


def _numbersign() -> Letter:
    v1 = _rect(120, 0, 240, 720)
    v2 = _rect(320, 0, 440, 720)
    h1 = _rect(20, 240, 540, 360)
    h2 = _rect(20, 440, 540, 560)
    zones = {
        "v1_lo": (145, 25, 215, 215),
        "v1_hi": (145, 585, 215, 695),
        "v2_lo": (345, 25, 415, 215),
        "v2_hi": (345, 585, 415, 695),
    }
    return _punct("#", "numbersign", 560, _merge(v1, v2, h1, h2), zones,
                  "crossed bars")


def _plus() -> Letter:
    v = _rect(220, 100, 340, 620)
    h = _rect(20, 300, 540, 420)
    zones = {
        "v_top": (245, 445, 315, 595),
        "v_bot": (245, 125, 315, 275),
        "h_left": (45, 325, 195, 395),
        "h_right": (365, 325, 515, 395),
    }
    return _punct("+", "plus", 560, _merge(v, h), zones, "cross")


def _equal() -> Letter:
    top = _rect(20, 420, 540, 540, {0: 12, 1: 12, 2: 12, 3: 12})
    bot = _rect(20, 220, 540, 340, {0: 12, 1: 12, 2: 12, 3: 12})
    zones = {
        "bar_top": (45, 445, 515, 515),
        "bar_bot": (45, 245, 515, 315),
    }
    return _punct("=", "equal", 560, _merge(top, bot), zones, "two bars")


def _underscore() -> Letter:
    body = _merge(_rect(0, 0, 560, 120, {1: 14, 2: 14}))
    zones = {"bar": (25, 25, 535, 95)}
    return _punct("_", "underscore", 560, body, zones, "low bar")


def _bar() -> Letter:
    body = _merge(_rect(170, 0, 310, 720, {0: 16, 1: 16}))
    zones = {"bar": (195, 25, 285, 695)}
    return _punct("|", "bar", 480, body, zones, "pillar")


def _dollar() -> Letter:
    top = _rect(0, 560, 520, 720, {1: 12, 2: 18, 3: 16})
    upper = _rect(0, 340, 160, 620)
    mid = _rect(0, 280, 520, 460, {0: 10, 1: 10, 2: 10, 3: 10})
    lower = _rect(360, 100, 520, 380)
    bot = _rect(0, 0, 520, 160, {0: 16, 1: 18, 2: 12})
    bar = _rect(230, -40, 310, 760, {0: 8, 1: 8, 2: 8, 3: 8})
    zones = {
        "top": (25, 585, 495, 695),
        "upper": (25, 380, 135, 590),
        "mid_l": (25, 305, 205, 435),
        "mid_r": (335, 305, 495, 435),
        "lower": (385, 120, 495, 255),
        "bot": (25, 25, 495, 135),
    }
    return _punct("$", "dollar", 560, _merge(top, upper, mid, lower, bot, bar),
                  zones, "S + bar")


def _percent() -> Letter:
    top_outer = geom.rounded_rect(0, 440, 240, 720, 60)
    bot_outer = geom.rounded_rect(280, 0, 520, 280, 60)
    slash = _contour([(180, 60), (340, 60), (400, 660), (240, 660)],
                     {2: 14, 3: 14})
    top_hole = geom.rounded_rect(60, 500, 180, 660, 0).reversed()
    bot_hole = geom.rounded_rect(340, 60, 460, 220, 0).reversed()
    body = _merge(top_outer, bot_outer, slash) + [top_hole, bot_hole]
    zones = {
        "slash_hi": (265, 450, 352, 550),
        "slash_lo": (234, 250, 334, 350),
    }
    return _punct("%", "percent", 560, body, zones, "rings + slash")


def _at() -> Letter:
    outer = geom.rounded_rect(0, 0, 520, 720, 110)
    hole = geom.rounded_rect(120, 140, 400, 580, 0).reversed()
    island = _merge(geom.rounded_rect(220, 260, 340, 500, 70),
                    _rect(300, 220, 390, 300))
    island_hole = geom.rounded_rect(250, 320, 310, 440, 0).reversed()
    body = [outer, hole] + island + [island_hole]
    zones = {
        "top": (145, 605, 375, 695),
        "bot": (145, 25, 375, 115),
        "wall_l": (25, 185, 95, 535),
        "wall_r": (425, 185, 495, 535),
    }
    return _punct("@", "at", 560, body, zones, "ring + a")


def _ampersand() -> Letter:
    top = _rect(60, 600, 300, 720, {2: 18, 3: 16})
    upper_left = _rect(60, 460, 140, 720)
    upper_right = _rect(220, 460, 300, 720, {2: 12})
    upper_bot = _rect(60, 460, 300, 520)
    waist = _rect(60, 380, 420, 480, {1: 10, 2: 10})
    lower_left = _rect(60, 180, 140, 460)
    lower_right = _rect(340, 180, 420, 380)
    bottom = _rect(60, 0, 420, 180, {0: 16, 1: 18})
    leg = _contour([(340, 180), (420, 180), (520, 720), (440, 720)],
                   {2: 12, 3: 10})
    zones = {
        "top": (85, 625, 275, 695),
        "waist": (165, 405, 315, 455),
        "bot": (85, 25, 395, 155),
    }
    return _punct("&", "ampersand", 560,
                  _merge(top, upper_left, upper_right, upper_bot, waist,
                         lower_left, lower_right, bottom, leg),
                  zones, "small loop + leg")


def _asterisk() -> Letter:
    cx, cy, R, r = 280, 540, 160, 64
    pts = []
    for i in range(12):
        ang = math.radians(90 + i * 30)
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    zones = {"core": (252, 512, 308, 568)}
    return _punct("*", "asterisk", 560, [geom.poly(pts)], zones, "six-point star")


def _less() -> Letter:
    body = geom.stroke_path([[(420, 650), (120, 540), (420, 430)]],
                            width=130, cap="butt", join="bevel")
    zones = {"core": (300, 600, 380, 650)}
    return _punct("<", "less", 560, body.contours, zones, "chevron")


def _greater() -> Letter:
    body = geom.stroke_path([[(140, 650), (440, 540), (140, 430)]],
                            width=130, cap="butt", join="bevel")
    zones = {"core": (180, 600, 260, 650)}
    return _punct(">", "greater", 560, body.contours, zones, "chevron")


def _asciicircum() -> Letter:
    body = _merge(_contour([
        (40, 360), (280, 720), (520, 360),
        (360, 360), (280, 480), (200, 360),
    ]))
    zones = {"core": (245, 520, 310, 620)}
    return _punct("^", "asciicircum", 560, body, zones, "caret")


def _asciitilde() -> Letter:
    band = geom.strokes_to_fill(
        [[(60, 420), (180, 560), (340, 400), (460, 540)]], width=100)
    zones = {"core": (238, 458, 282, 502)}
    return _punct("~", "asciitilde", 560, band.contours, zones, "wave")


def _grave() -> Letter:
    body = _merge(_contour([(40, 440), (260, 440), (340, 620), (120, 620)],
                           {0: 10, 1: 10, 2: 14, 3: 14}))
    zones = {"tick": (110, 470, 245, 530)}
    return _punct("`", "grave", 480, body, zones, "slanted tick")


def _braceleft() -> Letter:
    top = _rect(160, 560, 480, 720, {1: 14, 2: 18, 3: 16})
    upper = _rect(160, 400, 320, 720)
    nub = _rect(60, 300, 320, 420, {0: 12, 2: 12, 3: 12})
    lower = _rect(160, 0, 320, 320)
    bot = _rect(160, 0, 480, 160, {0: 16, 1: 18, 2: 14})
    zones = {
        "top": (185, 585, 455, 695),
        "upper": (185, 425, 295, 535),
        "nub": (85, 325, 235, 395),
        "lower": (185, 185, 295, 275),
        "bot": (185, 25, 455, 135),
    }
    return _punct("{", "braceleft", 520, _merge(top, upper, nub, lower, bot),
                  zones, "brace")


def _braceright() -> Letter:
    top = _rect(40, 560, 360, 720, {0: 16, 1: 14, 2: 18, 3: 18})
    upper = _rect(200, 400, 360, 720)
    nub = _rect(200, 300, 460, 420, {1: 12, 2: 12, 3: 12})
    lower = _rect(200, 0, 360, 320)
    bot = _rect(40, 0, 360, 160, {0: 18, 1: 16, 2: 14})
    zones = {
        "top": (65, 585, 335, 695),
        "upper": (225, 425, 335, 535),
        "nub": (285, 325, 435, 395),
        "lower": (225, 185, 335, 275),
        "bot": (65, 25, 335, 135),
    }
    return _punct("}", "braceright", 520, _merge(top, upper, nub, lower, bot),
                  zones, "brace")


# --------------------------------------------------------------------------- #
# Composed letters and currencies
# --------------------------------------------------------------------------- #
def _scaled_path(letter, sx, sy, tx=0.0, ty=0.0) -> geom.Path:
    return geom.Path([c.transformed(sx, sy, tx, ty) for c in letter.body.contours])


def _ae() -> Letter:
    a, e = _a(), _e()
    body = geom.union([_scaled_path(a, 600 / 780, 1.0),
                       _scaled_path(e, 380 / 700, 1.0, 600, 0)])
    zones = {
        "leg_l": (195, 585, 263, 650),
        "leg_r": (337, 585, 405, 650),
        "bar": (180, 325, 420, 405),
        "etop": (625, 585, 955, 695),
        "emid": (720, 325, 920, 405),
        "ebot": (625, 25, 955, 135),
    }
    return _punct("\u00c6", "AE", 1000, body.contours, zones, "A + E")


def _oe() -> Letter:
    o, e = _o(), _e()
    body = geom.union([_scaled_path(o, 600 / 780, 1.0),
                       _scaled_path(e, 380 / 700, 1.0, 600, 0)])
    zones = {
        "wall_l": (25, 185, 98, 535),
        "wall_r": (502, 185, 575, 535),
        "etop": (625, 585, 955, 695),
        "emid": (720, 325, 920, 405),
        "ebot": (625, 25, 955, 135),
    }
    return _punct("\u0152", "OE", 1000, body.contours, zones, "O + E")


def _eth() -> Letter:
    d = _d()
    bar = _contour([(0, 320), (240, 320), (240, 440), (0, 440)])
    body = geom.union([d.body, geom.Path([bar])])
    return _punct("\u00d0", "Eth", d.adv, body.contours, d.zones,
                  "D + bar")


def _thorn() -> Letter:
    p = _p()
    stem = _rect(0, -120, 160, 0)
    body = geom.union([p.body, geom.Path([stem])])
    return _punct("\u00de", "Thorn", p.adv, body.contours, p.zones,
                  "P + descender")


def _ostroke() -> Letter:
    o = _o()
    slash = _contour([(0, 70), (90, 0), (780, 650), (690, 720)],
                     {1: 10, 2: 14, 3: 10})
    body = geom.union([o.body, geom.Path([slash])])
    zones = {
        "wall_l": (25, 250, 135, 535),
        "wall_r": (645, 185, 735, 440),
        "top": (185, 585, 540, 695),
        "bot": (300, 25, 690, 135),
    }
    return _punct("\u00d8", "Oslash", o.adv, body.contours, zones, "O + slash")


def _euro() -> Letter:
    c = _c()
    shifted = geom.Path([cont.transformed(1, 1, 60, 0)
                         for cont in c.body.contours])
    bar1 = _rect(0, 430, 560, 490, {1: 8, 2: 8})
    bar2 = _rect(0, 290, 560, 350, {1: 8, 2: 8})
    body = _merge(*shifted.contours, bar1, bar2)
    zones = {
        "top": (245, 585, 795, 695),
        "stem": (85, 185, 195, 535),
        "bot": (245, 25, 795, 135),
    }
    return _punct("\u20ac", "Euro", 860, body, zones, "C + bars")


def _sterling() -> Letter:
    stem = _rect(0, 0, 160, 720)
    foot = _rect(0, 0, 720, 160, {0: 18, 1: 20})
    top = _contour([(0, 560), (320, 560), (420, 720), (0, 720)],
                   {2: 14, 3: 10})
    bar = _rect(0, 300, 520, 400, {1: 8, 2: 8})
    body = _merge(stem, foot, top, bar)
    zones = {
        "top": (25, 585, 300, 695),
        "stem": (25, 425, 135, 535),
        "bar": (185, 325, 495, 375),
        "bot": (185, 25, 695, 135),
    }
    return _punct("\u00a3", "Sterling", 800, body, zones, "L + sloped top")


def _yen() -> Letter:
    y = _y()
    bar1 = _rect(200, 300, 620, 360, {0: 8, 1: 8})
    bar2 = _rect(200, 440, 620, 500, {0: 8, 1: 8})
    body = _merge(*y.contours, bar1, bar2)
    return _punct("\u00a5", "Yen", y.adv, body, y.zones, "Y + bars")


def _cent() -> Letter:
    c = _c()
    bar = _rect(330, 60, 430, 660, {2: 8, 3: 8})
    body = _merge(*c.contours, bar)
    return _punct("\u00a2", "Cent", c.adv, body, c.zones, "C + bar")


# --------------------------------------------------------------------------- #
# Typographic marks
# --------------------------------------------------------------------------- #
def _ellipsis() -> Letter:
    dots = [_rect(120 + i * 280, 0, 300 + i * 280, 200,
                  {0: 16, 1: 16, 2: 14, 3: 14}) for i in range(3)]
    zones = {
        "dot1": (145, 25, 275, 175),
        "dot2": (425, 25, 555, 175),
        "dot3": (705, 25, 835, 175),
    }
    return _punct("\u2026", "ellipsis", 1000, _merge(*dots), zones, "three dots")


def _bullet() -> Letter:
    body = _merge(_contour([(240, 260), (360, 380), (240, 500), (120, 380)],
                           {0: 16, 1: 16, 2: 16, 3: 16}))
    zones = {"core": (210, 350, 270, 410)}
    return _punct("\u2022", "bullet", 420, body, zones, "diamond")


def _degree() -> Letter:
    outer = geom.ellipse(210, 620, 90, 90)
    inner = geom.ellipse(210, 620, 55, 55).reversed()
    zones = {"core": ((189, 599, 231, 641), "yellow")}
    return _punct("\u00b0", "degree", 420, [outer, inner], zones, "ring")


def _plusminus() -> Letter:
    v = _rect(220, 220, 340, 620)
    h = _rect(20, 360, 540, 480)
    bar = _rect(20, 100, 540, 180)
    zones = {
        "v_top": (245, 505, 315, 595),
        "h_left": (45, 385, 195, 455),
        "h_right": (365, 385, 515, 455),
    }
    return _punct("\u00b1", "plusminus", 560, _merge(v, h, bar), zones, "plus + bar")


def _multiply() -> Letter:
    x = _x()
    body = _scaled_path(x, 0.72, 0.72, 6.4, 100.8)
    zones = {"core": (260, 342, 310, 392)}
    return _punct("\u00d7", "multiply", 560, body.contours, zones, "X form")


def _divide() -> Letter:
    top = _rect(200, 470, 360, 630, {0: 16, 1: 16, 2: 16, 3: 16})
    bar = _rect(20, 330, 540, 390)
    bot = _rect(200, 90, 360, 250, {0: 16, 1: 16, 2: 16, 3: 16})
    zones = {
        "dot_top": (225, 495, 335, 605),
        "dot_bot": (225, 115, 335, 225),
    }
    return _punct("\u00f7", "divide", 560, _merge(top, bar, bot), zones, "bar + dots")


def _copyright() -> Letter:
    outer = geom.rounded_rect(0, 0, 520, 720, 110)
    hole = geom.rounded_rect(140, 140, 380, 580, 0).reversed()
    c = _c()
    island = _scaled_path(c, 0.263, 0.278, 160, 260)
    body = [outer, hole] + island.contours
    zones = {
        "top": (145, 605, 375, 695),
        "bot": (145, 25, 375, 115),
        "wall_l": (25, 185, 95, 535),
        "wall_r": (425, 185, 495, 535),
    }
    return _punct("\u00a9", "copyright", 560, body, zones, "ring + C")


def _registered() -> Letter:
    outer = geom.rounded_rect(0, 0, 520, 720, 110)
    hole = geom.rounded_rect(140, 140, 380, 580, 0).reversed()
    r = _r()
    island = _scaled_path(r, 0.263, 0.278, 160, 260)
    body = [outer, hole] + island.contours
    zones = {
        "top": (145, 605, 375, 695),
        "bot": (145, 25, 375, 115),
        "wall_l": (25, 185, 95, 535),
        "wall_r": (425, 185, 495, 535),
    }
    return _punct("\u00ae", "registered", 560, body, zones, "ring + R")


def _trademark() -> Letter:
    t, m = _t(), _m()
    body = geom.union([_scaled_path(t, 0.6, 0.6, 0, 288),
                       _scaled_path(m, 0.4, 0.6, 456, 288)])
    zones = {"core": (200, 320, 256, 680)}
    return _punct("\u2122", "trademark", 900, body.contours, zones, "T + M")


def _single_quote(char, name, flip=False) -> Letter:
    head = _rect(170, 580, 310, 720, {2: 14, 3: 14})
    if not flip:
        tail = _contour([(170, 580), (250, 580), (210, 500), (130, 500)],
                        {2: 12, 3: 12})
    else:
        tail = _contour([(230, 580), (310, 580), (330, 500), (250, 500)],
                        {2: 12, 3: 12})
    zones = {"head": (195, 605, 285, 695)}
    return _punct(char, name, 400, _merge(head, tail), zones, "curly quote")


def _double_quote(char, name, flip=False) -> Letter:
    h1 = _rect(100, 580, 220, 720, {2: 14, 3: 14})
    h2 = _rect(320, 580, 440, 720, {2: 14, 3: 14})
    if not flip:
        t1 = _contour([(100, 580), (180, 580), (140, 500), (60, 500)],
                      {2: 12, 3: 12})
        t2 = _contour([(320, 580), (400, 580), (360, 500), (280, 500)],
                      {2: 12, 3: 12})
    else:
        t1 = _contour([(140, 580), (220, 580), (260, 500), (180, 500)],
                      {2: 12, 3: 12})
        t2 = _contour([(360, 580), (440, 580), (480, 500), (400, 500)],
                      {2: 12, 3: 12})
    zones = {"head1": (125, 605, 195, 695), "head2": (345, 605, 415, 695)}
    return _punct(char, name, 540, _merge(h1, h2, t1, t2), zones, "curly double")


def _quoteleft() -> Letter:
    return _single_quote("\u2018", "quoteleft", flip=True)


def _quoteright() -> Letter:
    return _single_quote("\u2019", "quoteright")


def _quotedblleft() -> Letter:
    return _double_quote("\u201c", "quotedblleft", flip=True)


def _quotedblright() -> Letter:
    return _double_quote("\u201d", "quotedblright")



# --------------------------------------------------------------------------- #
_LETTERS = {
    "T": _t, "O": _o, "E": _e, "M": _m,
    "A": _a, "B": _b, "C": _c, "D": _d,
    "F": _f, "G": _g, "H": _h, "I": _i, "J": _j,
    "K": _k, "L": _l, "N": _n, "P": _p, "Q": _q, "R": _r,
    "S": _s, "U": _u, "V": _v, "W": _w, "X": _x, "Y": _y, "Z": _z,
}

_DIGITS = {
    "0": _zero, "1": _one, "2": _two, "3": _three, "4": _four,
    "5": _five, "6": _six, "7": _seven, "8": _eight, "9": _nine,
}

_PUNCT = {
    ".": _period, ",": _comma, ":": _colon, ";": _semicolon,
    "!": _exclam, "?": _question, "'": _quotesingle, '"': _quotedbl,
    "-": _hyphen, "\u2013": _endash, "\u2014": _emdash,
    "(": _parenleft, ")": _parenright,
    "[": _bracketleft, "]": _bracketright,
    "/": _slash, "\\": _backslash, "#": _numbersign,
    "+": _plus, "=": _equal, "_": _underscore, "|": _bar,
    "&": _ampersand, "@": _at, "$": _dollar, "%": _percent,
    "*": _asterisk, "<": _less, ">": _greater, "^": _asciicircum,
    "~": _asciitilde, "`": _grave, "{": _braceleft, "}": _braceright,
}

# --------------------------------------------------------------------------- #
# Uppercase accents and Latin-1 letterforms
# --------------------------------------------------------------------------- #
def _accent_mark(kind, cx):
    if kind == "acute":
        return [_contour([(cx - 75, 738), (cx + 5, 738),
                          (cx + 65, 792), (cx - 15, 792)])]
    if kind == "grave":
        return [_contour([(cx - 5, 738), (cx + 75, 738),
                          (cx + 15, 792), (cx - 65, 792)])]
    if kind == "circumflex":
        return [_contour([(cx - 80, 738), (cx, 792), (cx + 80, 738),
                          (cx + 40, 738), (cx, 772), (cx - 40, 738)])]
    if kind == "tilde":
        return geom.stroke_path(
            [[(cx - 85, 752), (cx - 30, 780), (cx + 30, 752), (cx + 85, 780)]],
            width=30).contours
    if kind == "dieresis":
        return [_rect(cx - 65, 745, cx - 25, 785, {2: 10, 3: 10}),
                _rect(cx + 25, 745, cx + 65, 785, {2: 10, 3: 10})]
    if kind == "ring":
        return [geom.ellipse(cx, 766, 46, 30),
                geom.ellipse(cx, 766, 24, 14).reversed()]
    if kind == "cedilla":
        return geom.stroke_path(
            [[(cx + 15, 0), (cx + 15, -52), (cx - 28, -88)]],
            width=34).contours
    raise ValueError(kind)


def _make_accented(char, base_char, mark, name):
    def build():
        base = _LETTERS[base_char]()
        b = base.body.bounds()
        cx = (b[0] + b[2]) / 2.0
        contours = list(base.contours) + _accent_mark(mark, cx)
        return Letter(char, base.adv, contours, base.zones, base.art,
                      f"{base.label} + {mark}", name)
    return build


_ACCENTS = {
    "À": _make_accented("À", "A", "grave", "Agrave"),
    "Á": _make_accented("Á", "A", "acute", "Aacute"),
    "Â": _make_accented("Â", "A", "circumflex", "Acircumflex"),
    "Ã": _make_accented("Ã", "A", "tilde", "Atilde"),
    "Ä": _make_accented("Ä", "A", "dieresis", "Adieresis"),
    "Å": _make_accented("Å", "A", "ring", "Aring"),
    "Ç": _make_accented("Ç", "C", "cedilla", "Ccedilla"),
    "È": _make_accented("È", "E", "grave", "Egrave"),
    "É": _make_accented("É", "E", "acute", "Eacute"),
    "Ê": _make_accented("Ê", "E", "circumflex", "Ecircumflex"),
    "Ë": _make_accented("Ë", "E", "dieresis", "Edieresis"),
    "Ì": _make_accented("Ì", "I", "grave", "Igrave"),
    "Í": _make_accented("Í", "I", "acute", "Iacute"),
    "Î": _make_accented("Î", "I", "circumflex", "Icircumflex"),
    "Ï": _make_accented("Ï", "I", "dieresis", "Idieresis"),
    "Ñ": _make_accented("Ñ", "N", "tilde", "Ntilde"),
    "Ò": _make_accented("Ò", "O", "grave", "Ograve"),
    "Ó": _make_accented("Ó", "O", "acute", "Oacute"),
    "Ô": _make_accented("Ô", "O", "circumflex", "Ocircumflex"),
    "Õ": _make_accented("Õ", "O", "tilde", "Otilde"),
    "Ö": _make_accented("Ö", "O", "dieresis", "Odieresis"),
    "Ù": _make_accented("Ù", "U", "grave", "Ugrave"),
    "Ú": _make_accented("Ú", "U", "acute", "Uacute"),
    "Û": _make_accented("Û", "U", "circumflex", "Ucircumflex"),
    "Ü": _make_accented("Ü", "U", "dieresis", "Udieresis"),
    "Ý": _make_accented("Ý", "Y", "acute", "Yacute"),
    "Ÿ": _make_accented("Ÿ", "Y", "dieresis", "Ydieresis"),
    "Æ": _ae, "Œ": _oe, "Ð": _eth,
    "Þ": _thorn, "Ø": _ostroke,
}

_SYMBOLS = {
    "€": _euro, "£": _sterling, "¥": _yen, "¢": _cent,
    "…": _ellipsis, "•": _bullet, "°": _degree,
    "±": _plusminus, "×": _multiply, "÷": _divide,
    "©": _copyright, "®": _registered, "™": _trademark,
    "‘": _quoteleft, "’": _quoteright,
    "“": _quotedblleft, "”": _quotedblright,
}

_ALL = {**_LETTERS, **_ACCENTS, **_DIGITS, **_PUNCT, **_SYMBOLS}

# The four hand-tuned proof-of-concept glyphs.
POC_CHARS = ["T", "O", "E", "M"]

LETTER_CHARS = sorted(_LETTERS)
ACCENT_CHARS = sorted(_ACCENTS)
DIGIT_CHARS = sorted(_DIGITS)
PUNCT_CHARS = sorted(_PUNCT)
SYMBOL_CHARS = sorted(_SYMBOLS)

# All-caps face: lowercase codepoints map to the capital glyphs.
LOWERCASE_MAP = {chr(ord("a") + i): chr(ord("A") + i) for i in range(26)}
LOWERCASE_MAP.update({
    "\u00e0": "\u00c0", "\u00e1": "\u00c1", "\u00e2": "\u00c2",
    "\u00e3": "\u00c3", "\u00e4": "\u00c4", "\u00e5": "\u00c5",
    "\u00e6": "\u00c6", "\u00e7": "\u00c7", "\u00e8": "\u00c8",
    "\u00e9": "\u00c9", "\u00ea": "\u00ca", "\u00eb": "\u00cb",
    "\u00ec": "\u00cc", "\u00ed": "\u00cd", "\u00ee": "\u00ce",
    "\u00ef": "\u00cf", "\u00f0": "\u00d0", "\u00f1": "\u00d1",
    "\u00f2": "\u00d2", "\u00f3": "\u00d3", "\u00f4": "\u00d4",
    "\u00f5": "\u00d5", "\u00f6": "\u00d6", "\u00f8": "\u00d8",
    "\u00f9": "\u00d9", "\u00fa": "\u00da", "\u00fb": "\u00db",
    "\u00fc": "\u00dc", "\u00fd": "\u00dd", "\u00fe": "\u00de",
    "\u00ff": "\u0178", "\u0153": "\u0152", "\u00df": "S",
})

# Everything currently built.
CHARS = (LETTER_CHARS + ACCENT_CHARS + DIGIT_CHARS +
         PUNCT_CHARS + SYMBOL_CHARS)


def all_letters() -> dict:
    return {ch: _ALL[ch]() for ch in CHARS}
