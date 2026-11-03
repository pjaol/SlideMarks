"""Release zip: everything a user needs, no Python or Node required (PRD F-11)."""

import hashlib
import zipfile
from pathlib import Path

FIXED_DATE = (2026, 1, 1, 0, 0, 0)  # deterministic zip entries

USER_README = """SlideMarks {version}

fonts/SlideMarks-Regular.ttf   Install this font (Windows: right-click > Install;
                               macOS: double-click > Install Font).
web/                           SlideMarks-Regular.woff2 + slidemarks.css for websites.
svg/                           One SVG per glyph, for design tools.
glyphs.md                      Every glyph with its name and code point.
SHA256SUMS                     Checksums for the files above.

Full instructions: https://github.com/pjaol/SlideMarks#readme
"""


def build_zip(root: Path, manifest) -> Path:
    version = manifest["manifestVersion"]
    dist = root / "dist"
    files = sorted(p for sub in ("fonts", "web", "svg") for p in (dist / sub).rglob("*") if p.is_file())
    entries = {f"{p.relative_to(dist)}": p.read_bytes() for p in files}
    entries["glyphs.md"] = (root / "docs/glyphs.md").read_text().replace("](glyphs/", "](svg/").replace('src="glyphs/', 'src="svg/').encode()
    entries["README.txt"] = USER_README.format(version=version).encode()
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(entries.items()))
    entries["SHA256SUMS"] = sums.encode()

    out = dist / f"SlideMarks-{version}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(entries):
            info = zipfile.ZipInfo(f"SlideMarks-{version}/{name}", FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, entries[name])
    return out
