// Cursor in a table cell: generic Office insert, then try to style what's now selected.
await setSelectedData(GLYPH);
return await PowerPoint.run(async (context) => {
  const shapes = context.presentation.getSelectedShapes();
  shapes.load("items/name,items/type");
  await context.sync();
  const out = { shapes: shapes.items.map((s) => `${s.name}:${s.type}`) };
  try {
    const sel = context.presentation.getSelectedTextRange();
    sel.font.name = FONT;
    await context.sync();
    out.fontApplied = true;
  } catch (e) { out.fontApplied = `ERROR ${e.code}`; }
  return out;
});
