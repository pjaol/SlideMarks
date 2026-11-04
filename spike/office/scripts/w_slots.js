// Word: which insertion method leaves text typed after the symbol with clean font slots?
const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
const pkg = (runs) => `<pkg:package xmlns:pkg="http://schemas.microsoft.com/office/2006/xmlPackage">
<pkg:part pkg:name="/_rels/.rels" pkg:contentType="application/vnd.openxmlformats-package.relationships+xml"><pkg:xmlData>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>
</pkg:xmlData></pkg:part>
<pkg:part pkg:name="/word/document.xml" pkg:contentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"><pkg:xmlData>
<w:document xmlns:w="${W}"><w:body><w:p>${runs}</w:p></w:body></w:document>
</pkg:xmlData></pkg:part></pkg:package>`;
const four = `<w:rFonts w:ascii="${FONT}" w:hAnsi="${FONT}" w:eastAsia="${FONT}" w:cs="${FONT}"/>`;
const variants = {
  V0_fourSlots: () => pkg(`<w:r><w:rPr>${four}</w:rPr><w:t>${GLYPH}</w:t></w:r>`),
  V1_sym: () => pkg(`<w:r><w:sym w:font="${FONT}" w:char="E003"/></w:r>`),
  V3_zwsp: () => pkg(`<w:r><w:rPr>${four}</w:rPr><w:t>${GLYPH}</w:t></w:r><w:r><w:t>\u200B</w:t></w:r>`),
};
const out = {};
for (const [name, build] of [...Object.entries(variants), ["V2_resetFont", variants.V0_fourSlots]]) {
  out[name] = await Word.run(async (context) => {
    const p = context.document.body.insertParagraph(`${name}: Before `, "End");
    p.font.name = "Cambria";
    await context.sync();
    p.getRange("End").select("End");
    await context.sync();
    const sel = context.document.getSelection();
    sel.font.load("name");
    await context.sync();
    const original = sel.font.name;
    const inserted = context.document.getSelection().insertOoxml(build(), "Replace");
    await context.sync();
    inserted.select("End");
    await context.sync();
    if (name === "V2_resetFont") { context.document.getSelection().font.name = original; await context.sync(); }
    const typed = context.document.getSelection().insertText("typed", "Replace");
    await context.sync();
    const ooxml = p.getRange("Whole").getOoxml();
    await context.sync();
    const body = ooxml.value.slice(ooxml.value.indexOf("<w:body>"), ooxml.value.indexOf("</w:body>"));
    const runs = [...body.matchAll(/<w:r\b[^>]*>(?:(?!<\/w:r>)[\s\S])*?<\/w:r>/g)].map((m) => {
      const r = m[0];
      const fonts = (r.match(/<w:rFonts[^>]*\/>/) || [""])[0].replace(/w:/g, "");
      const text = (r.match(/<w:t[^>]*>([^<]*)<\/w:t>/) || [, ""])[1];
      const sym = (r.match(/<w:sym[^>]*\/>/) || [""])[0];
      return `${JSON.stringify(text)}${sym ? " " + sym : ""} ${fonts}`;
    });
    return { original, runs };
  });
}
return out;
