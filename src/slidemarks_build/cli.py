"""`slidemarks build` compiles the font and regenerates both review specimens."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import specimen_docx, specimen_html, specimen_pptx
from .font import build_font
from .manifest import validate
from .metrics import measure

ROOT = Path(__file__).resolve().parents[2]


def build(args) -> int:
    tokens = json.loads((ROOT / "source/design-tokens.json").read_text())
    manifest = json.loads((ROOT / "source/symbols.json").read_text())
    errors = validate(manifest)
    if errors:
        for e in errors:
            print(f"manifest error: {e}", file=sys.stderr)
        return 1

    dist = ROOT / "dist"
    out = build_font(tokens, manifest, dist)
    records = measure(out["ttf"], tokens, manifest)

    review = ROOT / "review"
    info = {"built": datetime.now().strftime("%Y-%m-%d %H:%M")}
    specimen_html.render(tokens, manifest, records, out["woff2"], out["svg_paths"], review / "specimen.html", info)
    specimen_pptx.render(manifest, out["ttf"], review / "specimen.pptx")
    specimen_docx.render(manifest, out["ttf"], review / "specimen.docx")

    findings = [(r["id"], f) for r in records for f in r["findings"]]
    print(f"built {len(records)} glyphs → {out['ttf'].relative_to(ROOT)}, {out['woff2'].relative_to(ROOT)}")
    print("review → review/specimen.html, review/specimen.pptx, review/specimen.docx")
    for gid, f in findings:
        print(f"  ! {gid}: {f}")
    print(f"{len(findings)} consistency findings")
    return 1 if (findings and args.strict) else 0


def main():
    parser = argparse.ArgumentParser(prog="slidemarks")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="compile font and regenerate review specimens")
    b.add_argument("--strict", action="store_true", help="exit non-zero if any consistency finding")
    b.set_defaults(func=build)
    args = parser.parse_args()
    sys.exit(args.func(args))
