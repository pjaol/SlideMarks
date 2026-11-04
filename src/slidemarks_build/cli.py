"""`slidemarks build` compiles the font, web package, glyph reference and review
specimens; `slidemarks package` also writes the release zip."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import check, office, package, reference, screen_readers, specimen_docx, specimen_html, specimen_pptx, web
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
    web.render_css(manifest, dist / "web" / "slidemarks.css")
    web.render_json(manifest, dist / "web" / "slidemarks.json")
    web.render_example(manifest, dist / "web" / "example.html")
    reference.render(tokens, manifest, out["svg_paths"], ROOT / "docs")
    screen_readers.render(manifest, dist / "screen-readers")
    office.build(ROOT, tokens, manifest, out["woff2"], out["ttf"], prod_base_url=getattr(args, "office_base_url", None))

    review = ROOT / "review"
    info = {"built": datetime.now().strftime("%Y-%m-%d %H:%M")}
    specimen_html.render(tokens, manifest, records, out["woff2"], out["svg_paths"], review / "specimen.html", info)
    specimen_pptx.render(manifest, out["ttf"], review / "specimen.pptx")
    specimen_docx.render(manifest, out["ttf"], review / "specimen.docx")

    findings = [(r["id"], f) for r in records for f in r["findings"]]
    print(f"built {len(records)} glyphs → {out['ttf'].relative_to(ROOT)}, {out['woff2'].relative_to(ROOT)}")
    print("web → dist/web/ (slidemarks.css, slidemarks.json, example.html) · reference → docs/glyphs.md, docs/preview.svg")
    print("screen readers → dist/screen-readers/ (VoiceOver, NVDA, JAWS)")
    print("office add-in → dist/office/ (taskpane.html, picker.html, manifest.dev.xml"
          + (", manifest.xml" if getattr(args, "office_base_url", None) else "") + ")")
    print("review → review/specimen.html, review/specimen.pptx, review/specimen.docx")
    for gid, f in findings:
        print(f"  ! {gid}: {f}")
    print(f"{len(findings)} consistency findings")
    return 1 if (findings and args.strict) else 0


def package_cmd(args) -> int:
    status = build(args)
    if status:
        return status
    manifest = json.loads((ROOT / "source/symbols.json").read_text())
    print(f"package → {package.build_zip(ROOT, manifest).relative_to(ROOT)}")
    return 0


def voiceover_merge_cmd(args) -> int:
    manifest = json.loads((ROOT / "source/symbols.json").read_text())
    src = Path(args.export)
    out = Path(args.output) if args.output else src.with_name(f"{src.stem} + SlideMarks.voprefs")
    data, stats = screen_readers.voiceover_merge(manifest, src.read_bytes())
    out.write_bytes(data)
    print(f"kept {stats['kept']} of your pronunciations, replaced {stats['replaced']} earlier SlideMarks entries, "
          f"added {stats['added']} SlideMarks pronunciations")
    print(f"→ {out}  (import with VoiceOver Utility: File → Import Preferences)")
    return 0


def check_cmd(args) -> int:
    manifest = json.loads((ROOT / "source/symbols.json").read_text())
    report, errors, warnings = {}, 0, 0
    for name in args.files:
        findings = check.check_file(Path(name), manifest)
        errors += sum(f.severity == check.ERROR for f in findings)
        warnings += sum(f.severity == check.WARNING for f in findings)
        report[name] = check.as_dicts(findings)
        if not args.json:
            print(f"{name}: {len(findings)} finding(s)")
            for f in findings:
                print(f"  {f.severity:7} {f.rule:18} {f.location}: {f.message}")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def office_serve_cmd(args) -> int:
    import http.server
    import ssl
    certs = Path.home() / ".office-addin-dev-certs"
    if not (certs / "localhost.crt").exists():
        print("No dev certificate. Run once: npx office-addin-dev-certs install", file=sys.stderr)
        return 1
    root = ROOT / "dist/office"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    server = http.server.ThreadingHTTPServer(("localhost", args.port), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certs / "localhost.crt", certs / "localhost.key")
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"serving dist/office at https://localhost:{args.port}")
    print("sideload: npx office-addin-dev-settings sideload dist/office/manifest.dev.xml desktop --app powerpoint|word")
    server.serve_forever()
    return 0


def main():
    parser = argparse.ArgumentParser(prog="slidemarks")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="compile font and regenerate review specimens")
    b.add_argument("--strict", action="store_true", help="exit non-zero if any consistency finding")
    b.add_argument("--office-base-url", help="also write dist/office/manifest.xml pointing at this HTTPS host")
    b.set_defaults(func=build)
    p = sub.add_parser("package", help="build, then write the release zip to dist/")
    p.add_argument("--strict", action="store_true", help="exit non-zero if any consistency finding")
    p.add_argument("--office-base-url", help="also write dist/office/manifest.xml pointing at this HTTPS host")
    p.set_defaults(func=package_cmd)
    o = sub.add_parser("office-serve", help="serve dist/office over HTTPS for sideloading (dev)")
    o.add_argument("--port", type=int, default=3443)
    o.set_defaults(func=office_serve_cmd)
    c = sub.add_parser("check", help="check PowerPoint/Word files for SlideMarks accessibility and rendering problems")
    c.add_argument("files", nargs="+", help=".pptx or .docx files")
    c.add_argument("--json", action="store_true", help="machine-readable output")
    c.set_defaults(func=check_cmd)
    v = sub.add_parser("voiceover-merge", help="add SlideMarks pronunciations to your own VoiceOver Utility export")
    v.add_argument("export", help="file from VoiceOver Utility: File → Export Preferences")
    v.add_argument("-o", "--output", help="output file (default: '<export> + SlideMarks.voprefs' next to it)")
    v.set_defaults(func=voiceover_merge_cmd)
    args = parser.parse_args()
    sys.exit(args.func(args))
