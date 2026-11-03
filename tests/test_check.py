"""slidemarks check: plant each problem in a small deck/document and confirm it's found,
and that the accessible pattern (symbol + visible text) comes out clean."""

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from pptx import Presentation
from pptx.util import Inches

from slidemarks_build.check import check_file
from slidemarks_build.specimen_docx import _embed_font as embed_docx
from slidemarks_build.specimen_docx import _set_font as docx_font
from slidemarks_build.specimen_pptx import _embed_font as embed_pptx
from slidemarks_build.specimen_pptx import _set_font as pptx_font

H75, ARROW_PUA, ARROW_STD = "", "", "→"
# cell contents: list of (text, font) runs
CELLS = {
    (1, 0): [(H75, "SlideMarks")],                               # silent-symbol
    (1, 1): [(H75, "SlideMarks"), (" 75%", "Calibri")],          # clean: symbol + text
    (1, 2): [(ARROW_STD, "SlideMarks")],                         # clean: announced by name
    (2, 0): [(ARROW_PUA, "SlideMarks"), (" Rising", "Calibri")], # prefer-standard
    (2, 1): [(H75 + " 75%", "Calibri")],                         # font-not-applied
    (2, 2): [("plain text", "Calibri")],                         # nothing to do with SlideMarks
}
HEADERS = ["A", "B", "C"]


def _rules(findings, where=None):
    return sorted({f.rule for f in findings if where is None or where in f.location})


def make_pptx(path, ttf=None, header=True):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    table = slide.shapes.add_table(3, 3, Inches(1), Inches(1), Inches(6), Inches(2)).table
    table._tbl.tblPr.set("firstRow", "1" if header else "0")
    for c, h in enumerate(HEADERS):
        table.cell(0, c).text = h
    for (r, c), runs in CELLS.items():
        p = table.cell(r, c).text_frame.paragraphs[0]
        for text, font in runs:
            run = p.add_run()
            run.text = text
            pptx_font(run, font)
    if ttf:
        embed_pptx(prs, ttf)
    prs.save(str(path))
    return path


def make_docx(path, ttf=None, header=True):
    doc = Document()
    table = doc.add_table(rows=3, cols=3)
    if header:
        table.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for c, h in enumerate(HEADERS):
        table.cell(0, c).text = h
    for (r, c), runs in CELLS.items():
        p = table.cell(r, c).paragraphs[0]
        for text, font in runs:
            docx_font(p.add_run(text), font)
    if ttf:
        embed_docx(doc, ttf)
    doc.save(str(path))
    return path


def test_pptx_findings(tmp_path, manifest, built):
    findings = check_file(make_pptx(tmp_path / "t.pptx", built["ttf"]), manifest)
    assert _rules(findings, "row 2, column 1") == ["silent-symbol"]
    assert _rules(findings, "row 2, column 2") == []
    assert _rules(findings, "row 2, column 3") == []
    assert _rules(findings, "row 3, column 1") == ["prefer-standard"]
    assert _rules(findings, "row 3, column 2") == ["font-not-applied"]
    assert _rules(findings, "row 3, column 3") == []
    assert "no-header-row" not in _rules(findings) and "font-not-embedded" not in _rules(findings)


def test_docx_findings(tmp_path, manifest, built):
    findings = check_file(make_docx(tmp_path / "t.docx", built["ttf"]), manifest)
    assert _rules(findings, "row 2, column 1") == ["silent-symbol"]
    assert _rules(findings, "row 2, column 2") == []
    assert _rules(findings, "row 2, column 3") == []
    assert _rules(findings, "row 3, column 1") == ["prefer-standard"]
    assert _rules(findings, "row 3, column 2") == ["font-not-applied"]
    assert "no-header-row" not in _rules(findings) and "font-not-embedded" not in _rules(findings)


def test_missing_header_and_embedding_are_reported(tmp_path, manifest):
    for path in (make_pptx(tmp_path / "t.pptx", header=False), make_docx(tmp_path / "t.docx", header=False)):
        rules = _rules(check_file(path, manifest))
        assert "no-header-row" in rules and "font-not-embedded" in rules, path


def test_accessible_scorecard_slide_is_clean(tmp_path, manifest, built):
    from slidemarks_build import specimen_pptx
    deck = tmp_path / "specimen.pptx"
    specimen_pptx.render(manifest, built["ttf"], deck)
    titles = [next(sh.text_frame.paragraphs[0].text for sh in slide.shapes if sh.has_text_frame)
              for slide in Presentation(str(deck)).slides]
    n = next(i for i, t in enumerate(titles, start=1) if t.startswith("Accessible scorecard"))
    assert [f for f in check_file(deck, manifest) if f.location.startswith(f"slide {n},")] == []
