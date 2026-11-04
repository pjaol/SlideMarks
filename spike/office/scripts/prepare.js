// Read the live document, have the server add the embed flag + SlideMarks, open the result as a new document.
const isPpt = Office.context.host === Office.HostType.PowerPoint;
const kind = isPpt ? "pptx" : "docx";
const mode = (await (await fetch("prepare-mode.txt")).text()).trim() || "full";
const data = await window.fileBase64();
const res = await (await fetch("/prepare", { method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ kind, mode, data }) })).json();
if (isPpt) await PowerPoint.createPresentation(res.data);
else await Word.run(async (context) => { context.application.createDocument(res.data).open(); await context.sync(); });
return { kind, mode, originalBytes: data.length, preparedBase64: res.data.length };
