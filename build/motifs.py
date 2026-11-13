"""Motif library for Tribal Totem Display.

Every motif receives a box (x0, y0, x1, y1) that is already inset from the
letter body by the required yellow margin plus half the art stroke. Motifs
return (strokes, solids):

    strokes : list of polylines (closed when first point == last point)
    solids  : list of geom.Contour filled with the art colour

All coordinates are font units, y up.
"""
from __future__ import annotations

import math

import geom

TAU = math.tau


def _arc(cx, cy, rx, ry, a0, a1, n=6):
    return [
        (cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
         cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
        for i in range(n + 1)
    ]


# --------------------------------------------------------------------------- #
# Linear motifs
# --------------------------------------------------------------------------- #
def zigzag(box, n=6, vertical=False):
    x0, y0, x1, y1 = box
    pts = []
    for i in range(n + 1):
        t = i / n
        if vertical:
            pts.append((x0 if i % 2 == 0 else x1, y0 + t * (y1 - y0)))
        else:
            pts.append((x0 + t * (x1 - x0), y0 if i % 2 == 0 else y1))
    return [pts], []


def greek_key(box, vertical=False):
    x0, y0, x1, y1 = box
    if vertical:
        length, width = y1 - y0, x1 - x0
    else:
        length, width = x1 - x0, y1 - y0
    u = width / 3.0
    key = [(0, 0), (3, 0), (3, 3), (1, 3), (1, 1), (2, 1), (2, 2)]
    reps = max(1, int(length // (3.3 * u)))
    total = reps * 3.3 * u
    off = (length - total) / 2.0
    pts = []
    for r in range(reps):
        ox = off + r * 3.3 * u
        for kx, ky in key:
            pl = ox + kx * u
            pw = ky * u + (width - 3 * u) / 2.0
            pts.append((x0 + pw, y0 + pl) if vertical else (x0 + pl, y0 + pw))
    return [pts], []


def chevrons(box, n=4, vertical=False):
    x0, y0, x1, y1 = box
    out = []
    if vertical:
        xm = (x0 + x1) / 2.0
        amp = (x1 - x0) * 0.30
        step = (y1 - y0) / n
        for k in range(n):
            y = y0 + (k + 0.5) * step
            out.append([(x0, y), (xm + amp, y - step * 0.50), (x1, y)])
    else:
        ym = (y0 + y1) / 2.0
        amp = (y1 - y0) * 0.30
        step = (x1 - x0) / n
        for k in range(n):
            x = x0 + (k + 0.5) * step
            out.append([(x, y0), (x + step * 0.35, ym + amp), (x, y1)])
    return out, []


def hatch(box, n=6, vertical=False):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    out = []
    if vertical:
        slope = -1.0
        c_lo, c_hi = y0 - x1, y1 - x0
        step = (c_hi - c_lo) / (n + 1)
        for k in range(1, n + 1):
            c = c_lo + k * step
            xa = max(x0, y0 - c)
            xb = min(x1, y1 - c)
            if xb - xa > 1:
                out.append([(xa, xa + c), (xb, xb + c)])
    else:
        slope = 1.0
        c_lo, c_hi = y0 - x1, y1 - x0
        step = (c_hi - c_lo) / (n + 1)
        for k in range(1, n + 1):
            c = c_lo + k * step
            xa = max(x0, y0 - c)
            xb = min(x1, y1 - c)
            if xb - xa > 1:
                out.append([(xa, xa + c), (xb, xb + c)])
    return out, []


def diamonds(box, n=3, vertical=True):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    out = []
    if vertical:
        rx = w * 0.34
        step = h / n
        ry = step * 0.34
        cx = (x0 + x1) / 2.0
        for k in range(n):
            cy = y0 + (k + 0.5) * step
            out.append([(cx, cy + ry), (cx + rx, cy), (cx, cy - ry),
                        (cx - rx, cy), (cx, cy + ry)])
    else:
        ry = h * 0.34
        step = w / n
        rx = step * 0.34
        cy = (y0 + y1) / 2.0
        for k in range(n):
            cx = x0 + (k + 0.5) * step
            out.append([(cx, cy + ry), (cx + rx, cy), (cx, cy - ry),
                        (cx - rx, cy), (cx, cy + ry)])
    return out, []


def dots(box, n=4, vertical=True):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    solids = []
    if vertical:
        step = h / n
        r = min(w * 0.34, step * 0.30)
        cx = (x0 + x1) / 2.0
        for k in range(n):
            solids.append(geom.ellipse(cx, y0 + (k + 0.5) * step, r, r))
    else:
        step = w / n
        r = min(h * 0.34, step * 0.30)
        cy = (y0 + y1) / 2.0
        for k in range(n):
            solids.append(geom.ellipse(x0 + (k + 0.5) * step, cy, r, r))
    return [], solids


def star(box):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    R = min(x1 - x0, y1 - y0) / 2.0
    r = R * 0.42
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pts.append(pts[0])
    return [pts], []


# --------------------------------------------------------------------------- #
# Figurative motifs
# --------------------------------------------------------------------------- #
def spear(box, vertical=True):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    strokes = []
    solids = []
    if vertical:
        cx = (x0 + x1) / 2.0
        strokes.append([(cx, y0 + 0.02 * h), (cx, y1 - 0.20 * h)])
        solids.append(geom.poly([
            (cx, y1), (cx - 0.20 * w, y1 - 0.13 * h),
            (cx, y1 - 0.26 * h), (cx + 0.20 * w, y1 - 0.13 * h)]))
        for k in range(1, 4):
            yy = y0 + 0.13 * h * k
            strokes.append([(cx - 0.34 * w, yy + 0.08 * h), (cx, yy)])
            strokes.append([(cx + 0.34 * w, yy + 0.08 * h), (cx, yy)])
    else:
        cy = (y0 + y1) / 2.0
        strokes.append([(x0 + 0.02 * w, cy), (x1 - 0.20 * w, cy)])
        solids.append(geom.poly([
            (x1, cy), (x1 - 0.10 * w, cy - 0.22 * h),
            (x1 - 0.20 * w, cy), (x1 - 0.10 * w, cy + 0.22 * h)]))
        for k in range(1, 4):
            xx = x0 + 0.13 * w * k
            strokes.append([(xx + 0.08 * w, cy - 0.30 * h), (xx, cy)])
            strokes.append([(xx + 0.08 * w, cy + 0.30 * h), (xx, cy)])
    return strokes, solids


def mask(box):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    w, h = x1 - x0, y1 - y0
    rx, ry = w * 0.42, h * 0.44
    strokes = []
    solids = []
    # face outline
    strokes.append(_arc(cx, cy, rx, ry, 90, 450, 24))
    # brow band
    strokes.append([(cx - 0.30 * w, cy + 0.17 * h), (cx + 0.30 * w, cy + 0.17 * h)])
    # almond eyes (solid)
    for sx in (-1, 1):
        ex = cx + sx * 0.17 * w
        ey = cy + 0.04 * h
        solids.append(geom.poly([(ex, ey + 0.055 * h), (ex + 0.06 * w, ey),
                                 (ex, ey - 0.055 * h), (ex - 0.06 * w, ey)]))
    # nose: vertical line with a base tick
    strokes.append([(cx, cy + 0.10 * h), (cx, cy - 0.12 * h)])
    strokes.append([(cx - 0.05 * w, cy - 0.12 * h), (cx + 0.05 * w, cy - 0.12 * h)])
    # mouth: straight bar plus teeth ticks
    my = cy - 0.26 * h
    strokes.append([(cx - 0.20 * w, my), (cx + 0.20 * w, my)])
    for i in (-1, 0, 1):
        tx = cx + i * 0.10 * w
        strokes.append([(tx, my), (tx, my + 0.045 * h)])
    # forehead diamond
    d = min(w, h) * 0.05
    solids.append(geom.poly([
        (cx, cy + 0.30 * h + d), (cx + d, cy + 0.30 * h),
        (cx, cy + 0.30 * h - d), (cx - d, cy + 0.30 * h)]))
    return strokes, solids


def sun(box):
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    R = min(x1 - x0, y1 - y0) / 2.0
    r = R * 0.52
    strokes = [_arc(cx, cy, r, r, 0, 360, 32)]
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        strokes.append([(cx + math.cos(a) * r * 1.22, cy + math.sin(a) * r * 1.22),
                        (cx + math.cos(a) * r * 1.75, cy + math.sin(a) * r * 1.75)])
    solids = [geom.ellipse(cx, cy, r * 0.16, r * 0.16)]
    return strokes, solids


def maraca(box):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2.0
    w, h = x1 - x0, y1 - y0
    head_cy = y0 + h * 0.66
    rx, ry = w * 0.40, h * 0.27
    strokes = [
        _arc(cx, head_cy, rx, ry, 90, 450, 24),
        [(cx, head_cy - ry), (cx, y0 + 0.02 * h)],
    ]
    # two curved stripes across the head
    for k in (-1, 1):
        strokes.append([
            (cx + k * rx * 0.92, head_cy + ry * 0.30),
            (cx + k * rx * 0.34, head_cy + ry * 0.62),
            (cx + k * rx * 0.34, head_cy - ry * 0.62),
            (cx + k * rx * 0.92, head_cy - ry * 0.30),
        ])
    # seed dots on the head
    solids = [geom.ellipse(cx, head_cy, rx * 0.10, ry * 0.13)]
    for sx in (-1, 1):
        solids.append(geom.ellipse(cx + sx * rx * 0.42, head_cy + ry * 0.20,
                                   rx * 0.055, rx * 0.055))
    return strokes, solids


def shield(box):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2.0
    h = y1 - y0
    outline = [
        (x0, y1), (x1, y1),
        (x1, y0 + 0.38 * h),
        (cx, y0),
        (x0, y0 + 0.38 * h),
        (x0, y1),
    ]
    strokes = [outline, [(cx, y1 - 0.02 * h), (cx, y0 + 0.22 * h)]]
    for k in (0.42, 0.60):
        yy = y0 + k * h
        strokes.append([(x0 + 0.18 * (x1 - x0), yy), (cx, yy - 0.09 * h)])
        strokes.append([(x1 - 0.18 * (x1 - x0), yy), (cx, yy - 0.09 * h)])
    return strokes, []


def drum(box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    body = geom.rounded_rect(x0, y0, x1, y1, min(w, h) * 0.18)
    strokes = [body.sampled(10)]
    for k in (0.22, 0.78):
        yy = y0 + k * h
        strokes.append([(x0 + 0.06 * w, yy), (x1 - 0.06 * w, yy)])
    # lacing
    n = 4
    for i in range(n):
        t0 = i / n
        t1 = (i + 1) / n
        strokes.append([(x0 + (0.10 + 0.80 * t0) * w, y0 + 0.24 * h),
                        (x0 + (0.10 + 0.80 * t1) * w, y0 + 0.76 * h)])
        strokes.append([(x0 + (0.10 + 0.80 * t1) * w, y0 + 0.24 * h),
                        (x0 + (0.10 + 0.80 * t0) * w, y0 + 0.76 * h)])
    return strokes, []


MOTIFS = {
    "zigzag": zigzag,
    "greek_key": greek_key,
    "chevrons": chevrons,
    "hatch": hatch,
    "diamonds": diamonds,
    "dots": dots,
    "star": star,
    "spear": spear,
    "mask": mask,
    "sun": sun,
    "maraca": maraca,
    "shield": shield,
    "drum": drum,
}
