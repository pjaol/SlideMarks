// Shared helpers. Classic scripts (no modules) so picker.html also works from file://.
window.SM = window.SM || {};

SM.FONT = "SlideMarks";
SM.$ = (id) => document.getElementById(id);

SM.esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

SM.toast = (() => {
  let timer;
  return (message, kind = "") => {
    const el = SM.$("toast");
    el.textContent = message;
    el.className = `toast show ${kind}`;
    clearTimeout(timer);
    timer = setTimeout(() => { el.className = "toast"; }, kind === "warn" ? 6000 : 2600);
  };
})();

// Recents and favorites persist per machine. localStorage can be unavailable (privacy modes): fail soft.
SM.store = {
  get(key, fallback) {
    try { return JSON.parse(localStorage.getItem(`slidemarks.${key}`)) ?? fallback; } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(`slidemarks.${key}`, JSON.stringify(value)); } catch { /* not persisted */ }
  },
};

SM.isSymbolChar = (ch) => {
  const p = ch.codePointAt(0);
  return p >= 0xe000 && p <= 0xf8ff;
};

// Visible text that carries a symbol's meaning when "Add a text label" is ticked.
SM.labelText = (sym) => {
  const m = sym.family === "harvey" && /(\d+) percent/.exec(sym.label);
  if (m) return `${m[1]}%`;
  return sym.label.charAt(0).toUpperCase() + sym.label.slice(1);
};
