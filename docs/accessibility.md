# Accessibility

Status: v0.1.0 (2026-11-03). This page describes what SlideMarks does for screen-reader users, what a font can't do, and how to author accessible documents with it. The decision behind the dual encoding is in [ADR 0002](adr/0002-dual-encoding-unicode-aliases.md).

## What a font can and can't do

Screen readers read **characters**, not glyphs. They never see the font's drawing, its glyph names or its metadata. So:

- **Private Use Area glyphs (U+E000…) have no meaning to a screen reader.** Depending on the reader and its settings they're skipped or announced as an unknown symbol. No font-level metadata changes that.
- **A standard Unicode character has a name** that screen readers may know ("right arrow", "less than"). SlideMarks therefore also answers to a standard code point for glyphs with an exact equivalent: the same outline, reached by two code points.
- **Ligatures are not used.** PowerPoint doesn't apply OpenType features and Word applies ligatures only when the user turns them on, so they would fail in exactly the documents SlideMarks targets.

**Verified so far (2026-11-03), VoiceOver on macOS:**
- Standard aliases are announced by name and PUA code points are silent, for the same SlideMarks glyph, in both Word and PowerPoint for Mac.
- A custom VoiceOver pronunciation makes a PUA glyph speak its meaning ("Harvey ball 50 percent").

Windows screen readers (NVDA, Narrator, JAWS) have not been tested yet.

**Goal: speech should say what the symbol means**, e.g. "Harvey ball 50 percent", not what it looks like ("circle with right half black"). There are three ways to get there:
1. **Visible text** next to the symbol. Works for everyone.
2. **Pronunciation packs** (below), for people who install them.
3. **Standard Unicode aliases**, only where the official character name already *is* the meaning.

