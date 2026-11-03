# SlideMarks

A presentation symbol font (Harvey balls, arrows, status marks, trends) that behaves like text in Word and PowerPoint table cells. See `SlideMarks_Requirements_v0.1.md` for the full spec and `docs/design-goals.md` for the design principles.

## Build and review

```sh
uv run slidemarks build          # compile font + regenerate review specimens
uv run slidemarks build --strict # fail if any consistency finding
```

Outputs:

| Path | What |
|---|---|
| `dist/SlideMarks-Regular.ttf` / `.woff2` | The font |
| `dist/svg/*.svg` | Per-glyph SVG generated from the same geometry |
| `review/specimen.html` | Review sheet: families with guides, onion skin, size ladder, tables, source-vs-font, measurements. Opens offline. |
| `review/specimen.pptx` | Same checks in real PowerPoint tables. The font is embedded (uncompressed EOT in `ppt/fonts/font1.fntdata`), so no install is needed. Verified in PowerPoint for Mac without the font installed, 2026-11-03. Windows not yet tested. |
| `review/specimen.docx` | The same families, scorecards and size ladder in Word. The font is embedded as an obfuscated `.odttf` (ECMA-376 §17.8.1). Verified in Word for Mac without the font installed, 2026-11-03. Windows not yet tested. |

## Where things live

- `source/design-tokens.json`: every dimension (frame, center, stroke, family parameters). Change here to restyle a family.
- `source/symbols.json`: immutable ids, PUA code points, names, tags, and which builder draws each glyph.
- `src/slidemarks_build/glyphs.py`: one builder per family (see `docs/adr/0001-parametric-glyph-source.md`).

## Adding a glyph

1. Add an entry to `source/symbols.json`, with a new code point in its family's block. Never reuse a code point.
2. Use an existing builder with new params, or add a builder to `glyphs.py` driven by tokens.
3. Run `uv run slidemarks build`, open `review/specimen.html`, and check the onion skin and size ladder against its family.
