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
| **PowerPoint: one path for all text.** Snapshot the text the add-in can see in the selection (text frames, including lists and grouped shapes, and table cells with their runs) → `setSelectedDataAsync` at the real cursor → diff → style what changed: `getSubstring` in a text frame, a `textRuns` rewrite in a table cell that keeps every run's own formatting | `setSelectedDataAsync` is the only insert that reaches the cursor everywhere. PowerPoint for Mac reports the word next to a blinking cursor as the selected text, so the add-in never edits the reported selection (replacing it swallowed the word). Table cells have no substring API, and writing `textRuns` resets anything left out. Text add-ins can't see (SmartArt) still gets the symbol, and the user is told to set its font |
| Gate on `getSelectedDataAsync`: insert only with a blinking cursor or a highlight; refuse when nothing is selected (error 1001) or a whole box or table is selected (the text contains a line break); remove any shape the insert creates | The common API reports the real selection, unlike `getSelectedTextRange` on Mac. A whole selected box would otherwise lose all its text (seen in testing), and `setSelectedDataAsync` without a cursor makes a stray text box (spike) |
| Tables in content placeholders count as tables | They report shape type `Placeholder` with `containedType` `Table` |
| Embedding is **guided**, with detection via `getFileAsync` + a small ZIP reader | Office.js can't embed fonts; prepared copies lose embedding on save (spike) |
| Walkthroughs use real screenshots with highlight boxes where we have them (Mac Preferences, PowerPoint for Windows Options), and HTML mock-ups of the dialogs elsewhere | Users found the mock-ups harder to match to the real window; mock-ups remain where no screenshot exists yet and in the steps that name the user's file |
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

## Verified (Mac, Office 16.114, 2026-11-04)

| Area | Result |
|---|---|
| PowerPoint (2026-11-05, driven live) | ✅ Cursor at the end of a word (the word is kept), bulleted list item, highlighted word (replaced), whole box selected (refused, text untouched), nothing selected (refused, no stray shape), placeholder table and standalone table cells, mixed-format cell (italic "EM" and regular "AIL" kept), empty cell with a text label. SmartArt: inserted, with the "set the font" card. Grouped text boxes: not yet tested |
| Word: paragraph and table cell | ✅ Saved runs have `ascii`/`hAnsi`/`eastAsia`/`cs` all set to SlideMarks; surrounding text unchanged |
| Embedding detection and walkthrough | ✅ Both apps: red → green after following the steps and saving; the saved files contain the embedded font |
| Ribbon icon | ✅ 75% Harvey ball; hashed file names stop Office showing a stale cached icon |
| Font-installed detection | ⚠️ Works in Chrome (standalone picker). Inside Office the web view hides user-installed fonts, so the panel asks instead of accusing |

**Embedding differs between the apps:**
- **PowerPoint:** radio buttons (*Embed all characters*); the dropdown shows the name without extension.
- **Word:** a checkbox (*Embed only the characters used* — leave unticked); the dropdown shows the name **with** `.docx`. Word also embeds every other font the document uses (2.6 MB in testing).

**Word slot carry-over (investigated, mitigated):** text typed immediately after a symbol inherits the symbol's `eastAsia`/`cs` slots. Experiments (`spike/office/scripts/w_*.js`):
- Resetting the font at the cursor through the API doesn't take.
- `w:sym` keeps the font on the symbol only, but Word then reports the character as "(", which breaks screen readers, copy-paste and the standard-character aliases.
- An invisible trailing character with the original formatting works, but leaves hidden content in the document.

None of these is acceptable. In practice:
- Word writes a suitable font back when typed text needs a script SlideMarks lacks; observed for Latin text, where `ascii`/`hAnsi` returned to Cambria.
- With **Add a text label**, the label carries the original formatting, so text after it is completely clean.

**Fixed along the way:** inserted symbols now carry the formatting at the cursor (size, colour, bold), captured with a placeholder. Previously they fell back to the style's default size.

**Not yet verified:** Windows, Office on the web, undo granularity.
