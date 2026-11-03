# SlideMarks — Product Requirements, Symbol Inventory & Design System

**Version:** 0.1 draft  
**Date:** 2026-11-03  
**Status:** Implementation-ready proposal; platform-dependent features require validation  
**Product:** SlideMarks (working name)

## 1. Executive summary

SlideMarks is an original, deterministic, presentation-oriented **symbol typeface** and its supporting asset/tooling ecosystem. Symbols are used as **text**, particularly inside table cells in Microsoft PowerPoint and Word, rather than positioned SVG images. Every glyph has deliberately controlled geometry, alignment, stroke, optical scale and color behavior. The font must be usable offline on Windows/macOS/Linux; deliverable as installable TTF/OTF and web WOFF2; embeddable in editable Office documents where the application supports embedding; and paired with an offline searchable catalog. Phase 2 adds optional JavaScript task-pane add-ins for Word and PowerPoint, reusing the same catalog and renderer.

**Non-goals:** Another general-purpose pictogram library; dependence on external font rendering for special Unicode symbols; account system, subscription, cloud dependency; dynamically editable vector pie charts within a single monochrome glyph; universal custom-font support in Google Slides; claims of guaranteed font fidelity in every third-party viewer.

### 1.1 Problem statement

Existing symbol workflows make tables difficult to maintain: stock Unicode Harvey balls use unrelated font metrics; SVGs behave as floating objects rather than text; icons need per-object resizing/recoloring; colors, weights, and baselines drift. Users need a stable set of presentation primitives that can be typed, pasted, formatted, aligned and edited **like ordinary characters**.

### 1.2 Product principles

1. **Font-first:** each symbol is a real vector outline in the custom font.
2. **No glyph fallback as success:** unsupported/missing-font results are flagged, never presented as equivalent.
3. **Single source of truth:** each symbol is described once and compiled to TTF/OTF, WOFF2, SVG preview, web catalog data and reference documentation.
4. **Consistent families:** all related glyphs use fixed metrics and explicit design rules.
5. **Zero runtime dependencies for using the font:** install/select/copy/paste works without any app or service.
6. **Friendly input:** searchable character picker, cheat sheet and mappings; add-ins later.
7. **Stable contracts:** glyph semantic IDs and code points survive redesigns and new releases.
8. **Platform reality:** Windows/macOS/Linux font install, Office document embedding, WOFF2 web embedding and Office.js add-in capabilities are separate compatibility targets.

## 2. Phases and deliverables

| Phase | Scope | Deliverables | Exit criterion |
|---|---|---|---|
| 0: Feasibility | Small, risk-driven prototype | 5 Harvey balls, 4 arrows, check/cross; TTF/OTF/WOFF2; test PPTX and DOCX; smoke test web; investigate Office.js table insertion | Fonts render consistently, carry the same metrics and pass embedding/editability checks in target desktop Office versions |
| 1: Core | Production symbol font and no-install picker | Curated 100+ glyph release; canonical source and manifest; font builds; SVG asset exports; WOFF2/CSS; searchable offline HTML picker; printable cheat sheet; examples; tests and CI | Full symbol/metric coverage, documented mapping, versioned releases, no account required |
| 2: Office integrations | Optional Word and PowerPoint JS task panes | Shared picker UI, separate host adapters, Office manifests, insert/format actions where host API supports them; fallback user guidance | Word insertion/formatting passes supported-host tests; PowerPoint existing-table-cell workflow is validated or clearly scoped to manual paste |
| 3: Optional enhancements | More weights, symbols, features | Regular/Medium/Bold families, requested industry packs, favorites, shortcuts, accessible descriptions | Only after real-world table editing feedback |

### 2.1 Explicit success / failure criteria

- A table containing 0, 25, 50, 75, 100% Harvey balls maintains **identical outside diameter and advance width** at equal font size.
- At 10, 12, 14, 18 and 24 pt, glyphs remain visually centered in cells with no per-cell adjustments.
- Changing run text color recolors the entire glyph; the unfilled area remains transparent (background shows through).
- Copy/paste retains the intended code point; when the font is assigned, appearance is deterministic.
- Fonts embed in PowerPoint and Word desktop files where supported; documents are reopened on a target system without the font installed and checked for display **and editability**. No blanket promise for all viewers.
- Web example loads bundled WOFF2 locally and shows all glyphs offline; no network calls.
- Golden master SVGs and generated font outlines are traced to the same source and checked for unexpected differences.
- Every symbol has a semantic name, immutable ID, stable code point, category, human-readable description, tags, design status and preview.

