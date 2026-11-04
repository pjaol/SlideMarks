// Host adapters: insert a symbol at the cursor. Each returns
//   { ok, message?, warn?, confirm?: { label, run } }
// Behavior follows docs/office-js-spike.md; comments cite the finding each step relies on.

SM.copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Office web views and file:// pages may refuse the async clipboard; fall back to a selection copy.
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
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

async function pptContext() {
  try {
    return await PowerPoint.run(async (context) => {
      const sel = context.presentation.getSelectedTextRangeOrNullObject();
      sel.load("text,start,length"); // throws InvalidArgument when the cursor is inside a table cell
      const shapes = context.presentation.getSelectedShapes();
      shapes.load("items/type");
      await context.sync();
      if (!sel.isNullObject) return { kind: "text", length: sel.length };
      return { kind: shapes.items.some((s) => s.type === "Table") ? "table" : "none" };
    });
  } catch (e) {
    if (e.code === "InvalidArgument") return { kind: "table" }; // cursor inside a table cell (spike)
    throw e;
  }
}

async function pptInsertText(sym, text, length) {
  const glyphLen = sym.char.length;
  if (length > 0) {
    // A selection: replace it, then style only the symbol (verified: surrounding text keeps its font).
    await PowerPoint.run(async (context) => {
      const sel = context.presentation.getSelectedTextRange();
      sel.text = text;
      await context.sync();
      sel.getSubstring(0, glyphLen).font.name = SM.FONT;
      await context.sync();
    });
    return { ok: true, message: `Inserted ${sym.name}` };
  }
  // A blinking cursor: the generic insert leaves the new text selected, which we then style.
  await setSelectedData(text);
  return PowerPoint.run(async (context) => {
    const sel = context.presentation.getSelectedTextRangeOrNullObject();
    sel.load("text");
    await context.sync();
    if (sel.isNullObject || !sel.text.startsWith(sym.char)) {
      return { ok: true, warn: true, message: "Inserted, but couldn't set its font. Select the symbol and choose SlideMarks in the font menu." };
    }
    sel.getSubstring(0, glyphLen).font.name = SM.FONT;
    await context.sync();
    return { ok: true, message: `Inserted ${sym.name}` };
  });
}

function insertedSpan(before, after) {
  let start = 0;
  while (start < before.length && before[start] === after[start]) start++;
  let end = 0;
  while (end < before.length - start && before[before.length - 1 - end] === after[after.length - 1 - end]) end++;
  return { start, end: after.length - end };
}

function cellRuns(text, glyphSpan, font) {
  // Symbol characters (all PUA, plus the just-inserted glyph) get SlideMarks; everything else
  // gets the cell's own formatting carried forward, because writing textRuns resets it (spike).
  const runs = [];
  [...text].forEach((ch, i, chars) => {
    const offset = chars.slice(0, i).join("").length;
    const sym = SM.isSymbolChar(ch) || (offset >= glyphSpan.start && offset < glyphSpan.end);
    const last = runs[runs.length - 1];
    if (last && last.sym === sym) last.text += ch;
    else runs.push({ sym, text: ch });
  });
  return runs.map(({ sym, text: t }) => ({ text: t, font: sym ? { ...font, name: SM.FONT } : { ...font } }));
}

async function pptInsertTable(sym, text) {
  return PowerPoint.run(async (context) => {
    const shapes = context.presentation.getSelectedShapes();
    shapes.load("items/type,items/id");
    await context.sync();
    const shape = shapes.items.find((s) => s.type === "Table");
    if (!shape) return { ok: false, message: "Click inside a table cell or text box first." };
    const table = shape.getTable();
    table.load("rowCount,columnCount");
    await context.sync();

    const cells = [];
    for (let r = 0; r < table.rowCount; r++)
      for (let c = 0; c < table.columnCount; c++) {
        const cell = table.getCellOrNullObject(r, c);
        cell.load("text");
        cell.font.load(FONT_PROPS.join(","));
        cells.push({ r, c, cell });
      }
    await context.sync();
    const before = cells.map(({ cell }) => ({ text: cell.text, font: cell.font.toJSON() }));

    // No API reports which cell holds the cursor; insert, then find the one cell that changed (spike).
    await setSelectedData(text);
    cells.forEach(({ cell }) => cell.load("text"));
    await context.sync();
    const changed = cells.map((x, i) => i).filter((i) => cells[i].cell.text !== before[i].text);
    if (changed.length === 0) {
      return { ok: false, message: "Click inside a table cell so the cursor is blinking there (not the whole table), then insert again." };
    }
    if (changed.length > 1) return { ok: false, message: "Couldn't tell which cell received the symbol. Undo and try again." };

    const i = changed[0];
    const { r, c } = cells[i];
    const afterText = cells[i].cell.text;
    const span = insertedSpan(before[i].text, afterText);
    const glyphSpan = { start: span.start, end: span.start + sym.char.length };
    const font = {};
    let mixed = false;
    for (const p of FONT_PROPS) {
      const v = before[i].font[p];
      if (v === null || v === undefined) mixed = true;
      else if (p !== "name") font[p] = v;
    }
    if (before[i].font.name) font.name = before[i].font.name;

    const apply = async (carry) => {
      await PowerPoint.run(async (ctx) => {
        const t = ctx.presentation.getSelectedSlides().getItemAt(0).shapes.getItem(shape.id).getTable();
        t.getCellOrNullObject(r, c).textRuns = cellRuns(afterText, glyphSpan, carry);
        await ctx.sync();
      });
    };
    if (!mixed) {
      await apply(font);
      return { ok: true, message: `Inserted ${sym.name}` };
    }
    return {
      ok: true,
      warn: true,
      message: "Inserted, but this cell has mixed formatting (for example one bold word), so the symbol isn't in SlideMarks yet.",
      confirm: {
        label: "Set the symbol's font (simplifies this cell's formatting)",
        run: async () => { await apply(font); return { ok: true, message: "Symbol set to SlideMarks." }; },
      },
    };
  });
}

SM.hosts.powerpoint = {
  name: "PowerPoint",
  canInsert: true,
  async insert(sym, { label }) {
    const text = label ? `${sym.char} ${SM.labelText(sym)}` : sym.char;
    const where = await pptContext();
    if (where.kind === "text") return pptInsertText(sym, text, where.length);
    if (where.kind === "table") return pptInsertTable(sym, text);
    // Never call setSelectedDataAsync without a text cursor: it creates a stray shape (spike).
    return { ok: false, message: "Click into a text box or a table cell first, then insert." };
  },
};

// ── Standalone page ─────────────────────────────────────────────────────────

SM.hosts.browser = { name: "Browser", canInsert: false };
