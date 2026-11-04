// SPIKE: probe symbol insertion paths in PowerPoint and Word, report to the local server.
const GLYPH = String.fromCodePoint(0xE003); // Harvey ball 75%
const FONT = "SlideMarks";
const $ = (id) => document.getElementById(id);

async function post(path, body) {
  await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

async function log(probe, ok, detail) {
  const entry = { t: new Date().toISOString(), host: Office.context.host, probe, ok, detail };
  const line = document.createElement("div");
  line.className = ok ? "ok" : "fail";
  line.textContent = `${ok ? "✓" : "✗"} ${probe}: ${JSON.stringify(detail)}`;
  $("log").appendChild(line);
  await post("/log", entry);
}

function err(e) {
  return { name: e.name, code: e.code, message: e.message, debugInfo: e.debugInfo };
}

async function probe(name, fn) {
  try {
    await log(name, true, await fn());
  } catch (e) {
    await log(name, false, err(e));
  }
}

function hex(s) {
  return [...(s || "")].map((c) => c.codePointAt(0).toString(16).toUpperCase().padStart(4, "0")).join(" ");
}

function sets(prefix, max) {
  const out = {};
  for (let i = 1; i <= max; i++) out[`${prefix} 1.${i}`] = Office.context.requirements.isSetSupported(prefix, `1.${i}`);
  return out;
}

async function exportFile(name) {
  const file = await new Promise((res, rej) =>
    Office.context.document.getFileAsync(Office.FileType.Compressed, { sliceSize: 4194304 }, (r) =>
      r.status === "succeeded" ? res(r.value) : rej(r.error)));
  const bytes = [];
  for (let i = 0; i < file.sliceCount; i++) {
    const slice = await new Promise((res, rej) =>
      file.getSliceAsync(i, (r) => (r.status === "succeeded" ? res(r.value) : rej(r.error))));
    bytes.push(...slice.data);
  }
  file.closeAsync();
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.slice(i, i + 0x8000));
  await post("/file", { name, data: btoa(bin) });
  return { bytes: bytes.length };
}

function setSelectedData(text) {
  return new Promise((res, rej) =>
    Office.context.document.setSelectedDataAsync(text, { coercionType: Office.CoercionType.Text }, (r) =>
      r.status === "succeeded" ? res() : rej(r.error)));
}

// ── PowerPoint ──────────────────────────────────────────────────────────────

async function pptFixtures(context) {
  context.presentation.slides.add();
  const slides = context.presentation.slides;
  slides.load("items");
  await context.sync();
  const slide = slides.items[slides.items.length - 1];
  const box = slide.shapes.addTextBox("Score: done", { left: 40, top: 40, width: 400, height: 50 });
  box.name = "probe-textbox";
  const tableShape = slide.shapes.addTable(3, 3, {
    left: 40, top: 140, width: 600, height: 150,
    values: [["Capability", "Option A", "Option B"], ["Offline", "Score: ", "x"], ["Web", "y", ""]],
  });
  tableShape.name = "probe-table";
  await context.sync();
  return { slide, box, tableShape };
}

async function pptRunsOf(range) {
  // font name of each character, so we can see exactly what was formatted
  range.load("text");
  await range.context.sync();
  const chars = [...range.text];
  const subs = chars.map((_, i) => {
    const s = range.getSubstring(i, 1);
    s.load("text");
    s.font.load("name");
    return s;
  });
  await range.context.sync();
  return subs.map((s) => `${s.text}=${s.font.name}`).join(" | ");
}

