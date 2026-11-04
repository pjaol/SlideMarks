# SlideMarks design system

Status: v0.1.0 draft (2026-11-03). Values live in `source/design-tokens.json`, and the glyph inventory and code points in `source/symbols.json`. This document records the **why** behind them. Design principles are in `docs/design-goals.md`.

## Shared metrics

| Property | Value | Notes |
|---|---|---|
| Em / advance | 1000 / 1000 | every glyph |
| Ascender / descender | 800 / −200 | `USE_TYPO_METRICS` set; hhea, typo and win metrics agree |
| Frame | x 170–830, y 90–750 | ink must stay inside unless the manifest records a `frameException` |
| Center | (500, 420) | asymmetric glyphs are centered by ink box |
| Stroke | regular 56, thin 36, heavy 84 | thin/heavy only for explicit weight variants and separators |
| Caps / joins | round for line glyphs; sharp for geometric outlines (squares, diamonds, process boxes, progress segments) | |
| Arrowhead | open, 225 long, 45° half-angle | shared by every arrow, every trend (including oscillating) and every curved arrow; loops and the branch arrow are the exceptions (below) |

## Decisions

| # | Decision | Why |
|---|---|---|
| D1 | Glyph center stays at y = 420 | Checked in PowerPoint and Word on Mac and Windows, where glyphs sit well against Calibri at 10–36 pt |
| D2 | Regular stroke stays at 56 (PRD suggested 48) | Holds at 10 pt on Windows and isn't heavy at 36 pt |
| D3 | Trend shapes unchanged | Reviewed on Windows; reads well enough |
| D4 | Cross half-span reduced from 250 to 225 | The cross read heavier than the check |
| D5 | Rating dots (440) are kept separate from Harvey 0% (660) | They mean different things (a rating mark vs a percentage) and differ clearly in size |
| D6 | RAG family is two new glyphs (ring-with-dot, half-filled) and reuses `dot-empty`/`dot-filled` | The PRD's "solid dot" and "empty ring" would duplicate existing glyphs, and §4 says not to duplicate |
| D7 | Heavy check pulls its centerline in so its ink box matches the regular check | Weight variants differ in weight only, not size |
| D8 | Loop arrows use a 150-unit head | The shared 225 head is as long as the loop radius and collides with the arc |
| D9 | Diagonal arrows are exact 45° rotations, so their ink box is smaller than the cardinal arrows' | Rotation keeps every direction the same construction (PRD §5.2.5) |
| D10 | Workflow nodes and Ownership glyphs are status `candidate` | PRD lists them as P2, and legibility at 10–12 pt decides whether they stay in the core font |
| D11 | Long arrows and the horizontal separator may leave the frame (`frameException`) | Long arrows need the length; the separator spans the full advance so repeated glyphs join into one rule |
| D12 | Trend oscillating ends in the shared arrowhead, pointing level after two even swings | Every trend carries a head; ending level keeps it neutral instead of reading as falling. Its repeated swings separate it from trend flat (one wiggle, then level) |
| D13 | Circled 1 is centered on its stem, not its ink box | Ink-box centering let the flag pull the stem right of center; numerals are judged by their main stroke |
| D14 | Arrows and comparison operators are also mapped from their standard Unicode code points; the missing-font empty-box rule is relaxed for those glyphs only | Screen readers can name standard characters but never PUA ones; a system arrow keeps the meaning when the font is missing. See ADR 0002 and `docs/accessibility.md` |
| D15 | Branch arrow uses a 150-unit head (like loops), with its tips at the frame edges | With the shared 225 head, the two inner head arms pointed at each other about 166 units apart (about 4 px at picker size) and read as one bar; now about 428 units apart |

## Code point blocks

| Range | Family |
|---|---|
| E000–E00F | Harvey balls (quarters E000–E004, deciles E005–E00C) |
| E010–E01F | Progress segments |
| E020–E04F | Arrows: direction, bidirectional, variants, curved, chevrons (E040–E047) |
| E050–E05F | Checks & outcomes, circular statuses |
| E060–E06F | Rating dots/squares/diamonds, RAG |
| E070–E07F | Trend indicators |
| E080–E08F | Priority & emphasis |
| E090–E09F | Business comparisons |
| E0A0–E0AF | Decision & workflow nodes |
| E0B0–E0B7 | Simple markers |
| E0B8–E0BF | Ownership & action |
| E0C0–E0FF | Reserved; never reuse a removed glyph's code point |

Some glyphs are also reachable through standard Unicode aliases (D14). Those aliases are listed per glyph in `source/symbols.json` and `docs/glyphs.md`.

The Phase 0 glyphs kept their original code points. Code points are stable from here on, even before 1.0.

## Consistency checks (automatic, measured from the compiled TTF)

- Advance width is 1000; the ink center is within ±2 units of (500, 420); ink stays inside the frame unless excepted.
- `identical-bounds` groups (Harvey, progress, rating shapes, circular statuses, priority circles, stars, filled chevrons) share an exact ink box within ±1 unit.
- `same-footprint` groups (arrow directions and weights, trend pairs, chevrons, comparison angles) share box dimensions in any orientation.
- Everything else is judged visually in `review/specimen.html` (family filter, onion skin, size ladder) and in the Office specimens.
