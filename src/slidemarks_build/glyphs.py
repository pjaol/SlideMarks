"""Family builders. Each family derives every member from one construction,
driven only by design tokens, so members cannot drift apart.

Conventions: font units, y-up, baseline 0. Centerline coordinates are stroked
with round caps/joins at a token stroke weight; stroke weight never scales with
a glyph. Asymmetric glyphs are centered on the shared center by ink box."""

import math

import pathops

from . import geometry as g


def _w(t, weight="regular") -> float:
    return t["stroke"][weight]


def _c(t):
    return t["center"]["x"], t["center"]["y"]


def _head(t, tip, heading_rad, weight="regular", length=None):
    """Open arrowhead shared by every arrow-like glyph."""
    a = t["arrow"]
    length, half = length or a["headLength"], math.radians(a["headAngleDeg"])
    back = heading_rad + math.pi
    pts = [
        (tip[0] + length * math.cos(back + half), tip[1] + length * math.sin(back + half)),
        tip,
        (tip[0] + length * math.cos(back - half), tip[1] + length * math.sin(back - half)),
    ]
    return g.stroked_polyline(pts, _w(t, weight))


def _centered(t, path):
    return g.center_ink(path, *_c(t))


# ── Harvey & progress ────────────────────────────────────────────────────────

def harvey(t, fraction: float):
    cx, cy = _c(t)
    r = t["harvey"]["diameter"] / 2
    w = _w(t)
    rim = g.ring(cx, cy, r, w)
    if fraction <= 0:
        return rim
    gap = t["harvey"]["wedgeGap"]
    wedge_r = r if gap == 0 else r - w - gap
    return g.union(rim, g.wedge(cx, cy, wedge_r, fraction))


def progress(t, filled: int, segments: int = 4):
    cx, cy = _c(t)
    p, f = t["progress"], t["frame"]
    seg_w = (f["xMax"] - f["xMin"] - (segments - 1) * p["gap"]) / segments
    y0, y1 = cy - p["height"] / 2, cy + p["height"] / 2
    parts = []
    for i in range(segments):
        x0 = f["xMin"] + i * (seg_w + p["gap"])
        pts = [(x0, y0), (x0, y1), (x0 + seg_w, y1), (x0 + seg_w, y0)]
        parts.append(g.polygon(pts) if i < filled else g.polygon_outline(pts, p["emptyStroke"], round_join=False))
    return g.union(*parts)


# ── Arrows ───────────────────────────────────────────────────────────────────

def arrow(t, rotateDeg: float, weight: str = "regular", length: str = "standard", heads: str = "end"):
    """Canonical right-pointing arrow; every direction is an exact rotation."""
    cx, cy = _c(t)
    w = _w(t, weight)
    half = t["arrow"]["halfLength"][length] - w / 2  # token is ink extent; caps add w/2
    tip, tail = (cx + half, cy), (cx - half, cy)
    shape = g.union(g.stroked_polyline([tail, tip], w), _head(t, tip, 0.0, weight))
    if heads == "both":
        shape = g.union(shape, _head(t, tail, math.pi, weight))
    return g.rotate(shape, rotateDeg, cx, cy)


