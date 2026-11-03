"""Compile manifest + tokens into TTF, WOFF2 and per-glyph SVG."""

from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from .glyphs import build_outline

FAMILY = "SlideMarks"
STYLE = "Regular"
# Fixed timestamp keeps builds byte-reproducible (seconds since 1904-01-01).
FIXED_TIMESTAMP = 3_844_800_000


def glyph_name(symbol_id: str) -> str:
    return symbol_id.replace("-", "_")


def _tt_glyph(path):
    pen = TTGlyphPen(None)
    path.draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=False))
    return pen.glyph()


def _notdef(t):
    pen = TTGlyphPen(None)
    f, w = t["frame"], t["stroke"]["regular"]
    for (x0, y0, x1, y1), cw in (((f["xMin"], f["yMin"], f["xMax"], f["yMax"]), True),
                                 ((f["xMin"] + w, f["yMin"] + w, f["xMax"] - w, f["yMax"] - w), False)):
        pts = [(x0, y0), (x0, y1), (x1, y1), (x1, y0)] if cw else [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    return pen.glyph()


def build_font(tokens, manifest, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    symbols = manifest["symbols"]
    adv = tokens["advanceWidth"]

    outlines = {s["id"]: build_outline(tokens, s) for s in symbols}
    glyph_order = [".notdef", "space"] + [glyph_name(s["id"]) for s in symbols]
    glyphs = {".notdef": _notdef(tokens), "space": TTGlyphPen(None).glyph()}
    glyphs.update({glyph_name(s["id"]): _tt_glyph(outlines[s["id"]]) for s in symbols})
    cmap = {0x20: "space"} | {int(s["codepoint"], 16): glyph_name(s["id"]) for s in symbols}

    fb = FontBuilder(tokens["unitsPerEm"], isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    metrics = {}
    glyf = fb.font["glyf"]
    for name in glyph_order:
        width = adv // 3 if name == "space" else adv
        metrics[name] = (width, getattr(glyf[name], "xMin", 0))
    fb.setupHorizontalMetrics(metrics)
    asc, desc = tokens["ascender"], tokens["descender"]
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    version = manifest["manifestVersion"]
    major, minor, patch = (int(x) for x in version.split("."))
    fb.setupHead(unitsPerEm=tokens["unitsPerEm"], fontRevision=major + (minor * 100 + patch) / 1000,
                 created=FIXED_TIMESTAMP, modified=FIXED_TIMESTAMP)
    fb.setupNameTable({
        "familyName": FAMILY,
        "styleName": STYLE,
        "uniqueFontIdentifier": f"{FAMILY}-{STYLE};{version}",
        "fullName": f"{FAMILY} {STYLE}",
        "psName": f"{FAMILY}-{STYLE}",
        "version": f"Version {version}",
    })
    fb.setupOS2(
        version=4, sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
        usWinAscent=asc, usWinDescent=-desc,
        fsType=tokens["fsType"],
        fsSelection=0x40 | 0x80,  # REGULAR | USE_TYPO_METRICS
        achVendID="NONE",
        ulUnicodeRange1=1,  # Basic Latin (space)
        ulUnicodeRange2=1 << (60 - 32),  # Private Use Area
        ulCodePageRange1=1,  # Latin 1, so Office lists the font normally
        sxHeight=0, sCapHeight=700, usDefaultChar=0, usBreakChar=0x20,
        usFirstCharIndex=0x20, usLastCharIndex=max(cmap),
    )
    fb.setupPost(keepGlyphNames=True)

    ttf_path = out_dir / f"{FAMILY}-{STYLE}.ttf"
    fb.save(str(ttf_path))

    woff2_path = out_dir / f"{FAMILY}-{STYLE}.woff2"
    font = TTFont(str(ttf_path))
    font.flavor = "woff2"
    font.save(str(woff2_path))

    svg_dir = out_dir / "svg"
    svg_dir.mkdir(exist_ok=True)
    svgs = {}
    for s in symbols:
        svgs[s["id"]] = glyph_svg_path(outlines[s["id"]], asc)
        (svg_dir / f"{s['id']}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {adv} {tokens["unitsPerEm"]}">'
            f'<path d="{svgs[s["id"]]}"/></svg>\n'
        )
    return {"ttf": ttf_path, "woff2": woff2_path, "svg_paths": svgs}


def glyph_svg_path(path, ascender: int) -> str:
    """SVG path data in a y-down em box whose top is the font ascender."""
    pen = SVGPathPen(None)
    path.draw(TransformPen(pen, (1, 0, 0, -1, 0, ascender)))
    return pen.getCommands()