## 3. Detailed functional requirements

| ID | Priority | Requirement / validation |
|---|---|---|
| F-01 | P0 | Glyphs are native OpenType/TrueType vector outlines, not bitmap images, emoji or glyphs borrowed from installed system fonts. Inspect generated outlines and font cmap. |
| F-02 | P0 | Fixed advance widths for families; exact shared outer geometry for Harvey balls and other rated indicators. Automated bounding box assertions. |
| F-03 | P0 | Supports regular text formatting (point size, color, alignment) in Word/PPT cells. Test editable cells. |
| F-04 | P0 | Private Use Area (PUA) Unicode values assigned in a manifest; no dependence on arbitrary Unicode fallback shapes. Stable mapping after 1.0. |
| F-05 | P0 | Shipping font includes `.notdef` and required OpenType tables and passes font validation (e.g., fontTools/OTS as feasible). |
| F-06 | P0 | TTF desktop build (preferred for initial Office compatibility), optional OTF build and WOFF2 web build. |
| F-07 | P0 | Explicit embedding permission `OS/2.fsType=0x0008` (Editable) or `0x0000` (Installable) based on final licensing decision; verify using fontTools and real Office files. Never mark restricted third-party source fonts permissive. |
| F-08 | P0 | Web CSS generated with `@font-face` (`font-family: SlideMarks`, `font-display: block` or an intentional choice), scoped usage class and per-symbol code point classes. |
| F-09 | P0 | Offline searchable catalog includes preview, name, category, code point, tags, copy button, adjustable preview size, accessible label; copy writes actual code point, never an SVG. |
| F-10 | P0 | PDF/HTML printable cheat sheet generated from manifest; no hand-maintained mismatches. |
| F-11 | P0 | Manifest version and checksums published with fonts; release zip installable without Node/Python. |
| F-12 | P1 | Sample PPTX/DOCX and web showcase; keep examples independent of private plug-ins. |
| F-13 | P1 | Optional text shortcuts document (OS-specific), but not a dependency for insertion. |
| F-14 | P1 | Font weights may be separate static families; support optical matching between weights. No synthetic bold if avoidable. |
| F-15 | P2 | Reusable TypeScript `@slidemarks/catalog` package for querying/filtering glyphs, retrieving character/code point and SVG preview. |
| F-16 | P2 | Office.js Word adapter inserts at current selection and applies SlideMarks family to inserted range, preserving neighboring text. |
| F-17 | P2/RISK | PowerPoint adapter inserts a text glyph at selection or uses a documented paste workflow. **Do not promise automatic font formatting of existing PowerPoint table cells.** Current Office.js table API permits text updates but not subsequent cell font formatting. Prove the exact workflow and host versions before declaring support. |
| F-18 | P2 | Feature detection for Office requirements; adapters return supported/unsupported with actionable feedback and never silently convert text into floating shapes. |
| F-19 | P0 | Missing font/fallback tests show a clear warning in catalog/docs; product never represents fallback glyphs as identical. |
| F-20 | P0 | Security/privacy: static site no analytics by default, local assets, no login, no code execution macros in Office sample documents. |

## 4. Symbol inventory and release priorities

**Inventory is a candidate design backlog, not a claim that all items already exist.** `P0` first wave, `P1` expanded first release, `P2` optional packs. Approximate total: **~120–140 glyphs**, depending on how many direction/weight variants survive design review. Prefer completeness within a family over indiscriminate icon count.

