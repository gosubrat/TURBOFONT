"""Geometry primitives for the Tribal Totem Display font build.

Coordinate system: font units, y up, baseline at y=0, cap height 720.
All art is defined in this system and flipped to SVG's y-down system only at
export time.
"""
from __future__ import annotations

import math

K = 0.5522847498307936  # circle -> cubic bezier
ART_STROKE = 20.0


# --------------------------------------------------------------------------- #
# Contours and paths
# --------------------------------------------------------------------------- #
class Contour:
    """A single closed contour made of line ('L') and cubic ('C') segments."""

    __slots__ = ("cmds",)

    def __init__(self, cmds=None):
        self.cmds = list(cmds) if cmds else []

    # -- construction ------------------------------------------------------ #
    def move(self, x, y):
        self.cmds.append(("M", float(x), float(y)))
        return self

    def line(self, x, y):
        self.cmds.append(("L", float(x), float(y)))
        return self

    def curve(self, c1x, c1y, c2x, c2y, x, y):
        self.cmds.append(("C", float(c1x), float(c1y),
                          float(c2x), float(c2y), float(x), float(y)))
        return self

    def close(self):
        return self

    # -- inspection -------------------------------------------------------- #
    def sampled(self, steps=12):
        """Polyline approximation, used for bounds/area/distance checks."""
        pts = []
        cur = None
        start = None
        for cmd in self.cmds:
            if cmd[0] == "M":
                cur = (cmd[1], cmd[2])
                start = cur
                pts.append(cur)
            elif cmd[0] == "L":
                cur = (cmd[1], cmd[2])
                pts.append(cur)
            elif cmd[0] == "C":
                x1, y1, x2, y2, x3, y3 = cmd[1:]
                p0 = cur
                for i in range(1, steps + 1):
                    t = i / steps
                    mt = 1 - t
                    x = (mt ** 3) * p0[0] + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t ** 3 * x3
                    y = (mt ** 3) * p0[1] + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t ** 3 * y3
                    pts.append((x, y))
                cur = (x3, y3)
        return pts

    def signed_area(self):
        pts = self.sampled()
        a = 0.0
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            a += x0 * y1 - x1 * y0
        return a / 2.0

    def bounds(self):
        pts = self.sampled()
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def closed(self):
        return True

    # -- transforms -------------------------------------------------------- #
    def reversed(self):
        segs = []
        cur = None
        for cmd in self.cmds:
            if cmd[0] == "M":
                cur = (cmd[1], cmd[2])
            elif cmd[0] == "L":
                segs.append((cur, (cmd[1], cmd[2]), "L"))
                cur = (cmd[1], cmd[2])
            elif cmd[0] == "C":
                segs.append((cur, (cmd[5], cmd[6]), "C",
                             (cmd[1], cmd[2]), (cmd[3], cmd[4])))
                cur = (cmd[5], cmd[6])
        out = Contour()
        if not segs:
            return out
        out.move(*segs[-1][1])
        for seg in reversed(segs):
            p0 = seg[0]
            if seg[2] == "L":
                out.line(*p0)
            else:
                c1, c2 = seg[3], seg[4]
                out.curve(c2[0], c2[1], c1[0], c1[1], p0[0], p0[1])
        return out

    def translated(self, dx, dy):
        out = Contour()
        for cmd in self.cmds:
            if cmd[0] == "M":
                out.cmds.append(("M", cmd[1] + dx, cmd[2] + dy))
            elif cmd[0] == "L":
                out.cmds.append(("L", cmd[1] + dx, cmd[2] + dy))
            else:
                out.cmds.append(("C", cmd[1] + dx, cmd[2] + dy,
                                 cmd[3] + dx, cmd[4] + dy,
                                 cmd[5] + dx, cmd[6] + dy))
        return out

    def transformed(self, sx, sy, tx=0.0, ty=0.0):
        out = Contour()
        for cmd in self.cmds:
            if cmd[0] == "M":
                out.cmds.append(("M", cmd[1] * sx + tx, cmd[2] * sy + ty))
            elif cmd[0] == "L":
                out.cmds.append(("L", cmd[1] * sx + tx, cmd[2] * sy + ty))
            else:
                out.cmds.append(("C",
                                 cmd[1] * sx + tx, cmd[2] * sy + ty,
                                 cmd[3] * sx + tx, cmd[4] * sy + ty,
                                 cmd[5] * sx + tx, cmd[6] * sy + ty))
        return out

    # -- export ------------------------------------------------------------ #
    def to_svg(self, flip=True):
        def t(x, y):
            return x, (-y if flip else y)

        parts = []
        for cmd in self.cmds:
            if cmd[0] == "M":
                x, y = t(cmd[1], cmd[2])
                parts.append(f"M{x:g} {y:g}")
            elif cmd[0] == "L":
                x, y = t(cmd[1], cmd[2])
                parts.append(f"L{x:g} {y:g}")
            else:
                a = t(cmd[1], cmd[2])
                b = t(cmd[3], cmd[4])
                c = t(cmd[5], cmd[6])
                parts.append(f"C{a[0]:g} {a[1]:g} {b[0]:g} {b[1]:g} {c[0]:g} {c[1]:g}")
        parts.append("Z")
        return "".join(parts)


