"""Standalone picker (dist/office/picker.html) driven through agent-browser.
Skipped where agent-browser isn't installed."""

import functools
import http.server
import json
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

from slidemarks_build import office

pytestmark = pytest.mark.skipif(shutil.which("agent-browser") is None, reason="agent-browser not installed")
SESSION = "slidemarks-picker-tests"
REPO = Path(__file__).resolve().parents[1]


def _ab(*args):
    out = subprocess.run(["agent-browser", "--session", SESSION, *args, "--json"],
                         capture_output=True, text=True, timeout=60, check=True).stdout
    return json.loads(out)["data"]


def _eval(js):
    return json.loads(_ab("eval", f"JSON.stringify({js})")["result"])


@pytest.fixture(scope="module")
def picker(tmp_path_factory, tokens, manifest, built):
    root = tmp_path_factory.mktemp("repo")
    shutil.copytree(REPO / "apps/office", root / "apps/office")
    out = office.build(root, tokens, manifest, built["woff2"], built["ttf"])
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _ab("open", f"http://127.0.0.1:{server.server_address[1]}/picker.html")
    _ab("eval", "localStorage.clear()")
    _ab("reload")
    _ab("wait", "400")
    yield
    server.shutdown()
    subprocess.run(["agent-browser", "--session", SESSION, "close"], capture_output=True)


def test_lists_every_symbol(picker, manifest):
    assert _eval("document.querySelectorAll('#grid [role=option]').length") == len(manifest["symbols"])


def test_search_finds_by_meaning_and_code_point(picker):
    _ab("fill", "#q", "harvey 75")
    assert _eval("[...document.querySelectorAll('#grid [role=option]')].map(o => o.dataset.id)") == ["harvey-75"]
    _ab("fill", "#q", "u+2192")
    assert _eval("[...document.querySelectorAll('#grid [role=option]')].map(o => o.dataset.id)") == ["arrow-right"]
    _ab("fill", "#q", "")


def test_preview_explains_standard_character(picker):
    _ab("fill", "#q", "right arrow")
    assert "U+2192" in _eval("document.getElementById('pv-meta').innerText")
    _ab("fill", "#q", "")


def test_keyboard_navigation_and_copy_records_recent(picker):
    _ab("select", "#family", "status")
    _ab("focus", "#opt-status-check")
    _ab("press", "ArrowRight")
    assert _eval("document.activeElement.dataset.id") == "status-cross"
    _ab("press", "Enter")  # Enter copies on the standalone page
    _ab("wait", "200")
    assert "Copied Cross" in _eval("document.getElementById('toast').textContent")
    assert _eval("JSON.parse(localStorage.getItem('slidemarks.recent'))")[0] == "status-cross"
    _ab("select", "#family", "")


def test_no_insert_button_outside_office(picker):
    assert _eval("getComputedStyle(document.getElementById('pv-insert')).display") == "none"


def test_passes_axe(picker):
    result = _ab("a11y")
    assert [v["id"] for v in result["violations"]] == []


def test_copy_puts_formatted_html_and_plain_text_on_the_clipboard(picker):
    # Capture what the page hands to the clipboard (no system clipboard permission needed).
    _ab("eval", """window.__clip = null;
      navigator.clipboard.write = async (items) => {
        const item = items[0];
        window.__clip = { types: item.types,
          html: await (await item.getType('text/html')).text(),
          text: await (await item.getType('text/plain')).text() };
      }; 1""")
    _ab("fill", "#q", "harvey 75")
    _ab("click", "#pv-copy")
    _ab("wait", "200")
    clip = _eval("window.__clip")
    assert set(clip["types"]) == {"text/html", "text/plain"}
    assert clip["text"] == "\ue003"
    # Word only sets the East Asian slot (which it draws these characters from) via mso-fareast-font-family.
    for prop in ["font-family:SlideMarks", "mso-fareast-font-family:SlideMarks", "mso-ascii-font-family:SlideMarks"]:
        assert prop in clip["html"]
    _ab("fill", "#q", "")
