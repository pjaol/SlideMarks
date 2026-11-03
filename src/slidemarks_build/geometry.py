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
