// Host adapters: insert a symbol at the cursor. Each returns
//   { ok, message?, warn?, next?: { title, html } }
// ok: false means nothing was inserted and the message says what to do; warn means it was inserted
// but needs a follow-up; next is a step only the user can do, shown as a card. Unexpected failures throw.
// Behavior follows docs/office-js-spike.md; comments cite the finding each step relies on.

// Copy as formatted text as well as plain text, so pasting into Word or PowerPoint keeps the
// SlideMarks font. Plain text alone pastes in the destination's font, which has no SlideMarks
// characters, so it shows as a box. The mso-* properties make Word set all four font slots
// (it draws these characters from the East Asian slot); verified by pasting into Word for Mac.
SM.clipboardHtml = (char, label) => {
  const f = SM.FONT;
  const style = `font-family:${f};mso-ascii-font-family:${f};mso-hansi-font-family:${f};mso-fareast-font-family:${f};mso-bidi-font-family:${f}`;
  return `<span style="${style}">${SM.esc(char)}</span>${label ? `<span> ${SM.esc(label)}</span>` : ""}`;
};

SM.copyText = async (text, html) => {
  try {
    if (html && window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
      await navigator.clipboard.write([new ClipboardItem({
        "text/html": new Blob([html], { type: "text/html" }),
        "text/plain": new Blob([text], { type: "text/plain" }),
      })]);
    } else {
      await navigator.clipboard.writeText(text);
    }
    return true;
  } catch {
    // Office web views and file:// pages may refuse the async clipboard. Fall back to copying a
    // selection, which still carries the formatting when html is given.
    const holder = document.createElement(html ? "div" : "textarea");
    holder.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0";
    if (html) { holder.contentEditable = "true"; holder.innerHTML = html; } else { holder.value = text; }
    document.body.appendChild(holder);
    if (html) {
      const range = document.createRange();
      range.selectNodeContents(holder);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    } else {
      holder.select();
    }
    const ok = document.execCommand("copy");
    holder.remove();
    return ok;
  }
};

function setSelectedData(text) {
  return new Promise((resolve, reject) =>
    Office.context.document.setSelectedDataAsync(text, { coercionType: Office.CoercionType.Text }, (r) =>
      r.status === Office.AsyncResultStatus.Succeeded ? resolve() : reject(r.error)));
}

// ── Word ────────────────────────────────────────────────────────────────────
// insertText + font.name leaves the East Asian slot unset, and Word draws PUA characters from it
// (w:hint="eastAsia"), so the symbol goes in as an OOXML run with all four slots set. That run also
// carries the formatting at the cursor (size, colour, bold…), captured by briefly typing a Latin
// placeholder that inherits it; otherwise the symbol would fall back to the style's default size.
// (w:sym was tried and rejected: Word then reports the character as "(", which breaks screen
// readers and copy-paste.)

const W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";

function wordPackage(runs) {
  return `<pkg:package xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage">
<pkg:part pkg:name="/_rels/.rels" pkg:contentType="application/vnd.openxmlformats-package.relationships+xml"><pkg:xmlData>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>
</pkg:xmlData></pkg:part>
<pkg:part pkg:name="/word/document.xml" pkg:contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"><pkg:xmlData>
<w:document xmlns:w="${W_NS}"><w:body><w:p>${runs}</w:p></w:body></w:document>
</pkg:xmlData></pkg:part></pkg:package>`;
}

function runProperties(ooxml) {
  // The run holding the placeholder "x": its full properties, and the same without fonts.
  const body = ooxml.slice(ooxml.indexOf("<w:body>"), ooxml.indexOf("</w:body>"));
  const run = [...body.matchAll(/<w:r\b[^>]*>(?:(?!<\/w:r>)[\s\S])*?<\/w:r>/g)].map((m) => m[0]).find((r) => />x<\/w:t>/.test(r)) || "";
  const full = (run.match(/<w:rPr>([\s\S]*?)<\/w:rPr>/) || [, ""])[1];
  return { full, withoutFonts: full.replace(/<w:rFonts[^>]*\/>/, "") };
}

SM.hosts = {};

SM.hosts.word = {
  name: "Word",
  canInsert: true,
  async insert(sym, { label }) {
    await Word.run(async (context) => {
      const holder = context.document.getSelection().insertText("x", "Replace");
      const captured = holder.getOoxml();
      await context.sync();
      const props = runProperties(captured.value);
      const f = SM.FONT;
      const symbolRun = `<w:r><w:rPr><w:rFonts w:ascii="${f}" w:hAnsi="${f}" w:eastAsia="${f}" w:cs="${f}"/>${props.withoutFonts}</w:rPr><w:t>${SM.esc(sym.char)}</w:t></w:r>`;
      // The label keeps the original formatting, fonts included, so text typed after it is clean too.
      const labelRun = label ? `<w:r><w:rPr>${props.full}</w:rPr><w:t xml:space="preserve"> ${SM.esc(SM.labelText(sym))}</w:t></w:r>` : "";
      const inserted = holder.insertOoxml(wordPackage(symbolRun + labelRun), "Replace");
      await context.sync();
      inserted.select("End");
      await context.sync();
    });
    return { ok: true, message: `Inserted ${sym.name}` };
  },
};

