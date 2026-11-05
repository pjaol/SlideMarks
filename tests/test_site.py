"""Public site assembly (dist/site/): pages, production manifest, relative links."""

import re
import shutil
import zipfile
from pathlib import Path

from slidemarks_build import office, site

REPO = Path(__file__).resolve().parents[1]
BASE = "https://pjaol.github.io/SlideMarks"


def test_site_is_complete_and_folder_safe(tmp_path, tokens, manifest, built):
    root = tmp_path / "repo"
    shutil.copytree(REPO / "apps/office", root / "apps/office")
    shutil.copytree(REPO / "installers", root / "installers")
    office.build(root, tokens, manifest, built["woff2"], built["ttf"], prod_base_url=f"{BASE}/office")
    (root / "dist/fonts").mkdir(parents=True)
    shutil.copy(built["ttf"], root / "dist/fonts")
    shutil.copytree(REPO / "docs/glyphs", root / "docs/glyphs")
    shutil.copy(REPO / "docs/preview.svg", root / "docs/preview.svg")
    shutil.copytree(REPO / "docs/images", root / "docs/images")
    zip_path = root / "dist/SlideMarks-test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("SlideMarks-test/SHA256SUMS", "abc  fonts/SlideMarks-Regular.ttf\n")

    out = site.build(root, manifest, zip_path, BASE)

    for page in ["index.html", "glyphs/index.html", "support/index.html", "privacy/index.html",
                 "terms/index.html", "picker/index.html", "office/taskpane.html", "office/picker.html", ".nojekyll", "install.sh", "install.ps1"]:
        assert (out / page).exists(), page
    assert not (out / "office/manifest.dev.xml").exists()  # never publish the localhost manifest
    xml = (out / "office/manifest.xml").read_text()
    assert f"{BASE}/office/taskpane.html" in xml and "localhost" not in xml
    for html in out.rglob("*.html"):
        # Root-relative links would break under /SlideMarks/; everything must be relative or absolute https.
        assert not re.search(r'(href|src)="/(?!/)', html.read_text()), html
    assert (out / "download/SlideMarks-Regular.ttf").exists() and (out / "download/SHA256SUMS").exists()
    support = (out / "support/index.html").read_text()
    for anchor in ["after-install", "mac-access", "uninstall", "manual"]:  # the installers link to these
        assert f'id="{anchor}"' in support, anchor
    assert (out / "office/assets/walkthrough/word-mac-addins.png").exists()


def test_windows_network_path_keeps_both_leading_backslashes():
    from slidemarks_build.site import _support
    assert r"\\YOUR-PC\SlideMarks" in _support(BASE)  # a UNC path needs two leading backslashes
