"""PowerPoint specimen: real table cells, so glyphs are judged where they'll be used."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from .office_fonts import ttf_to_eot
from .font import FAMILY
from .specimen_content import LADDER_PT, SCORECARD_HEADER, SCORECARD_ROWS, families

TEXT_FONT = "Calibri"
DARK = RGBColor(0x14, 0x16, 0x1A)
LIGHT = RGBColor(0xF3, 0xF4, 0xF6)


def _set_font(run, typeface: str):
    """Assign the typeface to every script slot. PowerPoint may classify PUA
    characters outside the Latin slot, so setting only <a:latin> is not enough."""
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs", "a:sym"):
        el = rpr.find(qn(tag))
        if el is None:
            el = rpr.makeelement(qn(tag), {})
            rpr.append(el)
        el.set("typeface", typeface)


def _add_run(paragraph, text, typeface, size_pt, color=None, bold=False):
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    _set_font(run, typeface)
    return run


def _cell(cell, text, typeface, size_pt, align=PP_ALIGN.CENTER, color=None, fill=None, bold=False):
    tf = cell.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = align
    _add_run(p, text, typeface, size_pt, color, bold)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    if fill is not None:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill


def _title(slide, text, sub=None):
    box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9))
    p = box.text_frame.paragraphs[0]
    _add_run(p, text, TEXT_FONT, 24, bold=True)
    if sub:
        p2 = box.text_frame.add_paragraph()
        _add_run(p2, sub, TEXT_FONT, 12, color=RGBColor(0x6B, 0x72, 0x80))


def _table(slide, rows, cols, top, height_per_row):
    shape = slide.shapes.add_table(rows, cols, Inches(0.5), top, Inches(12.3), Emu(int(height_per_row * rows)))
    return shape.table


def render(manifest, ttf_path: Path, out_path: Path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    symbols = manifest["symbols"]
    ch = {s["id"]: chr(int(s["codepoint"], 16)) for s in symbols}
    fams = families(manifest)
    width = max(len(m) for _, _, m in fams)

    # 1 · Families: one row per family, a few families per slide
    per_slide = 6
    for start in range(0, len(fams), per_slide):
        chunk = fams[start:start + per_slide]
        slide = prs.slides.add_slide(blank)
        _title(slide, f"Families · 18pt  ({start // per_slide + 1}/{-(-len(fams) // per_slide)})",
               "Each family in one row of centred table cells. Compare outer size, centre and weight.")
        t = _table(slide, len(chunk), width + 1, Inches(1.4), Inches(0.8))
        t.columns[0].width = Inches(2.3)
        for c in range(1, width + 1):
            t.columns[c].width = Emu(int(Inches(10.0) / width))
        for r, (_, title, members) in enumerate(chunk):
            _cell(t.cell(r, 0), title, TEXT_FONT, 12, align=PP_ALIGN.LEFT)
            for c in range(width):
                _cell(t.cell(r, c + 1), ch[members[c]["id"]] if c < len(members) else "", FAMILY, 18)

    # 2 · Scorecard in light and dark
    rows, header = SCORECARD_ROWS, SCORECARD_HEADER
    for size, dark in ((12, False), (18, False), (18, True)):
        slide = prs.slides.add_slide(blank)
        _title(slide, f"Scorecard · {size}pt{' · dark' if dark else ''}",
               "Typical usage: no per-cell adjustment. Change cell font colour/size to confirm glyphs behave like text.")
        t = _table(slide, len(rows) + 1, len(header), Inches(1.5), Inches(0.12 + size / 72 * 1.6))
        t.columns[0].width = Inches(3.3)
        for c in range(1, len(header)):
            t.columns[c].width = Inches(1.8)
        fg, bg = (LIGHT, DARK) if dark else (None, None)
        for c, h in enumerate(header):
            _cell(t.cell(0, c), h, TEXT_FONT, 14, align=PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER, bold=True, color=fg, fill=bg)
        for r, (label, *ids) in enumerate(rows, start=1):
            _cell(t.cell(r, 0), label, TEXT_FONT, 14, align=PP_ALIGN.LEFT, color=fg, fill=bg)
            for c, gid in enumerate(ids, start=1):
                _cell(t.cell(r, c), ch[gid], FAMILY, size, color=fg, fill=bg)

    # 3 · Size ladder: each family inline with Calibri text, split across slides to fit
    for pt in LADDER_PT:
        lines = max(1, int(380 / (pt * 1.35)))
        for start in range(0, len(fams), lines):
            slide = prs.slides.add_slide(blank)
            _title(slide, f"Size ladder · {pt}pt", "Glyphs mixed with Calibri text in one paragraph. Check baseline and cap alignment.")
            box = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(12.3), Inches(5.8))
            tf = box.text_frame
            tf.word_wrap = True
            for i, (_, title, members) in enumerate(fams[start:start + lines]):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                _add_run(p, "Hx 50% ", TEXT_FONT, pt)
                _add_run(p, " ".join(ch[s["id"]] for s in members), FAMILY, pt)
                _add_run(p, f" {title}", TEXT_FONT, pt)

    # 4 · Instructions
    slide = prs.slides.add_slide(blank)
    _title(slide, "How to review this file")
    box = slide.shapes.add_textbox(Inches(0.5), Inches(1.4), Inches(12.3), Inches(5))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate([
        "1. SlideMarks is embedded in this file; no install needed. If PowerPoint warns about embedded fonts, allow them.",
        "2. Empty boxes or wrong shapes mean the embedded font was not loaded. That is a missing dependency, not a design issue.",
        "3. Select a table cell, change font colour and size: the glyph must behave exactly like text.",
        "4. PowerPoint drops embedded fonts on re-save unless Preferences → Save → Embed fonts in the file is on.",
        "    This file is regenerated by `slidemarks build`; edit the generator, not the deck.",
    ]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        _add_run(p, line, TEXT_FONT, 16)

    _embed_font(prs, ttf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))


def _embed_font(prs, ttf_path: Path):
    """Embed the full font so the deck renders without SlideMarks installed."""
    pres_part = prs.part
    font_part = Part(PackURI("/ppt/fonts/font1.fntdata"), "application/x-fontdata", pres_part.package, ttf_to_eot(ttf_path))
    rid = pres_part.relate_to(font_part, RT.FONT)

    pres = pres_part._element
    pres.set("embedTrueTypeFonts", "1")
    lst = pres.makeelement(qn("p:embeddedFontLst"), {})
    entry = lst.makeelement(qn("p:embeddedFont"), {})
    entry.append(entry.makeelement(qn("p:font"), {"typeface": FAMILY, "pitchFamily": "2", "charset": "0"}))
    entry.append(entry.makeelement(qn("p:regular"), {qn("r:id"): rid}))
    lst.append(entry)
    # Schema order: embeddedFontLst follows sldSz/notesSz/smartTags and precedes custShowLst/defaultTextStyle.
    anchor = pres.find(qn("p:smartTags"))
    if anchor is None:
        anchor = pres.find(qn("p:notesSz"))
    anchor.addnext(lst)
