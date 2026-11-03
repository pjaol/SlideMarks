"""Self-contained HTML review sheet. The font is embedded as a data URI so the
file opens offline from disk with no server and no network calls."""

import base64
import html
import json
from pathlib import Path

from .specimen_content import LADDER_PT, SCORECARD_HEADER, SCORECARD_ROWS, families as family_list


def _char(s) -> str:
    return f"&#x{s['codepoint']};"


def _guides_svg(t) -> str:
    """Construction guides in the same y-down em box as the rendered glyph."""
    asc = t["ascender"]
    f, c = t["frame"], t["center"]
    y = lambda v: asc - v  # noqa: E731
    r = t["harvey"]["diameter"] / 2
    return (
        f'<svg class="guides" viewBox="0 0 {t["advanceWidth"]} {t["unitsPerEm"]}" aria-hidden="true">'
        f'<line class="g-base" x1="0" x2="1000" y1="{y(0)}" y2="{y(0)}"/>'
        f'<line class="g-cap" x1="0" x2="1000" y1="{y(700)}" y2="{y(700)}"/>'
        f'<rect class="g-frame" x="{f["xMin"]}" y="{y(f["yMax"])}" width="{f["xMax"] - f["xMin"]}" height="{f["yMax"] - f["yMin"]}"/>'
        f'<circle class="g-circle" cx="{c["x"]}" cy="{y(c["y"])}" r="{r}"/>'
        f'<line class="g-center" x1="{c["x"]}" x2="{c["x"]}" y1="{y(f["yMax"]) - 30}" y2="{y(f["yMin"]) + 30}"/>'
        f'<line class="g-center" x1="{f["xMin"] - 30}" x2="{f["xMax"] + 30}" y1="{y(c["y"])}" y2="{y(c["y"])}"/>'
        "</svg>"
    )


def _cell(s, record, guides) -> str:
    flags = record["findings"]
    badge = f'<span class="badge bad" title="{html.escape("; ".join(flags))}">{len(flags)}</span>' if flags else '<span class="badge ok">✓</span>'
    if s["status"] != "approved":
        badge += f'<span class="badge st">{s["status"]}</span>'
    return (
        f'<figure class="cell" data-id="{s["id"]}">'
        f'<div class="em">{guides}<span class="sm glyph">{_char(s)}</span></div>'
        f'<figcaption><b>{html.escape(s["name"])}</b><code>U+{s["codepoint"]}</code>{badge}</figcaption>'
        "</figure>"
    )


