"""`slidemarks check`: accessibility and rendering lint for PowerPoint and Word files.

Screen readers read characters, so the useful checks are mechanical: is a SlideMarks
symbol the only content of a cell (silent to screen readers), is a PUA code point used
where a standard character would be announced, is the symbol's run set to the
SlideMarks font, and is the font embedded for recipients. See docs/accessibility.md."""

from dataclasses import asdict, dataclass
from pathlib import Path

from docx import Document
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn as pqn
from docx.oxml.ns import qn as wqn

from .font import FAMILY

ERROR, WARNING = "error", "warning"


@dataclass
class Finding:
    severity: str
    rule: str
    location: str
    message: str


class Glyphs:
    """Lookup of SlideMarks characters from the manifest."""

    def __init__(self, manifest):
        self.pua = {chr(int(s["codepoint"], 16)): s for s in manifest["symbols"]}
        self.alias = {chr(int(a, 16)): s for s in manifest["symbols"] for a in s["unicodeAliases"]}

    def is_pua(self, ch):
        return 0xE000 <= ord(ch) <= 0xF8FF

    def describe(self, text):
        return "".join(f"[{self.pua[c]['spokenLabel']}]" if c in self.pua else c for c in text).strip()


def _check_runs(glyphs, runs, location, findings):
    """runs: list of (text, explicit_fonts) for one cell or paragraph."""
    text = "".join(t for t, _ in runs)
    pua = [c for c in text if glyphs.is_pua(c)]
    if not pua:
        return False
    if not "".join(c for c in text if not glyphs.is_pua(c)).strip():
        findings.append(Finding(ERROR, "silent-symbol", location,
                                f"only SlideMarks symbols, no readable text: {glyphs.describe(text)!r}. "
                                "Add visible text (e.g. the value) so screen readers get the meaning"))
    for t, fonts in runs:
        if fonts and FAMILY not in fonts and any(glyphs.is_pua(c) for c in t):
            findings.append(Finding(ERROR, "font-not-applied", location,
                                    f"SlideMarks symbol in a run set to {', '.join(sorted(fonts))}; it will show as an empty box"))
    for c in dict.fromkeys(pua):
        sym = glyphs.pua.get(c)
        if sym is None:
            findings.append(Finding(WARNING, "unknown-code-point", location,
                                    f"U+{ord(c):04X} is a private-use character SlideMarks doesn't define"))
        elif sym["unicodeAliases"]:
            alias = sym["unicodeAliases"][0]
            findings.append(Finding(WARNING, "prefer-standard", location,
                                    f"{sym['name']} uses U+{ord(c):04X}; use the standard character U+{alias} "
                                    f"({chr(int(alias, 16))}) so screen readers announce it"))
    return True


# ── PowerPoint ───────────────────────────────────────────────────────────────

def _pptx_run_fonts(r):
    rpr = r._r.find(pqn("a:rPr"))
    if rpr is None:
        return set()
    return {el.get("typeface") for tag in ("a:latin", "a:ea", "a:cs", "a:sym")
            if (el := rpr.find(pqn(tag))) is not None and el.get("typeface")}


def _pptx_runs(paragraphs):
    return [(r.text, _pptx_run_fonts(r)) for p in paragraphs for r in p.runs]


def _pptx_shapes(shapes):
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _pptx_shapes(shape.shapes)
        else:
            yield shape