| Family | Glyphs / members | Count | Priority | Exact design rules |
|---|---|---:|---|---|
| Harvey balls (quarters) | 0, 25, 50, 75, 100% | 5 | P0 | Same outer circle, center, transparent unfilled portion; clockwise fill from 12 o'clock; same strokes |
| Harvey balls (deciles) | 10, 20, 30, 40, 60, 70, 80, 90%; quarters and extremes already counted | 8 | P1 | Same outline geometry; semantic percentages, not ad hoc Unicode |
| Rating dots | Empty/filled circle; empty/filled square; empty/filled diamond | 6 | P0 | Families share visual height and margins |
| Checks and outcomes | Check, heavy check, cross, heavy cross, minus, plus, question, exclamation | 8 | P0 | Comparable strokes, no emoji presentation |
| Circular statuses | Circle-check, circle-cross, circle-minus, circle-question, circle-exclamation | 5 | P1 | Shared circle, center and padding |
| Direction arrows | Left, right, up, down, NE, NW, SE, SW | 8 | P0 | Consistent shaft, arrowhead angles, bounding boxes |
| Bidirectional arrows | L↔R, U↕D, NE↙SW, NW↘SE | 4 | P1 | Same optical shaft length per group |
| Arrow variants | Thin right/left/up/down; heavy right/left/up/down; short right/left; long right/left | 12 | P1 | Families differentiate by weight and length, not arbitrary shape |
| Curved / workflow arrows | Turn-left, turn-right, U-turn-left, U-turn-right, loop clockwise, loop counterclockwise, return, branching | 8 | P1 | Match turns, radii, heads and optical area |
| Trend indicators | Rising, falling, flat, sharply rising, sharply falling, oscillating | 6 | P0 | Common baseline/endpoints and line weight |
| Chevron / flow | Chevron right/left/up/down, double right/left, filled right/left | 8 | P1 | Consistent wedge and spacing |
| Priority / emphasis | 1, 2, 3 inside circle; flag, star-outline, star-filled, bookmark, pin | 8 | P1 | Numeric shapes use optical centering; no need to match surrounding typography perfectly |
| Progress segments | 0/4, 1/4, 2/4, 3/4, 4/4 horizontal bar | 5 | P1 | Same footprint and segment spacing; decorative, not accessible alone |
| RAG indicators | Empty ring, ring with center dot, solid dot, half-filled dot | 4 | P1 | No hard-coded red/amber/green; text color sets state |
| Simple markers | Bullet small/medium/large, open bullet, dash, vertical separator, horizontal separator | 6 | P1 | Distinct purposes and consistent centers |
| Decision / workflow nodes | Process square, rounded square, decision diamond, terminator pill, database cylinder outline, connector circle | 6 | P2 | Inline shorthand only, not full diagram replacement |
| Business comparisons | Equals, not-equals, approximately, greater, less, greater-equal, less-equal, delta | 8 | P1 | Respect mathematical semantics; author original matching outlines |
| Ownership / action | User, users, lock, unlock, clock, calendar, link, unlink | 8 | P2 | Tiny glyph legibility determines whether these belong in core |

**Candidate total: 123 glyphs** using the listed rows (subject to manifest reconciliation). The source manifest, not this prose count, must be the definitive inventory. Avoid duplicating semantically equivalent symbols just to reach a round number.

### 4.1 Recommended Phase 0 subset

- Harvey: 0/25/50/75/100 (5)
- Arrow: right, left, up, down (4)
- Status: check, cross, empty circle, full circle (4)
- Trend: rising and falling (2)
- **Total: 15 glyphs**; enough to test geometry, baseline, filled/outline behavior, web and Office embedding.

### 4.2 Future symbol request rule

Add a symbol only when it (a) has a presentation use case, (b) works readably at 10–12 pt, (c) is meaningfully different from existing glyphs, and (d) can share family geometry. Otherwise keep it as an SVG asset outside the core font.

## 5. Design system: metrics and drawing style

### 5.1 Typeface-wide metrics (initial proposed values; adjust through visual testing)