// ── PowerPoint ──────────────────────────────────────────────────────────────

const FONT_PROPS = ["name", "size", "bold", "italic", "color", "underline"];

// A table inserted into a layout's content placeholder reports type "Placeholder", with the table
// as its contained type; one inserted onto the slide reports "Table".
async function pptTables(context, shapes) {
  const placeholders = shapes.filter((s) => s.type === "Placeholder");
  placeholders.forEach((s) => s.placeholderFormat.load("containedType"));
  if (placeholders.length) await context.sync();
  return shapes.filter((s) => s.type === "Table" || (s.type === "Placeholder" && s.placeholderFormat.containedType === "Table"));
}

// What's selected, from the common API, which reports the real selection on Mac (getSelectedTextRange
// reports the word next to a blinking cursor). Verified 2026-11-05: "" for a blinking cursor in a text
// box or table cell; the highlighted text; the whole text with line breaks when a whole text box or
// table is selected; error 1001 when nothing holding text is selected. Returns null for that error.
function pptSelectedText() {
  return new Promise((resolve, reject) =>
    Office.context.document.getSelectedDataAsync(Office.CoercionType.Text, (r) => {
      if (r.status === Office.AsyncResultStatus.Succeeded) resolve(r.value);
      else if (r.error.code === 1001) resolve(null);
      else reject(r.error);
    }));
}

function insertedSpan(before, after) {
  let start = 0;
  while (start < before.length && before[start] === after[start]) start++;
  let end = 0;
  while (end < before.length - start && before[before.length - 1 - end] === after[after.length - 1 - end]) end++;
  return { start, end: after.length - end };
}

function cleanFont(font) {
  const out = {};
  for (const [k, v] of Object.entries(font || {})) if (v !== null && v !== undefined) out[k] = v;
  return out;
}

// Rebuild a cell's runs after an insert: every original character keeps its own run's formatting;
// the inserted text takes its neighbor's (the character before it, else after it), and the glyph
// itself is set to SlideMarks. Writing textRuns replaces the whole cell, so nothing may be left out.
function spliceRuns(beforeRuns, beforeText, afterText, glyphLen, fallbackFont) {
  const fonts = [];
  for (const run of beforeRuns) for (let k = 0; k < run.text.length; k++) fonts.push(cleanFont(run.font));
  if (fonts.length !== beforeText.length) throw new Error("PowerPoint returned runs that don't match the cell's text.");
  const span = insertedSpan(beforeText, afterText);
  const removed = beforeText.length - (afterText.length - (span.end - span.start));
  const neighbor = fonts[span.start - 1] || fonts[span.start + removed] || cleanFont(fallbackFont);
  const after = [
    ...fonts.slice(0, span.start),
    ...[...Array(span.end - span.start)].map((_, k) => (k < glyphLen ? { ...neighbor, name: SM.FONT } : { ...neighbor })),
    ...fonts.slice(span.start + removed),
  ];
  const runs = [];
  for (let k = 0; k < afterText.length; k++) {
    const last = runs[runs.length - 1];
    if (last && JSON.stringify(last.font) === JSON.stringify(after[k])) last.text += afterText[k];
    else runs.push({ text: afterText[k], font: after[k] });
  }
  return runs;
}

// After inserting into text the add-in can't otherwise see: if the selection is now exactly the
// inserted text, set the symbol's font and read it back. Never touch a selection that differs
// (PowerPoint for Mac may report a neighboring word). In SmartArt the selection's text is null
// (docs/office-js-spike.md, round 3), so this returns false there.
async function pptFormatSelectionIfInserted(context, sym, text) {
  const sel = context.presentation.getSelectedTextRangeOrNullObject();
  sel.load("text");
  try {
    await context.sync();
  } catch (e) {
    if (e.code === "InvalidArgument") return false; // the selection can't be read here
    throw e;
  }
  if (sel.isNullObject || sel.text !== text) return false;
  const glyph = sel.getSubstring(0, sym.char.length);
  glyph.font.name = SM.FONT;
  glyph.font.load("name");
  await context.sync();
  return glyph.font.name === SM.FONT;
}

