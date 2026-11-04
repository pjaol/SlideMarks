// Insert at the cursor in a table cell, find the changed cell by diffing, then restyle only symbol characters.
const isSymbol = (c) => { const p = c.codePointAt(0); return p >= 0xE000 && p <= 0xF8FF; };
const snapshot = async (context, table) => {
  table.load("rowCount,columnCount");
  await context.sync();
  const cells = [];
  for (let r = 0; r < table.rowCount; r++)
    for (let c = 0; c < table.columnCount; c++) {
      const cell = table.getCellOrNullObject(r, c);
      cell.load("text");
      cells.push({ r, c, cell });
    }
  await context.sync();
  return cells.map(({ r, c, cell }) => ({ r, c, text: cell.text }));
};
return await PowerPoint.run(async (context) => {
  const shapes = context.presentation.getSelectedShapes();
  shapes.load("items/type,items/name");
  await context.sync();
  const shape = shapes.items.find((s) => s.type === "Table");
  if (!shape) return { error: "selection is not in a table" };
  const table = shape.getTable();
  const before = await snapshot(context, table);
  await setSelectedData(GLYPH);
  const after = await snapshot(context, table);
  const changed = after.filter((a, i) => a.text !== before[i].text);
  if (changed.length !== 1) return { error: "could not identify a single changed cell", changed };
  const { r, c, text } = changed[0];
  const runs = [];
  for (const ch of [...text]) {
    const sym = isSymbol(ch);
    const last = runs[runs.length - 1];
    if (last && last.sym === sym) last.text += ch; else runs.push({ sym, text: ch });
  }
  const cell = table.getCellOrNullObject(r, c);
  cell.textRuns = runs.map(({ sym, text }) => (sym ? { text, font: { name: FONT } } : { text }));
  await context.sync();
  return { cell: [r, c], textHex: hex(text), runs: runs.map((x) => `${x.sym ? "SM" : "--"}:${hex(x.text)}`) };
});
