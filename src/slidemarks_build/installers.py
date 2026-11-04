"""One-step installers: install.sh (Mac) and install.ps1 (Windows) for the website, and a
signed, notarized SlideMarks.pkg for Mac. Templates live in installers/."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from .office import ADDIN_ID, icon_png

PKG_ID = "io.github.pjaol.slidemarks"
SCRIPTS = ("install.sh", "install.ps1")


def render(text: str, base_url: str, **extra) -> str:
    values = {"BASE_URL": base_url.rstrip("/"), "ADDIN_ID": ADDIN_ID, **extra}
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    if "{{" in text:
        raise ValueError(f"unfilled placeholder in installer template: {text[text.index('{{'):][:40]}")
    return text


def write_scripts(root: Path, out: Path, base_url: str) -> None:
    for name in SCRIPTS:
        dest = out / name
        dest.write_text(render((root / "installers" / name).read_text(), base_url), newline="\n")
        dest.chmod(0o755)


LOGO_POINTS = 96  # Harvey-ball logo in the installer window's bottom-left corner


def build_pkg(root: Path, tokens, manifest, ttf: Path, office_manifest: Path, base_url: str, out: Path,
              sign: str | None = None) -> Path:
    """Scripts-only package: postinstall runs install.sh --from with the bundled font and manifest."""
    version = manifest["manifestVersion"]
    src = root / "installers/pkg"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        scripts = tmp / "scripts"
        scripts.mkdir()
        (scripts / "postinstall").write_text(render((src / "postinstall").read_text(), base_url))
        write_scripts(root, scripts, base_url)
        (scripts / "install.ps1").unlink()
        shutil.copy(ttf, scripts / "SlideMarks-Regular.ttf")
        shutil.copy(office_manifest, scripts / "manifest.xml")
        for f in scripts.iterdir():
            f.chmod(0o755 if f.suffix in ("", ".sh") else 0o644)

        resources = tmp / "resources"
        resources.mkdir()
        for page in ("welcome.html", "conclusion.html"):
            (resources / page).write_text(render((src / page).read_text(), base_url, VERSION=version))
        # Installer takes one image; a two-resolution TIFF stays sharp on Retina screens.
        for scale in (1, 2):
            (tmp / f"logo@{scale}x.png").write_bytes(icon_png(tokens, manifest, LOGO_POINTS * scale))
        subprocess.run(["tiffutil", "-cathidpicheck", str(tmp / "logo@1x.png"), str(tmp / "logo@2x.png"),
                        "-out", str(resources / "logo.tiff")], check=True, capture_output=True)
        dist_xml = tmp / "distribution.xml"
        dist_xml.write_text(render((src / "distribution.xml").read_text(), base_url, PKG_ID=PKG_ID, VERSION=version))

        subprocess.run(["pkgbuild", "--nopayload", "--scripts", str(scripts), "--identifier", PKG_ID,
                        "--version", version, str(tmp / "slidemarks.pkg")], check=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["productbuild", "--distribution", str(dist_xml), "--resources", str(resources),
               "--package-path", str(tmp)]
        if sign:
            cmd += ["--sign", sign, "--timestamp"]
        subprocess.run([*cmd, str(out)], check=True)
    return out


def notarize(pkg: Path, keychain_profile: str) -> None:
    subprocess.run(["xcrun", "notarytool", "submit", str(pkg), "--keychain-profile", keychain_profile, "--wait"], check=True)
    subprocess.run(["xcrun", "stapler", "staple", str(pkg)], check=True)