class Path:
    __slots__ = ("contours",)

    def __init__(self, contours=None):
        self.contours = list(contours) if contours else []

    def add(self, contour):
        self.contours.append(contour)
        return self

    def extend(self, other):
        self.contours.extend(other.contours)
        return self

    def bounds(self):
        if not self.contours:
            return (0, 0, 0, 0)
        bs = [c.bounds() for c in self.contours]
        return (min(b[0] for b in bs), min(b[1] for b in bs),
                max(b[2] for b in bs), max(b[3] for b in bs))

    def area(self):
        return sum(c.signed_area() for c in self.contours)

    def to_svg_d(self, flip=True):
        return "".join(c.to_svg(flip=flip) for c in self.contours)

    def draw(self, pen):
        for c in self.contours:
            cur = None
            for cmd in c.cmds:
                if cmd[0] == "M":
                    cur = (cmd[1], cmd[2])
                    pen.moveTo(cur)
                elif cmd[0] == "L":
                    cur = (cmd[1], cmd[2])
                    pen.lineTo(cur)
                else:
                    pen.curveTo((cmd[1], cmd[2]), (cmd[3], cmd[4]),
                                (cmd[5], cmd[6]))
                    cur = (cmd[5], cmd[6])
            pen.closePath()

    def orient(self, outer_ccw=True):
        """Force outers CCW and holes CW, decided by nesting depth.

        Alternating by contour index is not enough for letters such as B, D
        or P, whose bodies are unioned from blocks and can carry two holes.
        """
        polys = [c.sampled(steps=24) for c in self.contours]
        for i, c in enumerate(self.contours):
            probe = polys[i][0]
            depth = sum(1 for j, other in enumerate(polys)
                        if j != i and point_in_polygon(probe, other))
            want_ccw = outer_ccw if depth % 2 == 0 else (not outer_ccw)
            if (c.signed_area() > 0) != want_ccw:
                self.contours[i] = c.reversed()
        return self


# --------------------------------------------------------------------------- #
# Shape builders
# --------------------------------------------------------------------------- #
def poly(points):
    c = Contour().move(*points[0])
    for p in points[1:]:
        c.line(*p)
    return c


def ellipse(cx, cy, rx, ry):
    c = Contour()
    c.move(cx + rx, cy)
    c.curve(cx + rx, cy + K * ry, cx + K * rx, cy + ry, cx, cy + ry)
    c.curve(cx - K * rx, cy + ry, cx - rx, cy + K * ry, cx - rx, cy)
    c.curve(cx - rx, cy - K * ry, cx - K * rx, cy - ry, cx, cy - ry)
    c.curve(cx + K * rx, cy - ry, cx + rx, cy - K * ry, cx + rx, cy)
    return c


def rounded_rect(x0, y0, x1, y1, r):
    r = max(0.0, min(r, (x1 - x0) / 2.0, (y1 - y0) / 2.0))
    if r <= 0:
        return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    c = Contour()
    c.move(x0 + r, y0)
    c.line(x1 - r, y0)
    c.curve(x1 - r + K * r, y0, x1, y0 + r - K * r, x1, y0 + r)
    c.line(x1, y1 - r)
    c.curve(x1, y1 - r + K * r, x1 - r + K * r, y1, x1 - r, y1)
    c.line(x0 + r, y1)
    c.curve(x0 + r - K * r, y1, x0, y1 - r + K * r, x0, y1 - r)
    c.line(x0, y0 + r)
    c.curve(x0, y0 + r - K * r, x0 + r - K * r, y0, x0 + r, y0)
    return c