def curved(t, kind: str, mirror: bool = False):
    w, r = _w(t), t["curved"]["radius"]
    if kind == "turn":
        line = g.Sketch().move(330, 118).line(330, 400).arc(330 + r, 400, r, 180, 90).line(802, 400 + r)
        shape = g.union(line.stroke(w), _head(t, (802, 400 + r), 0.0))
    elif kind == "uturn":
        R = t["curved"]["uturnRadius"]
        line = g.Sketch().move(300, 130).line(300, 470).arc(300 + R, 470, R, 180, 0).line(300 + 2 * R, 160)
        shape = g.union(line.stroke(w), _head(t, (300 + 2 * R, 160), -math.pi / 2))
    elif kind == "loop":
        lr, sweep = t["loop"]["radius"], t["loop"]["sweepDeg"]
        start = t["loop"]["startDeg"]  # opening on the right, head arriving at the top-right like ↻
        end = start - sweep
        line = g.Sketch().arc(500, 420, lr, start, end)
        e = math.radians(end)
        tip = (500 + lr * math.cos(e), 420 + lr * math.sin(e))
        heading = math.atan2(-math.cos(e), math.sin(e))  # clockwise tangent
        shape = g.union(line.stroke(w), _head(t, tip, heading, length=t["loop"]["headLength"]))
    elif kind == "return":
        line = g.Sketch().move(780, 700).line(780, 380 + r).arc(780 - r, 380 + r, r, 0, -90).line(222, 380)
        shape = g.union(line.stroke(w), _head(t, (222, 380), math.pi))
    elif kind == "branch":
        # Arms at 45°, matching the diagonal arrows. Each head then has one horizontal arm pointing at
        # the other head, so the heads are shorter (documented exception, like loops) and the tips sit
        # at the frame edges to keep a clear gap between them at small sizes.
        bt = t["branch"]
        fork = (500, bt["forkY"])
        left, right = ((500 + s * bt["spread"], bt["forkY"] + bt["spread"]) for s in (-1, 1))
        stem = g.stroked_polyline([(500, 110), fork], w)
        arms = [g.stroked_polyline([fork, end], w) for end in (left, right)]
        heads = [_head(t, end, math.atan2(end[1] - fork[1], end[0] - fork[0]), length=bt["headLength"]) for end in (left, right)]
        shape = g.union(stem, *arms, *heads)
    else:
        raise ValueError(kind)
    shape = _centered(t, shape)
    return g.mirror_x(shape, t["center"]["x"]) if mirror else shape


def chevron(t, rotateDeg: float = 0, kind: str = "single"):
    cx, cy = _c(t)
    w = _w(t)
    arm = t["chevron"]["armLength"]
    d = arm * math.cos(math.radians(t["arrow"]["headAngleDeg"]))

    def one(tip_x):
        return [(tip_x - d, cy + d), (tip_x, cy), (tip_x - d, cy - d)]

    if kind == "single":
        shape = g.stroked_polyline(one(cx), w)
    elif kind == "double":
        gap = t["chevron"]["doubleOffset"]
        shape = g.union(g.stroked_polyline(one(cx), w), g.stroked_polyline(one(cx + gap), w))
    elif kind == "filled":
        pts = one(cx)
        closed = g.Sketch().move(*pts[0]).line(*pts[1]).line(*pts[2]).close()
        shape = g.union(closed.fill(), closed.stroke(w))
    else:
        raise ValueError(kind)
    return g.rotate(_centered(t, shape), rotateDeg, cx, cy)


# ── Status & outcomes ────────────────────────────────────────────────────────

def check(t, weight: str = "regular", scale: float = 1.0):
    # Heavier strokes pull the centerline in so the ink box matches the regular check.
    pts = t["check"]["points"]
    half_ink = (max(x for x, _ in pts) - min(x for x, _ in pts)) / 2 + _w(t) / 2
    fit = (half_ink - _w(t, weight) / 2) / (half_ink - _w(t) / 2)
    pts = g.scale_points(pts, scale * fit, *_c(t))
    return _centered(t, g.stroked_polyline(pts, _w(t, weight)))


def cross(t, weight: str = "regular", scale: float = 1.0):
    cx, cy = _c(t)
    s = t["cross"]["halfSpan"] * scale
    w = _w(t, weight)
    return g.union(
        g.stroked_polyline([(cx - s, cy - s), (cx + s, cy + s)], w),
        g.stroked_polyline([(cx - s, cy + s), (cx + s, cy - s)], w),
    )


def minus(t, scale: float = 1.0):
    cx, cy = _c(t)
    s = t["mark"]["halfSpan"] * scale
    return g.stroked_polyline([(cx - s, cy), (cx + s, cy)], _w(t))


def plus(t, scale: float = 1.0):
    cx, cy = _c(t)
    s = t["mark"]["halfSpan"] * scale
    return g.union(minus(t, scale), g.stroked_polyline([(cx, cy - s), (cx, cy + s)], _w(t)))


def _dot_radius(t):
    return _w(t) * t["mark"]["dotRatio"] / 2