| Property | Initial rule |
|---|---|
| Units per em | 1,000 UPM |
| Ascender / descender | +800 / −200 |
| Default glyph advance | 1,000 UPM for primary symbol set |
| Visible primary glyph box | x=170..830 (660 wide), reference y=90..750 (660 high), aligned to target cap center after specimen testing |
| Target cap-height reference | 700 UPM |
| Common circle diameter | 660 UPM (all Harvey balls and circular statuses) |
| Circle center | x=500, y=420 in a glyph coordinate system with baseline y=0 |
| Stroke weight, Regular | 48 UPM as a starting point; adjust after 10–24 pt proofs |
| Stroke cap/join | Rounded for directional/line icons; explicit corner treatment for geometric shapes |
| Optical inset | Small, documented per-family exceptions allowed; never change Harvey diameter |
| Vertical alignment | Shared family center and baseline; match symbols in one cell at same font size |
| Side bearings | 170 UPM for centered 660-wide circle; symmetric unless justified by optical test |
| Rendering | Monochrome outlines; no color layers or raster/bitmap strikes |

**Coordinate clarification:** SVG source files may use y-down viewBoxes, but build tools must normalize to font y-up and preserve intended centered placement. The precise cap-height alignment should be tuned against an actual text face in PowerPoint, not assumed from canvas coordinates.

### 5.2 Core drawing rules

1. **Same family, same skeleton:** identical bounding geometry; stroke/shape portions differ only for semantics.
2. **Harvey balls:** fixed 660-unit external diameter; use a circle and one continuous filled sector; start at twelve o'clock and fill clockwise; outer edge remains exactly the same at all percentages; percentage is computed from geometry, not visually approximated. For `100%`, no perimeter stroke makes it look bigger: create the filled circle to the same outer perimeter used by partial balls; consider using filled wedge clipped to a shared circle with the rim accounted for.
3. **Stroke construction:** build from a canonical vector path and expand strokes to outlines before font compilation. Font rendering should not depend on SVG strokes surviving conversion.
4. **Filled/unfilled areas:** in a monochrome font, the filled region uses current text color and unfilled region is transparent. No independently settable background color. At 100% the entire circle is text color.
5. **Consistent arrowheads:** common arrowhead angle (e.g., 45°), head length and shaft thickness within each weight; use rotated versions of canonical paths for directions instead of redrawing each.
6. **Optical adjustment:** checkmarks and diagonal arrows may exceed nominal boxes by a small documented amount for perceived size, but Harvey circles are mathematically fixed.
7. **Proportions:** balanced and minimalist; no shadows, gradients, 3D, emojis, decorative fills, high detail or asymmetrical embellishments.
8. **Accessibility:** each glyph is a symbol, not the only carrier of meaning in critical documentation; catalog carries text labels and descriptions; samples include legends.
9. **No accidental ligatures:** user copying one character should result in one glyph unless a separately specified ligature feature is deliberately added in a later release.
10. **No automatic stylistic substitutions:** glyph identity must be stable regardless of user app typography settings.

### 5.3 Optical checks

- Test contact sheets at 10/12/14/18/24/36 pt on white and dark backgrounds, in 1.0 and 1.25 line spacing, centered and left-aligned table cells.
- Render in Windows ClearType and macOS text rasterization, export to PDF and compare expected outer geometry.
- Document exceptions per glyph and require review before merging.
- Prefer real PowerPoint table screenshots to an SVG preview when judging baseline and cap alignment.

## 6. Glyph identity and mappings

All symbols receive immutable string IDs (`harvey-50`, `arrow-right`, `status-check`), independently assigned PUA code points, display names and search keywords. **Do not map symbols over ASCII letters or rely on disparate pre-existing Unicode pictogram designs.** The picker copies the PUA character; the SlideMarks font draws its intended glyph.

### 6.1 Proposed mapping blocks (illustrative; freeze at v1.0)

| Range | Purpose | Example |
|---|---|---|
| U+E000–U+E01F | Harvey and progress | `harvey-50` → `U+E002` |
| U+E020–U+E04F | Arrows and direction | `arrow-right` → `U+E021` |
| U+E050–U+E06F | Status/outcomes | `status-check` → `U+E050` |
| U+E070–U+E08F | Trend/priority | `trend-up` → `U+E070` |
| U+E090–U+E0BF | Comparison/workflow | `decision-diamond` → `U+E090` |
| U+E0C0–U+E0FF | Reserved | Never recycle removed glyphs |

The blocks are **semantic allocations**, not a license to renumber existing characters. Existing manifest mappings win. Keep a machine-readable compatibility history.

### 6.2 Example manifest entry

