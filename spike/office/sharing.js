// SPIKE: "Sharing" panel. Reads the live document and reports whether SlideMarks
// will travel with the file (embed-fonts setting on + SlideMarks embedded).

const SM = "SlideMarks";

// Minimal ZIP reader: central directory + DecompressionStream, no dependencies.
async function unzipText(bytes, wanted) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let eocd = bytes.length - 22;
  while (eocd >= 0 && view.getUint32(eocd, true) !== 0x06054b50) eocd--;
  if (eocd < 0) throw new Error("not a zip file");
  const count = view.getUint16(eocd + 10, true);
  let p = view.getUint32(eocd + 16, true);
  const out = {};
  for (let i = 0; i < count; i++) {
    const method = view.getUint16(p + 10, true);
    const compSize = view.getUint32(p + 20, true);
    const nameLen = view.getUint16(p + 28, true);
    const extraLen = view.getUint16(p + 30, true);
    const commentLen = view.getUint16(p + 32, true);
    const local = view.getUint32(p + 42, true);
    const name = new TextDecoder().decode(bytes.subarray(p + 46, p + 46 + nameLen));
    p += 46 + nameLen + extraLen + commentLen;
    if (!wanted(name)) { out[name] = null; continue; }
    const start = local + 30 + view.getUint16(local + 26, true) + view.getUint16(local + 28, true);
    let data = bytes.subarray(start, start + compSize);
    if (method === 8) {
      const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
      data = new Uint8Array(await new Response(stream).arrayBuffer());
    }
    out[name] = new TextDecoder().decode(data);
  }
  return out; // wanted parts as text; other part names present with null
}

async function documentBytes() {
  const b64 = await window.fileBase64();
  return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
}

async function sharingStatus() {
  const isPpt = Office.context.host === Office.HostType.PowerPoint;
  const parts = await unzipText(await documentBytes(), (n) =>
    isPpt ? n === "ppt/presentation.xml" || /^ppt\/slides\/slide\d+\.xml$/.test(n)
          : ["word/document.xml", "word/settings.xml", "word/fontTable.xml"].includes(n));
  const names = Object.keys(parts);
  if (isPpt) {
    const pres = parts["ppt/presentation.xml"] || "";
    const flag = /<p:presentation[^>]*embedTrueTypeFonts="(1|true)"/.test(pres);
    const embedded = new RegExp(`<p:embeddedFont>\\s*<p:font[^>]*typeface="${SM}"`).test(pres);
    const used = names.some((n) => /^ppt\/slides\//.test(n) && (parts[n] || "").includes(`typeface="${SM}"`));
    return { flag, embedded, used, fontParts: names.filter((n) => n.startsWith("ppt/fonts/")) };
  }
  const settings = parts["word/settings.xml"] || "";
  const fonts = parts["word/fontTable.xml"] || "";
  const flag = /<w:embedTrueTypeFonts(\s|\/|>)/.test(settings) && !/<w:embedTrueTypeFonts w:val="(0|false)"/.test(settings);
  const embedded = new RegExp(`<w:font w:name="${SM}"[^>]*>(?:(?!</w:font>).)*<w:embed(Regular|Bold|Italic)`, "s").test(fonts);
  const used = (parts["word/document.xml"] || "").includes(`"${SM}"`);
  return { flag, embedded, used, fontParts: names.filter((n) => n.startsWith("word/fonts/")) };
}

const STEPS = {
  Mac: (app) => [
    `${app} menu → <b>Preferences</b> (or Settings) → <b>Save</b>.`,
    `Tick <b>Embed fonts in the file</b> and choose <b>Embed all characters</b> so others can edit.`,
    `Save the ${app === "PowerPoint" ? "presentation" : "document"} (⌘S), then press <b>Check again</b>.`,
  ],
  PC: (app) => [
    `<b>File → Options → Save</b>.`,
    `Under <i>Preserve fidelity when sharing</i>, tick <b>Embed fonts in the file</b> and choose <b>Embed all characters</b>.`,
    `Save (Ctrl+S), then press <b>Check again</b>.`,
  ],
  OfficeOnline: (app) => [
    `${app} on the web can't embed fonts.`,
    `Open the file in the desktop app (<b>Editing → Open in Desktop App</b>) and turn embedding on there.`,
  ],
};

function renderSharing(status) {
  const app = Office.context.host === Office.HostType.PowerPoint ? "PowerPoint" : "Word";
  const box = document.getElementById("sharing");
  let state, title, note;
  if (status.flag && status.embedded) {
    state = "ok"; title = "SlideMarks travels with this file";
    note = "Embedding is on and the font is embedded. Recipients without SlideMarks will still see your symbols.";
  } else if (status.flag) {
    state = "pending"; title = "Embedding is on: save to finish";
    note = "Office embeds the font when you save. Save now, then check again.";
  } else {
    state = "warn"; title = "Do this first: embed SlideMarks";
    note = "Without embedding, anyone who doesn't have SlideMarks installed sees empty boxes instead of your symbols.";
  }
  const steps = state === "ok" ? [] : (STEPS[Office.context.platform] || STEPS.Mac)(app);
  box.className = `sharing ${state}`;
  box.innerHTML = `<div class="badge">${state === "ok" ? "✓" : state === "pending" ? "…" : "!"}</div>
    <div><b>${title}</b><p>${note}</p>${steps.length ? `<ol>${steps.map((s) => `<li>${s}</li>`).join("")}</ol>` : ""}
    <button id="sharing-check">Check again</button></div>`;
  document.getElementById("sharing-check").onclick = checkSharing;
}

async function checkSharing() {
  try {
    const status = await sharingStatus();
    renderSharing(status);
    await post("/log", { t: new Date().toISOString(), host: Office.context.host, probe: "sharing.status", ok: true, detail: status });
    return status;
  } catch (e) {
    document.getElementById("sharing").textContent = `Couldn't read the document: ${e.message}`;
    await post("/log", { t: new Date().toISOString(), host: Office.context.host, probe: "sharing.status", ok: false, detail: { message: e.message } });
  }
}
window.checkSharing = checkSharing;