def check_pptx(path: Path, glyphs: Glyphs) -> list[Finding]:
    prs = Presentation(str(path))
    findings, used = [], False
    for n, slide in enumerate(prs.slides, start=1):
        tables = 0
        for shape in _pptx_shapes(slide.shapes):
            if shape.has_table:
                tables += 1
                table_used = False
                for r, row in enumerate(shape.table.rows, start=1):
                    for c, cell in enumerate(row.cells, start=1):
                        loc = f"slide {n}, table {tables}, row {r}, column {c}"
                        table_used |= _check_runs(glyphs, _pptx_runs(cell.text_frame.paragraphs), loc, findings)
                if table_used and shape.table._tbl.tblPr.get("firstRow") != "1":
                    findings.append(Finding(WARNING, "no-header-row", f"slide {n}, table {tables}",
                                            "table uses SlideMarks but has no header row (Table Design → Header Row)"))
                used |= table_used
            elif shape.has_text_frame:
                for i, p in enumerate(shape.text_frame.paragraphs, start=1):
                    loc = f"slide {n}, '{shape.name}', paragraph {i}"
                    used |= _check_runs(glyphs, _pptx_runs([p]), loc, findings)
    if used:
        embedded = prs.part._element.find(pqn("p:embeddedFontLst"))
        names = {f.get("typeface") for f in embedded.iter(pqn("p:font"))} if embedded is not None else set()
        if FAMILY not in names:
            findings.append(Finding(WARNING, "font-not-embedded", "presentation",
                                    "SlideMarks isn't embedded; recipients without the font see empty boxes "
                                    "(Preferences/Options → Save → Embed fonts in the file)"))
    return findings


# ── Word ─────────────────────────────────────────────────────────────────────

def _docx_run_fonts(r):
    rpr = r._r.rPr
    fonts = rpr.find(wqn("w:rFonts")) if rpr is not None else None
    if fonts is None:
        return set()
    return {fonts.get(wqn(a)) for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs") if fonts.get(wqn(a))}


def _docx_runs(paragraphs):
    return [(r.text, _docx_run_fonts(r)) for p in paragraphs for r in p.runs]


def _docx_tables(tables, prefix, glyphs, findings):
    used = False
    for t, table in enumerate(tables, start=1):
        name = f"{prefix}table {t}"
        table_used = False
        for r, row in enumerate(table.rows, start=1):
            for c, cell in enumerate(row.cells, start=1):
                loc = f"{name}, row {r}, column {c}"
                table_used |= _check_runs(glyphs, _docx_runs(cell.paragraphs), loc, findings)
                table_used |= _docx_tables(cell.tables, f"{loc}, nested ", glyphs, findings)
        if table_used:
            first = table.rows[0]._tr
            trpr = first.trPr
            if trpr is None or trpr.find(wqn("w:tblHeader")) is None:
                findings.append(Finding(WARNING, "no-header-row", name,
                                        "table uses SlideMarks but its first row isn't marked as a header "
                                        "(Table Properties → Row → Repeat as header row)"))
        used |= table_used
    return used


def check_docx(path: Path, glyphs: Glyphs) -> list[Finding]:
    doc = Document(str(path))
    findings = []
    used = False
    for i, p in enumerate(doc.paragraphs, start=1):
        used |= _check_runs(glyphs, _docx_runs([p]), f"paragraph {i}", findings)
    used |= _docx_tables(doc.tables, "", glyphs, findings)
    if used:
        font_table = next((p for p in doc.part.package.iter_parts() if p.partname == "/word/fontTable.xml"), None)
        blob = font_table.blob.decode("utf-8", "ignore") if font_table is not None else ""
        if f'w:name="{FAMILY}"' not in blob or "w:embedRegular" not in blob:
            findings.append(Finding(WARNING, "font-not-embedded", "document",
                                    "SlideMarks isn't embedded; recipients without the font see empty boxes "
                                    "(Preferences/Options → Save → Embed fonts in the file)"))
    return findings


def check_file(path: Path, manifest) -> list[Finding]:
    glyphs = Glyphs(manifest)
    suffix = path.suffix.lower()
    if suffix == ".pptx":
        return check_pptx(path, glyphs)
    if suffix == ".docx":
        return check_docx(path, glyphs)
    raise ValueError(f"{path}: only .pptx and .docx are supported")


def as_dicts(findings):
    return [asdict(f) for f in findings]
