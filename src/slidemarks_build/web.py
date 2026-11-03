"""Web package: @font-face + utility classes generated from the manifest (PRD F-08).

Glyph classes are decorative by default: the second `content` declaration gives the
generated character empty alternative text, so screen readers don't announce a
private-use character. Browsers without CSS alt-text support ignore that line and
keep the first. Meaningful symbols must be named in the HTML (see docs/accessibility.md)."""

from pathlib import Path

from .font import FAMILY, STYLE
from .manifest import preferred_codepoint


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
        cp = preferred_codepoint(s)
        lines.append(f".sm-{s['id']}::before {{ content: \"\\{cp}\"; content: \"\\{cp}\" / \"\"; }}")
    out_path.write_text("\n".join(lines) + "\n")
