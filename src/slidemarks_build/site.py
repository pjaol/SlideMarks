"""Public website for GitHub Pages: dist/site/.

Layout (all relative, so the site works under any folder such as /SlideMarks/):
  index.html          landing page and install steps
  office/             the Office add-in (manifest.xml points here)
  picker/             standalone character map
  download/           font, release zip and checksums
  glyphs/             glyph reference
  support/ privacy/ terms/   pages Microsoft Marketplace requires
"""

import shutil
from html import escape
from pathlib import Path

from .specimen_content import families

REPO_URL = "https://github.com/pjaol/SlideMarks"
ISSUES_URL = f"{REPO_URL}/issues"

CSS = """
:root { --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; --panel:#f6f8fa; --accent:#6d3b8e; --bg:#fff; color-scheme: light dark; }
@media (prefers-color-scheme: dark) { :root { --fg:#e6edf3; --muted:#9198a1; --line:#3d444d; --panel:#1c2128; --accent:#b48bd4; --bg:#0d1117; } }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.6 -apple-system, "Segoe UI", system-ui, sans-serif; color: var(--fg); background: var(--bg); }
header.site { border-bottom: 1px solid var(--line); }
header.site .inner, main, footer .inner { max-width: 60rem; margin: 0 auto; padding: 0 1.25rem; }
header.site .inner { display: flex; align-items: center; gap: 1.5rem; height: 3.5rem; }
header.site a.brand { font-weight: 700; display: flex; align-items: center; gap: .5rem; color: var(--fg); text-decoration: none; }
header.site nav { display: flex; gap: 1rem; flex-wrap: wrap; }
a { color: var(--accent); }
main { padding-top: 1.5rem; padding-bottom: 3rem; }
h1 { font-size: 2rem; line-height: 1.2; margin: .5rem 0 1rem; }
h2 { margin-top: 2.2rem; }
.lede { font-size: 1.15rem; color: var(--muted); max-width: 42rem; }
.steps { counter-reset: s; list-style: none; padding: 0; }
.steps > li { counter-increment: s; position: relative; padding: .8rem 1rem .8rem 3.2rem; border: 1px solid var(--line); border-radius: 10px; margin: .7rem 0; background: var(--panel); }
.steps > li::before { content: counter(s); position: absolute; left: 1rem; top: .8rem; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: var(--accent); color: var(--bg); text-align: center; font-weight: 700; line-height: 1.6rem; }
.btn { display: inline-block; padding: .5rem 1rem; border-radius: 8px; background: var(--accent); color: var(--bg); text-decoration: none; font-weight: 600; }
.btn.secondary { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
code, pre { font: .9em ui-monospace, Menlo, monospace; }
pre { background: var(--panel); padding: .8rem; border-radius: 8px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .95rem; }
th, td { border-bottom: 1px solid var(--line); padding: .35rem .5rem; text-align: left; vertical-align: middle; }
td img { width: 32px; height: 32px; display: block; }
.preview { max-width: 100%; height: auto; border-radius: 12px; }
footer { border-top: 1px solid var(--line); color: var(--muted); font-size: .9rem; padding: 1.2rem 0; }
.vh { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.note { border-left: 4px solid var(--accent); background: var(--panel); padding: .6rem 1rem; border-radius: 0 8px 8px 0; }
"""


def _page(title: str, body: str, depth: int, version: str) -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · SlideMarks</title>
<link rel="icon" href="{up}office/assets/favicon.png">
<link rel="stylesheet" href="{up}site.css">
</head>
<body>
<header class="site"><div class="inner">
  <a class="brand" href="{up}index.html"><img src="{up}office/assets/favicon.png" alt="" width="24" height="24">SlideMarks</a>
  <nav aria-label="Site">
    <a href="{up}index.html#install">Install</a>
    <a href="{up}picker/index.html">Picker</a>
    <a href="{up}glyphs/index.html">Glyphs</a>
    <a href="{up}support/index.html">Support</a>
  </nav>
</div></header>
<main>
{body}
</main>
<footer><div class="inner">
  SlideMarks {escape(version)} · Font: <a href="{REPO_URL}/blob/main/OFL.txt">SIL OFL 1.1</a> ·
  Code: <a href="{REPO_URL}/blob/main/LICENSE">Apache 2.0</a> ·
  <a href="{up}privacy/index.html">Privacy</a> · <a href="{up}terms/index.html">Terms</a> ·
  <a href="{REPO_URL}">Source</a>
</div></footer>
</body>
</html>
"""


def _landing(manifest, version: str, zip_name: str) -> str:
    count = len(manifest["symbols"])
    return f"""
<h1>Presentation symbols that behave like text</h1>
<p class="lede">Harvey balls, arrows, checks, ratings and trends for PowerPoint and Word tables.
One consistent family of {count} symbols: type, paste, resize and recolor them like any character. Free and open source.</p>
<p><img class="preview" src="preview.svg" alt="All {count} SlideMarks symbols, grouped by family"></p>

