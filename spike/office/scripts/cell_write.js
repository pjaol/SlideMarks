// Cursor in a table cell: write the symbol and set its font without reading position first.
return await PowerPoint.run(async (context) => {
  const sel = context.presentation.getSelectedTextRange();
  sel.text = GLYPH;
  sel.font.name = FONT;
  await context.sync();
  return { written: true };
});