def _unit(vx, vy):
    d = math.hypot(vx, vy) or 1.0
    return vx / d, vy / d


def chamfer_polygon(points, cuts):
    """Replace corners with 45-degree-ish cuts of the given size (index -> size)."""
    n = len(points)
    out = []
    for i, p in enumerate(points):
        cut = cuts.get(i, 0.0)
        if cut <= 0:
            out.append(p)
            continue
        prev = points[(i - 1) % n]
        nxt = points[(i + 1) % n]
        v1 = _unit(prev[0] - p[0], prev[1] - p[1])
        v2 = _unit(nxt[0] - p[0], nxt[1] - p[1])
        c = min(cut, math.dist(prev, p) / 2.0, math.dist(nxt, p) / 2.0)
        out.append((p[0] + v1[0] * c, p[1] + v1[1] * c))
        out.append((p[0] + v2[0] * c, p[1] + v2[1] * c))
    return out


# --------------------------------------------------------------------------- #
# Stroke -> fill (for COLR layers) and distance checks
# --------------------------------------------------------------------------- #
class _CollectPen:
    def __init__(self):
        self.contours = []
        self._cur = None

    def moveTo(self, pt):
        self._cur = Contour().move(*pt)
        self.contours.append(self._cur)

    def lineTo(self, pt):
        self._cur.line(*pt)

    def curveTo(self, *pts):
        if len(pts) == 3:
            (c1x, c1y), (c2x, c2y), (x, y) = pts
            self._cur.curve(c1x, c1y, c2x, c2y, x, y)
        else:  # quadratic -> cubic
            (cx, cy), (x, y) = pts
            # caller should pass control + end; approximate
            raise NotImplementedError("quadratic pen not supported")

    def qCurveTo(self, *pts):
        pts = list(pts)
        end = pts[-1]
        ctrl = pts[-2]
        self._cur.curve(ctrl[0], ctrl[1], ctrl[0], ctrl[1], end[0], end[1])

    def closePath(self):
        pass

    def endPath(self):
        pass

    def addComponent(self, *a, **k):
        pass


def stroke_path(polylines, width=ART_STROKE, cap="round", join="round"):
    """Expand polylines into a Path with the requested cap/join style."""
    import pathops

    caps = {"round": pathops.LineCap.ROUND_CAP,
            "butt": pathops.LineCap.BUTT_CAP,
            "square": pathops.LineCap.SQUARE_CAP}
    joins = {"round": pathops.LineJoin.ROUND_JOIN,
             "miter": pathops.LineJoin.MITER_JOIN,
             "bevel": pathops.LineJoin.BEVEL_JOIN}

    p = pathops.Path()
    pen = p.getPen()
    for pts in polylines:
        if len(pts) < 2:
            continue
        pen.moveTo(pts[0])
        for q in pts[1:]:
            pen.lineTo(q)
        if math.dist(pts[0], pts[-1]) < 1e-6:
            pen.closePath()
    p.stroke(width, caps[cap], joins[join], 4.0)
    try:
        p.convertConicsToQuads()
    except Exception:
        pass
    pen = _CollectPen()
    p.draw(pen)
    return Path(pen.contours)


def strokes_to_fill(polylines, width=ART_STROKE):
    """Expand polylines into a filled outline using round caps and joins."""
    return stroke_path(polylines, width, cap="round", join="round")


def union(paths):
    import pathops

    if not paths:
        return Path()
    if len(paths) == 1:
        return paths[0]
    pss = []
    for path in paths:
        p = pathops.Path()
        path.draw(p.getPen())
        pss.append(p)
    out = pathops.Path()
    pathops.union(pss, out.getPen(), fix_winding=True)
    pen = _CollectPen()
    out.draw(pen)
    return Path(pen.contours)


def point_in_polygon(p, pts):
    """Even-odd ray cast. `pts` is a closed polyline (no repeated first point)."""
    x, y = p
    inside = False
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xin = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xin:
                inside = not inside
    return inside


def point_segment_distance(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.dist(p, a)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def distance_to_path(p, path):
    best = float("inf")
    for c in path.contours:
        pts = c.sampled(steps=24)
        for i in range(len(pts)):
            d = point_segment_distance(p, pts[i], pts[(i + 1) % len(pts)])
            if d < best:
                best = d
    return best