```json
{
  "id": "harvey-50",
  "codepoint": "E002",
  "name": "Harvey ball 50%",
  "category": "harvey",
  "tags": ["rating", "half", "score", "50 percent"],
  "source": "glyphs/harvey/harvey-50.svg",
  "advanceWidth": 1000,
  "geometryGroup": "harvey-circle-660",
  "status": "approved",
  "introduced": "1.0.0"
}
```

### 6.3 Clipboard behavior

The offline web catalog copies the actual PUA character **as plain text**. This is portable as character data, **not** as styling. For reliable appearance, users apply SlideMarks to pasted text or paste into a cell already formatted with SlideMarks. The future Office add-in will attempt to insert and format in one action where host APIs permit. An optional rich-text clipboard experiment may be considered but must be tested independently in every host.

## 7. Build pipeline and assets

### 7.1 Authoring model

Use SVG as the **editable source geometry**, not as the primary insertion format. Each icon SVG uses the common 1,000×1,000 source drawing grid (or normalized equivalent). A build script verifies it, expands strokes to paths and converts to glyph outlines.

Proposed build sequence:

1. Read `symbols.json`/`symbols.yaml` manifest.
2. Validate unique IDs/codepoints, required metadata and source file existence.
3. Normalize SVG geometry (viewBox, scaling, transforms, stroke outline conversion).
4. Generate TrueType font; optional OpenType CFF font.
5. Apply OpenType metadata and `fsType` embedding flags; write semantic version.
6. Convert fonts to WOFF2 and generate CSS and TypeScript exports.
7. Generate canonical glyph SVG previews, web catalog data, printed reference PDF and specimen documents.
8. Run font validators, bounding-box tests, visual regression and smoke test packages.
9. Release immutable versioned artifacts and checksum manifest.

Suggested tools: Python `fontTools` + font generation/conversion tooling (FontForge/FontBuilder, and a vetted SVG path-to-outline converter), `woff2` support, TypeScript/Vite for the catalog. Final tool selection should be driven by reproducible builds and reliable path conversion, not an arbitrary framework preference.

### 7.2 Desktop vs web packages

| Artifact | Purpose | Embedded/installed how |
|---|---|---|
| `SlideMarks-Regular.ttf` | Windows/Mac/Linux desktop | User installs; Office may embed in saved document |
| `SlideMarks-Regular.otf` | Alternative desktop distribution | Optional, after compatibility testing |
| `SlideMarks-Regular.woff2` | Browser/website | Served alongside CSS; may be self-hosted |
| `slidemarks.css` | `@font-face` + namespaced `sm-*` utility classes | Imported into web app |
| `symbols.json` | Canonical IDs, code points, metadata | Bundled with picker or apps |
| `catalog.html` (+ local assets) | Search/copy/preview offline | Open locally; no accounts |
| `SlideMarks-CheatSheet.pdf` | Print reference | No font required if exported with outlines/embedded font |
| `SlideMarks-Examples.pptx` | Demonstrations and table specimens | Font embedded where possible; examples include validation instructions |
| `SlideMarks-Examples.docx` | Word table specimens | Font embedded where possible |
| `glyphs/*.svg` | Designers and fallback assets | Shapes, not cell text |

**Web:** Use a bundled WOFF2 and CSS, never Google Fonts or a third-party runtime. Fonts are protected by standard browser font loading rules/CORS when hosted across origins. A `file://` HTML demo may behave differently by browser; if necessary, ship a single-file self-contained catalog with font embedded as a data URI or document a minimal localhost static server for offline use.

**Example CSS:**

```css
@font-face {
  font-family: 'SlideMarks';
  src: url('./SlideMarks-Regular.woff2') format('woff2');
  font-style: normal;
  font-weight: 400;
  font-display: block;
}
.slidemarks {
  font-family: 'SlideMarks' !important;
  font-weight: 400;
  font-variant-ligatures: none;
  speak: none;
}
```

When glyphs are used as decorative icons on websites, include `aria-hidden="true"`; when semantic, add a real accessible label in the host markup.

## 8. Embedding and compatibility policy

### 8.1 Word / PowerPoint desktop

