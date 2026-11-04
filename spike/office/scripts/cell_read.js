// Cursor in a table cell: what can we read? Each property separately, since start/length throw.
const out = {};
for (const prop of ["text", "start", "length"]) {
  try {
    out[prop] = await PowerPoint.run(async (context) => {
      const sel = context.presentation.getSelectedTextRange();
      sel.load(prop);
      await context.sync();
      return prop === "text" ? hex(sel.text) : sel[prop];
    });
  } catch (e) { out[prop] = `ERROR ${e.code}`; }
}
try {
  out.font = await PowerPoint.run(async (context) => {
    const sel = context.presentation.getSelectedTextRange();
    sel.font.load("name");
    await context.sync();
    return sel.font.name;
  });
} catch (e) { out.font = `ERROR ${e.code}`; }
return out;
