# Office.js insertion spike: findings

- Date: 2026-11-04
- Branch: `spike/powerpoint-insert` (code in `spike/office/`, throwaway)
- Environment: macOS 26, PowerPoint and Word for Mac 16.114.3 (Office.com build), add-in sideloaded with `office-addin-dev-settings`
- Requirement sets: PowerPointApi 1.1–1.10 and WordApi 1.1–1.9 all supported
- Not yet tested: Windows, Office on the web, the visual rendering of inserted symbols with SlideMarks installed

## Question

Can an Office add-in insert a SlideMarks symbol **at the user's cursor**, in ordinary text and inside an existing table cell, with only the symbol set to SlideMarks and the surrounding text and formatting unchanged? (PRD F-16, F-17; `docs/charmap.md` §2)

## Answer

**Yes, in both apps.** PowerPoint table cells need a workaround with one limitation.

| Context | Recipe | Result |
|---|---|---|
| Word: paragraph or table cell | `getSelection().insertOoxml(run, "Replace")`, where the run sets all four font slots | ✅ Inline at the cursor, surrounding text untouched, no extra paragraph |
| PowerPoint: text box or placeholder | `getSelectedTextRange()`, then set `.text` and `.font.name` | ✅ Only the symbol becomes SlideMarks |
| PowerPoint: cursor in a table cell | Snapshot cell texts → `setSelectedDataAsync(symbol)` → diff to find the cell → read the cell's uniform font → rewrite `TableCell.textRuns` with symbols in SlideMarks | ✅ Symbol at the cursor, styled; text and uniform formatting kept |
| PowerPoint: table cell with **mixed** formatting | Same | ⚠️ Mixed run formatting (e.g. one bold word) can't be read, so the rewrite would flatten it. Warn, or fall back to copy and paste |

## What we learned

### Word
- `insertText` + `font.name` is **not enough**. Word classifies Private Use Area characters as East Asian (`w:hint="eastAsia"`), and `font.name` only sets the ASCII and high-ANSI slots. The symbol then renders in the theme's East Asian font, and `font.name` reads back "Calibri". Inserting a run as OOXML with `ascii`, `hAnsi`, `eastAsia` and `cs` all set to SlideMarks fixes it.
- Word can place the cursor programmatically (`range.select()`), so Word insertion was tested end to end with no user interaction.

### PowerPoint
- `getSelectedTextRange()` with the cursor **inside a table cell** returns an object whose `text` reads as empty, but `start`, `length` and `font` throw `InvalidArgument`, and **setting `.text` throws** too. This matches [office-js#6906](https://github.com/officedev/office-js/issues/6906).
- `Shape.textFrame` on a table shape throws `InvalidArgument`.
- `setSelectedDataAsync` **does** insert at the cursor inside a table cell, but the symbol inherits the cell's font, and it can't be styled through the selection afterwards.
- No API reports *which* cell holds the cursor. Diffing every cell's text before and after the insert identifies it reliably (exactly one cell changes).
- `TableCell.textRuns` is **write-only on Mac** (reading returns nothing). Writing runs works and supports per-run fonts.
- Rewriting `textRuns` drops existing formatting in that cell. `TableCell.font` reads the cell's formatting when it's uniform (and `null` for any mixed property), so uniform formatting can be carried onto the new runs. Verified: a bold 28pt green cell stayed bold 28pt green, with the symbol in SlideMarks at the same size and color.
- **Never call `setSelectedDataAsync` without a text cursor.** With a newly created slide or programmatic selection, it inserted the symbol into a **new rectangle shape**. With the whole table selected (no cursor), it did nothing, which the diff detects ("click into a cell").
- PowerPoint's AppleScript can't place a cursor in a table cell, so the table tests needed a human click. Every other step was driven remotely.
- `font.name` in PowerPoint sets only the Latin slot (`a:latin`). Our generated specimens set all four slots. **Open question:** does a Latin-only symbol render in SlideMarks on Windows, where PowerPoint may classify Private Use Area characters differently? Test on Windows.

## Consequences for the picker (`docs/charmap.md`)

1. **Insert at cursor is viable** in Word and PowerPoint, including existing PowerPoint tables. The original spec's gate (PRD F-17) is cleared on Mac.
2. Separate host adapters are required:
   - **Word:** OOXML run insertion.
   - **PowerPoint:** a text-range path and a table-cell path (diff + `textRuns`).
3. The PowerPoint table path must:
   - check that exactly one cell changed;
   - read the cell's font and refuse to flatten mixed formatting without telling the user;
   - offer copy and paste as the fallback.
4. Insertion goes through two API calls in PowerPoint tables, so undo may take two steps. Untested.
5. The inserted symbol needs the SlideMarks font **installed** (or embedded) to display. Without it, the add-in inserts correctly, but users see a "?" box. The picker should detect and explain this.

## How the spike was driven (reusable for the real add-in's tests)

- `npx office-addin-dev-certs install` (trusted localhost HTTPS) and `npx office-addin-dev-settings sideload manifest.xml desktop --app powerpoint|word` (sideload and launch with the task pane open), with no `package.json` or bundler.
- `spike/office/server.py`: HTTPS static server, plus `/log` (probe results), `/file` (the document exported via `getFileAsync`) and `/cmd` (remote commands the pane polls for, including `script:<name>` to run `spike/office/scripts/<name>.js`).
- Verification: the exported `.pptx`/`.docx` inspected with python-pptx and raw XML, so every claim above is checked against the saved file, not just the API's return values.