async function pptAuto() {
  await PowerPoint.run(async (context) => {
    const { box, tableShape } = await pptFixtures(context);
    const tr = box.textFrame.textRange;

    await probe("ppt.textbox.cursor.getSelectedTextRange", async () => {
      tr.getSubstring(7, 0).setSelected();
      await context.sync();
      const sel = context.presentation.getSelectedTextRange();
      sel.load("text,start,length");
      await context.sync();
      const before = { start: sel.start, length: sel.length, text: sel.text };
      sel.text = GLYPH;
      sel.font.name = FONT;
      await context.sync();
      return { before, after: await pptRunsOf(tr) };
    });

    await probe("ppt.textbox.selection.replace", async () => {
      tr.getSubstring(0, 5).setSelected(); // "Score"
      await context.sync();
      const sel = context.presentation.getSelectedTextRange();
      sel.text = GLYPH;
      sel.font.name = FONT;
      await context.sync();
      return { after: await pptRunsOf(tr) };
    });

    await probe("ppt.textbox.cursor.setSelectedDataAsync", async () => {
      tr.load("text");
      await context.sync();
      tr.getSubstring([...tr.text].length, 0).setSelected();
      await context.sync();
      await setSelectedData(GLYPH);
      const sel = context.presentation.getSelectedTextRange();
      sel.load("text,start,length");
      await context.sync();
      return { selectionAfterInsert: { start: sel.start, length: sel.length, text: hex(sel.text) }, after: await pptRunsOf(tr) };
    });

    await probe("ppt.textbox.setSelectedDataAsync.thenFont", async () => {
      const fresh = (await pptFixtures(context)).box; // new slide with clean "Score: done"
      const r = fresh.textFrame.textRange;
      r.getSubstring(7, 4).setSelected(); // "done": replace with the symbol
      await context.sync();
      await setSelectedData(GLYPH);
      const sel = context.presentation.getSelectedTextRange();
      sel.load("text,start,length");
      await context.sync();
      const selected = { start: sel.start, length: sel.length, text: hex(sel.text) };
      sel.font.name = FONT;
      await context.sync();
      return { selected, after: await pptRunsOf(r) };
    });

    const table = tableShape.getTable();

    await probe("ppt.table.textRuns.read", async () => {
      const cell = table.getCellOrNullObject(1, 1);
      cell.load("textRuns");
      await context.sync();
      return { type: typeof cell.textRuns, value: cell.textRuns ?? null, json: cell.toJSON() };
    });

    await probe("ppt.table.textRuns.write", async () => {
      const cell = table.getCellOrNullObject(1, 2); // "x"
      cell.textRuns = [{ text: "Score: " }, { text: GLYPH, font: { name: FONT } }];
      await context.sync();
      return { written: true };
    });

    await probe("ppt.table.textRuns.append", async () => {
      const cell = table.getCellOrNullObject(1, 1); // "Score: "
      cell.load("text,textRuns");
      await context.sync();
      const before = cell.textRuns || [];
      cell.textRuns = [...before, { text: GLYPH, font: { name: FONT } }];
      await context.sync();
      cell.load("text,textRuns");
      await context.sync();
      return { before, after: cell.textRuns, textHex: hex(cell.text) };
    });

    await probe("ppt.table.cell.font", async () => {
      const cell = table.getCellOrNullObject(2, 2);
      cell.text = GLYPH;
      cell.font.name = FONT;
      await context.sync();
      cell.load("text,textRuns");
      await context.sync();
      return { after: cell.textRuns };
    });

    await probe("ppt.table.shape.textFrame", async () => {
      const t = tableShape.textFrame.textRange;
      t.load("text");
      await context.sync();
      return { text: t.text };
    });
  });
  await probe("ppt.export", () => exportFile("probe.pptx"));
}

async function pptManualRange() {
  await probe("ppt.manual.getSelectedTextRange", async () =>
    PowerPoint.run(async (context) => {
      const sel = context.presentation.getSelectedTextRange();
      sel.load("text,start,length");
      const shapes = context.presentation.getSelectedShapes();
      shapes.load("items/name,items/type");
      await context.sync();
      const before = { start: sel.start, length: sel.length, text: sel.text, shapes: shapes.items.map((s) => `${s.name}:${s.type}`) };
      sel.text = GLYPH;
      sel.font.name = FONT;
      await context.sync();
      return { before, insertedFont: FONT };
    }));
}

async function pptManualData() {
  await probe("ppt.manual.setSelectedDataAsync", async () => {
    await setSelectedData(GLYPH);
    return PowerPoint.run(async (context) => {
      const shapes = context.presentation.getSelectedShapes();
      shapes.load("items/name,items/type");
      await context.sync();
      return { shapes: shapes.items.map((s) => `${s.name}:${s.type}`) };
    });
  });
}

// ── Word ────────────────────────────────────────────────────────────────────

