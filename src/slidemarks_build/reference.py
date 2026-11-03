"""User-facing glyph reference (docs/glyphs.md) and README overview image,
generated from the manifest so they can never disagree with the font."""

from html import escape
from pathlib import Path

from .specimen_content import families

# Previews carry their own light tile: an <img> SVG can't see GitHub's theme, and
# prefers-color-scheme follows the OS, so self-contained colours are the only reliable choice.
TILE = "#f6f8fa"
INK = "#1f2328"
LABEL = "font:600 26px -apple-system,'Segoe UI',Helvetica,sans-serif"


def render(tokens, manifest, svg_paths: dict, docs_dir: Path):
    em, adv = tokens["unitsPerEm"], tokens["advanceWidth"]
    preview_dir = docs_dir / "glyphs"
    preview_dir.mkdir(parents=True, exist_ok=True)
    for stale in preview_dir.glob("*.svg"):
        stale.unlink()
    for s in manifest["symbols"]:
        (preview_dir / f"{s['id']}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {adv} {em}" width="40" height="40">'
            f'<rect width="{adv}" height="{em}" rx="120" fill="{TILE}"/><path fill="{INK}" d="{svg_paths[s["id"]]}"/></svg>\n'
        )

    fams = families(manifest)
    out = [
        "# SlideMarks glyph reference",
        "",
        f"Version {manifest['manifestVersion']} · {len(manifest['symbols'])} glyphs. "
        "Generated from `source/symbols.json`; do not edit by hand.",
        "",
        "Code points are in the Unicode Private Use Area. They only show as these shapes when the **SlideMarks** font is applied. "
        "See the [README](../README.md#typing-a-symbol) for how to insert them.",
        "",
        "Glyphs marked *candidate* may change or be removed before 1.0. All others keep their code points.",
        "",
        "| Family | |",
        "|---|---|",
    ]
    out += [f"| [{title}](#{_anchor(title)}) | {len(members)} glyphs |" for _, title, members in fams]
    for _, title, members in fams:
        out += ["", f"## {title}", "", "| | Name | Code point | CSS class | Status |", "|---|---|---|---|---|"]
        for s in members:
            out.append(
                f"| <img src=\"glyphs/{s['id']}.svg\" width=\"32\" height=\"32\" alt=\"\"> | {s['name']} | `U+{s['codepoint']}` "
                f"| `sm-{s['id']}` | {s['status']} |"
            )
    (docs_dir / "glyphs.md").write_text("\n".join(out) + "\n")
    _overview(tokens, fams, svg_paths, docs_dir / "preview.svg")


def _anchor(title: str) -> str:
    return "".join(c for c in title.lower().replace(" ", "-") if c.isalnum() or c == "-")


def _overview(tokens, fams, svg_paths, out_path: Path):
    """One row per family, every glyph, for the top of the README."""
    cell, label_w, per_row = 80, 380, 13
    rows = []
    for _, title, members in fams:
        for i in range(0, len(members), per_row):
            rows.append((title if i == 0 else "", members[i:i + per_row]))
    width, height = label_w + per_row * cell, len(rows) * cell + 20
    scale = 64 / tokens["unitsPerEm"]
    width += 40
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -10 {width} {height + 20}" width="{width}" height="{height + 20}">',
             f'<rect x="-20" y="-10" width="{width}" height="{height + 20}" rx="16" fill="{TILE}"/>']
    for r, (title, members) in enumerate(rows):
        y = 10 + r * cell
        if title:
            parts.append(f'<text x="0" y="{y + 46}" fill="#59636e" style="{LABEL}">{escape(title)}</text>')
        for c, s in enumerate(members):
            x = label_w + c * cell + 8
            parts.append(f'<path fill="{INK}" transform="translate({x} {y + 8}) scale({scale})" d="{svg_paths[s["id"]]}"/>')
    parts.append("</svg>")
    out_path.write_text("".join(parts) + "\n")
