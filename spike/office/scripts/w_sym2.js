// V4: capture the cursor's formatting, insert the symbol as w:sym carrying that formatting.
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
return await Word.run(async (context) => {
  const p = context.document.body.insertParagraph("V4: Before ", "End");
  p.font.name = "Cambria"; p.font.size = 20; p.font.bold = true; p.font.color = "#1A7F37";
  await context.sync();
  p.getRange("End").select("End");
  await context.sync();
  // 1. A placeholder typed at the cursor inherits exactly the formatting the user would get.
  const holder = context.document.getSelection().insertText("⁠", "Replace");
  const hx = holder.getOoxml();
  await context.sync();
  const rPr = (runsOf(hx.value).find((r) => r.includes("⁠")) || "").match(/<w:rPr>[\s\S]*?<\/w:rPr>/);
  const props = rPr ? rPr[0] : "";
  // 2. Replace it with the symbol as w:sym carrying the same formatting (font only on the symbol).
  const inserted = holder.insertOoxml(pkg(`<w:r>${props}<w:sym w:font="${FONT}" w:char="E003"/></w:r>`), "Replace");
  await context.sync();
  inserted.select("End");
  await context.sync();
  context.document.getSelection().insertText("typed", "Replace");
  p.load("text");
  const ooxml = p.getRange("Whole").getOoxml();
  await context.sync();
  return { capturedRPr: props, paragraphTextHex: [...p.text].map((c) => c.codePointAt(0).toString(16)).join(" "), runs: runsOf(ooxml.value) };
});