// One path for every kind of text. The generic insert goes to the real cursor wherever it is (and
// replaces a real highlight). PowerPoint for Mac reports the word next to a blinking cursor as the
// selected text, so the add-in never edits the reported selection itself. Instead it snapshots the
// text it can see (text frames, including lists and grouped shapes, and table cells), inserts, and
// formats whatever changed. Text add-ins can't see (SmartArt, notes) still gets the symbol; the
// user is told to set its font.
async function pptInsert(sym, text) {
  return PowerPoint.run(async (context) => {
    const slideShapes = context.presentation.getSelectedSlides().getItemAt(0).shapes;
    slideShapes.load("items/id");
    const selected = context.presentation.getSelectedShapes();
    selected.load("items/type,items/id");
    await context.sync();
    const shapeIdsBefore = new Set(slideShapes.items.map((s) => s.id));

    const groups = selected.items.filter((s) => s.type === "Group");
    groups.forEach((g) => g.group.shapes.load("items/type,items/id"));
    if (groups.length) await context.sync();
    const shapes = [...selected.items.filter((s) => s.type !== "Group"), ...groups.flatMap((g) => g.group.shapes.items)];
    const tables = await pptTables(context, shapes);

    const frames = [];
    for (const shape of shapes.filter((s) => !tables.includes(s))) {
      const range = shape.textFrame.textRange;
      range.load("text");
      try {
        await context.sync();
        frames.push({ range, before: range.text });
      } catch (e) {
        if (e.code !== "InvalidArgument") throw e; // a shape without text (picture, chart, SmartArt)
      }
    }
    const cells = [];
    for (const shape of tables) {
      const table = shape.getTable();
      table.load("rowCount,columnCount");
      await context.sync();
      for (let r = 0; r < table.rowCount; r++)
        for (let c = 0; c < table.columnCount; c++) {
          const cell = table.getCellOrNullObject(r, c);
          cell.load("text,textRuns");
          cell.font.load(FONT_PROPS.join(","));
          cells.push({ cell });
        }
    }
    await context.sync();
    cells.forEach((x) => Object.assign(x, { before: x.cell.text, runs: x.cell.textRuns || [], font: x.cell.font.toJSON() }));

    await setSelectedData(text);

    slideShapes.load("items/id");
    frames.forEach((f) => f.range.load("text"));
    cells.forEach((x) => x.cell.load("text"));
    await context.sync();

    const stray = slideShapes.items.filter((s) => !shapeIdsBefore.has(s.id));
    if (stray.length) {
      // No real cursor after all: PowerPoint made a new text box for the symbol. Take it away again.
      stray.forEach((s) => s.delete());
      await context.sync();
      return { ok: false, message: "Click into the text so the cursor is blinking there, then insert again." };
    }

    const changedFrames = frames.filter((f) => f.range.text !== f.before);
    const changedCells = cells.filter((x) => x.cell.text !== x.before);
    if (changedFrames.length + changedCells.length === 0) {
      // Text the add-in can't see (SmartArt): see whether PowerPoint now reports the inserted text
      // as the selection, and format it only if it's exactly what was inserted.
      if (await pptFormatSelectionIfInserted(context, sym, text)) return { ok: true, message: `Inserted ${sym.name}` };
      return { ok: true, next: {
        title: "One more step: set the font",
        html: `PowerPoint doesn't let add-ins format text here (SmartArt, for example). Select the new symbol if it isn't
          already selected, then choose <b>SlideMarks</b> in the font box on the Home tab.`,
      } };
    }
    if (changedFrames.length + changedCells.length > 1) {
      return { ok: true, warn: true, message: "Inserted, but couldn't tell where, so its font isn't set. Select the symbol and choose SlideMarks in the font menu." };
    }
    if (changedFrames.length) {
      const f = changedFrames[0];
      const span = insertedSpan(f.before, f.range.text);
      f.range.getSubstring(span.start, sym.char.length).font.name = SM.FONT;
    } else {
      // Cells have no substring API: rewrite the cell's runs, keeping each run's formatting.
      const x = changedCells[0];
      x.cell.textRuns = spliceRuns(x.runs, x.before, x.cell.text, sym.char.length, x.font);
    }
    await context.sync();
    return { ok: true, message: `Inserted ${sym.name}` };
  });
}

SM.hosts.powerpoint = {
  name: "PowerPoint",
  canInsert: true,
  async insert(sym, { label }) {
    const selected = await pptSelectedText();
    if (selected === null) return { ok: false, message: "Click into the text where the symbol should go, then insert." };
    if (/[\r\n]/.test(selected)) {
      // A whole text box or table: inserting would replace all of its text.
      return { ok: false, message: "The whole text box or table is selected, so the symbol would replace all of it. "
        + "Click where the symbol should go (or highlight just the text to replace), then insert." };
    }
    return pptInsert(sym, label ? `${sym.char} ${SM.labelText(sym)}` : sym.char);
  },
};

// ── Standalone page ─────────────────────────────────────────────────────────

SM.hosts.browser = { name: "Browser", canInsert: false };
