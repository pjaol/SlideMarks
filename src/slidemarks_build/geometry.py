"""Path primitives in font units (y-up). All glyph shapes are filled outlines;
strokes are expanded here so the font never depends on stroke rendering."""

import math

import pathops

KAPPA = 0.5522847498  # cubic approximation of a quarter circle


def circle(cx: float, cy: float, r: float) -> pathops.Path:
    k = r * KAPPA
    p = pathops.Path()
    p.moveTo(cx, cy + r)
    p.cubicTo(cx + k, cy + r, cx + r, cy + k, cx + r, cy)
    p.cubicTo(cx + r, cy - k, cx + k, cy - r, cx, cy - r)
    p.cubicTo(cx - k, cy - r, cx - r, cy - k, cx - r, cy)
    p.cubicTo(cx - r, cy + k, cx - k, cy + r, cx, cy + r)
    p.close()
    return p


def ring(cx: float, cy: float, r_outer: float, width: float) -> pathops.Path:
    return pathops.op(circle(cx, cy, r_outer), circle(cx, cy, r_outer - width), pathops.PathOp.DIFFERENCE)


def _clock_point(cx, cy, r, theta):
    """theta in radians, 0 at twelve o'clock, increasing clockwise."""
    return cx + r * math.sin(theta), cy + r * math.cos(theta)


def wedge(cx: float, cy: float, r: float, fraction: float) -> pathops.Path:
    """Filled sector starting at twelve o'clock, sweeping clockwise."""
    if fraction >= 1.0:
        return circle(cx, cy, r)
    sweep = 2 * math.pi * fraction
    segments = max(1, math.ceil(sweep / (math.pi / 2)))
    step = sweep / segments
    # Control-point distance for a circular arc of angle `step`
    h = 4 / 3 * math.tan(step / 4) * r
    p = pathops.Path()
    p.moveTo(cx, cy)
    x0, y0 = _clock_point(cx, cy, r, 0)
    p.lineTo(x0, y0)
    for i in range(segments):
        a0, a1 = i * step, (i + 1) * step
        x1, y1 = _clock_point(cx, cy, r, a1)
        # Tangent direction for clockwise travel: (cos a, -sin a)
        c0 = (x0 + h * math.cos(a0), y0 - h * math.sin(a0))
        c1 = (x1 - h * math.cos(a1), y1 + h * math.sin(a1))
        p.cubicTo(*c0, *c1, x1, y1)
        x0, y0 = x1, y1
    p.close()
    return p


