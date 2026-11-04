// V5: capture the cursor's formatting with a Latin placeholder, insert the symbol as normal text
// carrying that formatting plus all four SlideMarks slots.
const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
const pkg = (runs) => `<pkg:package xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage">
<pkg:part pkg:name="/_rels/.rels" pkg:contentType="application/vnd.openxmlformats-package.relationships+xml"><pkg:xmlData>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>
</pkg:xmlData></pkg:part>
<pkg:part pkg:name="/word/document.xml" pkg:contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"><pkg:xmlData>
<w:document xmlns:w="${W}"><w:body><w:p>${runs}</w:p></w:body></w:document>
</pkg:xmlData></pkg:part></pkg:package>`;
const runsOf = (ooxml) => {
  const body = ooxml.slice(ooxml.indexOf("<w:body>"), ooxml.indexOf("</w:body>"));
  return [...body.matchAll(/<w:r\b[^>]*>(?:(?!<\/w:r>)[\s\S])*?<\/w:r>/g)].map((m) =>
    m[0].replace(/ w:rsid\w*="\w+"/g, "").replace(/<w:lang[^>]*\/>/g, ""));
};
const four = `<w:rFonts w:ascii="${FONT}" w:hAnsi="${FONT}" w:eastAsia="${FONT}" w:cs="${FONT}"/>`;
return await Word.run(async (context) => {
  const p = context.document.body.insertParagraph("V5: Before ", "End");
  p.font.name = "Cambria"; p.font.size = 20; p.font.bold = true; p.font.color = "#1A7F37";
  await context.sync();
  p.getRange("End").select("End");
  await context.sync();
  const holder = context.document.getSelection().insertText("x", "Replace");
  const hx = holder.getOoxml();
  await context.sync();
  const run = runsOf(hx.value).find((r) => />x</.test(r)) || "";
  const rPr = ((run.match(/<w:rPr>([\s\S]*?)<\/w:rPr>/) || [, ""])[1]).replace(/<w:rFonts[^>]*\/>/, "");
  const inserted = holder.insertOoxml(pkg(`<w:r><w:rPr>${four}${rPr}</w:rPr><w:t>${GLYPH}</w:t></w:r>`), "Replace");
  await context.sync();
  inserted.select("End");
  await context.sync();
  p.load("text");
  const ooxml = p.getRange("Whole").getOoxml();
  await context.sync();
  return { carried: rPr, textHex: [...p.text].map((c) => c.codePointAt(0).toString(16)).join(" "), runs: runsOf(ooxml.value) };
});