<h2 id="install">Install</h2>
<ol class="steps">
  <li><strong>Install the font.</strong> <a href="download/SlideMarks-Regular.ttf">Download SlideMarks-Regular.ttf</a>.
    On a Mac, double-click it and choose <em>Install Font</em>. On Windows, right-click and choose <em>Install for all users</em>.
    Then <strong>quit every Office app and reopen it</strong>: Office only picks up new fonts when it restarts.</li>
  <li><strong>Add SlideMarks to Word and PowerPoint</strong> <em>(optional)</em>. Until the Microsoft Marketplace listing is live,
    install it from the add-in manifest: <a href="office/manifest.xml" download>manifest.xml</a>.
    See <a href="support/index.html#add-in">how to install the add-in</a>.</li>
  <li><strong>Use it.</strong> Open <em>SlideMarks</em> on the Home tab, search for a symbol and click <em>Insert</em>.
    Or use the <a href="picker/index.html">web picker</a> to copy symbols into any app with the SlideMarks font.</li>
</ol>
<p class="note">Sharing a file? Turn on <em>Embed fonts in the file</em> so recipients see your symbols without installing anything.
The add-in walks you through it and checks that it worked.</p>

<h2>Downloads</h2>
<p><a class="btn" href="download/{escape(zip_name)}">Everything (zip)</a>
<a class="btn secondary" href="download/SlideMarks-Regular.ttf">Font only (.ttf)</a>
<a class="btn secondary" href="download/SHA256SUMS">Checksums</a></p>
<p>The zip has the desktop font, web font and CSS, an SVG per glyph, the glyph reference, and optional screen-reader pronunciation packs.</p>

<h2>Accessibility</h2>
<p>Screen readers can't describe most symbols, so pair each symbol with text (the add-in can add a label for you).
Arrows and comparison signs are inserted as standard characters so screen readers announce them.
Pronunciation packs for VoiceOver, NVDA and JAWS are in the zip.
<a href="{REPO_URL}/blob/main/docs/accessibility.md">Accessibility guide</a>.</p>
"""


def _support() -> str:
    return f"""
<h1>Support</h1>
<p>Questions, bugs and requests: <a href="{ISSUES_URL}">open an issue on GitHub</a>.
Please mention your app (Word or PowerPoint), platform (Mac, Windows or web) and Office version.</p>

<h2>Symbols show as empty boxes</h2>
<p>The SlideMarks font isn't available. Install it (see <a href="../index.html#install">Install</a>), then <strong>quit every Office app
and reopen it</strong>. If you received the file from someone else, ask them to turn on font embedding before sending.</p>

<h2 id="paste">Pasting from the web picker</h2>
<p>The picker copies the symbol <em>with</em> the SlideMarks font, but whether Office keeps the font depends on how you paste:</p>
<ul>
  <li><strong>PowerPoint:</strong> after pasting, click the <em>Paste Options</em> button and choose <strong>Keep Source Formatting</strong>.
    PowerPoint's default ("Use Destination Theme") switches the font to the theme font, and the symbol shows as a box.</li>
  <li><strong>Word:</strong> if the symbol shows as a box, use <em>Paste Options › Keep Source Formatting</em> too.</li>
  <li><strong>Alternative:</strong> set the text or table cell to the <em>SlideMarks</em> font first, then use <em>Edit › Paste Special › Unformatted Text</em>.</li>
</ul>
<p>The Office add-in avoids all of this: its <em>Insert</em> button sets the font for you.</p>

<h2 id="add-in">Installing the add-in from the manifest</h2>
<p>Until the Microsoft Marketplace listing is live, the add-in is installed from its manifest file:</p>
<ul>
  <li><strong>Office on the web and Microsoft 365 accounts:</strong> <em>Home → Add-ins → More Add-ins → My Add-ins → Upload My Add-in</em>, then choose
    <a href="../office/manifest.xml" download>manifest.xml</a>.</li>
  <li><strong>Mac (Word or PowerPoint):</strong> copy <code>manifest.xml</code> into
    <code>~/Library/Containers/com.microsoft.Word/Data/Documents/wef/</code> (or <code>com.microsoft.Powerpoint</code>), creating the
    <code>wef</code> folder if needed, then restart the app and open <em>Home → Add-ins</em>.</li>
  <li><strong>Organizations:</strong> administrators can deploy the manifest to users from the Microsoft 365 admin center
    (<em>Settings → Integrated apps → Upload custom apps</em>).</li>
</ul>

<h2>Embedding the font when sharing</h2>
<p>Open the SlideMarks pane and follow <em>Show me how</em>. It shows the exact steps for your app and checks the result.</p>

<h2>Name and trademark</h2>
<p>Official releases come only from this site and <a href="{REPO_URL}">github.com/pjaol/SlideMarks</a>.
See the <a href="{REPO_URL}/blob/main/TRADEMARKS.md">name and logo policy</a>.</p>
"""


def _privacy() -> str:
    return f"""