def exclamation(t, scale: float = 1.0):
    cx, cy = _c(t)
    w = _w(t)
    stem = g.stroked_polyline([(cx, cy - 80 * scale), (cx, cy + 300 * scale)], w)
    dot = g.circle(cx, cy - 280 * scale, _dot_radius(t))
    return _centered(t, g.union(stem, dot))


def question(t, scale: float = 1.0):
    cx, cy = _c(t)
    w = _w(t)
    r = 145 * scale
    hook_cy = cy + 155 * scale
    hook = (g.Sketch().arc(cx, hook_cy, r, 160, -45)
            .line(cx, cy - 20 * scale).line(cx, cy - 80 * scale))
    dot = g.circle(cx, cy - 280 * scale, _dot_radius(t))
    return _centered(t, g.union(hook.stroke(w), dot))


MARKS = {"check": check, "cross": cross, "minus": minus, "question": question, "exclamation": exclamation}


def circled(t, mark: str):
    """Shared Harvey circle with a scaled inner mark at full stroke weight."""
    cx, cy = _c(t)
    rim = g.ring(cx, cy, t["harvey"]["diameter"] / 2, _w(t))
    inner = g.center_ink(MARKS[mark](t, scale=t["circleMark"]["scale"]), cx, cy)
    return g.union(rim, inner)


# ── Rating & RAG ─────────────────────────────────────────────────────────────

def dot(t, filled: bool):
    cx, cy = _c(t)
    r = t["dot"]["diameter"] / 2
    return g.circle(cx, cy, r) if filled else g.ring(cx, cy, r, _w(t))


def square(t, filled: bool):
    cx, cy = _c(t)
    h = t["square"]["side"] / 2
    pts = [(cx - h, cy - h), (cx - h, cy + h), (cx + h, cy + h), (cx + h, cy - h)]
    return g.polygon(pts) if filled else g.polygon_outline(pts, _w(t), round_join=False)


def diamond(t, filled: bool):
    cx, cy = _c(t)
    h = t["diamond"]["halfDiagonal"]
    pts = [(cx, cy + h), (cx + h, cy), (cx, cy - h), (cx - h, cy)]
    return g.polygon(pts) if filled else g.polygon_outline(pts, _w(t), round_join=False)


def rag(t, kind: str):
    cx, cy = _c(t)
    r = t["dot"]["diameter"] / 2
    rim = g.ring(cx, cy, r, _w(t))
    if kind == "ring-dot":
        return g.union(rim, g.circle(cx, cy, t["rag"]["centerDot"]))
    if kind == "half":
        lower = g.polygon([(cx - r, cy - r), (cx - r, cy), (cx + r, cy), (cx + r, cy - r)])
        return g.union(rim, g.intersection(g.circle(cx, cy, r), lower))
    raise ValueError(kind)


# ── Trend ────────────────────────────────────────────────────────────────────

def trend(t, shape: str = "rising", mirror: bool = False, head: bool = True):
    """Polyline trends; falling variants are exact vertical mirrors."""
    w = _w(t)
    pts = t["trend"][shape]
    path = g.stroked_polyline(pts, w)
    if head:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        path = g.union(path, _head(t, (x1, y1), math.atan2(y1 - y0, x1 - x0)))
    path = _centered(t, path)
    return g.mirror_y(path, t["center"]["y"]) if mirror else path


# ── Priority & emphasis ──────────────────────────────────────────────────────

def _digit(t, digit: int):
    cx, cy = _c(t)
    if digit == 1:
        return g.Sketch().move(cx - 80, cy + 95).line(cx, cy + 150).line(cx, cy - 150)
    if digit == 2:
        return (g.Sketch().arc(cx, cy + 70, 85, 165, -30)
                .line(cx - 95, cy - 150).line(cx + 100, cy - 150))
    if digit == 3:
        return (g.Sketch().arc(cx - 5, cy + 80, 72, 155, -90)
                .arc(cx - 5, cy - 74, 82, 90, -155))
    raise ValueError(digit)


