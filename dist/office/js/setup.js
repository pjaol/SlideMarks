// Setup checklist: is SlideMarks installed on this computer, and is it embedded in this file?
// Embedding can't be switched on by an add-in, so the panel detects it from the saved
// document (getFileAsync) and walks the user through Office's own setting.

SM.setup = (() => {
  const state = { font: "unknown", embed: null, expanded: false, walk: null, checking: false, lastCheck: 0 };
  const isOffice = () => document.body.dataset.mode === "office";
  const host = () => (Office.context.host === Office.HostType.PowerPoint ? "PowerPoint" : "Word");
  const noun = () => (host() === "PowerPoint" ? "presentation" : "document");
  const platform = () => (isOffice() ? Office.context.platform : null);

  // ── Font installed? ───────────────────────────────────────────────────────
  // Draw the symbols with the installed family and with the bundled preview copy. If the
  // pixels match, the installed SlideMarks drew them; if not, a fallback box was drawn.
  async function fontInstalled() {
    const probe = "\ue003\ue021\ue050";
    await document.fonts.load('48px "SlideMarks Preview"', probe);
    const draw = (family) => {
      const canvas = document.createElement("canvas");
      canvas.width = 180; canvas.height = 64;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      ctx.font = `48px ${family}`;
      ctx.fillText(probe, 4, 50);
      return ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    };
    const installed = draw(`"${SM.FONT}", serif`), bundled = draw('"SlideMarks Preview"');
    let diff = 0, ink = 0;
    for (let i = 3; i < bundled.length; i += 4) {
      if (bundled[i] > 0) ink++;
      if (Math.abs(installed[i] - bundled[i]) > 64) diff++;
    }
    return ink > 0 && diff / ink < 0.05;
  }

  // ── Embedded in this file? ────────────────────────────────────────────────
  function documentBytes() {
    return new Promise((resolve, reject) =>
      Office.context.document.getFileAsync(Office.FileType.Compressed, { sliceSize: 4194304 }, async (r) => {
        if (r.status !== Office.AsyncResultStatus.Succeeded) return reject(r.error);
        const file = r.value;
        const parts = [];
        let total = 0;
        try {
          for (let i = 0; i < file.sliceCount; i++) {
            const slice = await new Promise((res, rej) =>
              file.getSliceAsync(i, (s) => (s.status === Office.AsyncResultStatus.Succeeded ? res(s.value) : rej(s.error))));
            parts.push(slice.data);
            total += slice.data.length;
          }
        } catch (e) {
          file.closeAsync();
          return reject(e);
        }
        file.closeAsync();
        const bytes = new Uint8Array(total);
        let off = 0;
        for (const p of parts) { bytes.set(p, off); off += p.length; }
        resolve(bytes);
      }));
  }

  async function embedStatus() {
    const ppt = host() === "PowerPoint";
    const zip = await SM.unzip(await documentBytes(), (n) =>
      ppt ? n === "ppt/presentation.xml" || /^ppt\/slides\/slide\d+\.xml$/.test(n)
          : ["word/document.xml", "word/settings.xml", "word/fontTable.xml"].includes(n));
    const t = zip.text;
    const fam = `"${SM.FONT}"`;
    if (ppt) {
      const pres = t["ppt/presentation.xml"] || "";
      return {
        flag: /<p:presentation[^>]*\sembedTrueTypeFonts="(1|true)"/.test(pres),
        embedded: new RegExp(`<p:embeddedFont>\\s*<p:font[^>]*typeface=${fam}`).test(pres),
        used: Object.keys(t).some((n) => n.startsWith("ppt/slides/") && t[n].includes(`typeface=${fam}`)),
      };
    }
    const settings = t["word/settings.xml"] || "";
    return {
      flag: /<w:embedTrueTypeFonts(\s|\/|>)/.test(settings) && !/<w:embedTrueTypeFonts w:val="(0|false)"/.test(settings),
      embedded: new RegExp(`<w:font w:name=${fam}[^>]*>(?:(?!</w:font>)[\\s\\S])*<w:embed(Regular|Bold|Italic|BoldItalic)`).test(t["word/fontTable.xml"] || ""),
      used: (t["word/document.xml"] || "").includes(fam),
    };
  }

  function fileName() {
    const url = Office.context.document.url || "";
    const last = decodeURIComponent(url.split(/[\\/]/).pop() || "");
    return last.replace(/\.(pptx|docx|pptm|docm|potx|dotx)$/i, "");
  }

  // ── Walkthroughs ──────────────────────────────────────────────────────────
  const mockWindow = (title, body) =>
    `<div class="mock" aria-hidden="true"><div class="title"><span class="lights"><i></i><i></i><i></i></span>${title}</div>${body}</div>`;

  function embedSteps() {
    const app = host(), name = fileName() || `your ${noun()}`;
    const dialogFields = (closeHint) => mockWindow(platform() === "PC" ? `${app} Options › Save` : "Save", `
      <div class="group-label">${platform() === "PC" ? `Preserve fidelity when sharing this ${noun()}` : "Font Embedding"}</div>
      <div class="field hl"><span>${platform() === "PC" ? "" : `Preserve fidelity when sharing this ${noun()}:`}</span><span class="select">${SM.esc(name)} ⌄</span></div>
      <div class="field"><span class="tick hl">Embed fonts in the file</span></div>
      <div class="field"><span class="radio off">Embed only the characters used</span></div>
      <div class="field"><span class="radio hl">Embed all characters (best for editing by other people)</span></div>
      ${closeHint}`);
    if (platform() === "PC") {
      return [
        { text: `Click <b>File</b> at the top left, then <b>Options</b> at the bottom of the list.`,
          mock: mockWindow(app, `<div class="menu"><div>Info</div><div>Save As</div><div>Export</div><div class="sep"></div><div class="hl">Options</div></div>`) },
        { text: `In the window that opens, choose <b>Save</b> in the list on the left.`,
          mock: mockWindow(`${app} Options`, `<div class="menu"><div>General</div><div>Proofing</div><div class="hl">Save</div><div>Language</div></div>`) },
        { text: `At the bottom, make sure the dropdown shows <b>${SM.esc(name)}</b>. Tick <b>Embed fonts in the file</b> and choose <b>Embed all characters</b>.`,
          mock: dialogFields(`<div class="row"><span class="select">OK</span></div>`) },
        { text: `Click <b>OK</b>, then save with <span class="kbd">Ctrl</span>+<span class="kbd">S</span>. This panel turns green once the font is in the file.`, mock: "" },
      ];
    }
    return [
      { text: `Open the <b>${app}</b> menu (next to the Apple menu) and choose <b>Preferences…</b> (or <b>Settings…</b>). Shortcut: <span class="kbd">⌘</span>+<span class="kbd">,</span>`,
        mock: mockWindow(app, `<div class="menu"><div>About Microsoft ${app}</div><div class="sep"></div><div class="hl">Preferences…  ⌘,</div><div>Services</div></div>`) },
      { text: `In the Preferences window, under <b>Output and Sharing</b>, click <b>Save</b> (the floppy-disk icon).`,
        mock: app === "PowerPoint"
          // Real screenshot (PowerPoint for Mac 16.114); the highlight box is positioned over the Save icon.
          ? `<div class="shot" aria-hidden="true"><img src="assets/walkthrough/powerpoint-mac-preferences.png" alt="">
               <span class="shot-hl" style="left:3.5%;top:58.5%;width:9%;height:13%"></span></div>`
          : mockWindow(`${app} Preferences`, `
              <div class="group-label">Authoring and Proofing Tools</div>
              <div class="icons"><div>⚙︎<br>General</div><div>▤<br>View</div><div>✎<br>Edit</div><div>✓<br>Spelling</div></div>
              <div class="group-label">Output and Sharing</div>
              <div class="icons"><div class="hl"><span style="font-size:20px">💾</span><br>Save</div><div>⎙<br>Print</div></div>
              <div class="group-label">Personal Settings</div>
              <div class="icons"><div>👤<br>User Information</div><div>🔒<br>Security</div><div>🛡︎<br>Privacy</div></div>`) },
      { text: `Under <b>Font Embedding</b>, set the dropdown to <b>${SM.esc(name)}</b>. This setting is per ${noun()}, so check the name. Then tick <b>Embed fonts in the file</b> and choose <b>Embed all characters</b>.`,
        mock: dialogFields("") },
      { text: `Close Preferences and save with <span class="kbd">⌘</span>+<span class="kbd">S</span>. This panel turns green once the font is in the file.`, mock: "" },
    ];
  }

  function fontSteps() {
    const url = new URL("fonts/SlideMarks-Regular.ttf", location.href).href;
    const download = `<button data-action="download" data-url="${SM.esc(url)}">Download SlideMarks-Regular.ttf</button>`;
    if (platform() === "PC") {
      return [
        { text: `Download the font file.`, mock: `<div class="row">${download}</div>` },
        { text: `Open your Downloads folder, right-click <b>SlideMarks-Regular.ttf</b> and choose <b>Install for all users</b> (or <b>Install</b>).`, mock: "" },
        { text: `<b>Close every Office app</b> (PowerPoint, Word, Excel, Outlook) and reopen this file. Office only picks up new fonts when it restarts.`, mock: "" },
      ];
    }
    return [
      { text: `Download the font file.`, mock: `<div class="row">${download}</div>` },
      { text: `Double-click <b>SlideMarks-Regular.ttf</b> in your Downloads folder, then click <b>Install Font</b>.`,
        mock: mockWindow("SlideMarks Regular", `<div style="font-size:28px" class="sm">  </div><div class="row"><span class="select hl">Install Font</span></div>`) },
      { text: `<b>Quit every Office app</b> (PowerPoint, Word, Excel, Outlook) with <span class="kbd">⌘</span>+<span class="kbd">Q</span> and reopen this file. Office only picks up new fonts when it restarts.`, mock: "" },
    ];
  }

  // ── Rendering ─────────────────────────────────────────────────────────────
  function items() {
    const list = [];
    if (state.font === "ok") list.push({ id: "font", level: "ok", title: "SlideMarks is installed", text: "" });
    // Not detected doesn't mean not installed: Office's web view hides user-installed fonts
    // from add-ins (verified on Mac), so ask rather than accuse.
    else list.push({
      id: "font", level: state.font === "confirmed" ? "ok" : "unknown",
      title: state.font === "confirmed" ? "SlideMarks is installed (confirmed by you)" : "Is the SlideMarks font installed?",
      text: state.font === "confirmed" ? "" : "We can't check this from inside Office. If symbols you insert show as boxes, install the font on this computer.",
      walk: state.font === "confirmed" ? null : "font",
      extra: state.font === "confirmed" ? "" : `<button data-action="confirm-font">It's already installed</button>`,
    });
    if (!isOffice()) return list;
    if (platform() === "OfficeOnline") {
      list.push({ id: "embed", level: "unknown", title: `Embedding isn't available on the web`,
        text: `${host()} on the web can't embed fonts. Open this ${noun()} in the desktop app (Editing › Open in Desktop App) and turn embedding on there.` });
      return list;
    }
    const e = state.embed;
    if (!e) list.push({ id: "embed", level: "unknown", title: "Checking this file…", text: "" });
    else if (e.error) list.push({ id: "embed", level: "unknown", title: "Couldn't check this file", text: SM.esc(e.error) });
    else if (e.flag && (e.embedded || !e.used)) list.push({ id: "embed", level: "ok",
      title: e.embedded ? "SlideMarks travels with this file" : "Embedding is on for this file",
      text: e.embedded ? "" : "SlideMarks is embedded when you save after inserting symbols." });
    else if (e.flag) list.push({ id: "embed", level: "pending", title: "Save to finish embedding",
      text: `Embedding is on. Save the ${noun()} to put SlideMarks inside it.` });
    else list.push({ id: "embed", level: "warn", title: "Do this first: embed SlideMarks in this file",
      text: `Without it, anyone who doesn't have SlideMarks installed sees empty boxes instead of your symbols.`, walk: "embed" });
    return list;
  }

  function render() {
    const box = SM.$("setup");
    const list = items();
    const allOk = list.every((i) => i.level === "ok");
    box.hidden = false;
    if (allOk && !state.expanded) {
      box.innerHTML = `<button class="status-line" data-action="expand" aria-expanded="false">
        ${list.map((i) => `<span class="dot ok"></span><span>${SM.esc(i.title)}</span>`).join("")}</button>`;
      return;
    }
    const walk = state.walk;
    box.innerHTML = list.map((i) => `
      <div class="check-item ${i.level}">
        <h3><span class="badge ${i.level}" aria-hidden="true">${i.level === "ok" ? "✓" : i.level === "warn" ? "!" : "…"}</span>${SM.esc(i.title)}</h3>
        ${i.text ? `<p>${i.text}</p>` : ""}
        ${walk && walk.id === i.walk ? walkHtml(walk) : i.walk ? `<div class="row"><button class="primary" data-action="walk" data-walk="${i.walk}">Show me how</button>${i.extra || ""}</div>` : i.extra ? `<div class="row">${i.extra}</div>` : ""}
      </div>`).join("") + (isOffice() ? `<div class="row"><button data-action="recheck">Check again</button>${allOk ? `<button data-action="collapse">Hide</button>` : ""}</div>` : "");
  }

  function walkHtml(walk) {
    const steps = walk.id === "embed" ? embedSteps() : fontSteps();
    const i = Math.min(walk.step, steps.length - 1);
    const step = steps[i];
    return `<div class="walk" role="group" aria-label="Step ${i + 1} of ${steps.length}">
      <div class="step-count">Step ${i + 1} of ${steps.length}</div>
      <div class="step-text">${step.text}</div>
      ${step.mock}
      <div class="nav">
        <button data-action="step" data-delta="-1" ${i === 0 ? "disabled" : ""}>Back</button>
        ${i < steps.length - 1 ? `<button class="primary" data-action="step" data-delta="1">Next</button>` : `<button class="primary" data-action="done">Done</button>`}
      </div></div>`;
  }

  async function refresh({ force = false } = {}) {
    if (state.font !== "confirmed") state.font = (await fontInstalled()) ? "ok" : "warn";
    if (!isOffice() || platform() === "OfficeOnline") return render();
    if (state.checking || (!force && Date.now() - state.lastCheck < 4000)) return render();
    state.checking = true;
    try {
      state.embed = await embedStatus();
    } catch (e) {
      state.embed = { error: e.message || String(e) };
    } finally {
      state.checking = false;
      state.lastCheck = Date.now();
    }
    if (state.walk && state.walk.id === "embed" && state.embed.flag) state.walk = null;
    render();
  }

  function onClick(ev) {
    const btn = ev.target.closest("[data-action]");
    if (!btn) return;
    const a = btn.dataset.action;
    if (a === "expand") { state.expanded = true; render(); }
    else if (a === "collapse") { state.expanded = false; render(); }
    else if (a === "recheck") refresh({ force: true });
    else if (a === "walk") { state.walk = { id: btn.dataset.walk, step: 0 }; render(); }
    else if (a === "step") { state.walk.step += Number(btn.dataset.delta); render(); }
    else if (a === "done") { state.walk = null; refresh({ force: true }); }
    else if (a === "confirm-font") { state.font = "confirmed"; SM.store.set("fontConfirmed", true); render(); }
    else if (a === "download") {
      const url = btn.dataset.url;
      if (isOffice() && Office.context.ui && Office.context.ui.openBrowserWindow) Office.context.ui.openBrowserWindow(url);
      else window.open(url, "_blank");
    }
  }

  function init() {
    if (SM.store.get("fontConfirmed", false)) state.font = "confirmed";
    SM.$("setup").addEventListener("click", onClick);
    // Re-check when the user comes back from Office's Preferences or after saving.
    window.addEventListener("focus", () => refresh());
    document.addEventListener("visibilitychange", () => { if (!document.hidden) refresh(); });
    return refresh({ force: true });
  }

  return { init, refresh, embedStatus, fontInstalled, state };
})();