async function wordAuto() {
  await Word.run(async (context) => {
    const body = context.document.body;
    const para = body.insertParagraph("Score: done", "End");
    const table = body.insertTable(3, 3, "End", [["Capability", "Option A", "Option B"], ["Offline", "Score: ", "x"], ["Web", "y", ""]]);
    await context.sync();

    await probe("word.paragraph.cursor.selection", async () => {
      para.search("done").getFirst().select("Start"); // collapsed cursor before "done"
      await context.sync();
      const inserted = context.document.getSelection().insertText(GLYPH, "Replace");
      inserted.font.name = FONT;
      para.load("text");
      await context.sync();
      return { paragraphHex: hex(para.text) };
    });

    await probe("word.table.cursor.selection", async () => {
      table.getCell(1, 1).body.getRange("End").select("End"); // cursor at end of "Score: "
      await context.sync();
      const inserted = context.document.getSelection().insertText(GLYPH, "Replace");
      inserted.font.name = FONT;
      inserted.load("text");
      inserted.font.load("name");
      await context.sync();
      const cell = table.getCell(1, 1).body;
      cell.load("text");
      await context.sync();
      return { cellHex: hex(cell.text), insertedFont: inserted.font.name };
    });
  });
  await probe("word.export", () => exportFile("probe.docx"));
}

async function wordManualRange() {
  await probe("word.manual.selection", async () =>
    Word.run(async (context) => {
      const inserted = context.document.getSelection().insertText(GLYPH, "Replace");
      inserted.font.name = FONT;
      inserted.font.load("name");
      await context.sync();
      return { insertedFont: inserted.font.name };
    }));
}

// ── Boot ────────────────────────────────────────────────────────────────────

Office.onReady(async (info) => {
  $("status").textContent = `Host: ${info.host} · ${info.platform}`;
  const d = Office.context.diagnostics;
  await log("env", true, {
    host: info.host, platform: info.platform, version: d && d.version,
    sets: info.host === Office.HostType.PowerPoint ? sets("PowerPointApi", 10) : sets("WordApi", 9),
  });
  const isPpt = info.host === Office.HostType.PowerPoint;
  $("manual").hidden = false;
  $("m-range").onclick = isPpt ? pptManualRange : wordManualRange;
  $("m-data").onclick = isPpt ? pptManualData : () => probe("word.manual.setSelectedDataAsync", async () => { await setSelectedData(GLYPH); return {}; });
  $("m-export").onclick = () => probe(isPpt ? "ppt.export.manual" : "word.export.manual", () => exportFile(isPpt ? "manual.pptx" : "manual.docx"));
  // Auto probes only when spike/office/autorun.flag exists (they add slides and move the selection).
  if ((await fetch("autorun.flag")).ok) { if (isPpt) await pptAuto(); else await wordAuto(); }
  // Remote control for the spike: the server hands out one command at a time.
  const commands = {
    range: isPpt ? pptManualRange : wordManualRange,
    data: $("m-data").onclick,
    datafont: pptDataThenFont,
    selinfo: pptSelectionInfo,
    export: $("m-export").onclick,
  };
  setInterval(async () => {
    const cmd = (await (await fetch("/cmd")).text()).trim();
    if (!cmd) return;
    if (cmd.startsWith("script:")) {
      // run spike/office/scripts/<name>.js as an async function body with helpers in scope
      const name = cmd.slice(7);
      const src = await (await fetch(`scripts/${name}.js`)).text();
      const fn = new Function("probe", "PowerPoint", "Word", "GLYPH", "FONT", "hex", "setSelectedData", "exportFile", `return (async () => {${src}})();`);
      await probe(`script.${name}`, () => fn(probe, window.PowerPoint, window.Word, GLYPH, FONT, hex, setSelectedData, exportFile));
    } else if (cmd === "reload") {
      location.reload();
    } else if (commands[cmd]) {
      await commands[cmd]();
    }
  }, 1000);
});

async function pptSelectionInfo() {
  await probe("ppt.cmd.selectionInfo", async () =>
    PowerPoint.run(async (context) => {
      const shapes = context.presentation.getSelectedShapes();
      shapes.load("items/name,items/type");
      const sel = context.presentation.getSelectedTextRangeOrNullObject();
      sel.load("text,start,length");
      await context.sync();
      return { shapes: shapes.items.map((s) => `${s.name}:${s.type}`),
               textRange: sel.isNullObject ? null : { start: sel.start, length: sel.length, text: sel.text } };
    }));
}

async function pptDataThenFont() {
  await probe("ppt.cmd.setSelectedDataAsync.thenFont", async () => {
    await setSelectedData(GLYPH);
    return PowerPoint.run(async (context) => {
      const sel = context.presentation.getSelectedTextRangeOrNullObject();
      sel.load("text,start,length");
      await context.sync();
      if (sel.isNullObject) return { selectionAfterInsert: null };
      const info = { start: sel.start, length: sel.length, text: hex(sel.text) };
      sel.font.name = FONT;
      await context.sync();
      return { selectionAfterInsert: info, fontApplied: FONT };
    });
  });
}
