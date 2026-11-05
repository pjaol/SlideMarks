"""Build the PowerPoint and Word files used as real establishing shots in the promo.

before_icons.pptx  icons placed as pictures over the table, positioned for the short row text;
                   the GDPR row's text is then lengthened so PowerPoint grows the row and the
                   pictures stay where they were dropped.
after.pptx         the same table with SlideMarks glyphs typed into the cells as text.
after.docx         the same table in Word.

Run: uv run --with python-pptx --with python-docx python build_decks.py
"""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt as DPt, RGBColor as DRGB
from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn as qn_pptx
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).parent
INK = RGBColor(0x1F, 0x23, 0x28)
MUTED = RGBColor(0x59, 0x63, 0x6E)
LINE = RGBColor(0xD1, 0xD9, 0xE0)
PANEL = RGBColor(0xF6, 0xF8, 0xFA)
ACCENT = RGBColor(0x6D, 0x3B, 0x8E)
FONT = "Aptos"
GLYPH_FONT = "SlideMarks"

SHORT_GDPR = "GDPR data residency"
LONG_GDPR = "GDPR data residency (EU and UK regions, customer-managed keys)"

# (requirement, product A, product B): glyph code point and the icon file standing in for it
ROWS = [
    ("SOC 2 Type II", ("", "harvey-100"), ("", "harvey-50")),
    (SHORT_GDPR, ("", "harvey-75"), ("", "harvey-0")),
    ("SSO / SAML", ("", "status-check"), ("", "status-cross")),
    ("Audit log coverage", ("", "trend-up"), ("", "trend-down")),
    ("Encryption at rest", ("", "harvey-100"), ("", "harvey-25")),
]

LEFT, TOP = Inches(0.8), Inches(2.0)
COLS = [Inches(6.3), Inches(2.85), Inches(2.85)]
HEADER_H, ROW_H = Inches(0.6), Inches(0.62)


