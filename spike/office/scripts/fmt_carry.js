// Read the cell's uniform font (null = mixed), then rewrite runs carrying it forward.
const PROPS = ["name", "size", "bold", "italic", "color", "underline"];
return await PowerPoint.run(async (context) => {
  const slides = context.presentation.slides;
  slides.load("items");
  await context.sync();
  const shapes = slides.items[2].shapes;
  shapes.load("items/name,items/type");
  await context.sync();
  const table = shapes.items.find((s) => s.type === "Table").getTable();
  const uniform = table.getCellOrNullObject(1, 2); // "x": give it uniform formatting first
  uniform.font.bold = true; uniform.font.color = "#00B050"; uniform.font.size = 28;
  await context.sync();
  const out = {};
  for (const [label, r, c] of [["uniform", 1, 2], ["mixed", 2, 0]]) {
    const cell = table.getCellOrNullObject(r, c);
    cell.load("text");
    cell.font.load(PROPS.join(","));
    await context.sync();
    const f = {};
    for (const p of PROPS) if (cell.font[p] !== null && cell.font[p] !== undefined) f[p] = cell.font[p];
    out[label] = { read: f };
    const base = { ...f };
    cell.textRuns = [{ text: cell.text + " ", font: base }, { text: GLYPH, font: { ...base, name: FONT } }];
    await context.sync();
  }
  await exportFile("fmt-carry.pptx");
  return out;
});
