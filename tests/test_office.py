"""Office add-in build: manifest, catalog data, icons, pages."""

import json
import struct
import xml.etree.ElementTree as ET

import pytest

from slidemarks_build import office

NS = {"o": "http://schemas.microsoft.com/office/appforoffice/1.1"}


def test_manifest_is_wellformed_and_points_at_base_url(manifest):
    xml = office.manifest_xml(manifest, "https://office.example.org/")
    root = ET.fromstring(xml.encode())
    assert root.find("o:Id", NS).text == office.ADDIN_ID
    assert root.find("o:DefaultSettings/o:SourceLocation", NS).get("DefaultValue") == "https://office.example.org/taskpane.html"
    assert {h.get("Name") for h in root.findall("o:Hosts/o:Host", NS)} == {"Presentation", "Document"}
    assert "https://localhost" not in xml


def test_manifest_version_is_at_least_one(manifest):
    root = ET.fromstring(office.manifest_xml(manifest, office.DEV_BASE_URL).encode())
    major = int(root.find("o:Version", NS).text.split(".")[0])
    assert major >= 1  # Office rejects add-in versions below 1.0


def test_catalog_data_covers_every_symbol(manifest):
    data = office.catalog_data(manifest)
    assert [s["id"] for s in data["symbols"]] == [s["id"] for s in manifest["symbols"]]
    by_id = {s["id"]: s for s in data["symbols"]}
    assert by_id["arrow-right"]["char"] == "→"  # preferred standard character
    assert by_id["harvey-75"]["char"] == ""
    assert all(s["label"] for s in data["symbols"])


@pytest.mark.parametrize("size", office.ICON_SIZES)
def test_icons_are_valid_rgba_pngs(tokens, manifest, size):
    png = office.icon_png(tokens, manifest, size)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    width, height, depth, colour = struct.unpack(">IIBB", png[16:26])
    assert (width, height, depth, colour) == (size, size, 8, 6)


def test_build_writes_both_pages_and_manifests(tmp_path, tokens, manifest, built):
    root = tmp_path / "repo"
    (root / "apps").mkdir(parents=True)
    import shutil
    from pathlib import Path
    repo = Path(__file__).resolve().parents[1]
    shutil.copytree(repo / "apps/office", root / "apps/office")
    out = office.build(root, tokens, manifest, built["woff2"], built["ttf"], prod_base_url="https://office.example.org")
    taskpane, picker = (out / "taskpane.html").read_text(), (out / "picker.html").read_text()
    assert "appsforoffice.microsoft.com/lib/1/hosted/office.js" in taskpane and 'data-mode="office"' in taskpane
    assert "office.js" not in picker and 'data-mode="browser"' in picker  # standalone page works offline
    assert (out / "manifest.dev.xml").exists() and (out / "manifest.xml").exists()
    data = json.loads((out / "js/catalog-data.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
    assert len(data["symbols"]) == len(manifest["symbols"])
    assert (out / "fonts/SlideMarks-Regular.ttf").exists()