<h1>Privacy</h1>
<p>SlideMarks collects no personal data. There are no accounts, no analytics, no tracking and no advertising.</p>
<ul>
  <li><strong>The font</strong> is a file installed on your computer. It doesn't connect to anything.</li>
  <li><strong>The Office add-in</strong> runs entirely in Office's task pane:
    <ul>
      <li>It inserts the symbols you choose into your document.</li>
      <li>To check whether the font is embedded, it reads your document <em>inside the add-in</em>. Nothing is uploaded or sent anywhere.</li>
      <li>It remembers your favorite and recent symbols in local browser storage on your computer.</li>
    </ul></li>
  <li><strong>Hosting:</strong> the add-in and this site are static files served by GitHub Pages. GitHub may log requests, as for any website
    (see <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub's privacy statement</a>).
    The add-in loads Office.js from Microsoft's servers, as all Office add-ins do.</li>
</ul>
<p>Questions: <a href="{ISSUES_URL}">open an issue</a>.</p>
"""


def _terms() -> str:
    return f"""
<h1>Terms of use</h1>
<p>SlideMarks is free and open source.</p>
<ul>
  <li>The <strong>font</strong> is licensed under the <a href="{REPO_URL}/blob/main/OFL.txt">SIL Open Font License 1.1</a>,
    with Reserved Font Name "SlideMarks". You may use it in any document, commercial or not, and embed it in files you share.</li>
  <li>The <strong>software</strong> (add-in, picker, tools) is licensed under the <a href="{REPO_URL}/blob/main/LICENSE">Apache License 2.0</a>.</li>
  <li>The <strong>name and logo</strong> are covered by the <a href="{REPO_URL}/blob/main/TRADEMARKS.md">name and logo policy</a>.</li>
</ul>
<p>SlideMarks is provided "as is", without warranty of any kind, as set out in those licences.
Screenshots of Microsoft Office in the add-in's guides are © Microsoft Corporation and used for instructional purposes.</p>
"""


def _glyphs(manifest) -> str:
    rows = []
    for _, title, members in families(manifest):
        rows.append(f'<h2 id="{escape(members[0]["category"])}">{escape(title)}</h2><table><thead><tr><th><span class="vh">Symbol</span></th><th>Name</th>'
                    '<th>Code point</th><th>Standard character</th><th>Spoken label</th><th>CSS class</th></tr></thead><tbody>')
        for s in members:
            std = ", ".join(f"U+{a}" for a in s["unicodeAliases"]) or "–"
            rows.append(f'<tr><td><img src="svg/{s["id"]}.svg" alt="{escape(s["spokenLabel"])}"></td><td>{escape(s["name"])}</td>'
                        f'<td><code>U+{s["codepoint"]}</code></td><td>{std}</td><td>{escape(s["spokenLabel"])}</td>'
                        f'<td><code>sm-{s["id"]}</code></td></tr>')
        rows.append("</tbody></table>")
    return f"""
<h1>Glyph reference</h1>
<p>Every SlideMarks symbol with its code point. Symbols only appear as these shapes when the SlideMarks font is applied.
Where a <em>standard character</em> is listed, it draws the same symbol and screen readers can announce it.
To search and copy, use the <a href="../picker/index.html">picker</a>.</p>
{''.join(rows)}
"""


def build(root: Path, manifest, zip_path: Path) -> Path:
    dist = root / "dist"
    out = dist / "site"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    version = manifest["manifestVersion"]

    shutil.copytree(dist / "office", out / "office", ignore=shutil.ignore_patterns("manifest.dev.xml"))
    if not (out / "office/manifest.xml").exists():
        raise SystemExit("dist/office/manifest.xml is missing: build with --office-base-url first")
    favicon = next((out / "office/assets").glob("icon-32.*.png"))
    shutil.copy(favicon, out / "office/assets/favicon.png")

    (out / "download").mkdir()
    shutil.copy(zip_path, out / "download" / zip_path.name)
    shutil.copy(dist / "fonts/SlideMarks-Regular.ttf", out / "download")
    import zipfile
    with zipfile.ZipFile(zip_path) as z:
        sums = next(n for n in z.namelist() if n.endswith("SHA256SUMS"))
        (out / "download/SHA256SUMS").write_bytes(z.read(sums))

    (out / "glyphs").mkdir()
    shutil.copytree(root / "docs/glyphs", out / "glyphs/svg")
    shutil.copy(root / "docs/preview.svg", out / "preview.svg")

    (out / "site.css").write_text(CSS)
    pages = {
        "index.html": ("SlideMarks", _landing(manifest, version, zip_path.name), 0),
        "glyphs/index.html": ("Glyph reference", _glyphs(manifest), 1),
        "support/index.html": ("Support", _support(), 1),
        "privacy/index.html": ("Privacy", _privacy(), 1),
        "terms/index.html": ("Terms of use", _terms(), 1),
    }
    for path, (title, body, depth) in pages.items():
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_text(_page(title, body, depth, version))
    (out / "picker").mkdir()
    (out / "picker/index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>SlideMarks picker</title>'
        '<meta http-equiv="refresh" content="0; url=../office/picker.html">'
        '<a href="../office/picker.html">Open the SlideMarks picker</a>\n')
    (out / ".nojekyll").write_text("")  # serve files as-is; no Jekyll processing
    return out