def circled_digit(t, digit: int):
    cx, cy = _c(t)
    rim = g.ring(cx, cy, t["harvey"]["diameter"] / 2, _w(t))
    numeral = _digit(t, digit).stroke(_w(t))
    if digit == 1:
        # Optical centering: the stem sits on the center line; ink-box centering
        # would let the flag pull the stem off-center. Center vertically only.
        _, y0, _, y1 = numeral.bounds
        numeral = g.translate(numeral, 0, cy - (y0 + y1) / 2)
    else:
        numeral = g.center_ink(numeral, cx, cy)
    return g.union(rim, numeral)


def flag(t):
    w = _w(t)
    pole = g.stroked_polyline([(330, 118), (330, 722)], w)
    banner = g.Sketch().move(330, 722).line(760, 722).line(660, 591).line(760, 460).line(330, 460).close()
    return _centered(t, g.union(pole, banner.fill(), banner.stroke(w)))


def star(t, filled: bool):
    cx, cy = _c(t)
    s = t["star"]
    pts = []
    for i in range(10):
        r = s["outerRadius"] if i % 2 == 0 else s["outerRadius"] * s["innerRatio"]
        a = math.radians(90 + i * 36)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    sk = g.Sketch().move(*pts[0])
    for p in pts[1:]:
        sk.line(*p)
    sk.close()
    shape = g.union(sk.fill(), sk.stroke(_w(t))) if filled else sk.stroke(_w(t))
    return _centered(t, shape)


def bookmark(t):
    sk = g.Sketch().move(340, 722).line(660, 722).line(660, 118).line(500, 250).line(340, 118).close()
    return _centered(t, sk.stroke(_w(t)))


def pin(t):
    cx = t["center"]["x"]
    p = t["pin"]
    r, head_cy, tip_y = p["radius"], p["headCenterY"], p["tipY"]
    d = head_cy - tip_y
    beta = math.acos(r / d)
    tangents = [(cx + r * math.cos(-math.pi / 2 + s * beta), head_cy + r * math.sin(-math.pi / 2 + s * beta)) for s in (1, -1)]
    body = g.union(g.circle(cx, head_cy, r), g.polygon([(cx, tip_y), tangents[0], tangents[1]]))
    return _centered(t, g.difference(body, g.circle(cx, head_cy, p["holeRadius"])))


# ── Comparisons ──────────────────────────────────────────────────────────────

def comparison(t, kind: str):
    cx, cy = _c(t)
    w = _w(t)
    c = t["comparison"]
    s, gap = c["halfSpan"], c["gap"]

    def bar(y):
        return g.stroked_polyline([(cx - s, y), (cx + s, y)], w)

    def wave(y):
        a = c["waveAmplitude"]
        return g.Sketch().move(cx - s, y).curve(cx - s / 2, y + a, cx + s / 2, y - a, cx + s, y).stroke(w)

    if kind == "equals":
        shape = g.union(bar(cy + gap), bar(cy - gap))
    elif kind == "not-equals":
        slash = g.stroked_polyline([(cx - 110, cy - 250), (cx + 110, cy + 250)], w)
        shape = g.union(bar(cy + gap), bar(cy - gap), slash)
    elif kind == "approx":
        shape = g.union(wave(cy + gap), wave(cy - gap))
    elif kind in ("greater", "less"):
        shape = g.stroked_polyline([(cx - 230, cy + 220), (cx + 230, cy), (cx - 230, cy - 220)], w)
        if kind == "less":
            shape = g.mirror_x(shape, cx)
    elif kind in ("greater-equal", "less-equal"):
        angle = g.stroked_polyline([(cx - 200, cy + 300), (cx + 200, cy + 120), (cx - 200, cy - 60)], w)
        base = g.stroked_polyline([(cx - 200, cy - 280), (cx + 200, cy - 280)], w)
        shape = g.union(angle, base)
        if kind == "less-equal":
            shape = g.mirror_x(shape, cx)
    elif kind == "delta":
        shape = g.Sketch().move(cx, cy + 300).line(cx + 300, cy - 290).line(cx - 300, cy - 290).close().stroke(w)
    else:
        raise ValueError(kind)
    return _centered(t, shape)


