# Contributing to SlideMarks

This guide is for people building or changing the font. If you just want to use SlideMarks, see the [README](README.md).

Background reading:
- `SlideMarks_Requirements_v0.1.md`: the product spec.
- `docs/design-goals.md`: the design principles.
- `docs/design-system.md`: metrics, design decisions and code point blocks.
- `docs/adr/`: architecture decisions.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run slidemarks build            # compile the font and regenerate everything below
uv run slidemarks build --strict   # also fail if there are any consistency findings
uv run slidemarks package          # build, then write dist/SlideMarks-<version>.zip
uv run pytest                      # manifest, alias, font, CSS and screen-reader pack tests
uv run slidemarks voiceover-merge <export.voprefs>   # add SlideMarks pronunciations to a VoiceOver export
```

## What a build produces

| Output | Audience | Notes |
|---|---|---|
| `dist/fonts/SlideMarks-Regular.ttf` | users | Desktop font |
| `dist/web/SlideMarks-Regular.woff2`, `slidemarks.css` | users | Web font plus generated `sm-<id>` classes |
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
src/slidemarks_build/
  geometry.py          path primitives (circles, arcs, strokes, booleans)
  glyphs.py            one builder per family; all geometry derives from tokens
  font.py              TTF/WOFF2/SVG compilation
  metrics.py           consistency checks measured from the compiled TTF
  manifest.py          manifest validation (ids, code points, Unicode aliases, semantic fields)
  office_fonts.py      EOT (PowerPoint) and obfuscated ODTTF (Word) embedding
  specimen_*.py        review sheets (HTML, PPTX, DOCX)
  web.py, reference.py, package.py, screen_readers.py   user-facing outputs
tests/                 pytest suite
docs/                  design docs, ADRs, accessibility, generated glyph reference
review/                generated review specimens
dist/                  generated user artifacts
```

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

## Releases

1. Bump `manifestVersion` in `source/symbols.json`.
2. Run `uv run pytest` and `uv run slidemarks package --strict`.
3. Attach `dist/SlideMarks-<version>.zip` to a GitHub release.