def stroked_polyline(points, width: float) -> pathops.Path:
    """Open polyline with round caps and joins, expanded to a filled outline."""
    p = pathops.Path()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    p.stroke(width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    p.convertConicsToQuads()  # Skia emits conics for round caps; fonts need quads/cubics
    return p


def union(*paths: pathops.Path) -> pathops.Path:
    result = paths[0]
    for p in paths[1:]:
        result = pathops.op(result, p, pathops.PathOp.UNION)
    return result


def rotate(path: pathops.Path, degrees: float, cx: float, cy: float) -> pathops.Path:
    """Counter-clockwise rotation about (cx, cy)."""
    t = math.radians(degrees)
    c, s = math.cos(t), math.sin(t)
    return path.transform(c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy)


def mirror_y(path: pathops.Path, cy: float) -> pathops.Path:
    return path.transform(1, 0, 0, -1, 0, 2 * cy)


def normalize(path: pathops.Path) -> pathops.Path:
    """Remove overlaps and orient contours clockwise (TrueType convention)."""
    return pathops.simplify(path, clockwise=True)


class Sketch:
    """Centerline builder for lines and circular arcs, stroked later.
    Arc angles are in degrees, math convention (0 = east, counter-clockwise positive)."""

    def __init__(self):
        self.path = pathops.Path()
        self._open = False
        self._closed = False

    def move(self, x, y):
        self.path.moveTo(x, y)
        self._open = True
        return self

    def line(self, x, y):
        self.path.lineTo(x, y)
        return self

    def arc(self, cx, cy, r, start_deg, end_deg):
        """Arc from start to end angle; sweeps clockwise when end < start."""
        a0, a1 = math.radians(start_deg), math.radians(end_deg)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        if self._open:
            self.path.lineTo(x0, y0)
        else:
            self.move(x0, y0)
        sweep = a1 - a0
        segments = max(1, math.ceil(abs(sweep) / (math.pi / 2)))
        step = sweep / segments
        h = 4 / 3 * math.tan(step / 4) * r
        for i in range(segments):
            s, e = a0 + i * step, a0 + (i + 1) * step
            x1, y1 = cx + r * math.cos(e), cy + r * math.sin(e)
            self.path.cubicTo(x0 - h * math.sin(s), y0 + h * math.cos(s),
                              x1 + h * math.sin(e), y1 - h * math.cos(e), x1, y1)
            x0, y0 = x1, y1
        return self

    def curve(self, c1x, c1y, c2x, c2y, x, y):
        self.path.cubicTo(c1x, c1y, c2x, c2y, x, y)
        return self

    def close(self):
        self.path.close()
        self._closed = True
        return self

    def stroke(self, width: float, round_join: bool = True) -> pathops.Path:
        p = pathops.Path()
        self.path.draw(p.getPen())
        join = pathops.LineJoin.ROUND_JOIN if round_join else pathops.LineJoin.MITER_JOIN
        p.stroke(width, pathops.LineCap.ROUND_CAP, join, 10)
        p.convertConicsToQuads()
        return p

    def fill(self) -> pathops.Path:
        p = pathops.Path()
        self.path.draw(p.getPen())
        return p


def polygon(points) -> pathops.Path:
    p = pathops.Path()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    p.close()
    return p


def polygon_outline(points, width: float, round_join: bool = True) -> pathops.Path:
    """Closed polygon stroked inward so the outer ink edge stays on `points`."""
    outer = polygon(points)
    stroked = Sketch()
    stroked.move(*points[0])
    for pt in points[1:]:
        stroked.line(*pt)
    stroked.close()
    band = stroked.stroke(width * 2, round_join)
    return pathops.op(outer, band, pathops.PathOp.INTERSECTION)


def rounded_rect(x0, y0, x1, y1, r) -> pathops.Path:
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    if r <= 0:
        return polygon([(x0, y0), (x0, y1), (x1, y1), (x1, y0)])
    k = r * KAPPA
    p = pathops.Path()
    p.moveTo(x0 + r, y1)
    p.lineTo(x1 - r, y1)
    p.cubicTo(x1 - r + k, y1, x1, y1 - r + k, x1, y1 - r)
    p.lineTo(x1, y0 + r)
    p.cubicTo(x1, y0 + r - k, x1 - r + k, y0, x1 - r, y0)
    p.lineTo(x0 + r, y0)
    p.cubicTo(x0 + r - k, y0, x0, y0 + r - k, x0, y0 + r)
    p.lineTo(x0, y1 - r)
    p.cubicTo(x0, y1 - r + k, x0 + r - k, y1, x0 + r, y1)
    p.close()
    return p


def rounded_rect_outline(x0, y0, x1, y1, r, width) -> pathops.Path:
    inner = rounded_rect(x0 + width, y0 + width, x1 - width, y1 - width, max(0, r - width))
    return difference(rounded_rect(x0, y0, x1, y1, r), inner)


def ellipse(cx, cy, rx, ry) -> pathops.Path:
    return circle(0, 0, 1).transform(rx, 0, 0, ry, cx, cy)


def difference(a: pathops.Path, b: pathops.Path) -> pathops.Path:
    return pathops.op(a, b, pathops.PathOp.DIFFERENCE)


def intersection(a: pathops.Path, b: pathops.Path) -> pathops.Path:
    return pathops.op(a, b, pathops.PathOp.INTERSECTION)


def translate(path: pathops.Path, dx: float, dy: float) -> pathops.Path:
    return path.transform(1, 0, 0, 1, dx, dy)


def scale(path: pathops.Path, s: float, cx: float, cy: float) -> pathops.Path:
    return path.transform(s, 0, 0, s, cx - s * cx, cy - s * cy)


def mirror_x(path: pathops.Path, cx: float) -> pathops.Path:
    return path.transform(-1, 0, 0, 1, 2 * cx, 0)


def center_ink(path: pathops.Path, cx: float, cy: float) -> pathops.Path:
    """Translate so the ink bounding box is centered on (cx, cy)."""
    x0, y0, x1, y1 = path.bounds
    return translate(path, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2)


def scale_points(points, s: float, cx: float, cy: float):
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in points]