def render(tokens, manifest, records, woff2_path: Path, svg_paths: dict, out_path: Path, build_info: dict):
    font_b64 = base64.b64encode(woff2_path.read_bytes()).decode()
    by_id = {r["id"]: r for r in records}
    fams = family_list(manifest)
    guides = _guides_svg(tokens)
    vb = f'0 0 {tokens["advanceWidth"]} {tokens["unitsPerEm"]}'

    families = "".join(
        f'<section class="family" data-family="{fid}"><h3>{html.escape(title)} <small>{len(members)}</small></h3>'
        f'<div class="row">{"".join(_cell(s, by_id[s["id"]], guides) for s in members)}</div></section>'
        for fid, title, members in fams
    )

    onion = "".join(
        f'<figure class="onion-cell" data-family="{fid}"><div class="em onion">{guides}'
        + "".join(f'<span class="sm glyph layer">{_char(s)}</span>' for s in members)
        + f'</div><figcaption>{html.escape(title)}</figcaption></figure>'
        for fid, title, members in fams
    )

    family_runs = "".join(
        f'<span class="sm" data-family="{fid}">{" ".join(_char(s) for s in members)} </span>' for fid, _, members in fams
    )
    ladder = "".join(
        f'<div class="ladder-row" style="font-size:{pt}pt"><span class="pt">{pt}pt</span>'
        f'<span class="txt">Hx 50%</span> {family_runs}<span class="txt">Done</span></div>'
        for pt in LADDER_PT
    )
    family_options = "".join(f'<option value="{fid}">{html.escape(title)} ({len(m)})</option>' for fid, title, m in fams)

    g = {s["id"]: _char(s) for s in manifest["symbols"]}
    rows = [(label, *(g[i] for i in ids)) for label, *ids in SCORECARD_ROWS]
    head = "".join(f"<th>{h}</th>" for h in SCORECARD_HEADER)

    def table(pt):
        body = "".join(
            f'<tr><th>{label}</th>' + "".join(f'<td><span class="sm">{c}</span></td>' for c in cells) + "</tr>"
            for label, *cells in rows
        )
        return (
            f'<table class="score" style="font-size:{pt}pt"><caption>{pt}pt table cells</caption>'
            f"<thead><tr>{head}</tr></thead>"
            f"<tbody>{body}</tbody></table>"
        )

    source_vs_font = "".join(
        f'<figure class="cmp" data-family="{s["category"]}"><div class="em big"><span class="sm glyph">{_char(s)}</span>'
        f'<svg class="src" viewBox="{vb}"><path d="{svg_paths[s["id"]]}"/></svg></div>'
        f'<figcaption>{s["id"]}</figcaption></figure>'
        for s in manifest["symbols"]
    )

    def fmt_bounds(b):
        return " ".join(f"{v:.0f}" for v in b)

    metric_rows = "".join(
        f'<tr class="{"bad" if r["findings"] else ""}" data-family="{r["category"]}"><td><span class="sm">{g[r["id"]]}</span></td><td>{r["id"]}</td>'
        f'<td>{r["group"]}</td><td>{r["advance"]}</td><td>{fmt_bounds(r["bounds"])}</td>'
        f'<td>{r["size"][0]:.0f}×{r["size"][1]:.0f}</td><td>{r["center"][0]:.0f}, {r["center"][1]:.0f}</td>'
        f'<td>{r["coverage"] * 100:.1f}%</td><td>{r["weightVsCategory"]:.2f}×</td>'
        f'<td>{html.escape("; ".join(r["findings"])) or html.escape(r["frameException"] or "") or "—"}</td></tr>'
        for r in records
    )
    total_findings = sum(len(r["findings"]) for r in records)

    page = TEMPLATE
    for key, value in {
        "FONT_B64": font_b64,
        "VERSION": html.escape(manifest["manifestVersion"]),
        "BUILD": html.escape(build_info["built"]),
        "COUNT": str(len(manifest["symbols"])),
        "FINDINGS": str(total_findings),
        "FINDINGS_CLASS": "bad" if total_findings else "ok",
        "TOKENS": html.escape(json.dumps({k: v for k, v in tokens.items() if not k.startswith("$")}, indent=2)),
        "FAMILIES": families,
        "ONION": onion,
        "LADDER": ladder,
        "TABLES": table(12) + table(18),
        "SOURCE_VS_FONT": source_vs_font,
        "METRICS": metric_rows,
        "FAMILY_OPTIONS": family_options,
    }.items():
        page = page.replace("{{" + key + "}}", value)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page)


