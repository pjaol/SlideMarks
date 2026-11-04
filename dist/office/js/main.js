// Boot: pick the host adapter, then start the picker and the setup checklist.
(function boot() {
  const start = (host) => {
    SM.picker.init(host);
    SM.setup.init();
    SM.$("app").removeAttribute("aria-busy");
  };
  if (document.body.dataset.mode !== "office" || !window.Office) return start(SM.hosts.browser);
  Office.onReady((info) => {
    if (info.host === Office.HostType.PowerPoint) start(SM.hosts.powerpoint);
    else if (info.host === Office.HostType.Word) start(SM.hosts.word);
    else {
      // taskpane.html opened in a normal browser: behave like the standalone page.
      document.body.dataset.mode = "browser";
      start(SM.hosts.browser);
    }
  });
})();