- Configure editable or installable embedding rights for **our own licensed font**, and test both file size and editability.
- Prefer embedding **all** glyphs for documents recipients will edit; subset embedding is fine for view-only use if validated.
- Maintain sample document procedures for Mac and Windows current desktop PowerPoint and Word versions.
- Embedded font support is application/file-format specific; opening a `.pptx` in an alternate viewer or web editor may still substitute fonts. **Never promise universal rendering.**
- If the font is missing in the target viewer, a PUA code point can display as tofu/empty box: this is correct to flag as a missing dependency, not to disguise with a different shape.

### 8.2 Browser / web

- WOFF2 with self-hosted CSS is the supported web route. Bundle the font with the site or static catalog.
- `@font-face` is not the same as embedding a font *into a Google Slides document*.
- Web PowerPoint/Word behavior is distinct from ordinary web pages; specific tests required.

### 8.3 PDF

- Generate PDF specimens and confirm embedded font/outlined glyph appearance. PDFs are the reliable distribution choice for final viewing/printing, not editable table workflows.

## 9. Catalog UX and cheat sheet

**Phase 1 catalog:** static SPA/site or single-file offline app; grid grouped by family; query and aliases; large preview; at-a-glance exact code point; click-to-copy; copy feedback; size (10–48 pt); foreground/background color controls; dark mode; keyboard navigation; printable output. No logins, analytics or network calls.

**Important:** Preview must use the bundled WOFF2, never default Unicode glyphs. Any missing font condition is surfaced.

**Cheat sheet:** grouped by family, with symbol preview, human name, code point, copy/paste instruction and legend. Generated from current release manifest.

**Potential optional keyboard features:** macOS text replacements, Windows text-expander mappings, optional custom layouts. Keep shortcuts out of the font core because they are platform-specific and may not apply font styling.

## 10. Phase 2 — Office.js Word and PowerPoint add-ins

**Architecture:** one shared `catalog` package and UI; separate host-specific insertion adapters. Add-in manifests are deployment artifacts and not core dependencies.

### Word (more straightforward)

- Task pane searchable by name/category/tags.
- Click a glyph; insert PUA text at selection; set inserted range font name to SlideMarks and optionally copy current point size/color.
- Handle insertion in existing Word table cells; do not alter adjacent content.
- Feature-detect APIs and test Windows/Mac/web versions.

### PowerPoint (important constraint)

Microsoft's published PowerPoint JavaScript table guidance (2026) says **existing table cell text can be updated but cell font formatting cannot subsequently be changed by that table API**. Therefore, *automatic insert-and-style inside arbitrary existing PPT tables is not a committed Phase 2 feature until a proof of capability succeeds.*

Plan three paths:

1. **Ideal, if supported:** insert glyph into text selection/table cell and apply SlideMarks to just that character.
2. **Reliable fallback:** picker copies the PUA character; user pastes into a **preformatted SlideMarks cell** or manually assigns SlideMarks using the ribbon. Add-in must clearly explain this.
3. **New-table authoring:** if useful, generate a new PowerPoint table with correct fonts during table creation (but do not rebuild a user's existing table just to insert one symbol without explicit request).

Do not switch to floating SVGs as a silent workaround: it breaks the key product proposition of true inline table content.

### Add-in acceptance tests

- Install/sideload Word and PowerPoint panes on supported Microsoft 365 Mac, Windows, web hosts.
- Search/load preview offline or in properly hosted HTTPS context (Office task panes may require HTTPS even though the font/catalog alone are offline).
- Insert into plain paragraphs, existing Word tables, ordinary PowerPoint text boxes, PowerPoint tables (the last is a **separate gated experiment**).
- Preserve rest of slide/document. Fail gracefully on unsupported selection type/API requirement set.
- No user account. Separate manifest/deployment instructions; core fonts remain usable without add-in.

## 11. Recommended repository layout

```text
slidemarks/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── docs/
│   ├── PRD.md                     # what / why / requirements
│   ├── design-system.md           # canonical geometry & proofs
│   ├── glyph-inventory.md         # human-readable generated inventory
│   ├── glyph-mapping.md           # PUA allocation/versioning
│   ├── compatibility.md           # supported host/version matrix
│   ├── embedding.md               # desktop, Office, WOFF2, PDF
│   ├── office-js-spike.md          # PowerPoint table API gating experiment
│   └── adr/                       # architecture decisions
├── source/
│   ├── symbols.json               # immutable IDs, names, codepoints, metadata
│   ├── design-tokens.json         # metrics, strokes, grid, geometry
│   ├── glyphs/
│   │   ├── harvey/
│   │   ├── arrows/
│   │   ├── status/
│   │   ├── trends/
│   │   ├── comparisons/
│   │   └── workflow/
│   └── templates/                  # master SVG drawing templates
├── packages/
│   ├── font-builder/               # font compilation, SVG normalization
│   ├── catalog/                    # TS semantic symbol API and search
│   ├── web-font/                   # generated WOFF2, CSS, typings
│   ├── renderer/                   # previews + reference sheets
│   └── office-core/                # generic interface; no host assumptions
├── apps/
│   ├── picker-web/                 # static searchable/offline catalog (phase 1)
│   ├── office-word/                # Office.js task pane + host adapter (phase 2)
│   └── office-powerpoint/          # Office.js task pane + host adapter (phase 2)
├── tests/
│   ├── metrics/                    # family geometry, bbox, advance width
│   ├── cmap/                       # unique mapping and compatibility
│   ├── visual/                     # golden renders/contact sheets
│   ├── font/                       # font tables, encoding, embedding flags
│   ├── web/                        # offline/CSS/copy behavior
│   └── office/                     # manual/automated host acceptance
├── examples/
│   ├── powerpoint/
│   ├── word/
│   ├── html/
│   └── pdf/
├── scripts/
│   ├── build-fonts.*
│   ├── generate-assets.*
│   ├── generate-cheatsheet.*
│   └── verify-release.*
├── dist/                            # generated artifacts, ignored or published
└── .github/workflows/             # CI build/tests/releases
```

### 11.1 Programmatic APIs

```ts
export type SymbolId = string;
export interface SymbolRecord {
  id: SymbolId;
  name: string;
  codepoint: number;
  category: string;
  tags: readonly string[];
  description?: string;
}
export function findSymbols(query: string): SymbolRecord[];
export function getSymbol(id: SymbolId): SymbolRecord | undefined;
export function toCharacter(symbol: SymbolRecord): string;
```

`office-core` defines a host-independent `insertSymbol(id, options)` contract and returns `supported`, `inserted`, `copied_for_manual_paste`, or `unsupported` results. Word/PowerPoint adapters implement it with capability checks. **Never put Office.js calls in the catalog package or SVG build pipeline.**

### 11.2 Reproducibility and release conventions

- One repository; Python for build where useful, TypeScript packages for UI/plugins.
- Lock dependencies, pin font toolchain versions, use deterministic input ordering, publish checksums.
- `symbols.json` is source of truth. Generate reference tables and type unions from it.
- Version font family and codepoint mapping; breaking mapping changes require major version and migration doc (prefer never reassigning PUA values).
- Tag releases; ship zip with fonts, web package, picker and cheat sheet.

## 12. Testing matrix

| Surface | Test | Must pass |
|---|---|---|
| Windows PowerPoint desktop | Use font in an existing table; recolor; resize; align; save/reopen; share with font embedded | P0 |
| Mac PowerPoint desktop | Same as above, with editability verified on a second machine | P0 |
| Windows Word desktop | Insert into table and paragraph, save/reopen with embedding | P0 |
| Mac Word desktop | Same | P0 |
| Linux LibreOffice | Install/use/export PDF; note any office file substitution | P1 |
| Chrome, Firefox, Safari, Edge | WOFF2 and CSS rendering, search/copy; high DPI | P0 |
| Offline web picker | Works with disconnected network using local assets | P0 |
| PDF export | All filled shapes and transparent sections correct | P0 |
| Office web apps | Investigate actual behavior with embedded fonts vs substitutions | P1 / compatibility disclosure |
| Google Slides | Test paste/appearance; document unsupported custom-font cases; SVG only fallback | Non-goal for custom editable font |
| Word Office.js | Insert/format symbol at selection and in a table | Phase 2 |
| PowerPoint Office.js | Discover current selection, insert in text box/table, format inserted run | Phase 2 go/no-go spike |

### 12.1 Geometry automated assertions

- Harvey exterior bounding boxes equal within **1 font unit**; centers identical; all advances identical.
- Percentage wedge angular extents match intended values within numeric tolerance; consistent rim/outline.
- Opposite arrow directions are transforms of one canonical geometry; equal advances and comparable visual boxes.
- Every glyph fits vertical line metric box without unwanted clipping; no unintended overlapping/self-intersecting contours.
- No duplicate PUA assignments or undocumented deletions.

## 13. Risks and decisions

| Risk | Mitigation / decision |
|---|---|
| PUA glyph appears as tofu if custom font missing | Design for missing-font detection and clear installation/embedding instructions; do not fake substitution |
| Clipboard copy does not include font styling | Picker documents apply/select font; optional future HTML clipboard experiment |
| PowerPoint existing-table APIs cannot style inserted text | Phase 2 gated spike; supported fallback is copy/paste into preformatted cell; do not promise full automation |
| Different apps use different line spacing/baselines | Test real table cells; adjust global metrics; publish limitations |
| Different antialiasing engines | Accept pixel-level differences while requiring identical outlines/geometry |
| Harvey partial wedges look too dark due to rims | Design filled geometry against fixed external diameter; inspect at 10 pt |
| Office embedding fails on an otherwise valid font | Check tables/permissions and exact desktop versions; test across devices |
| Web font fails via file:// CORS | Ship self-contained static HTML or documented localhost/offline deployment |
| Build tooling changes glyph geometry | Assert bounding boxes, normalize outlines, produce visual regression contact sheets |
| Licensing third-party icons | Draw original glyphs or track compatible licensed sources; only set embedding rights for artwork the project may legally distribute |

## 14. Suggested milestones and acceptance tasks

**M0 — Prove the hypothesis:** render 15 glyphs; compile TTF/WOFF2; show them in a PowerPoint table and HTML page. Record Mac/Windows output and embedding tests. Independently spike Word/PowerPoint Office.js insertion permissions to protect Phase 2 roadmap.

**M1 — Freeze the visual system:** approve grid, advance, cap alignment, circle diameter, stroke weight, filled-sector rule, naming and PUA allocation. Publish contact sheet.

**M2 — Core glyphs:** finish all P0 and P1 categories, quality review at table sizes, approve symbol registry.

**M3 — Distribution and usability:** static offline picker, cheat sheet, install instructions, specimen files, web CSS and packages.

**M4 — Release quality:** CI, visual regression, mapping stability checks, license review, compatibility matrix; tag v1.0.

**M5 — Phase 2:** shared TS catalog, Word/PowerPoint task panes, independently measured host support and graceful fallback.

## 15. Definition of done

SlideMarks v1.0 is ready when a user can download a small package, install the font, find a symbol in an offline catalog, copy it, paste it into a **preformatted Word/PowerPoint table cell**, change its size/color like text, and share an embedded-font document that passes the verified compatibility matrix—without accounts, add-ins, subscriptions, internet or manually resized icons.

**Phase 2 success is intentionally separate:** the Office.js add-ins improve insertion convenience without making the core font dependent on them. Word formatting is planned; PowerPoint existing-table-cell automated formatting remains a proven-capability gate, not an assumed implementation detail.

## 16. References / validation sources

- Microsoft, *Benefits of embedding custom fonts*: https://support.microsoft.com/en-gb/office/fonts/benefits-of-embedding-custom-fonts
- Microsoft, *OpenType OS/2 fsType embedding rules*: https://learn.microsoft.com/en-us/typography/opentype/spec/os2
- Microsoft, *Work with tables using the PowerPoint JavaScript API*: https://learn.microsoft.com/en-us/office/dev/add-ins/powerpoint/work-with-tables
- Microsoft, *Word add-ins overview*: https://learn.microsoft.com/office/dev/add-ins/reference/overview/word-add-ins-reference-overview
- Microsoft, *Office Add-ins platform*: https://learn.microsoft.com/en-us/office/dev/add-ins/develop/agent-and-add-in
- Microsoft, *Requirement sets*: https://github.com/OfficeDev/office-js-docs-reference/blob/main/docs/requirement-sets/requirement-sets.md
