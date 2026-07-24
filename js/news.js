/* CodeBlue BC — newsroom */
(function () {
  "use strict";
  var list = document.getElementById("news-list");
  if (!list) return;
  var CAT_META = {
    codeblue: { label: "CodeBlue BC", cls: "" },
    coalition: { label: "Coalition", cls: "t-coalition" },
    media: { label: "In the news", cls: "t-media" }
  };
  var items = [];
  var active = "all";

  function fmtDate(d) {
    if (!d) return "";
    var dt = new Date(d + "T12:00:00");
    if (isNaN(dt)) return d;
    return dt.toLocaleDateString("en-CA", { year: "numeric", month: "long", day: "numeric" });
  }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function render() {
    var subset = items.filter(function (it) { return !it.hidden && (active === "all" || it.cat === active); });
    subset.sort(function (a, b) { return (b.date || "").localeCompare(a.date || ""); });
    list.innerHTML = subset.map(function (it) {
      var m = CAT_META[it.cat] || CAT_META.media;
      return '<a class="news-item" href="' + esc(it.url) + '">' +
        '<span class="tag ' + m.cls + '">' + m.label + "</span>" +
        "<h3>" + esc(it.title) + "</h3>" +
        '<div class="src">' + esc(it.source || "") + (it.date ? " · " + fmtDate(it.date) : "") + "</div></a>";
    }).join("") || '<p class="small">Nothing here yet.</p>';
  }

  document.querySelectorAll(".news-filters button").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll(".news-filters button").forEach(function (x) { x.classList.remove("active"); });
      b.classList.add("active");
      active = b.getAttribute("data-cat");
      render();
    });
  });

  fetch("data/news.json?v=" + Math.floor(Date.now() / 3600000))
    .then(function (r) { return r.json(); })
    .then(function (d) {
      items = d.items || [];
      var up = document.getElementById("news-updated");
      if (up && d.updated) up.textContent = "Feed refreshed " + new Date(d.updated).toLocaleString("en-CA", { dateStyle: "medium", timeStyle: "short" });
      render();
    })
    .catch(function () {
      list.innerHTML = '<p class="small">Couldn&rsquo;t load the news feed. Try <a href="https://watershedsecurity.ca/news/">the Coalition newsroom</a> or <a href="https://www.codebluebc.ca/stories">CodeBlue stories</a>.</p>';
    });
})();
