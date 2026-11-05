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
    timer = setTimeout(() => { el.className = "toast"; }, kind ? 7000 : 2600); // hints and errors need reading time
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

// Visible text that carries a symbol's meaning when "Add a text label" is ticked.
SM.labelText = (sym) => {
  const m = sym.family === "harvey" && /(\d+) percent/.exec(sym.label);
  if (m) return `${m[1]}%`;
  return sym.label.charAt(0).toUpperCase() + sym.label.slice(1);
};
