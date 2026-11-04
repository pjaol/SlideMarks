# Contributing to SlideMarks

This guide is for people building or changing the font. If you just want to use SlideMarks, see the [README](README.md).

Background reading:
- `docs/SlideMarks_Requirements_v0.1.md`: the product spec.
- `docs/charmap.md`: Office add-in and distribution requirements (next phase).
- `docs/design-goals.md`: the design principles.
- `docs/design-system.md`: metrics, design decisions and code point blocks.
- `docs/adr/`: architecture decisions.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). The browser accessibility tests also use [agent-browser](https://github.com/vercel-labs/agent-browser) if it's installed, and skip otherwise.

```sh
uv sync
uv run slidemarks build            # compile the font and regenerate everything below
uv run slidemarks build --strict   # also fail if there are any consistency findings
uv run slidemarks package          # build, then write dist/SlideMarks-<version>.zip
uv run pytest                      # manifest, alias, font, CSS, screen-reader pack and browser a11y tests
uv run slidemarks voiceover-merge <export.voprefs>   # add SlideMarks pronunciations to a VoiceOver export
uv run slidemarks check <file.pptx|file.docx>        # lint a document for SlideMarks accessibility problems
```

## What a build produces

| Output | Audience | Notes |
|---|---|---|
| `dist/fonts/SlideMarks-Regular.ttf` | users | Desktop font |
| `dist/web/SlideMarks-Regular.woff2`, `slidemarks.css`, `slidemarks.json`, `example.html` | users | Web font, decorative `sm-<id>` classes, symbol data with spoken labels, accessible usage examples |
| `dist/svg/*.svg` | users | Plain black glyph outlines for design tools |
| `docs/glyphs.md`, `docs/glyphs/*.svg`, `docs/preview.svg` | users | Generated glyph reference and README image |
| `dist/screen-readers/` | users | VoiceOver archive, NVDA add-on and JAWS symbol lines mapping each code point to its `spokenLabel` |
| `dist/SlideMarks-<version>.zip` | users | Release asset (`package` only, not committed): fonts, web, svg, reference, checksums |
| `review/specimen.html` | designers | Review sheet. Opens offline. |
| `review/specimen.pptx`, `review/specimen.docx` | designers | The same checks in real Office tables, with the font embedded (PowerPoint: uncompressed EOT in `ppt/fonts/font1.fntdata`; Word: obfuscated `.odttf`, ECMA-376 §17.8.1). Verified without the font installed in PowerPoint and Word on Mac and Windows, 2026-11-03. |

Everything under `dist/`, `docs/glyphs*` and `review/` is generated. Don't edit it by hand.

The font is byte-reproducible: the same inputs always give an identical TTF.

## Repository layout

```text
source/
  design-tokens.json   every dimension: frame, center, strokes, family parameters
  symbols.json         families, immutable ids, PUA code points, names, tags, builder params
installers/             install.sh (Mac), install.ps1 (Windows), pkg/ (Mac package scripts); published with the site
apps/office/            Word/PowerPoint add-in and standalone picker (plain HTML/CSS/JS)
src/slidemarks_build/
  geometry.py          path primitives (circles, arcs, strokes, booleans)
  glyphs.py            one builder per family; all geometry derives from tokens
  font.py              TTF/WOFF2/SVG compilation
  metrics.py           consistency checks measured from the compiled TTF
  manifest.py          manifest validation (ids, code points, Unicode aliases, semantic fields)
  office_fonts.py      EOT (PowerPoint) and obfuscated ODTTF (Word) embedding
  specimen_*.py        review sheets (HTML, PPTX, DOCX)
  web.py, reference.py, package.py, screen_readers.py   user-facing outputs
  check.py             `slidemarks check` document linter
  office.py            assembles dist/office/ (add-in + standalone picker, manifests, icons)
  installers.py        renders the install scripts; builds, signs and notarizes SlideMarks.pkg
tests/                 pytest suite
docs/                  design docs, ADRs, accessibility, generated glyph reference
review/                generated review specimens
dist/                  generated user artifacts
```

## Office add-in (Word and PowerPoint)

The add-in's source is plain HTML, CSS and JavaScript in `apps/office/`: no framework, bundler or `package.json`. `slidemarks build` assembles `dist/office/`:
- `taskpane.html`: loads Office.js;
- `picker.html`: the standalone, offline page;
- the generated catalog, the embedded preview font and the icons;
- `manifest.dev.xml`, pointing at `https://localhost:3443`.

Design: `docs/office-addin-design.md`. Proven API behavior: `docs/office-js-spike.md`.

```sh
npx office-addin-dev-certs install          # once: trusted localhost HTTPS certificate (needs Node.js)
uv run slidemarks build
uv run slidemarks office-serve               # terminal 1: https://localhost:3443 (keep it running)
uv run slidemarks office-open --app word     # terminal 2: or --app powerpoint
```

### Opening Word or PowerPoint with the add-in

**Use `slidemarks office-open`.** It:
- checks the add-in server is running;
- clears stale sideload registrations, which go stale every build because the build replaces `dist/office/`;
- launches the app through Microsoft's sideload tool, with a document that has the SlideMarks pane attached.

**Why opening the app normally doesn't show the add-in:** a sideloaded add-in gets no ribbon button in ordinary documents. On Mac it's only listed under **Home → Add-ins** (the Add-ins button), as a developer add-in, and has to be picked from there each time. That manual route works too, provided `office-serve` is running.

- After changing **HTML, CSS or JS**, close and reopen the task pane. The server sends `no-store`.
- After changing the **manifest** (or icons), run `office-open` again.
- After changing the **font**:
  1. Quit every Office app.
  2. Copy `dist/fonts/SlideMarks-Regular.ttf` over the installed copy (`~/Library/Fonts` on Mac).
  3. Reopen. If symbols still look old, quit and reopen once more: Office reads fonts at launch and can start mid-rebuild of its font cache.
  4. Documents that already embed SlideMarks keep the old copy until they're saved again.
- Debugging on Mac: `defaults write com.microsoft.Powerpoint OfficeWebAddinDeveloperExtras -bool true`, then right-click the pane and choose **Inspect Element**.
- Production: `uv run slidemarks build --office-base-url https://<host>` also writes `dist/office/manifest.xml` for that HTTPS host. Publishing isn't set up yet.

## Design review workflow

1. Change tokens or builders and run `uv run slidemarks build`.
2. Check the consistency findings it prints. These are measured from the compiled font: advance width, ink center, frame bounds, and the geometry-group rules in `design-tokens.json`.
3. Open `review/specimen.html`:
   - **Family** filter: look at one family at a time.
   - **Onion skin**: every member of a family stacked. A consistent family shows one shared skeleton.
   - **Size ladder**: glyphs inline with text at 10–36 pt.
   - **In context**: scorecard tables in light and dark.
   - **Source vs font**: confirms the build didn't change the geometry.
4. Open `review/specimen.pptx` / `.docx` to judge glyphs in real Office tables. The font is embedded, so no install is needed. The *Encoding test* tables there are the screen-reader test sheet; record results in `docs/accessibility.md`.

## Adding a glyph

1. Add an entry to `source/symbols.json` under an existing family, with the next free code point in that family's block (see `docs/design-system.md`). **Never reuse or renumber a code point.**
2. Use an existing builder with new `params`, or add a builder to `glyphs.py`. Builders take every dimension from `design-tokens.json`; avoid one-off numbers.
3. Choose a `geometryGroup`. Use `identical-bounds` or `same-footprint` when the glyph must match siblings exactly; otherwise it's judged visually.
4. If the glyph must leave the shared frame, add a `frameException` with the reason. Don't loosen the check.
5. Fill in the accessibility fields:
   - `spokenLabel`: what the symbol means, as it should be spoken (e.g. "Harvey ball 50 percent"), not its shape.
   - `needsContext`: `true` for values and statuses.
   - `unicodeAliases`: only for an exact standard Unicode equivalent; see the rules in `docs/accessibility.md`. Otherwise use `[]`.
6. Build, run `uv run pytest`, review, and record any new design decision in `docs/design-system.md`.

New glyphs start as `draft`, or as `candidate` if they may not stay in the core set.

## Publishing the website

The public site is `https://pjaol.github.io/SlideMarks/` (GitHub Pages, built by `.github/workflows/pages.yml` on every push to `main`).

```sh
uv run slidemarks site      # dist/site/: landing, office/ (production manifest), picker/, download/, glyphs/, support/, privacy/, terms/
```

- Every link in the site is relative, so it works under the `/SlideMarks/` folder. `tests/test_site.py` enforces this.
- The add-in's production manifest is `dist/site/office/manifest.xml`, pointing at `https://pjaol.github.io/SlideMarks/office/`. **That address is baked into installed add-ins: don't rename the repo or move the site.**
- To preview locally under the same folder:
  `mkdir -p /tmp/pages && ln -sfn "$PWD/dist/site" /tmp/pages/SlideMarks && python3 -m http.server -d /tmp/pages 8780`
  Then open http://localhost:8780/SlideMarks/.

## Installers

`install.sh` and `install.ps1` (in `installers/`) are published at the site root with the site's address filled in.
They install per user (no admin):

- **Mac:** the font goes to `~/Library/Fonts`. The manifest goes to `~/Library/Containers/com.microsoft.{Word,Powerpoint}/Data/Documents/wef/`,
  but only for apps whose container already exists; the script never creates another app's container.
- **Windows:** the font goes to `%LOCALAPPDATA%\Microsoft\Windows\Fonts` and is registered under HKCU. The manifest is registered under
  `HKCU\Software\Microsoft\Office\16.0\WEF\Developer` (value name = add-in ID, data = manifest path), as Microsoft's
  `office-addin-dev-settings` does.

`tests/test_installers.py` runs `install.sh` against a fake home folder, and parses `install.ps1` where PowerShell is available (CI).

### Mac package

`SlideMarks.pkg` is a scripts-only package: its `postinstall` runs the same `install.sh --from` as the console user,
with the font and production manifest bundled. Build it on a Mac with a Developer ID Installer certificate:

```sh
# once: store notarization credentials (app-specific password from appleid.apple.com)
xcrun notarytool store-credentials slidemarks --apple-id <apple-id> --team-id <team-id>

uv run slidemarks mac-pkg --sign "Developer ID Installer: <name> (<team-id>)" --notarize slidemarks
```

The website links to `releases/latest/download/SlideMarks.pkg`, so attach it to every GitHub release under exactly that name.

## Releases

1. Bump `manifestVersion` in `source/symbols.json`.
2. Run `uv run pytest` and `uv run slidemarks package --strict`.
3. Build the Mac package (above).
4. Attach `dist/SlideMarks-<version>.zip` and `dist/SlideMarks.pkg` to a GitHub release.