def title(slide, text, sub):
    box = slide.shapes.add_textbox(LEFT, Inches(0.7), Inches(11.7), Inches(0.8))
    p = box.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = text
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = FONT, Pt(34), True, INK
    p2 = box.text_frame.add_paragraph()
    r2 = p2.add_run()
    r2.text = sub
    r2.font.name, r2.font.size, r2.font.color.rgb = FONT, Pt(16), MUTED
    bar = slide.shapes.add_shape(1, LEFT, Inches(0.55), Inches(0.6), Inches(0.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()


def cell_text(cell, text, *, font=FONT, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT):
    cell.text = ""
    tf = cell.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = font, Pt(size), bold, color
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = cell.margin_right = Inches(0.18)


def table(slide, glyphs: bool, gdpr_text: str):
    shape = slide.shapes.add_table(len(ROWS) + 1, 3, LEFT, TOP, sum(COLS), HEADER_H + ROW_H * len(ROWS))
    tbl = shape.table
    tbl.first_row = True
    tbl.horz_banding = False
    for i, w in enumerate(COLS):
        tbl.columns[i].width = w
    tbl.rows[0].height = HEADER_H
    for heading, c in zip(("Requirement", "Product A", "Product B"), tbl.rows[0].cells):
        cell_text(c, heading, size=15, bold=True, color=MUTED,
                  align=PP_ALIGN.LEFT if heading == "Requirement" else PP_ALIGN.CENTER)
    for r, (req, a, b) in enumerate(ROWS, start=1):
        tbl.rows[r].height = ROW_H
        cell_text(tbl.cell(r, 0), gdpr_text if req == SHORT_GDPR else req, size=20)
        for col, (cp, _) in ((1, a), (2, b)):
            cell_text(tbl.cell(r, col), cp if glyphs else "", font=GLYPH_FONT, size=28,
                      color=ACCENT if col == 1 else INK, align=PP_ALIGN.CENTER)
    for r in range(len(ROWS) + 1):
        for c in range(3):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = PANEL if r == 0 else RGBColor(0xFF, 0xFF, 0xFF)
            hairlines(cell)
    return shape


def hairlines(cell):
    """Bottom rule only; no vertical or top borders."""
    tcPr = cell._tc.get_or_add_tcPr()
    # borders must precede the cell fill in tcPr
    for i, (tag, show) in enumerate((("a:lnL", False), ("a:lnR", False), ("a:lnT", False), ("a:lnB", True))):
        ln = etree.Element(qn_pptx(tag), w=str(Pt(1) if show else 0))
        tcPr.insert(i, ln)
        if show:
            fill = etree.SubElement(ln, qn_pptx("a:solidFill"))
            etree.SubElement(fill, qn_pptx("a:srgbClr"), val="D1D9E0")
        else:
            etree.SubElement(ln, qn_pptx("a:noFill"))


def place_icons(slide):
    """Drop each icon where the short-text layout puts it, a little off like hand placement."""
    jitter = [(0, 2), (-6, 4), (5, -3), (-2, 6), (7, 0), (-4, -5), (3, 3), (-7, 2), (2, -6), (6, 5)]
    size = Inches(0.42)
    k = 0
    for r, (_, a, b) in enumerate(ROWS):
        cy = TOP + HEADER_H + ROW_H * r + ROW_H // 2
        for col, (_, icon) in ((1, a), (2, b)):
            cx = LEFT + sum(COLS[:col], Emu(0)) + COLS[col] // 2
            dx, dy = jitter[k]
            k += 1
            s = size + Emu(Inches(0.04) * ((k % 3) - 1))
            slide.shapes.add_picture(str(HERE / "icons" / f"{icon}.png"),
                                     cx - s // 2 + Pt(dx), cy - s // 2 + Pt(dy), s, s)


def deck(name, *, glyphs, icons, gdpr_text):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title(slide, "Compliance: Product A vs Product B", "Status as of Q4 review")
    table(slide, glyphs, gdpr_text)
    if icons:
        place_icons(slide)
    prs.save(HERE / name)


def word(name):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, DPt(11)
    h = doc.add_paragraph()
    run = h.add_run("Compliance: Product A vs Product B")
    run.bold, run.font.size, run.font.color.rgb = True, DPt(22), DRGB(0x1F, 0x23, 0x28)
    doc.add_paragraph("Product A leads on every requirement we track this quarter. "
                      "Symbols sit inline with the text, so they read in a sentence too: "
                      "SSO ").add_run("").font.name = GLYPH_FONT
    t = doc.add_table(rows=1, cols=3)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    word_hairlines(t)
    for c, heading in zip(t.rows[0].cells, ("Requirement", "Product A", "Product B")):
        c.text = ""
        rr = c.paragraphs[0].add_run(heading)
        rr.bold = True
        if heading != "Requirement":
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for req, (ca, _), (cb, _) in ROWS:
        cells = t.add_row().cells
        cells[0].text = LONG_GDPR if req == SHORT_GDPR else req
        for c, cp, color in ((cells[1], ca, DRGB(0x6D, 0x3B, 0x8E)), (cells[2], cb, DRGB(0x1F, 0x23, 0x28))):
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            g = p.add_run(cp)
            g.font.name, g.font.size, g.font.color.rgb = GLYPH_FONT, DPt(16), color
            g._element.rPr.rFonts.set(qn("w:cs"), GLYPH_FONT)
    for c in t.rows[0].cells:
        shd = etree.SubElement(c._tc.get_or_add_tcPr(), qn("w:shd"), {qn("w:val"): "clear", qn("w:fill"): "F6F8FA"})
        c.paragraphs[0].runs[0].font.color.rgb = DRGB(0x59, 0x63, 0x6E)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_before = p.paragraph_format.space_after = DPt(5)
    doc.save(HERE / name)


def word_hairlines(t):
    """Horizontal rules only, matching the slide."""
    tblPr = t._tbl.tblPr
    borders = etree.SubElement(tblPr, qn("w:tblBorders"))
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        show = edge in ("bottom", "insideH")
        etree.SubElement(borders, qn(f"w:{edge}"), {qn("w:val"): "single" if show else "nil",
                         qn("w:sz"): "6", qn("w:color"): "D1D9E0"})


if __name__ == "__main__":
    deck("before_empty.pptx", glyphs=False, icons=False, gdpr_text=SHORT_GDPR)
    deck("before_icons.pptx", glyphs=False, icons=True, gdpr_text=SHORT_GDPR)
    deck("before_broken.pptx", glyphs=False, icons=True, gdpr_text=LONG_GDPR)
    deck("after.pptx", glyphs=True, icons=False, gdpr_text=LONG_GDPR)
    word("after.docx")
    print("built")
