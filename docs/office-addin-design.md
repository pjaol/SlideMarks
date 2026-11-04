# SlideMarks Office add-in: design

Status: building (2026-11-04). Inputs: `docs/charmap.md` (requirements), `docs/office-js-spike.md` (proven API behavior). Excel is out of scope: `.xlsx` can't embed fonts.

## What it is

A **SlideMarks** button on the Home tab of Word and PowerPoint opens a task pane with:
1. **Picker:** search and browse all glyphs by family, preview a glyph, and **Insert** it at the cursor (or Copy). Recent and favorite glyphs are kept, and it works from the keyboard.
2. **Setup:** a short checklist shown when something needs attention:
   - is the SlideMarks font installed?
   - is it embedded in *this* file?

   Each item has a step-by-step walkthrough for the user's platform that names their file. Once both items are green it collapses to a small status badge.

The same picker also ships as a standalone page (`dist/web/picker.html`) with Copy instead of Insert. It works offline and outside Office.

## Decisions

| Decision | Why |
|---|---|
| Plain HTML, CSS and ES modules; no framework, bundler or `package.json` | Keeps the repo lean (user preference). The UI is small, and the spike showed nothing needs a build step |
| `slidemarks build` assembles `dist/office/` from `apps/office/` + generated data | One build for font, web and add-in; catalog and manifest come from `source/symbols.json` |
| Office.js from Microsoft's CDN in the add-in only | Required for Marketplace; the standalone page doesn't load it, so it works offline |
| Insert the **preferred character** (standard Unicode alias when one exists) | Screen readers announce aliases (verified with VoiceOver) |
| **Word:** `insertOoxml` with all four font slots | `insertText` + `font.name` leaves the East Asian slot unset, and Word draws PUA from that slot |
| **PowerPoint text:** replace the selection, or insert at the cursor and style it | Verified for selections; the collapsed-cursor path is verified live |
| **PowerPoint table cell:** snapshot cells → `setSelectedDataAsync` → diff → rewrite `textRuns`, carrying uniform cell formatting | The only path that works in existing tables (spike). Mixed formatting can't be read, so the user is told and given a choice instead of a silent flattening |
| Never call `setSelectedDataAsync` without a confirmed text cursor | It creates stray shapes otherwise (spike) |
| Embedding is **guided**, with detection via `getFileAsync` + a small ZIP reader | Office.js can't embed fonts; prepared copies lose embedding on save (spike) |
| Walkthroughs use illustrated HTML mock-ups of the real dialogs, showing the user's actual file name | Hand-drawn mock-ups stay accurate in light and dark themes and can name the file; screenshots can't |
| Dev hosting: `slidemarks office-serve` (HTTPS on localhost:3443 with Microsoft's dev certificate); sideload with `npx office-addin-dev-settings` | Proven in the spike; no Node project |
| Production hosting and Marketplace: **not in this build** | Publishing is a public step and needs a domain decision. The build generates a production manifest for any base URL so it's ready |

## Out of scope for this build
- Publishing (hosting, domain, Marketplace listing, privacy and terms pages).
- Windows and Office on the web verification (the code feature-detects; the testing is a separate pass).
- Excel.

## Verification plan
- Python tests: generated manifest (valid XML, URLs, hosts), catalog data, and build outputs.
- agent-browser tests on the standalone picker: search, filter, preview, keyboard navigation, copy, and an axe audit.
- Live runs in PowerPoint and Word on this Mac: insert in text, selection and table cell; mixed-format warning; font and embedding status.
