// Does rewriting textRuns (without font props) drop existing formatting? Cell-level vs run-level.
return await PowerPoint.run(async (context) => {
  const slides = context.presentation.slides;
  slides.load("items");
  await context.sync();
  const shapes = slides.items[2].shapes;
  shapes.load("items/name,items/type");
  await context.sync();
  const table = shapes.items.find((s) => s.type === "Table").getTable();
  // cell (2,0) "Web": run-level formatting; cell (2,1) "y": cell-level formatting
  const runCell = table.getCellOrNullObject(2, 0);
  runCell.textRuns = [{ text: "Bold red ", font: { bold: true, color: "#C00000", size: 24 } }, { text: "plain" }];
  const cellLevel = table.getCellOrNullObject(2, 1);
  cellLevel.font.bold = true;
  cellLevel.font.color = "#0070C0";
  cellLevel.font.size = 24;
  await context.sync();
  await exportFile("fmt-before.pptx");
  // now rewrite both the way the insert does: plain runs + SlideMarks run
  runCell.textRuns = [{ text: "Bold red plain " }, { text: GLYPH, font: { name: FONT } }];
  cellLevel.textRuns = [{ text: "y " }, { text: GLYPH, font: { name: FONT } }];
  await context.sync();
  await exportFile("fmt-after.pptx");
  return { done: true };
});