# ── Workflow nodes ───────────────────────────────────────────────────────────

def workflow(t, kind: str):
    cx, cy = _c(t)
    w = _w(t)
    f = t["frame"]
    wf = t["workflow"]
    x0, x1 = f["xMin"], f["xMax"]
    if kind == "process":
        h = wf["boxHeight"] / 2
        shape = g.rounded_rect_outline(x0, cy - h, x1, cy + h, 0, w)
    elif kind == "rounded":
        h = wf["boxHeight"] / 2
        shape = g.rounded_rect_outline(x0, cy - h, x1, cy + h, wf["cornerRadius"], w)
    elif kind == "decision":
        h = (x1 - x0) / 2
        shape = g.polygon_outline([(cx, cy + h), (cx + h, cy), (cx, cy - h), (cx - h, cy)], w, round_join=False)
    elif kind == "terminator":
        h = wf["pillHeight"] / 2
        shape = g.rounded_rect_outline(x0, cy - h, x1, cy + h, h, w)
    elif kind == "database":
        rx, ry, top, bottom = wf["dbRadiusX"], wf["dbRadiusY"], cy + 222, cy - 222
        lid = g.Sketch()
        lid.path = g.ellipse(cx, top, rx, ry)
        base = g.Sketch()
        base.path = g.ellipse(cx, bottom, rx, ry)
        lower_half = g.polygon([(cx - rx - w, bottom - ry - w), (cx - rx - w, bottom), (cx + rx + w, bottom), (cx + rx + w, bottom - ry - w)])
        sides = g.union(g.stroked_polyline([(cx - rx, top), (cx - rx, bottom)], w),
                        g.stroked_polyline([(cx + rx, top), (cx + rx, bottom)], w))
        shape = g.union(lid.stroke(w), g.intersection(base.stroke(w), lower_half), sides)
    elif kind == "connector":
        shape = g.ring(cx, cy, wf["connectorDiameter"] / 2, w)
    else:
        raise ValueError(kind)
    return _centered(t, shape)


# ── Simple markers ───────────────────────────────────────────────────────────

def marker(t, kind: str):
    cx, cy = _c(t)
    m = t["marker"]
    if kind in ("bullet-small", "bullet-medium", "bullet-large"):
        return g.circle(cx, cy, m[kind.split("-")[1]])
    if kind == "bullet-open":
        return g.ring(cx, cy, m["medium"], _w(t))
    if kind == "dash":
        return g.stroked_polyline([(cx - m["dashHalf"], cy), (cx + m["dashHalf"], cy)], _w(t))
    if kind == "separator-vertical":
        f = t["frame"]
        w = _w(t, "thin")
        return g.stroked_polyline([(cx, f["yMin"] + w / 2), (cx, f["yMax"] - w / 2)], w)
    if kind == "separator-horizontal":
        # Spans the full advance with flat ends so repeated glyphs join into one rule.
        h = _w(t, "thin") / 2
        return g.polygon([(0, cy - h), (0, cy + h), (t["advanceWidth"], cy + h), (t["advanceWidth"], cy - h)])
    raise ValueError(kind)


# ── Ownership & action ───────────────────────────────────────────────────────

def _person(t, cx, base_y, s):
    """Outline person: returns (ink, silhouette) so neighbours can be knocked out."""
    w = _w(t)
    head_r, head_cy = 125 * s, base_y + 497 * s
    sh_r, sh_cy = 220 * s, base_y + 82 * s
    head = g.ring(cx, head_cy, head_r, w)
    body = g.Sketch().move(cx - sh_r, base_y).line(cx - sh_r, sh_cy).arc(cx, sh_cy, sh_r, 180, 0).line(cx + sh_r, base_y)
    ink = g.union(head, body.stroke(w))
    body_fill = g.union(g.circle(cx, sh_cy, sh_r + w / 2),
                        g.polygon([(cx - sh_r - w / 2, base_y - w), (cx - sh_r - w / 2, sh_cy), (cx + sh_r + w / 2, sh_cy), (cx + sh_r + w / 2, base_y - w)]))
    silhouette = g.union(g.circle(cx, head_cy, head_r), body_fill)
    return ink, silhouette


