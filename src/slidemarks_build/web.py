"""Web package: @font-face + utility classes generated from the manifest (PRD F-08)."""

from pathlib import Path

from .font import FAMILY, STYLE


def render_css(manifest, out_path: Path):
    lines = [
        f"/* SlideMarks {manifest['manifestVersion']} · generated from source/symbols.json — do not edit */",
        "@font-face {",
        f"  font-family: '{FAMILY}';",
        f"  src: url('./{FAMILY}-{STYLE}.woff2') format('woff2');",
        "  font-style: normal;",
        "  font-weight: 400;",
        "  font-display: block;",
        "}",
        "",
        ".slidemarks {",
        f"  font-family: '{FAMILY}' !important;",
        "  font-style: normal;",
        "  font-weight: 400;",
        "  font-variant-ligatures: none;",
        "  line-height: 1;",
        "  speak: never;",
        "}",
        "",
    ]
    for s in manifest["symbols"]:
        lines.append(f".sm-{s['id']}::before {{ content: \"\\{s['codepoint']}\"; }}")
    out_path.write_text("\n".join(lines) + "\n")
