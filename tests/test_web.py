import re

from slidemarks_build.manifest import preferred_codepoint
from slidemarks_build.web import render_css


def test_css_matches_manifest_and_is_decorative(manifest, tmp_path):
    css = tmp_path / "slidemarks.css"
    render_css(manifest, css)
    rules = dict(re.findall(r"^\.sm-([\w-]+)::before \{ (.+) \}$", css.read_text(), re.M))
    assert set(rules) == {s["id"] for s in manifest["symbols"]}
    for s in manifest["symbols"]:
        cp = preferred_codepoint(s)
        # fallback for browsers without CSS alt text, then empty alt text (decorative)
        assert rules[s["id"]] == f'content: "\\{cp}"; content: "\\{cp}" / "";', s["id"]