def ownership(t, kind: str):
    cx, cy = _c(t)
    w = _w(t)
    if kind == "user":
        shape, _ = _person(t, cx, 118, 1.0)
    elif kind == "users":
        gap = t["ownership"]["knockoutGap"]
        front, front_sil = _person(t, cx - 90, 118, 0.85)
        back, _ = _person(t, cx + 150, 200, 0.75)
        knockout = _outline(front_sil, gap * 2)
        shape = g.union(front, g.difference(back, knockout))
    elif kind in ("lock", "unlock"):
        body = g.rounded_rect(290, 110, 710, 450, 50)
        keyhole = g.union(g.circle(cx, 310, 48), g.polygon([(cx - 22, 190), (cx - 22, 310), (cx + 22, 310), (cx + 22, 190)]))
        right_end = 450 if kind == "lock" else 570
        shackle = g.Sketch().move(370, 450).line(370, 580).arc(500, 580, 130, 180, 0).line(630, right_end)
        shape = g.union(g.difference(body, keyhole), shackle.stroke(w))
    elif kind == "clock":
        rim = g.ring(cx, cy, t["harvey"]["diameter"] / 2, w)
        hands = g.stroked_polyline([(cx, cy + 210), (cx, cy), (cx + 150, cy - 90)], w)
        shape = g.union(rim, hands)
    elif kind == "calendar":
        x0, y0, x1, y1, r = 200, 110, 800, 680, 60
        outline = g.rounded_rect_outline(x0, y0, x1, y1, r, w)
        header = g.intersection(g.rounded_rect(x0, y0, x1, y1, r), g.polygon([(x0, 540), (x0, y1), (x1, y1), (x1, 540)]))
        tabs = [g.stroked_polyline([(x, 600), (x, 722)], w) for x in (360, 640)]
        tab_gaps = [_outline(tab, 30) for tab in tabs]
        cells = [g.polygon([(x - 34, y - 34), (x - 34, y + 34), (x + 34, y + 34), (x + 34, y - 34)])
                 for x in (340, 500, 660) for y in (420, 260)]
        frame = g.union(outline, header)
        for gap in tab_gaps:
            frame = g.difference(frame, gap)
        shape = g.union(frame, *tabs, *cells)
    elif kind in ("link", "unlink"):
        lk = t["ownership"]["link"]
        lw, lh = lk["width"], lk["height"]
        off = lk["offset"] if kind == "link" else lk["unlinkOffset"]
        pills = [g.rounded_rect_outline(cx + dx - lw / 2, cy - lh / 2, cx + dx + lw / 2, cy + lh / 2, lh / 2, w) for dx in (-off, off)]
        shape = g.rotate(g.union(*pills), 45, cx, cy)
    else:
        raise ValueError(kind)
    return _centered(t, shape)


def _outline(path: pathops.Path, width: float) -> pathops.Path:
    """Grow a filled shape by width/2 on every side (used for knock-out gaps)."""
    grown = pathops.Path()
    path.draw(grown.getPen())
    grown.stroke(width, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    grown.convertConicsToQuads()
    return g.union(path, grown)


BUILDERS = {
    "harvey": harvey,
    "progress": progress,
    "arrow": arrow,
    "curved": curved,
    "chevron": chevron,
    "check": check,
    "cross": cross,
    "minus": minus,
    "plus": plus,
    "question": question,
    "exclamation": exclamation,
    "circled": circled,
    "dot": dot,
    "square": square,
    "diamond": diamond,
    "rag": rag,
    "trend": trend,
    "circled_digit": circled_digit,
    "flag": flag,
    "star": star,
    "bookmark": bookmark,
    "pin": pin,
    "comparison": comparison,
    "workflow": workflow,
    "marker": marker,
    "ownership": ownership,
}


def build_outline(tokens, symbol) -> pathops.Path:
    builder = BUILDERS[symbol["builder"]]
    return g.normalize(builder(tokens, **symbol["params"]))
