"""Browser accessibility checks via agent-browser (already used for visual review):
what Chrome exposes to assistive technology, plus an axe-core audit.
Skipped where agent-browser isn't installed."""

import functools
import http.server
import json
import re
import shutil
import subprocess
import threading
from html import escape

import pytest

from slidemarks_build.web import render_css, render_example

pytestmark = pytest.mark.skipif(shutil.which("agent-browser") is None, reason="agent-browser not installed")

SESSION = "slidemarks-a11y-tests"
PUA = re.compile("[-]")


def _ab(*args):
    out = subprocess.run(["agent-browser", "--session", SESSION, *args, "--json"],
                         capture_output=True, text=True, timeout=60, check=True).stdout
    return json.loads(out)["data"]


@pytest.fixture(scope="module")
def site(built, manifest, tmp_path_factory):
    root = tmp_path_factory.mktemp("site")
    shutil.copy(built["woff2"], root)
    render_css(manifest, root / "slidemarks.css")
    render_example(manifest, root / "example.html")
    decorative = "".join(f'<span class="slidemarks sm-{s["id"]}"></span>' for s in manifest["symbols"])
    named = "".join(f'<span class="slidemarks sm-{s["id"]}" role="img" aria-label="{escape(s["spokenLabel"])}"></span>'
                    for s in manifest["symbols"])
    (root / "all.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>All glyphs</title>'
        '<link rel="stylesheet" href="slidemarks.css"></head><body><main><h1>All glyphs</h1>'
        f'<p id="decorative">{decorative}</p><p id="named">{named}</p></main></body></html>', encoding="utf-8")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    subprocess.run(["agent-browser", "--session", SESSION, "close"], capture_output=True)


def _tree(url):
    _ab("open", url)
    _ab("wait", "500")
    return _ab("snapshot")["snapshot"]


def test_decorative_classes_expose_nothing(site):
    # Class-only glyphs rely on the CSS empty alt text: no PUA characters, no images.
    tree = _tree(f"{site}/all.html")
    decorative = tree.split('heading "All glyphs"')[1].split("image")[0]
    assert not PUA.search(tree), "a private-use character reached the accessibility tree"
    assert "StaticText" not in decorative


def test_named_glyphs_expose_their_spoken_label(site, manifest):
    tree = _tree(f"{site}/all.html")
    names = re.findall(r'image "([^"]*)"', tree)
    assert names == [s["spokenLabel"] for s in manifest["symbols"]]


def test_example_page_passes_axe(site):
    _ab("open", f"{site}/example.html")
    result = _ab("a11y")
    assert [v["id"] for v in result["violations"]] == []
    assert result["counts"]["incomplete"] == 0


def test_example_table_cells_carry_text(site):
    tree = _tree(f"{site}/example.html")
    assert 'cell " 75%"' in tree and 'cell "rising trend"' in tree
    assert 'columnheader "Coverage"' in tree and 'rowheader "Offline use"' in tree
