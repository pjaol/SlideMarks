"""Family builders. Each family derives every member from one construction,
driven only by design tokens, so members cannot drift apart."""

import math

import pathops

from . import geometry as g


def _stroke(t) -> float:
    return t["stroke"]["regular"]


def harvey(t, fraction: float) -> pathops.Path:
    cx, cy = t["center"]["x"], t["center"]["y"]
    r = t["harvey"]["diameter"] / 2
    w = _stroke(t)
    rim = g.ring(cx, cy, r, w)
    if fraction <= 0:
        return rim
    gap = t["harvey"]["wedgeGap"]
    wedge_r = r if gap == 0 else r - w - gap
    return g.union(rim, g.wedge(cx, cy, wedge_r, fraction))


def dot(t, filled: bool) -> pathops.Path:
    cx, cy = t["center"]["x"], t["center"]["y"]
    r = t["dot"]["diameter"] / 2
    return g.circle(cx, cy, r) if filled else g.ring(cx, cy, r, _stroke(t))


def check(t) -> pathops.Path:
    return g.stroked_polyline(t["check"]["points"], _stroke(t))


def cross(t) -> pathops.Path:
    cx, cy = t["center"]["x"], t["center"]["y"]
    s = t["cross"]["halfSpan"]
    w = _stroke(t)
    return g.union(
        g.stroked_polyline([(cx - s, cy - s), (cx + s, cy + s)], w),
        g.stroked_polyline([(cx - s, cy + s), (cx + s, cy - s)], w),
    )


def _arrow_head(tip, direction_rad, length, half_angle_rad):
    back = direction_rad + math.pi
    return [
        (tip[0] + length * math.cos(back + half_angle_rad), tip[1] + length * math.sin(back + half_angle_rad)),
        tip,
        (tip[0] + length * math.cos(back - half_angle_rad), tip[1] + length * math.sin(back - half_angle_rad)),
    ]


def arrow(t, rotateDeg: float) -> pathops.Path:
    """Canonical right-pointing arrow; other directions are exact rotations."""
    cx, cy = t["center"]["x"], t["center"]["y"]
    w = _stroke(t)
    a = t["arrow"]
    half = a["halfLength"] - w / 2  # token is ink extent; centerline is shorter by the cap
    tip = (cx + half, cy)
    shaft = g.stroked_polyline([(cx - half, cy), tip], w)
    head = g.stroked_polyline(_arrow_head(tip, 0.0, a["headLength"], math.radians(a["headAngleDeg"])), w)
    return g.rotate(g.union(shaft, head), rotateDeg, cx, cy)


def trend(t, direction: str) -> pathops.Path:
    """Canonical rising trend; falling is its exact vertical mirror."""
    w = _stroke(t)
    pts = t["trend"]["rising"]
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    heading = math.atan2(y1 - y0, x1 - x0)
    line = g.stroked_polyline(pts, w)
    head = g.stroked_polyline(
        _arrow_head((x1, y1), heading, t["trend"]["headLength"], math.radians(t["arrow"]["headAngleDeg"])), w
    )
    shape = g.union(line, head)
    if direction == "down":
        shape = g.mirror_y(shape, t["center"]["y"])
    return shape


BUILDERS = {
    "harvey": harvey,
    "dot": dot,
    "check": check,
    "cross": cross,
    "arrow": arrow,
    "trend": trend,
}


def build_outline(tokens, symbol) -> pathops.Path:
    builder = BUILDERS[symbol["builder"]]
    return g.normalize(builder(tokens, **symbol["params"]))
