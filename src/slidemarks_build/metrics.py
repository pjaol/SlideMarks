"""Measure the compiled font (not the source) and report consistency findings."""

import statistics
from collections import defaultdict
from pathlib import Path

from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from .font import glyph_name

TOLERANCE = 1  # font units, per PRD §12.1
CENTER_TOLERANCE = 2


def measure(ttf_path: Path, tokens, manifest) -> list[dict]:
    font = TTFont(str(ttf_path))
    glyph_set = font.getGlyphSet()
    hmtx = font["hmtx"]
    f = tokens["frame"]
    frame_area = (f["xMax"] - f["xMin"]) * (f["yMax"] - f["yMin"])

    records = []
    for s in manifest["symbols"]:
        name = glyph_name(s["id"])
        bp, ap = BoundsPen(glyph_set), AreaPen(glyph_set)
        glyph_set[name].draw(bp)
        glyph_set[name].draw(ap)
        x0, y0, x1, y1 = bp.bounds
        records.append({
            "id": s["id"],
            "category": s["category"],
            "group": s["geometryGroup"],
            "status": s["status"],
            "frameException": s.get("frameException"),
            "advance": hmtx[name][0],
            "bounds": (x0, y0, x1, y1),
            "size": (x1 - x0, y1 - y0),
            "center": ((x0 + x1) / 2, (y0 + y1) / 2),
            "area": abs(ap.value),
            "coverage": abs(ap.value) / frame_area,
            "findings": [],
        })
    _check(records, tokens)
    return records


def _check(records, tokens):
    cx, cy = tokens["center"]["x"], tokens["center"]["y"]
    rules = tokens["geometryGroups"]
    f = tokens["frame"]
    for r in records:
        if not r["frameException"]:
            x0, y0, x1, y1 = r["bounds"]
            over = max(f["xMin"] - x0, f["yMin"] - y0, x1 - f["xMax"], y1 - f["yMax"])
            if over > TOLERANCE:
                r["findings"].append(f"ink exceeds the frame by {over:.0f} units")
        if r["advance"] != tokens["advanceWidth"]:
            r["findings"].append(f"advance {r['advance']} ≠ {tokens['advanceWidth']}")
        dx, dy = r["center"][0] - cx, r["center"][1] - cy
        if abs(dx) > CENTER_TOLERANCE or abs(dy) > CENTER_TOLERANCE:
            r["findings"].append(f"ink center off by ({dx:+.0f}, {dy:+.0f})")
        x0, y0, x1, y1 = r["bounds"]
        if y1 > tokens["ascender"] or y0 < tokens["descender"]:
            r["findings"].append("ink exceeds ascender/descender (will clip)")

    by_group = defaultdict(list)
    for r in records:
        by_group[r["group"]].append(r)
    for group, members in by_group.items():
        rule = rules.get(group, "optical")
        ref = members[0]
        for m in members[1:]:
            if rule == "identical-bounds":
                diff = max(abs(a - b) for a, b in zip(m["bounds"], ref["bounds"]))
                if diff > TOLERANCE:
                    m["findings"].append(f"bounds differ from {ref['id']} by {diff:.0f} units")
            elif rule == "same-footprint":
                diff = max(abs(a - b) for a, b in zip(sorted(m["size"]), sorted(ref["size"])))
                if diff > TOLERANCE:
                    m["findings"].append(f"footprint differs from {ref['id']} by {diff:.0f} units")

    # Visual weight: informational spread within a category, shown in the review.
    by_cat = defaultdict(list)
    for r in records:
        by_cat[r["category"]].append(r)
    for members in by_cat.values():
        median = statistics.median(m["coverage"] for m in members)
        for m in members:
            m["weightVsCategory"] = m["coverage"] / median if median else 1.0
