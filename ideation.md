# SlideMarks — Product Requirements & Design Specification

Draft v0.1 · November 2026

SlideMarks is a lightweight, cross-platform symbol font designed specifically for professional presentations, tables, scorecards, and documents.

The objective is to replace the inconsistent collection of Unicode characters, icons, and individually positioned SVG graphics with a single, coherent visual system.

The project will be font-first, web-compatible, embeddable, offline-capable, and designed for future Word and PowerPoint integration through Office.js.

## 1. What we're building and why

The fundamental problem is not a shortage of icons. It's that existing symbols don't behave consistently when used as text.

SlideMarks should make inserting a Harvey ball, directional arrow, approval indicator, or other business symbol as straightforward as typing a letter.

### Core requirements

| ID  | Requirement                                            | Priority |
| --- | ------------------------------------------------------ | -------- |
| R01 | Native vector glyphs in TTF/OTF fonts                  | Must     |
| R02 | Identical geometry across related symbols              | Must     |
| R03 | Symbols work inline in Word and PowerPoint table cells | Must     |
| R04 | Change size and color using ordinary text formatting   | Must     |
| R05 | No dependence on system-provided symbol glyphs         | Must     |
| R06 | Support font embedding in Office documents             | Must     |
| R07 | Support WOFF2 for websites and web applications        | Must     |
| R08 | Offline searchable symbol catalog                      | Must     |
| R09 | Stable, documented Unicode character mappings          | Must     |
| R10 | No account, subscription, or runtime service required  | Must     |
| R11 | Generate font and SVG assets from one canonical source | Must     |
| R12 | Provide an API/catalog for future Office.js add-ins    | Must     |
| R13 | Optional Regular, Medium, and Bold weights             | Should   |
| R14 | Word and PowerPoint symbol picker add-ins              | Phase 2  |

## 2. The primary design principle

Every glyph is ours. Every dimension is intentional. No platform substitution.

For example, every Harvey ball will use the same circle diameter, center point, advance width, and baseline. Only the filled area changes.

HARVEY BALL FAMILY — DESIGN EXAMPLE

Five symbols, one construction system. The resulting font will use custom vector outlines rather than the illustrated Unicode characters.

This will be a genuine iconographic typeface—not a wrapper around symbols provided by Arial, Segoe UI, or Apple Symbols.

## 3. Complete implementation specification

I've created the full Markdown requirements document, suitable for putting directly into a Git repository or giving to a coding agent.

SlideMarks — Requirements v0.1

Markdown · Product requirements, design guide, architecture, testing and roadmap

Download the complete specification

The document contains:

- 123 proposed glyphs organized into 17 families, with priorities and construction rules.
- Typeface design specifications: 1,000-unit grid, consistent advance widths, stroke weights, optical alignment, and Harvey ball geometry.
- Font generation architecture for TTF, OTF, WOFF2, and SVG exports.
- A stable Unicode Private Use Area mapping strategy.
- Offline HTML picker and printable cheat sheet requirements.
- Monorepo layout supporting independent font, catalog, web, and Office.js packages.
- Release milestones, validation tests, and acceptance criteria.

## 4. Two engineering decisions worth highlighting

First: Embedding permissions are part of the font specification. We'll explicitly configure the OpenType embedding permissions for editable documents, then test real PowerPoint and Word files. Microsoft supports editable font embedding, but actual behavior depends on the application and file.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://support.microsoft.com\&sz=32)

Microsoft Support+1



Second: PowerPoint's JavaScript API has a limitation we need to design around. Microsoft currently documents that existing table-cell text can be updated programmatically, but subsequent cell font formatting is not supported through that table API. This means the Phase 2 PowerPoint add-in requires a feasibility test before we promise one-click insert-and-format into arbitrary existing tables.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn



Word has stronger JavaScript text insertion capabilities.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.microsoft.com\&sz=32)

Microsoft Learn



## 5. Suggested first development milestone

I'd start with just 15 carefully designed glyphs, not the entire library.

Phase 0

Prove the font system works

# 5

Harvey balls

All quarters

# 4

Arrows

Cardinal directions

# 6

Status & trends

Checks, dots, trends

Compile those into a real font, create a specimen PowerPoint table, embed the font, and open the file on another machine.

If the glyphs display consistently at 10–24 pt, are editable as text, and survive document sharing, we've proven the central proposition.

The main architectural decision is to keep the symbol design, font generation, searchable catalog, and eventual Office plugins separate. That way the font remains useful and maintainable even if we never build a single add-in.