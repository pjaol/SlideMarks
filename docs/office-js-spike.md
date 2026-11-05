# Office.js insertion spike: findings

- Date: 2026-11-04
- Branch: `spike/powerpoint-insert` (code in `spike/office/`, throwaway)
- Environment: macOS 26, PowerPoint and Word for Mac 16.114.3 (Office.com build), add-in sideloaded with `office-addin-dev-settings`
- Requirement sets: PowerPointApi 1.1–1.10 and WordApi 1.1–1.9 all supported
- Not yet tested: Windows, Office on the web

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

## Font installation, embedding and detection (round 2)

### Installing the font
- After copying SlideMarks into `~/Library/Fonts`, macOS registered it immediately, and CoreText rendered it correctly. **PowerPoint still showed boxes until it was restarted a second time.** It had launched while Office's shared font cache (`~/Library/Group Containers/UBF8T346G9.Office/FontCache`) was being rebuilt. The install guide must say: quit **all** Office apps after installing, then reopen.
- Slot test in PowerPoint for Mac, with the font installed and no embedding: SlideMarks set on `latin`, `ea` or `cs` alone **renders**; `sym` alone or no font does not. So Office.js `font.name` (Latin only) is enough for PowerPoint on Mac. Windows is still to be confirmed. Word still needs the four-slot OOXML insert (`w:hint="eastAsia"`).

### Embedding
- Office.js can't turn on font embedding or embed a font into the open document.
- **A "prepared copy" doesn't stick.** A copy with the embed flag and an embedded SlideMarks font, opened via `PowerPoint.createPresentation` or directly, lost both on the next save while the font wasn't installed. PowerPoint embeds from *installed* fonts at save time and rewrites the flag from the document's own setting. Not retested with the font installed: the guided route below made it unnecessary.
- **The guided route works.** With SlideMarks installed: Preferences → Save → *Embed fonts in the file* → *Embed all characters* → save. The saved `.pptx` contained `embedTrueTypeFonts="1"`, an `embeddedFont` entry for SlideMarks, and `ppt/fonts/font1.fntdata` (7 KB: PowerPoint compresses it).
- **Usability trap (Mac):** the setting is **per presentation**, and the *"Preserve fidelity when sharing this presentation"* dropdown picks which open presentation it applies to. In testing it was set on the wrong deck first. Walkthroughs must name the current file explicitly.

### Detecting embedding from the add-in
- `getFileAsync` returns the document as saved, including embedded fonts. A dependency-free ZIP reader (central directory plus `DecompressionStream("deflate-raw")`) checks:
  - **PowerPoint:** `embedTrueTypeFonts` in `ppt/presentation.xml`, and a `p:embeddedFont` entry with `typeface="SlideMarks"`.
  - **Word:** `w:embedTrueTypeFonts` in `word/settings.xml`, and a `w:embedRegular` entry under the SlideMarks entry in `word/fontTable.xml`.
  - **Both:** whether any slide or the document body uses SlideMarks.
- Verified both ways: the detection logic was checked in Node against known files (specimens embedded, spike exports not), and the live panel went red → green after the user enabled embedding and saved. The result matched the file on disk.

## PowerPoint insertion, round 3 (live, PowerPoint for Mac 16.114, 2026-11-05)

Findings from user testing of the shipped add-in, which led to the single snapshot-and-diff insertion path (`docs/office-addin-design.md`):

- **Blinking cursor reported as a word.** With the cursor at the end of a word and nothing highlighted, `getSelectedTextRange()` returns the word (for example "WORLD", length 5). Replacing that range swallowed the word. The add-in now never edits the reported selection; it inserts with `setSelectedDataAsync` and finds the new text by diffing.
- **The common API reports the real selection.** `Office.context.document.getSelectedDataAsync(Text)` gives:

  | Selection | Result |
  |---|---|
  | Blinking cursor in a text box | `""`, while `getSelectedTextRange` says "WORLD", start 6, length 5 |
  | Blinking cursor in a table cell | `""`, while `getSelectedTextRange` throws InvalidArgument |
  | A highlighted word | the word |
  | A whole text box selected (its border clicked) | the whole text plus `\r\n`; ⌘A inside the box gives the same |
  | A whole table selected | every cell's text separated by `\r\n` |
  | Nothing holding text (empty slide area) | error 1001, "The current selection is not supported" |

  The add-in uses this as its gate: an error means no cursor, and a line break means a whole box or table, which the insert would replace. Before this check, inserting with a text box selected replaced all of its text. That happened in testing; it wasn't hypothetical.
- **Tables in content placeholders** report shape type `Placeholder`, with `placeholderFormat.containedType` `Table`. A table inserted with Insert › Table reports `Table`.
- **Empty table cells** report `null` for unset font properties, the same value PowerPoint uses for mixed formatting. `TableCell.textRuns` is readable on Mac (verified: in a cell with italic "EM" and regular "AIL", inserting after it kept both). The add-in reads each run's formatting and writes it back, so nothing is flattened.
- **SmartArt** (a SmartArt diagram in a content placeholder):
  - `getSelectedShapes()` reports one shape of type **`Placeholder`** (not `SmartArt`).
  - Before inserting, `getSelectedTextRangeOrNullObject()` throws `InvalidArgument`, the same as in a table cell.
  - `setSelectedDataAsync` inserts at the cursor. The text arrives in the theme font, so a SlideMarks-only symbol shows as a box.
  - Afterwards, the selected shape's `textFrame.textRange` shows no change, and `getSelectedTextRangeOrNullObject()` returns a range whose `text` is **`null`**. The inserted character can't be positively identified, so its font can't be set safely.
  - **Pasting doesn't help either.** Pasting the picker's formatted copy into a SmartArt box shows no Paste Options button, so there's no Keep Source Formatting, and the symbol arrives in the theme font.
  - **Conclusion:** Office.js offers no supported way to format SmartArt text, and pasting can't carry the font in. Setting the font by hand is the only route. The add-in inserts the symbol and shows a "One more step: set the font" card. It never changes formatting it can't identify, and it doesn't convert SmartArt to shapes.

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
5. The inserted symbol needs the SlideMarks font **installed** (or embedded) to display. Without it, the add-in inserts correctly, but users see a "?" box. The picker should detect and explain this, including "restart Office after installing".
6. **Sharing panel:** a status (✓ embedded / … save to finish / ! do this first) driven by `getFileAsync`, plus a **detailed, per-platform walkthrough** that names the current file for the Mac dropdown. Embedding is a per-document step, so the panel should check on open and whenever the user returns to the pane.

## How the spike was driven (reusable for the real add-in's tests)

- `npx office-addin-dev-certs install` (trusted localhost HTTPS) and `npx office-addin-dev-settings sideload manifest.xml desktop --app powerpoint|word` (sideload and launch with the task pane open), with no `package.json` or bundler.
- `spike/office/server.py`: HTTPS static server, plus `/log` (probe results), `/file` (the document exported via `getFileAsync`) and `/cmd` (remote commands the pane polls for, including `script:<name>` to run `spike/office/scripts/<name>.js`).
- Verification: the exported `.pptx`/`.docx` inspected with python-pptx and raw XML, so every claim above is checked against the saved file, not just the API's return values.