**A standard code point is not proof that a glyph is screen-reader compatible.** Pronunciation varies by screen reader, language, verbosity and punctuation settings, and application. A glyph counts as verified only for the environments recorded in [Test results](#test-results).

## Two encodings, one glyph

| | PUA code point | Standard Unicode alias |
|---|---|---|
| Example | `U+E021` | `U+2192` RIGHTWARDS ARROW |
| With SlideMarks applied | SlideMarks arrow | the identical SlideMarks arrow |
| Font missing | empty box ("install or embed SlideMarks") | the system's own right arrow |
| Screen reader | no meaning | may announce "right arrow" |
| Available for | every glyph | only exact equivalents (below) |

**Prefer the alias when the glyph has one.** The glyph reference lists it in the *Standard Unicode* column, and `slidemarks.css` uses it automatically. All PUA code points stay valid permanently.

**Which glyphs have aliases.** Only unambiguous directional arrows and mathematical comparison operators:

- ← → ↑ ↓ ↖ ↗ ↘ ↙ ↔ ↕ ⤡ ⤢
- = ≠ ≈ < > ≤ ≥

Weight and length variants (thin, heavy, short, long) don't get aliases, because they aren't the canonical rendering of those characters. Status marks such as ✓ and ✗ need screen-reader testing first. Harvey balls, progress, RAG and trend glyphs have no exact Unicode equivalent and stay PUA-only.

**Rules for adding an alias** (the first three are enforced by `manifest.py`):
- It must be a standard character outside the Private Use Area.
- It must never be a letter, digit, space or control character.
- Each alias belongs to exactly one glyph.
- **Its official Unicode name must convey the glyph's meaning.** It isn't enough to match the shape. ◑ is named "circle with right half black", so it is *not* an alias for Harvey ball 50%, and ① ("circled digit one") is not an alias for priority 1. Those glyphs get their meaning from visible text or a pronunciation pack.

## Authoring patterns

### PowerPoint and Word

The reliable rule: **a symbol must never be the only carrier of meaning.** Pair it with text that a screen reader can read.

1. **Symbol plus visible text in the same cell**, e.g. a Harvey ball followed by "75%", or a check followed by "Done". This is the most robust pattern. See the *Accessible scorecard* in `review/specimen.pptx` / `.docx`.
2. **Use the standard character for arrows and comparisons**, e.g. `→` rather than `U+E021`.
3. **Mark the header row** (Table Design → Header Row) so readers announce column headers with each cell.
4. **Add a legend** when a table uses several symbols, e.g. a Harvey ball followed by "= 75% complete".

What doesn't work:
- **Alt text** applies to pictures and shapes, not characters.
- **Hidden text** is generally skipped by screen readers.
- **Glyph names inside the font** are never read.

### Checking a document

`slidemarks check` lints PowerPoint and Word files for these problems:

```sh
uv run slidemarks check deck.pptx report.docx     # human-readable; exit code 1 if any errors
uv run slidemarks check deck.pptx --json          # machine-readable
```

| Rule | Severity | Meaning |
|---|---|---|
| `silent-symbol` | error | A table cell or paragraph contains only SlideMarks private-use symbols, so a screen reader reads nothing. Add visible text |
| `font-not-applied` | error | A SlideMarks character is in a run explicitly set to another font, so it shows as an empty box |
| `prefer-standard` | warning | A private-use arrow or comparison sign where the standard character would be announced by name |
| `no-header-row` | warning | A table using SlideMarks has no header row, so cells are read without their column headers |
| `font-not-embedded` | warning | The file uses SlideMarks but doesn't embed it, so recipients without the font see empty boxes |
| `unknown-code-point` | warning | A private-use character that SlideMarks doesn't define |

Limitations:
- Font checks only see fonts set directly on a run. Fonts inherited from styles, layouts or themes aren't resolved.
- `silent-symbol` doesn't know whether the reader has a pronunciation pack installed. Visible text is the only fix that works for every recipient.

### PDF

PDFs exported from Word or PowerPoint contain the same characters as the document. PUA glyphs carry no meaning, while aliases and visible text do. Export with accessibility tags on:
- Windows: **Save as PDF → Options → Document structure tags for accessibility**.
- Mac: **Best for electronic distribution and accessibility**.

### Web

Glyph classes are **decorative by default**. The generated CSS gives each glyph empty alternative text (`content: "\E003" / ""`), so screen readers don't announce a private-use character. Browsers without CSS alt-text support fall back to the plain declaration. Decide per use:

```html
<!-- Decorative: meaning is already in the text -->
<span class="slidemarks sm-harvey-75" aria-hidden="true"></span> 75% complete

<!-- Meaningful on its own: give it a role and a name -->
<span class="slidemarks sm-harvey-75" role="img" aria-label="Harvey ball 75 percent"></span>
```

Don't rely on CSS generated content for meaning: some browser and screen-reader combinations don't expose it. And don't put `aria-label` on a plain `<span>` without `role="img"`, because ARIA ignores labels on generic elements.

**Labels as data.** `dist/web/slidemarks.json` lists every symbol by id with:
- `char` (the preferred character);
- `codepoint`, `puaCodepoint` and `unicodeAliases`;
- `cssClass`;
- `spokenLabel` (use it as the `aria-label`);
- `needsContext`.

Read labels from there instead of copying them by hand. `dist/web/example.html` shows the patterns above working, including a table with real header cells.

**Users who override fonts.** Some readability tools and dyslexia extensions force one font on every page. User style sheets beat the `!important` in `slidemarks.css`, so SlideMarks glyphs then show as empty boxes or system symbols. This affects every icon font and can't be fixed in CSS. Where a symbol must always be visible, use the generated SVG instead, with a text alternative:

```html
<img src="svg/harvey-75.svg" alt="Harvey ball 75 percent" width="20" height="20">
```

Symbols already paired with visible text (pattern 1) still read correctly when the glyph is lost.

**Contrast and color.**
- Meaningful symbols need at least **3:1** contrast against their background (WCAG 1.4.11 Non-text Contrast). Check the lightest glyphs most carefully at small sizes: the **thin arrows** and the **empty progress segments** use the 36-unit thin stroke, and the **separators** are thin by design.
- Color must never be the only signal (WCAG 1.4.1 Use of Color). A red and a green dot are the same glyph to a color-blind reader. The RAG family uses distinct shapes (ring, ring with dot, half, full) for this reason. Use shape or text, not tint alone.
- Glyphs are text, so they follow the user's text color in high-contrast modes, such as Windows contrast themes and forced colors. Test this in your own pages; no extra CSS is needed for the glyph itself.

## Pronunciation packs

Every major screen reader lets users add their own pronunciations. Each build generates packs from the manifest that map every SlideMarks code point to its `spokenLabel`. With a pack installed, the Harvey ball at U+E002 is spoken as "Harvey ball 50 percent" in any app.

Packs only help people who install them. They suit teams using SlideMarks internally. Recipients without a pack still need visible text.

| Screen reader | File (in `dist/screen-readers/` and the release zip) | Install | Status |
|---|---|---|---|
| **VoiceOver** (macOS) | `voiceover/SlideMarks-pronunciations.voprefs` (reference only; **don't import it directly**) | Merge into your own settings, then import (see *Installing the VoiceOver pack* below) | Pronunciations work once installed; merge install verified (2026-11-03) |
| **NVDA** (Windows) | `nvda/SlideMarks-symbols-<version>.nvda-addon` | Open the file, confirm the install, restart NVDA. Needs NVDA 2024.3 or later. | Not yet tested |
| **JAWS** (Windows) | `jaws/slidemarks-jaws-symbols.txt` | Append the lines to the `.sbl` symbol file of your synthesizer in your JAWS user settings folder, e.g. `%APPDATA%\Freedom Scientific\JAWS\<version>\Settings\enu\`, then restart JAWS | Not yet tested |

### Installing the VoiceOver pack

VoiceOver Utility's import **replaces** each kind of preference with the file's contents; only custom labels merge ([Apple](https://support.apple.com/guide/voiceover/export-import-and-reset-voiceover-preferences-vo27926/mac)). Importing a SlideMarks-only file therefore deletes the user's existing pronunciations, including Apple's defaults. So install by merging into the user's own export:

1. VoiceOver Utility (Control-Option-F8) → **File → Export Preferences**. Keep this file: it is also your backup.
2. `uv run slidemarks voiceover-merge "<your export>.voprefs"` writes `<your export> + SlideMarks.voprefs`, containing everything you exported plus the SlideMarks pronunciations. Running it again is safe.
3. VoiceOver Utility → **File → Import Preferences** → choose the merged file.

To undo, import the original export from step 1.

## Semantic metadata in the manifest

Every glyph in `source/symbols.json` carries:

| Field | Meaning |
|---|---|
| `spokenLabel` | What the symbol **means**, as it should be spoken, e.g. "Harvey ball 75 percent", "progress 2 of 4", "right arrow". Used by the pronunciation packs, web labels, catalogs and future add-ins |
| `needsContext` | `true` when the glyph encodes a value or status whose meaning depends on the document (ratings, RAG, priority, trends). Always pair these with text. |
| `unicodeAliases` | Standard code points that draw the same glyph (may be empty) |
| `tags` | Search keywords |

The manifest is the source of truth. Nothing in the font is advertised as screen-reader metadata.

## Testing protocol

Use the **Encoding test** table in `review/specimen.pptx` / `.docx`. Each row shows a glyph as its PUA character and its standard alias, both in SlideMarks.

1. Confirm the two columns look identical. A difference is a build bug.
2. Read each row with the screen reader in table navigation, and also by character where possible.
3. Record the results below: app and version, OS, screen reader and version, punctuation or verbosity level, glyph, and what was spoken for the PUA and for the alias.
4. Repeat for the **Accessible scorecard** to confirm the visible text is read with each cell.

Priority environments: VoiceOver with PowerPoint and Word on macOS; NVDA and Narrator with PowerPoint and Word on Windows; then JAWS.

**Web:** open `dist/web/example.html` from a local server (e.g. `python3 -m http.server` in `dist/web`). Check that:
- decorative glyphs are silent;
- named glyphs are announced by their label ("Harvey ball 75 percent");
- table cells are read with their headers.

Test VoiceOver with Safari 17.4+, NVDA with Firefox 128+ and Chrome, and Narrator with Edge.

**Automated (every `uv run pytest`):** `tests/test_web_a11y.py` drives Chrome through [agent-browser](https://github.com/vercel-labs/agent-browser), the tool already used for visual review. It checks every glyph:
- class-only glyphs put no private-use characters and no names into the accessibility tree;
- every `role="img"` glyph is exposed with exactly its `spokenLabel`;
- the example table cells carry their text and headers;
- the example page passes an axe-core audit (agent-browser's built-in `a11y` command).

This covers Chrome's accessibility tree, not what a screen reader actually says. The manual tests above are still needed. The tests skip where agent-browser isn't installed.

## Test results

| Date | App / OS | Screen reader (version, punctuation level) | Glyph | PUA spoken | Alias spoken | Notes |
|---|---|---|---|---|---|---|
| 2026-11-03 | Word for Mac (Microsoft 365), macOS 26 | VoiceOver (default punctuation) | `progress-2-4` (PUA U+E012, Families table) | caption "[?], selected": unknown character, no name | n/a (no alias) | Confirms PUA glyphs carry no meaning for VoiceOver |
| 2026-11-03 | Word for Mac (Microsoft 365), macOS 26 | VoiceOver (default punctuation) | `arrow-left` (Encoding test table) | blank: only the row header "Arrow left" is announced | **"left arrow"** | Same SlideMarks glyph in both cells. VoiceOver reads the row's first cell as a header, then the content: "Arrow left, left arrow" |
| 2026-11-03 | PowerPoint for Mac (Microsoft 365), macOS 26 | VoiceOver (default punctuation) | arrows; `compare-approx`, `compare-not-equals`, `compare-less`, `compare-greater-equal` (Encoding test slides) | blank | **announced by name** (approximately/almost equal, not equal, less than, greater than or equal) | Reported "all came out clean". Same pattern as Word: PUA silent, standard alias spoken |
| 2026-11-03 | Word for Mac (Microsoft 365), macOS 26 | VoiceOver with a custom **Pronunciation** entry (VoiceOver Utility → Speech → Pronunciation, All Apps) | `harvey-50` (PUA U+E002) | **"Harvey ball 50 percent"** (from the substitution) | n/a | VoiceOver substitutions work on PUA characters, so a pronunciation pack can give every glyph its meaning |
| 2026-11-03 | Word for Mac (Microsoft 365), macOS 26 | VoiceOver with the generated pack imported (`SlideMarks-pronunciations.voprefs`) | PUA glyphs in the Families and Encoding test tables | **spoken by meaning** | n/a | Import **replaced** the existing pronunciation list (Apple's defaults were removed) |
| 2026-11-03 | Word for Mac (Microsoft 365), macOS 26 | VoiceOver with the generated pack imported | Accessible scorecard (glyph followed by visible text in one cell) | not read | n/a | Under investigation: substitution may not apply when the glyph shares a cell with other text |
| 2026-11-03 | VoiceOver Utility, macOS 26 | n/a | Merge install: user export + `slidemarks voiceover-merge`, then Import Preferences | n/a | n/a | **Worked**: Apple's default pronunciations restored alongside the SlideMarks entries. Accessible-scorecard behavior still needs an experienced screen-reader tester |
