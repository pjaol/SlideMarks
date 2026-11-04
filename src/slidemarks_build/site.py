"""Public website for GitHub Pages: dist/site/.

Layout (all relative, so the site works under any folder such as /SlideMarks/):
  index.html          landing page and install steps
  install.sh, install.ps1   one-step installers (Mac, Windows), see installers/
  office/             the Office add-in (manifest.xml points here)
  picker/             standalone character map
  download/           font, release zip and checksums
  glyphs/             glyph reference
  support/ privacy/ terms/   pages Microsoft Marketplace requires
"""

import shutil
from html import escape
from pathlib import Path

from . import installers
from .specimen_content import families

REPO_URL = "https://github.com/pjaol/SlideMarks"
# GitHub mark from GitHub's Octicons (MIT licence), used to link to the repository.
GITHUB_MARK = ('<svg aria-hidden="true" viewBox="0 0 16 16" width="20" height="20" fill="currentColor"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 '
    '8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15'
    '.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51'
    '.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53'
    '.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/></svg>')
ISSUES_URL = f"{REPO_URL}/issues"
PKG_URL = f"{REPO_URL}/releases/latest/download/SlideMarks.pkg"  # signed, notarized; built with `slidemarks mac-pkg`

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
header.site a.gh { margin-left: auto; display: inline-flex; align-items: center; gap: .4rem; color: var(--fg); text-decoration: none; font-weight: 600; }
header.site a.gh:hover { color: var(--accent); }
@media (max-width: 34rem) { header.site a.gh span { display: none; } }
a { color: var(--accent); }
main { padding-top: 1.5rem; padding-bottom: 3rem; }
h1 { font-size: 2rem; line-height: 1.2; margin: .5rem 0 1rem; }
h2 { margin-top: 2.2rem; }
.lede { font-size: 1.15rem; color: var(--muted); max-width: 42rem; }
.steps { counter-reset: s; list-style: none; padding: 0; }
.steps > li { counter-increment: s; position: relative; padding: .8rem 1rem .8rem 3.2rem; border: 1px solid var(--line); border-radius: 10px; margin: .7rem 0; background: var(--panel); }
.steps > li::before { content: counter(s); position: absolute; left: 1rem; top: .8rem; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: var(--accent); color: var(--bg); text-align: center; font-weight: 700; line-height: 1.6rem; }
.btn { display: inline-block; padding: .5rem 1rem; border-radius: 8px; background: var(--accent); color: var(--bg); text-decoration: none; font-weight: 600; }
.steps p { margin: .6rem 0; }
.steps ul { margin: .3rem 0 .5rem; padding-left: 1.2rem; }
.btn.secondary { background: transparent; color: var(--accent); border: 1px solid var(--accent); }
code, pre { font: .9em ui-monospace, Menlo, monospace; }
pre { background: var(--panel); padding: .8rem; border-radius: 8px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: .95rem; }
th, td { border-bottom: 1px solid var(--line); padding: .35rem .5rem; text-align: left; vertical-align: middle; }
td img { width: 32px; height: 32px; display: block; }
.preview { max-width: 100%; height: auto; border-radius: 12px; }
footer { border-top: 1px solid var(--line); color: var(--muted); font-size: .9rem; padding: 1.2rem 0; }
.vh { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.platforms { display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: 1rem; }
.platforms section { border: 1px solid var(--line); border-radius: 10px; padding: 0 1rem .5rem; background: var(--panel); }
.platforms pre { background: var(--bg); white-space: pre-wrap; word-break: break-all; }
.small { font-size: .92rem; color: var(--muted); }
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
  <a class="gh" href="{REPO_URL}" aria-label="SlideMarks on GitHub" title="SlideMarks on GitHub">{GITHUB_MARK}<span>GitHub</span></a>
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


def _landing(manifest, version: str, zip_name: str, base_url: str) -> str:
    base = escape(base_url.rstrip("/"))
    count = len(manifest["symbols"])
    return f"""
<h1>Presentation symbols that behave like text</h1>
<p class="lede">Harvey balls, arrows, checks, ratings and trends for PowerPoint and Word tables.
One consistent family of {count} symbols: type, paste, resize and recolor them like any character. Free and open source.</p>
<p><img class="preview" src="preview.svg" alt="All {count} SlideMarks symbols, grouped by family"></p>

<h2 id="install">Install</h2>
<p>One step installs the font and adds SlideMarks to Word and PowerPoint. No administrator password needed.</p>
<div class="platforms">
<section>
  <h3>Mac</h3>
  <p><a class="btn" href="{PKG_URL}">Download the Mac installer</a></p>
  <p>Open <code>SlideMarks.pkg</code> and follow the steps. It's signed and notarized by Apple.</p>
  <p>Or paste this into <em>Terminal</em>:</p>
  <pre><code>curl -fsSL {base}/install.sh | sh</code></pre>
</section>
<section>
  <h3>Windows</h3>
  <p>Close Word and PowerPoint. Open <em>PowerShell</em> (Start menu, type <kbd>PowerShell</kbd>), paste this and press <kbd>Enter</kbd>:</p>
  <pre><code>irm {base}/install.ps1 | iex</code></pre>
</section>
</div>
<p class="small">See exactly what they do: <a href="install.sh">install.sh</a> · <a href="install.ps1">install.ps1</a>.
<a href="support/index.html#add-in">Uninstall, Office on the web, organizations and manual steps</a>.</p>
<ol class="steps">
  <li><strong>Quit Word and PowerPoint and reopen them.</strong> Office only sees new fonts and add-ins when it starts
    (if symbols show as boxes, restart Office once more).</li>
  <li><strong>Use it.</strong> On the Home tab, click <em>Add-ins</em>, then <em>SlideMarks</em> (<a href="support/index.html#after-install">where to find it</a>).
    Search for a symbol and click <em>Insert</em>.
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


def _support(base_url: str) -> str:
    base = escape(base_url.rstrip("/"))
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
    PowerPoint's default ("Use Destination Theme") switches the font to the theme font, and the symbol shows as a box.
    <p><img src="../office/assets/walkthrough/powerpoint-paste-options.png" width="360" style="max-width:100%;height:auto;border-radius:8px"
      alt="PowerPoint's Paste Options menu with Keep Source Formatting highlighted, above Use Destination Theme and Keep Text Only"></p></li>
  <li><strong>Word:</strong> if the symbol shows as a box, use <em>Paste Options › Keep Source Formatting</em> too.</li>
  <li><strong>Alternative:</strong> set the text or table cell to the <em>SlideMarks</em> font first, then use <em>Edit › Paste Special › Unformatted Text</em>.</li>
</ul>
<p>The Office add-in avoids all of this: its <em>Insert</em> button sets the font for you.</p>

<h2 id="add-in">Installing and uninstalling</h2>
<p>The <a href="../index.html#install">one-step installers</a> put the font and the add-in in your own user folders,
so they don't need administrator rights. Read them first if you like: <a href="../install.sh">install.sh</a> (Mac),
<a href="../install.ps1">install.ps1</a> (Windows).</p>

<h3 id="after-install">After installing: open SlideMarks</h3>
<ol>
  <li><strong>Quit Word and PowerPoint and reopen them</strong> (on a Mac, <kbd>⌘Q</kbd>; closing the window isn't enough).
    Office only loads new fonts and add-ins when it starts.</li>
  <li>On the <em>Home</em> tab, click <strong>Add-ins</strong>, then <strong>SlideMarks</strong>.
    Word lists it under <em>Developer Add-ins</em>; PowerPoint shows it at the top.
    <p><img src="../office/assets/walkthrough/word-mac-addins.png" width="316" style="max-width:100%;height:auto;border-radius:8px"
      alt="Word's Home tab with the Add-ins button open, showing SlideMarks under Developer Add-ins"></p></li>
  <li>The SlideMarks pane opens on the right. Search for a symbol and click <em>Insert</em>.</li>
</ol>
<p>If symbols show as empty boxes, quit Office once more: it sometimes needs a second restart to load a new font.</p>

<h3 id="mac-access">Mac: “would like to access data from other apps”</h3>
<p>While installing, macOS asks whether <em>Installer</em> (or <em>Terminal</em>, if you used the command) can access data from other apps.
Choose <strong>Allow</strong>. Word and PowerPoint only load add-ins from a folder inside their own app data, so the installer has to write there.
It adds one file and changes nothing else.</p>
<p>If you chose <em>Don't Allow</em>, the font is installed but the add-in isn't. Run the installer again and choose <em>Allow</em>.
If macOS doesn't ask again, add the add-in by hand with the <a href="#manual">manual steps</a> (Finder isn't blocked).</p>

<h3 id="uninstall">Uninstall</h3>
<ul>
  <li><strong>Mac</strong>, in Terminal: <pre><code>curl -fsSL {base}/install.sh | sh -s uninstall</code></pre></li>
  <li><strong>Windows</strong>, in PowerShell with Word and PowerPoint closed:
    <pre><code>&amp; ([scriptblock]::Create((irm {base}/install.ps1))) -Uninstall</code></pre></li>
</ul>

<h3 id="add-in-web">Office on the web</h3>
<ol>
  <li>Download the <a href="../office/manifest.xml" download="SlideMarks-manifest.xml">add-in manifest</a>.</li>
  <li>Open a document in Word or PowerPoint at <a href="https://www.office.com/">office.com</a>.</li>
  <li><em>Home → Add-ins → More Settings → Upload My Add-in</em>, choose the manifest file, then <em>Upload</em>.</li>
</ol>
<p>The web version can't embed fonts, so use the desktop app before sharing files.</p>

<h3 id="add-in-org">Organizations</h3>
<p>Administrators can deploy the <a href="../office/manifest.xml" download="SlideMarks-manifest.xml">add-in manifest</a> to users or groups
from the Microsoft 365 admin center (<em>Settings → Integrated apps → Upload custom apps</em>), so it appears in Word and PowerPoint
without any other steps. Deploy the font with your usual software tools.</p>

<h3 id="manual">Manual install</h3>
<p>If you can't run the installers, install the <a href="../download/SlideMarks-Regular.ttf" download>font</a> by double-clicking it
(Windows: right-click → <em>Install</em>), then add the <a href="../office/manifest.xml" download="SlideMarks-manifest.xml">add-in manifest</a>:</p>
<ul>
  <li id="add-in-mac"><strong>Mac:</strong> in Finder choose <em>Go → Go to Folder…</em> (<kbd>⇧⌘G</kbd>), open
    <code>~/Library/Containers/com.microsoft.Powerpoint/Data/Documents/</code> (for Word: <code>com.microsoft.Word</code>),
    create a folder named <code>wef</code> there if it's missing, and copy the manifest into it.</li>
  <li id="add-in-windows"><strong>Windows:</strong> put the manifest in a folder, share it (<em>Properties → Sharing → Share…</em>),
    then in Word or PowerPoint add the network path, such as <code>\\\\YOUR-PC\\SlideMarks</code>, under
    <em>File → Options → Trust Center → Trust Center Settings… → Trusted Add-in Catalogs</em> with <em>Show in Menu</em> ticked.
    After a restart, it's under <em>Home → Add-ins → Advanced → SHARED FOLDER</em>.</li>
</ul>
<p>Then quit and reopen Word and PowerPoint.</p>

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


def build(root: Path, manifest, zip_path: Path, base_url: str) -> Path:
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

    installers.write_scripts(root, out, base_url)

    (out / "glyphs").mkdir()
    shutil.copytree(root / "docs/glyphs", out / "glyphs/svg")
    shutil.copy(root / "docs/preview.svg", out / "preview.svg")

    (out / "site.css").write_text(CSS)
    pages = {
        "index.html": ("SlideMarks", _landing(manifest, version, zip_path.name, base_url), 0),
        "glyphs/index.html": ("Glyph reference", _glyphs(manifest), 1),
        "support/index.html": ("Support", _support(base_url), 1),
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
