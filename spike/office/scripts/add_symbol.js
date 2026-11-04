// Put a visible SlideMarks symbol on slide 1 so the document uses the font.
return await PowerPoint.run(async (context) => {
  const slide = context.presentation.slides.getItemAt(0);
  const box = slide.shapes.addTextBox(`Harvey 75%: ${GLYPH}`, { left: 60, top: 60, width: 500, height: 80 });
  box.name = "sm-sample";
  box.textFrame.textRange.font.size = 40;
  box.textFrame.textRange.getSubstring(12, 1).font.name = FONT;
  await context.sync();
  return { added: true };
});
