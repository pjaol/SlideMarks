// Word: insert the symbol as OOXML with all four font slots, at the cursor in a table cell.
const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
const run = `<w:r><w:rPr><w:rFonts w:ascii="${FONT}" w:hAnsi="${FONT}" w:eastAsia="${FONT}" w:cs="${FONT}"/></w:rPr><w:t>${GLYPH}</w:t></w:r>`;
const pkg = `<pkg:package xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage">
<pkg:part pkg:name="/_rels/.rels" pkg:contentType="application/vnd.openxmlformats-package.relationships+xml"><pkg:xmlData>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>
</pkg:xmlData></pkg:part>
<pkg:part pkg:name="/word/document.xml" pkg:contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"><pkg:xmlData>
<w:document xmlns:w="${W}"><w:body><w:p>${run}</w:p></w:body></w:document>
</pkg:xmlData></pkg:part></pkg:package>`;
return await Word.run(async (context) => {
  const tables = context.document.body.tables;
  tables.load("items");
  await context.sync();
  const table = tables.items[0];
  const cellBody = table.getCell(2, 1).body; // row "Web", column "Option A": "y"
  cellBody.getRange("End").select("End");
  await context.sync();
  const inserted = context.document.getSelection().insertOoxml(pkg, "Replace");
  await context.sync();
  cellBody.load("text");
  const paras = cellBody.paragraphs;
  paras.load("items");
  await context.sync();
  await exportFile("word-ooxml.docx");
  return { cellHex: hex(cellBody.text), paragraphs: paras.items.length };
});
