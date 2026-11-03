# SlideMarks design goals

Status: **proposed** (2026-11-03). Derived from `SlideMarks_Requirements_v0.1.md` and the Phase 0 spike. The review sheet (`review/specimen.html`) is how each goal is checked.

The one-line test: **a reader should never notice which glyphs came from which family.** Anything in a table cell should look like it was drawn by one hand, at one weight, on one grid.

## 1. One construction per family
Every member of a family is derived from a single parametric construction, never drawn independently. Harvey balls are one ring plus one computed wedge; the four arrows are rotations of one canonical arrow; falling trend is the mirror of rising.
*Checked by:* geometry-group rules in `design-tokens.json` (identical-bounds / same-footprint) and the **onion skin** view.

## 2. One shared frame and optical center
All glyphs sit in a 660 × 660 frame centered at (500, 420) on a 1000-unit em with a 1000 advance. Ink is centered on that point, so any glyph in a centered table cell lands in the same place.
*Checked by:* ink-center findings (±2 units) and the **families** view guides.

## 3. One stroke weight
Line glyphs and outline shapes share a single stroke (currently 56 units). Round caps and joins for line glyphs; geometric shapes keep crisp construction.
*Checked by:* tokens; visually in the size ladder.

## 4. Even visual weight within a family
Members of a family should *feel* equally heavy unless the weight difference carries meaning (Harvey fill level, filled vs empty dot). Optical adjustments (e.g. shrinking a cross so it doesn't overpower a check) are allowed but must be recorded as tokens, not ad hoc edits.
*Checked by:* coverage and weight-vs-family columns; size ladder; scorecard tables.

## 5. Behaves like text
Text color recolors the whole glyph and unfilled areas are transparent. Size and color come from ordinary run formatting. There are no color layers, ligatures or substitutions.
*Checked by:* Ink and Dark controls in HTML; the PowerPoint scorecard slides.

## 6. Legible at 10–12 pt
A glyph that can't be read in a 10–12 pt table cell doesn't belong in the core font (PRD §4.2).
*Checked by:* size ladder and the 12 pt scorecard, in both HTML and PowerPoint.

## 7. Quiet and minimal
No shadows, gradients, decorative detail or emoji styling. Simple geometry that sits alongside Calibri/Segoe/Helvetica without competing.

## 8. Deterministic and traceable
The same tokens and manifest always produce byte-identical fonts. The SVG previews and font outlines come from the same geometry, and code points never move once released.
*Checked by:* source-vs-font overlay; reproducible build hash; manifest validation.

## Open design questions surfaced by the spike
- **Check vs cross weight.** The cross covers about 19% of the frame and the check about 11%, and the cross reads heavier. Decide whether to shrink the cross or enlarge the check.
- **Vertical alignment against text.** The glyph center (420) sits above cap-height center (350). Judge this in real PowerPoint tables before freezing it (PRD §5.1).
- **Stroke weight.** Is 56 too heavy at 36 pt or too light at 10 pt? The PRD's starting value was 48.
- **Trend arrowheads.** The heads read slightly blunt at small sizes. Consider a shorter head or a smaller head angle for this family only.
- **Dots vs Harvey 0%.** The empty dot and the Harvey 0% ball differ only in size. Confirm both are needed and that their purposes are distinct.