TEMPLATE = """<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SlideMarks review · v{{VERSION}}</title>
<style>
@font-face {
  font-family: 'SlideMarks';
  src: url(data:font/woff2;base64,{{FONT_B64}}) format('woff2');
  font-display: block;
}
:root {
  --ink: #16181d; --paper: #ffffff; --muted: #6b7280; --rule: #e5e7eb; --panel: #f7f7f8;
  --guide: #e11d48; --guide2: #2563eb; --ok: #15803d; --bad: #b91c1c; --size: 96px;
}
[data-theme="dark"] { --ink: #f3f4f6; --paper: #14161a; --muted: #9ca3af; --rule: #2a2e35; --panel: #1b1e23; }
* { box-sizing: border-box; }
body { margin: 0; font: 14px/1.45 -apple-system, "Segoe UI", system-ui, sans-serif; color: var(--ink); background: var(--paper); }
header.bar { position: sticky; top: 0; z-index: 10; display: flex; gap: 20px; align-items: center; flex-wrap: wrap;
  padding: 10px 24px; background: var(--panel); border-bottom: 1px solid var(--rule); }
header.bar h1 { font-size: 15px; margin: 0 12px 0 0; }
header.bar label { display: flex; gap: 6px; align-items: center; color: var(--muted); }
main { padding: 8px 24px 64px; max-width: 1400px; }
h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 36px 0 4px; }
h2 + p { margin: 0 0 14px; color: var(--muted); max-width: 70ch; }
h3 { font-size: 14px; margin: 18px 0 8px; } h3 small { color: var(--muted); font-weight: 400; }
.sm { font-family: 'SlideMarks'; font-variant-ligatures: none; color: var(--glyph-ink, var(--ink)); }
.row { display: flex; flex-wrap: wrap; gap: 12px; }
.em { position: relative; width: var(--size); height: var(--size); font-size: var(--size); line-height: 1; background: var(--panel); }
.em .glyph { position: absolute; inset: 0; display: block; }
.guides { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; display: none; fill: none; stroke-width: 4; vector-effect: non-scaling-stroke; }
.guides * { vector-effect: non-scaling-stroke; stroke-width: 1px; }
body.show-guides .guides { display: block; }
.g-base { stroke: var(--muted); } .g-cap { stroke: var(--muted); stroke-dasharray: 4 3; }
.g-frame { stroke: var(--guide2); } .g-circle { stroke: var(--guide); stroke-dasharray: 3 3; } .g-center { stroke: var(--guide); }
.guides { z-index: 2; }
figure { margin: 0; }
figcaption { display: flex; gap: 6px; align-items: center; font-size: 11px; color: var(--muted); margin-top: 4px; max-width: calc(var(--size) + 60px); flex-wrap: wrap; }
figcaption b { color: var(--ink); font-weight: 500; }
code { font: 11px ui-monospace, Menlo, monospace; }
.badge { font-size: 10px; padding: 0 5px; border-radius: 8px; color: #fff; }
.badge.ok { background: var(--ok); } .badge.bad { background: var(--bad); }
.onion-row { display: flex; gap: 24px; flex-wrap: wrap; }
.onion { --size: 200px; }
.onion .layer { opacity: .28; }
.ladder-row { display: flex; flex-wrap: wrap; align-items: baseline; gap: .4em; border-bottom: 1px solid var(--rule); padding: 4px 0; }
[hidden] { display: none !important; }
.badge.st { background: #a16207; }
.ladder-row .pt { font: 11px ui-monospace, Menlo, monospace; color: var(--muted); width: 44px; flex: none; }
.ladder-row .txt { font-family: Calibri, "Segoe UI", -apple-system, sans-serif; }
.tables { display: flex; gap: 32px; flex-wrap: wrap; align-items: flex-start; }
table.score { border-collapse: collapse; font-family: Calibri, "Segoe UI", -apple-system, sans-serif; }
table.score caption { font: 11px ui-monospace, Menlo, monospace; color: var(--muted); text-align: left; padding-bottom: 4px; }
table.score th, table.score td { border: 1px solid var(--rule); padding: .35em .8em; }
table.score td { text-align: center; vertical-align: middle; }
table.score th { text-align: left; font-weight: 600; }
table.score thead th { background: var(--panel); }
.cmp-row { display: flex; flex-wrap: wrap; gap: 10px; }
.big { --size: 120px; }
.src { position: absolute; inset: 0; width: 100%; height: 100%; fill: none; stroke: var(--guide); stroke-width: 6; }
table.metrics { border-collapse: collapse; font-size: 12px; width: 100%; }
table.metrics th, table.metrics td { border-bottom: 1px solid var(--rule); padding: 4px 8px; text-align: left; white-space: nowrap; }
table.metrics td:first-child { font-size: 22px; }
table.metrics tr.bad td { color: var(--bad); }
.status { padding: 2px 8px; border-radius: 10px; color: #fff; font-size: 12px; }
.status.ok { background: var(--ok); } .status.bad { background: var(--bad); }
#font-missing { display: none; background: var(--bad); color: #fff; padding: 10px 24px; font-weight: 600; }
details pre { background: var(--panel); padding: 12px; overflow: auto; font-size: 11px; }
</style>
</head>
<body class="show-guides">
<div id="font-missing">SlideMarks font failed to load. Anything shown below is a fallback, not the real glyphs.</div>
<header class="bar">
  <h1>SlideMarks review · v{{VERSION}}</h1>
  <span>{{COUNT}} glyphs</span>
  <span class="status {{FINDINGS_CLASS}}">{{FINDINGS}} findings</span>
  <label>Family <select id="family"><option value="">All</option>{{FAMILY_OPTIONS}}</select></label>
  <label><input type="checkbox" id="guides" checked> Guides</label>
  <label><input type="checkbox" id="dark"> Dark</label>
  <label>Size <input type="range" id="size" min="16" max="200" value="96"> <span id="size-val">96px</span></label>
  <label>Ink <input type="color" id="ink" value="#16181d"></label>
  <span style="color:var(--muted)">built {{BUILD}}</span>
</header>
<main>
  <h2>1 · Families</h2>
  <p>Each tile is one full em (advance width 1000). Guides: blue = shared 660 frame, red dashed = Harvey circle, red cross = optical center, grey = baseline and cap height (700).</p>
  {{FAMILIES}}

  <h2>2 · Onion skin</h2>
  <p>Every member of a family stacked at low opacity. A consistent family shows one crisp shared skeleton; stray edges are inconsistencies.</p>
  <div class="onion-row">{{ONION}}</div>

  <h2>3 · Size ladder</h2>
  <p>All glyphs inline with ordinary text at presentation sizes. Look for glyphs that sit high/low against the text or look heavier/lighter than their neighbours.</p>
  {{LADDER}}

  <h2>4 · In context</h2>
  <p>Glyphs in centred table cells with no per-cell adjustment, as they'd appear on a slide. Use the Ink and Dark controls to check recolouring and transparency.</p>
  <div class="tables">{{TABLES}}</div>

  <h2>5 · Source vs compiled font</h2>
  <p>Font rendering (filled) with the source outline drawn over it in red. They should coincide exactly; any visible offset means the build changed the geometry.</p>
  <div class="cmp-row">{{SOURCE_VS_FONT}}</div>

  <h2>6 · Measurements</h2>
  <p>Measured from the compiled TTF. Coverage = ink area as a share of the 660×660 frame; weight is relative to the family median (a rough proxy for how heavy a glyph feels).</p>
  <table class="metrics">
    <thead><tr><th></th><th>id</th><th>group</th><th>adv</th><th>bounds</th><th>size</th><th>center</th><th>coverage</th><th>weight</th><th>findings</th></tr></thead>
    <tbody>{{METRICS}}</tbody>
  </table>

  <h2>7 · Design tokens</h2>
  <details><summary>Tokens used for this build</summary><pre>{{TOKENS}}</pre></details>
</main>
<script>
const $ = (id) => document.getElementById(id);
$('guides').onchange = (e) => document.body.classList.toggle('show-guides', e.target.checked);
$('dark').onchange = (e) => {
  document.documentElement.dataset.theme = e.target.checked ? 'dark' : 'light';
  $('ink').value = e.target.checked ? '#f3f4f6' : '#16181d';
  document.documentElement.style.removeProperty('--glyph-ink');
};
$('size').oninput = (e) => {
  document.documentElement.style.setProperty('--size', e.target.value + 'px');
  $('size-val').textContent = e.target.value + 'px';
};
$('family').onchange = (e) => {
  const v = e.target.value;
  document.querySelectorAll('[data-family]').forEach((el) => { el.hidden = !!v && el.dataset.family !== v; });
};
$('ink').oninput = (e) => document.documentElement.style.setProperty('--glyph-ink', e.target.value);
document.fonts.load('48px SlideMarks', '\\uE000').then((faces) => {
  if (!faces.length) $('font-missing').style.display = 'block';
}).catch(() => { $('font-missing').style.display = 'block'; });
</script>
</body>
</html>
"""
