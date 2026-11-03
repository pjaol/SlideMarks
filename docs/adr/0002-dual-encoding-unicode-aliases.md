# ADR 0002: Dual encoding with standard Unicode aliases for accessibility

- Status: accepted
- Date: 2026-11-03

## Context
Screen readers read characters, not fonts. Every SlideMarks glyph sits on a Private Use Area code point, which carries no meaning for assistive technology, and no font table offers a per-glyph spoken label that screen readers honor. OpenType ligatures (readable text drawn as a symbol) don't work in PowerPoint and are off by default in Word. Standard Unicode symbols such as arrows and comparison operators *are* commonly announced by name.

PRD principle 2 says a missing font must be visible as missing (an empty box) and never disguised by a substitute glyph.

## Decision
- One font, one outline per glyph. A glyph may also be mapped from **standard Unicode aliases** (`unicodeAliases` in the manifest), which share its glyph in the `cmap`.
- Aliases are added only where the standard character's official Unicode name conveys the glyph's meaning (a matching shape is not enough: ◑ "circle with right half black" is not Harvey ball 50%). Initially that's the directional arrows and the mathematical comparison operators. Weight and length variants, status marks, Harvey balls and other SlideMarks-specific glyphs keep PUA-only mappings.
- **Principle 2 is relaxed for aliased glyphs only.** If the font is missing, an aliased character falls back to the system's equivalent symbol, which preserves the meaning. PUA glyphs still show as empty boxes.
- Pickers, CSS and docs prefer the alias when one exists. PUA code points are never removed or renumbered.
- No ligatures, no separate "semantic" font family, and no font metadata presented as screen-reader labels.
- Semantic metadata (`spokenLabel`, `needsContext`) lives in the manifest. It drives generated screen-reader pronunciation packs (NVDA add-on, JAWS symbol lines, VoiceOver pronunciations), which make PUA glyphs speak their meaning for users who install them, plus web labels and the future add-ins.

## Consequences
- Existing documents are unaffected; new documents can carry meaningful characters for arrows and comparisons.
- The font's `cmap` covers a few Basic Latin characters (`=`, `<`, `>`), so text typed in SlideMarks gets the SlideMarks drawings of those operators. Letters and digits are never mapped.
- Screen-reader support is claimed only per tested environment (`docs/accessibility.md`, *Test results*), never inferred from a code point.
- For PUA-only glyphs, accessibility depends on authoring: visible text alongside the symbol.
