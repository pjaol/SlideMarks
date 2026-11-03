# ADR 0001: Glyphs are generated from parametric code, not hand-drawn SVG

- Status: proposed
- Date: 2026-11-03

## Context
PRD §7.1 proposes SVG files as the editable source geometry, normalized and stroke-expanded at build time. The project's main quality goal is consistency: identical outer geometry within families, a shared center, and one stroke weight (see `docs/design-goals.md`). Hand-drawn SVGs drift, and keeping families consistent then depends on assertions catching the drift after the fact.

## Decision
Each family is a Python builder (`src/slidemarks_build/glyphs.py`) that computes outlines from `source/design-tokens.json`. Members are parameters of one construction: a wedge fraction, a rotation, or a mirror. Strokes are expanded to filled outlines with skia-pathops, and overlaps are removed before compiling to TrueType. SVGs are a build **output** (`dist/svg/`), not the input.

## Consequences
- Consistency holds by construction, and changing one token reshapes the whole family.
- Optical exceptions have to be expressed as tokens or builder parameters, which makes them visible and reviewable.
- Organic or irregular glyphs (people, calendars, the P2 ownership pack) may be awkward to express in code. Those can be added later as SVG-sourced builders that go through the same normalize → compile path. The manifest's `builder` field already allows that.
