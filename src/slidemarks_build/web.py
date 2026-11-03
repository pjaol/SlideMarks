"""Web package generated from the manifest (PRD F-08): @font-face + utility classes,
symbol data for developers, and an example page of accessible usage.

Glyph classes are decorative by default: the second `content` declaration gives the
generated character empty alternative text, so screen readers don't announce a
private-use character. Browsers without CSS alt-text support ignore that line and
keep the first. Meaningful symbols must be named in the HTML (see docs/accessibility.md)."""

import json
from html import escape
from pathlib import Path

from .font import FAMILY, STYLE
from .manifest import preferred_codepoint
from .specimen_content import families


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
        "}",
        "",
    ]
    for s in manifest["symbols"]:
        cp = preferred_codepoint(s)
        lines.append(f".sm-{s['id']}::before {{ content: \"\\{cp}\"; content: \"\\{cp}\" / \"\"; }}")
    out_path.write_text("\n".join(lines) + "\n")


def symbol_data(manifest) -> dict:
    """Everything a web developer needs to label a symbol, keyed by id."""
    return {
        "version": manifest["manifestVersion"],
        "fontFamily": FAMILY,
        "families": [{"id": fid, "title": title} for fid, title, _ in families(manifest)],
        "symbols": {
            s["id"]: {
                "name": s["name"],
                "family": s["category"],
                "char": chr(int(preferred_codepoint(s), 16)),
                "codepoint": f"U+{preferred_codepoint(s)}",
                "puaCodepoint": f"U+{s['codepoint']}",
                "unicodeAliases": [f"U+{a}" for a in s["unicodeAliases"]],
                "cssClass": f"sm-{s['id']}",
                "spokenLabel": s["spokenLabel"],
                "needsContext": s["needsContext"],
                "status": s["status"],
            }
            for s in manifest["symbols"]
        },
    }


def render_json(manifest, out_path: Path):
    out_path.write_text(json.dumps(symbol_data(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _named(s) -> str:
    return f'<span class="slidemarks sm-{s["id"]}" role="img" aria-label="{escape(s["spokenLabel"])}"></span>'


def render_example(manifest, out_path: Path):
    """Static page showing the accessible patterns with real labels from the manifest."""
    by_id = {s["id"]: s for s in manifest["symbols"]}
    h75, h50, h25, check, cross, up, flat = (by_id[i] for i in (
        "harvey-75", "harvey-50", "harvey-25", "status-check", "status-cross", "trend-up", "trend-flat"))
    rows = [
        ("Offline use", h75, "75%", check, "Yes", up),
        ("Font embedding", h50, "50%", check, "Yes", flat),
        ("Web support", h25, "25%", cross, "No", up),
    ]
    body_rows = "\n".join(
        f'      <tr><th scope="row">{label}</th>'
        f'<td><span class="slidemarks sm-{ball["id"]}" aria-hidden="true"></span> {pct}</td>'
        f'<td><span class="slidemarks sm-{mark["id"]}" aria-hidden="true"></span> {word}</td>'
        f'<td>{_named(trend)}</td></tr>'
        for label, ball, pct, mark, word, trend in rows
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SlideMarks {manifest['manifestVersion']} · accessible usage examples</title>
<link rel="stylesheet" href="slidemarks.css">
<style>
  body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem; color: #1f2328; }}
  code, pre {{ font: 13px ui-monospace, Menlo, monospace; }}
  pre {{ background: #f6f8fa; padding: .75rem; overflow-x: auto; }}
  table {{ border-collapse: collapse; }}
  th, td {{ border: 1px solid #d0d7de; padding: .4rem .8rem; text-align: left; }}
  .demo {{ font-size: 1.5rem; }}
</style>
</head>
<body>
<main>
<h1>SlideMarks: accessible usage</h1>
<p>Generated from <code>source/symbols.json</code>. Labels come from <code>slidemarks.json</code> (<code>spokenLabel</code>). See <code>docs/accessibility.md</code> for the reasoning.</p>

<h2>1. Decorative: the text carries the meaning</h2>
<p class="demo"><span class="slidemarks sm-{h75['id']}" aria-hidden="true"></span> 75% complete</p>
<pre>&lt;span class="slidemarks sm-{h75['id']}" aria-hidden="true"&gt;&lt;/span&gt; 75% complete</pre>

<h2>2. Meaningful on its own: role and name</h2>
<p class="demo">{_named(h75)}</p>
<pre>{escape(_named(h75))}</pre>
<p>Put <code>role="img"</code> on the element. <code>aria-label</code> on a plain <code>span</code> without a role is ignored.</p>

<h2>3. Tables: symbol plus visible value, real header cells</h2>
<table>
  <caption>Capability scorecard</caption>
  <thead><tr><th scope="col">Capability</th><th scope="col">Coverage</th><th scope="col">Supported</th><th scope="col">Trend</th></tr></thead>
  <tbody>
{body_rows}
  </tbody>
</table>
<p>Coverage and Supported pair a decorative symbol with visible text. Trend has no visible text, so each symbol is named.</p>

<h2>4. Contrast and color</h2>
<p>Meaningful symbols need at least 3:1 contrast with their background (WCAG 1.4.11), and color must never be the only signal (WCAG 1.4.1). Use the shape (e.g. RAG ring, dot, half) or text, not red and green alone.</p>
</main>
</body>
</html>
"""
    out_path.write_text(page, encoding="utf-8")
