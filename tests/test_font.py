from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from slidemarks_build.font import build_font, glyph_name
from slidemarks_build.metrics import measure


def test_every_pua_code_point_is_mapped(built, manifest):
    cmap = TTFont(str(built["ttf"])).getBestCmap()
    for s in manifest["symbols"]:
        assert cmap[int(s["codepoint"], 16)] == glyph_name(s["id"])


def test_aliases_draw_the_identical_outline(built, manifest):
    font = TTFont(str(built["ttf"]))
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()

    def outline(cp):
        pen = RecordingPen()
        glyphs[cmap[cp]].draw(pen)
        return pen.value

    aliased = [s for s in manifest["symbols"] if s["unicodeAliases"]]
    assert aliased
    for s in aliased:
        for a in s["unicodeAliases"]:
            assert cmap[int(a, 16)] == cmap[int(s["codepoint"], 16)], s["id"]
            assert outline(int(a, 16)) == outline(int(s["codepoint"], 16)), s["id"]


def test_aliases_add_no_glyphs(built, manifest):
    # .notdef + space + one glyph per symbol; aliases reuse glyphs
    assert len(TTFont(str(built["ttf"])).getGlyphOrder()) == len(manifest["symbols"]) + 2


def test_build_is_reproducible(tokens, manifest, built, tmp_path):
    again = build_font(tokens, manifest, tmp_path)
    assert again["ttf"].read_bytes() == built["ttf"].read_bytes()


def test_no_consistency_findings(built, tokens, manifest):
    findings = [(r["id"], f) for r in measure(built["ttf"], tokens, manifest) for f in r["findings"]]
    assert findings == []
