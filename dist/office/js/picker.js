// Character-map picker: search, family filter, favorites and recents, keyboard navigation,
// preview, and Insert (Office) or Copy (standalone page). Host-independent.

SM.picker = (() => {
  const data = window.SM_DATA;
  const byId = Object.fromEntries(data.symbols.map((s) => [s.id, s]));
  const familyTitle = Object.fromEntries(data.families.map((f) => [f.id, f.title]));
  const haystack = Object.fromEntries(data.symbols.map((s) => [s.id, [
    s.name, s.id, s.label, familyTitle[s.family], ...s.tags,
    s.cp, `u+${s.cp}`, s.pua, `u+${s.pua}`, ...s.aliases.map((a) => `u+${a}`), s.char,
  ].join(" ").toLowerCase()]));
  const state = { query: "", family: "", selected: null, host: null, busy: false };
  const MAX_RECENT = 12;

  function matches() {
    const words = state.query.toLowerCase().split(/\s+/).filter(Boolean);
    return data.symbols.filter((s) =>
      (!state.family || s.family === state.family) && words.every((w) => haystack[s.id].includes(w)));
  }

  function optionHtml(s) {
    const sel = state.selected === s.id;
    return `<div role="option" class="cell sm" id="opt-${s.id}" data-id="${s.id}" aria-selected="${sel}"
      tabindex="${sel ? 0 : -1}" aria-label="${SM.esc(s.name)}" title="${SM.esc(s.name)}">${SM.esc(s.char)}</div>`;
  }

  function shelfHtml(title, ids) {
    const items = ids.map((id) => byId[id]).filter(Boolean);
    if (!items.length) return "";
    return `<div class="shelf"><h2>${title}</h2><div class="shelf-grid">${items.map((s) =>
      `<button class="cell sm" data-pick="${s.id}" aria-label="${SM.esc(s.name)}" title="${SM.esc(s.name)}">${SM.esc(s.char)}</button>`).join("")}</div></div>`;
  }

  function render() {
    const list = matches();
    const browsing = !state.query && !state.family;
    SM.$("shelves").innerHTML = browsing
      ? shelfHtml("Favorites", SM.store.get("favorites", [])) + shelfHtml("Recent", SM.store.get("recent", []))
      : "";
    if (!list.some((s) => s.id === state.selected)) state.selected = list[0] ? list[0].id : null;
    const groups = [];
    for (const s of list) {
      if (!groups.length || groups[groups.length - 1].family !== s.family) groups.push({ family: s.family, items: [] });
      groups[groups.length - 1].items.push(s);
    }
    SM.$("grid").innerHTML = groups.map((g) => `<div role="group" class="group" aria-label="${SM.esc(familyTitle[g.family])}">
      <h2 aria-hidden="true">${SM.esc(familyTitle[g.family])}</h2><div class="grid">${g.items.map(optionHtml).join("")}</div></div>`).join("");
    SM.$("grid").className = "";
    SM.$("empty").hidden = list.length > 0;
    renderPreview();
  }

  function renderPreview() {
    const s = byId[state.selected];
    const pv = SM.$("preview");
    pv.hidden = !s;
    if (!s) return;
    SM.$("pv-glyph").textContent = s.char;
    SM.$("pv-name").textContent = s.name;
    const std = s.aliases.length
      ? ` · inserts standard <code>U+${s.aliases[0]}</code> so screen readers say “${SM.esc(s.label)}”`
      : "";
    SM.$("pv-meta").innerHTML = `<code>U+${s.pua}</code> · ${SM.esc(familyTitle[s.family])}${s.status === "candidate" ? " · candidate" : ""}${std}`;
    SM.$("pv-label-text").textContent = `(“${SM.labelText(s)}”)`;
    const fav = SM.store.get("favorites", []).includes(s.id);
    SM.$("pv-fav").setAttribute("aria-pressed", String(fav));
    SM.$("pv-fav").firstElementChild.textContent = fav ? "★" : "☆";
    SM.$("pv-fav").title = fav ? "Remove from favorites" : "Add to favorites";
    SM.$("pv-insert").disabled = state.busy;
    const confirm = SM.$("pv-confirm");
    if (confirm) confirm.remove();
  }

  function select(id, { focus = false } = {}) {
    state.selected = id;
    document.querySelectorAll('#grid [role="option"]').forEach((el) => {
      const on = el.dataset.id === id;
      el.setAttribute("aria-selected", String(on));
      el.tabIndex = on ? 0 : -1;
    });
    const el = SM.$(`opt-${id}`);
    if (el) {
      if (focus) el.focus();
      el.scrollIntoView({ block: "nearest" });
    }
    renderPreview();
  }

  function remember(id) {
    const recent = [id, ...SM.store.get("recent", []).filter((x) => x !== id)].slice(0, MAX_RECENT);
    SM.store.set("recent", recent);
  }

  // A step only the user can do (it stays until dismissed, unlike a toast).
  function showNext(next) {
    SM.$("pv-confirm")?.remove();
    const div = document.createElement("div");
    div.id = "pv-confirm";
    div.className = "check-item pending";
    div.setAttribute("role", "status");
    div.innerHTML = `<p><b>${SM.esc(next.title)}</b></p><p>${next.html}</p>
      <div class="row"><button data-dismiss>Got it</button></div>`;
    div.querySelector("[data-dismiss]").onclick = () => div.remove();
    SM.$("preview").querySelector(".preview-info").appendChild(div);
  }

  async function insert() {
    const s = byId[state.selected];
    if (!s || state.busy) return;
    if (!state.host.canInsert) return copy();
    state.busy = true;
    renderPreview();
    try {
      const result = await state.host.insert(s, { label: SM.$("pv-label").checked });
      if (result.ok) remember(s.id);
      if (result.next) showNext(result.next);
      else SM.toast(result.message, result.ok && !result.warn ? "" : "hint");
      SM.setup.refresh({ force: true });
    } catch (e) {
      SM.toast(`Something went wrong: ${e.message || e}. Try again, or use Copy instead.`, "error");
    } finally {
      state.busy = false;
      SM.$("pv-insert").disabled = false;
    }
  }

  async function copy() {
    const s = byId[state.selected];
    if (!s) return;
    const label = SM.$("pv-label").checked ? SM.labelText(s) : "";
    const text = label ? `${s.char} ${label}` : s.char;
    const ok = await SM.copyText(text, SM.clipboardHtml(s.char, label));
    if (ok) remember(s.id);
    SM.toast(ok ? `Copied ${s.name}.` : "Couldn't copy. Select the symbol and copy it manually.", ok ? "" : "error");
    // PowerPoint's default paste ("Use Destination Theme") swaps the font for the theme font;
    // "Keep Source Formatting" keeps SlideMarks (verified on PowerPoint for Mac). Show how, right when it matters.
    if (ok && document.body.dataset.mode === "browser" && !SM.store.get("hidePasteHelp", false)) showPasteHelp();
  }

  function showPasteHelp() {
    SM.$("paste-help").hidden = false;
    SM.$("paste-help-open").setAttribute("aria-expanded", "true");
    SM.$("paste-help-ok").focus();
  }

  function hidePasteHelp() {
    SM.$("paste-help").hidden = true;
    SM.$("paste-help-open").setAttribute("aria-expanded", "false");
    SM.$("pv-copy").focus();
  }

  // Arrow keys move geometrically through the wrapped grid, across family groups.
  function move(key) {
    const opts = [...document.querySelectorAll('#grid [role="option"]')];
    const cur = SM.$(`opt-${state.selected}`);
    if (!opts.length || !cur) return;
    const i = opts.indexOf(cur);
    let next;
    if (key === "ArrowRight") next = opts[i + 1];
    else if (key === "ArrowLeft") next = opts[i - 1];
    else if (key === "Home") next = opts[0];
    else if (key === "End") next = opts[opts.length - 1];
    else {
      const r = cur.getBoundingClientRect();
      const down = key === "ArrowDown";
      const rowTops = [...new Set(opts.map((o) => Math.round(o.getBoundingClientRect().top)))].sort((a, b) => a - b);
      const at = rowTops.indexOf(Math.round(r.top));
      const targetTop = rowTops[at + (down ? 1 : -1)];
      if (targetTop === undefined) return;
      const row = opts.filter((o) => Math.round(o.getBoundingClientRect().top) === targetTop);
      next = row.reduce((best, o) => Math.abs(o.getBoundingClientRect().left - r.left) < Math.abs(best.getBoundingClientRect().left - r.left) ? o : best);
    }
    if (next) select(next.dataset.id, { focus: true });
  }

  function init(host) {
    state.host = host;
    SM.$("family").insertAdjacentHTML("beforeend", data.families.map((f) => `<option value="${f.id}">${SM.esc(f.title)}</option>`).join(""));
    SM.$("pv-insert").textContent = host.canInsert ? `Insert into ${host.name}` : "Insert";
    SM.$("pv-label").checked = SM.store.get("addLabel", false);
    SM.$("pv-label").onchange = (e) => SM.store.set("addLabel", e.target.checked);
    SM.$("q").addEventListener("input", (e) => { state.query = e.target.value; render(); });
    SM.$("family").addEventListener("change", (e) => { state.family = e.target.value; render(); });
    SM.$("q").addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown" || e.key === "Enter") {
        e.preventDefault();
        if (e.key === "Enter" && state.selected) return insert();
        if (state.selected) select(state.selected, { focus: true });
      }
    });
    SM.$("grid").addEventListener("click", (e) => { const o = e.target.closest('[role="option"]'); if (o) select(o.dataset.id); });
    SM.$("grid").addEventListener("dblclick", (e) => { if (e.target.closest('[role="option"]')) insert(); });
    SM.$("grid").addEventListener("keydown", (e) => {
      if (["ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown", "Home", "End"].includes(e.key)) { e.preventDefault(); move(e.key); }
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); insert(); }
    });
    SM.$("shelves").addEventListener("click", (e) => {
      const b = e.target.closest("[data-pick]");
      if (!b) return;
      state.query = ""; state.family = "";
      SM.$("q").value = ""; SM.$("family").value = "";
      render();
      select(b.dataset.pick, { focus: true });
    });
    SM.$("paste-help-open").onclick = showPasteHelp;
    SM.$("paste-help-ok").onclick = hidePasteHelp;
    SM.$("paste-help-never").onclick = () => { SM.store.set("hidePasteHelp", true); hidePasteHelp(); };
    SM.$("paste-help").addEventListener("keydown", (e) => { if (e.key === "Escape") hidePasteHelp(); });
    SM.$("pv-insert").onclick = insert;
    SM.$("pv-copy").onclick = copy;
    SM.$("pv-fav").onclick = () => {
      const favs = SM.store.get("favorites", []);
      const id = state.selected;
      SM.store.set("favorites", favs.includes(id) ? favs.filter((x) => x !== id) : [...favs, id]);
      render();
      select(id);
    };
    document.addEventListener("keydown", (e) => {
      if (e.key === "/" && document.activeElement !== SM.$("q")) { e.preventDefault(); SM.$("q").focus(); }
    });
    render();
  }

  return { init, matches, state };
})();
