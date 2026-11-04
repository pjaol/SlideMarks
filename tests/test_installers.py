"""One-step installers: install.sh run against a fake home folder, install.ps1 parsed by PowerShell
where it's available (GitHub's Ubuntu runners have pwsh), and the Mac package on macOS."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from slidemarks_build import installers, office

REPO = Path(__file__).resolve().parents[1]
BASE = "https://pjaol.github.io/SlideMarks"


@pytest.fixture
def scripts(tmp_path):
    out = tmp_path / "site"
    out.mkdir()
    installers.write_scripts(REPO, out, BASE + "/")
    return out


def test_scripts_point_at_the_site_and_the_add_in(scripts):
    for name in installers.SCRIPTS:
        text = (scripts / name).read_text()
        assert f"{BASE}/install.{name.split('.')[1]}" in text  # usage line shows the real command
        assert "/office/manifest.xml" in text and "/download/SlideMarks-Regular.ttf" in text
        assert office.ADDIN_ID in text and "{{" not in text and "//install" not in text


def test_unfilled_placeholder_is_an_error():
    with pytest.raises(ValueError):
        installers.render("{{NOPE}}", BASE)


def _run_sh(scripts, home, *args):
    return subprocess.run(["/bin/sh", str(scripts / "install.sh"), *args], env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
                          capture_output=True, text=True, check=True).stdout


def test_install_sh_installs_font_and_add_in_then_uninstalls(scripts, tmp_path, built):
    home = tmp_path / "home"
    containers = home / "Library/Containers"
    (containers / "com.microsoft.Powerpoint").mkdir(parents=True)  # PowerPoint installed, Word not
    stale = containers / "com.microsoft.Powerpoint/Data/Documents/wef" / f"{office.ADDIN_ID}.manifest.dev.xml"
    stale.parent.mkdir(parents=True)
    stale.write_text("dev")
    src = tmp_path / "bundle"
    src.mkdir()
    shutil.copy(built["ttf"], src / "SlideMarks-Regular.ttf")
    (src / "manifest.xml").write_text("<OfficeApp/>")

    out = _run_sh(scripts, home, "--from", str(src))
    assert (home / "Library/Fonts/SlideMarks-Regular.ttf").read_bytes() == built["ttf"].read_bytes()
    assert [p.name for p in stale.parent.iterdir()] == [f"{office.ADDIN_ID}.SlideMarks.xml"]  # dev copy replaced
    assert not (containers / "com.microsoft.Word").exists()  # never creates another app's container
    assert "Word not found" in out and "Add-in added to PowerPoint" in out

    _run_sh(scripts, home, "uninstall")
    assert not (home / "Library/Fonts/SlideMarks-Regular.ttf").exists()
    assert list(stale.parent.iterdir()) == []


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="PowerShell not installed")
def test_install_ps1_parses(scripts):
    check = ("$errors = $null; [System.Management.Automation.Language.Parser]::ParseFile("
             f"'{scripts / 'install.ps1'}', [ref]$null, [ref]$errors) | Out-Null; "
             "if ($errors) { $errors | ForEach-Object { Write-Error $_.Message }; exit 1 }")
    subprocess.run(["pwsh", "-NoProfile", "-Command", check], check=True)


def test_install_ps1_never_force_recreates_an_existing_registry_key(scripts):
    # New-Item -Force on an existing key replaces it, wiping the user's other fonts or add-ins.
    for line in (scripts / "install.ps1").read_text().splitlines():
        if "New-Item -Path $" in line:
            assert line.startswith("if (-not (Test-Path "), line


@pytest.mark.skipif(sys.platform != "darwin", reason="pkgbuild is macOS-only")
def test_unsigned_pkg_bundles_installer_font_and_manifest(tmp_path, tokens, manifest, built):
    xml = tmp_path / "manifest.xml"
    xml.write_text("<OfficeApp/>")
    pkg = installers.build_pkg(REPO, tokens, manifest, built["ttf"], xml, BASE, tmp_path / "SlideMarks.pkg")
    expanded = tmp_path / "expanded"
    subprocess.run(["pkgutil", "--expand", str(pkg), str(expanded)], check=True)
    scripts = expanded / "slidemarks.pkg/Scripts"
    assert sorted(p.name for p in scripts.iterdir()) == ["SlideMarks-Regular.ttf", "install.sh", "manifest.xml", "postinstall"]
    postinstall = (scripts / "postinstall").read_text()
    assert "--from" in postinstall and f"{BASE}/$page" in postinstall and "{{" not in postinstall
    resources = expanded / "Resources"
    assert {"welcome.html", "conclusion.html", "logo.tiff"} <= {p.name for p in resources.iterdir()}
    assert manifest["manifestVersion"] in (resources / "welcome.html").read_text()


def test_install_sh_reports_apps_macos_blocked_and_still_adds_the_others(scripts, tmp_path, built):
    # "Don't Allow" on macOS's app-data prompt makes writes into that app's container fail; a read-only folder does the same.
    home = tmp_path / "home"
    containers = home / "Library/Containers"
    (containers / "com.microsoft.Powerpoint").mkdir(parents=True)
    word_wef = containers / "com.microsoft.Word/Data/Documents/wef"
    word_wef.mkdir(parents=True)
    word_wef.chmod(0o555)
    src = tmp_path / "bundle"
    src.mkdir()
    shutil.copy(built["ttf"], src / "SlideMarks-Regular.ttf")
    (src / "manifest.xml").write_text("<OfficeApp/>")
    try:
        run = subprocess.run(["/bin/sh", str(scripts / "install.sh"), "--from", str(src)], env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
                             capture_output=True, text=True)
    finally:
        word_wef.chmod(0o755)
    assert run.returncode == 3  # the Mac package opens the support page at #mac-access for this
    assert "Add-in added to PowerPoint" in run.stdout
    assert "didn't allow adding the add-in to: Word" in run.stderr and "#mac-access" in run.stderr
    assert (home / "Library/Fonts/SlideMarks-Regular.ttf").exists()
