import re

from slidemarks_build.manifest import preferred_codepoint
import json

from slidemarks_build.web import render_css, render_example, symbol_data


def test_css_matches_manifest_and_is_decorative(manifest, tmp_path):
    css = tmp_path / "slidemarks.css"
    render_css(manifest, css)
    rules = dict(re.findall(r"^\.sm-([\w-]+)::before \{ (.+) \}$", css.read_text(), re.M))
    assert set(rules) == {s["id"] for s in manifest["symbols"]}
    for s in manifest["symbols"]:
        cp = preferred_codepoint(s)
        # fallback for browsers without CSS alt text, then empty alt text (decorative)
        assert rules[s["id"]] == f'content: "\\{cp}"; content: "\\{cp}" / "";', s["id"]


def test_css_has_no_speech_properties(manifest, tmp_path):
    css = tmp_path / "slidemarks.css"
    render_css(manifest, css)
    assert "speak" not in css.read_text()  # CSS Speech is unimplemented; empty alt text does the job


def test_symbol_data_matches_manifest(manifest):
    data = json.loads(json.dumps(symbol_data(manifest)))
    assert set(data["symbols"]) == {s["id"] for s in manifest["symbols"]}
    for s in manifest["symbols"]:
        d = data["symbols"][s["id"]]
        assert d["spokenLabel"] == s["spokenLabel"]
        assert d["char"] == chr(int(preferred_codepoint(s), 16))
        assert d["puaCodepoint"] == f"U+{s['codepoint']}"
        assert d["cssClass"] == f"sm-{s['id']}"


def test_example_names_meaningful_symbols(manifest, tmp_path):
    page = tmp_path / "example.html"
    render_example(manifest, page)
    html = page.read_text()
    assert 'role="img" aria-label="Harvey ball 75 percent"' in html
    assert 'aria-label="rising trend"' in html
    assert '<th scope="col">' in html
