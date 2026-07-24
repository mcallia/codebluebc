/* CodeBlue BC — shared behaviours */
(function () {
  "use strict";
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Header scrolled state */
  var header = document.querySelector(".site-header");
  function onScroll() {
    if (header) header.classList.toggle("scrolled", window.scrollY > 40);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* Mobile nav */
  var toggle = document.querySelector(".nav-toggle");
  var mobile = document.querySelector(".nav-mobile");
  if (toggle && mobile) {
    toggle.addEventListener("click", function () {
      var open = mobile.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
      toggle.querySelector(".ic-burger").style.display = open ? "none" : "block";
      toggle.querySelector(".ic-close").style.display = open ? "block" : "none";
    });
    mobile.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        mobile.classList.remove("open");
        document.body.style.overflow = "";
      });
    });
  }

  /* Reveal on scroll */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  /* Bar chart fills */
  var bars = document.querySelectorAll(".hbar .hb-fill[data-v]");
  function fillBar(el) { el.style.width = el.getAttribute("data-v") + "%"; }
  if ("IntersectionObserver" in window && !reduced) {
    var iob = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { fillBar(e.target); iob.unobserve(e.target); }
      });
    }, { threshold: 0.6 });
    bars.forEach(function (el) { iob.observe(el); });
  } else {
    bars.forEach(fillBar);
  }

  /* Hero word rotator */
  var rot = document.querySelector("[data-rotate]");
  if (rot) {
    var words = JSON.parse(rot.getAttribute("data-rotate"));
    var i = 0;
    if (!reduced && words.length > 1) {
      setInterval(function () {
        i = (i + 1) % words.length;
        rot.style.opacity = 0;
        setTimeout(function () {
          rot.textContent = words[i];
          rot.style.opacity = 1;
        }, 380);
      }, 3400);
      rot.style.transition = "opacity .38s ease";
    }
  }

  /* Scrolly pulse bar */
  var pulsebar = document.querySelector(".pulsebar");
  if (pulsebar) {
    var pbPath = pulsebar.querySelector("path");
    var pbStatus = pulsebar.querySelector(".pb-status");
    var PULSES = {
      healthy: { d: "M0,26 H120 l8,0 6,-14 6,26 6,-12 h84 l8,0 6,-14 6,26 6,-12 h84 l8,0 6,-14 6,26 6,-12 h84 l8,0 6,-14 6,26 6,-12 h84 l8,0 6,-14 6,26 6,-12 H1400", label: "PULSE · STEADY" },
      warn: { d: "M0,26 H90 l6,-10 5,18 5,-8 h120 l4,-16 5,26 5,-10 h40 l6,-6 5,10 5,-4 h150 l5,-18 5,30 6,-12 h130 l4,-8 5,12 4,-4 h180 l6,-16 5,24 5,-8 H1400", label: "PULSE · IRREGULAR" },
      crit: { d: "M0,26 H60 l4,-6 4,10 4,-4 h50 l3,-20 4,34 4,-14 h30 l4,-4 3,6 3,-2 h90 l3,-24 4,40 4,-16 h40 l4,-4 4,6 4,-2 h110 l3,-6 4,8 3,-2 h60 l3,-26 4,42 4,-16 H1400", label: "PULSE · CRITICAL" },
      flat: { d: "M0,26 H420 l5,-5 5,8 5,-3 H1000 l4,-4 4,6 4,-2 H1400", label: "PULSE · FLATLINING" },
      recover: { d: "M0,26 H150 l7,0 6,-12 6,22 6,-10 h130 l7,0 6,-13 6,24 6,-11 h130 l8,0 6,-14 6,26 6,-12 h130 l8,0 6,-15 6,28 6,-13 H1400", label: "PULSE · RETURNING" }
    };
    var chapters = document.querySelectorAll("[data-pulse]");
    if ("IntersectionObserver" in window) {
      var ioc = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            var st = e.target.getAttribute("data-pulse");
            var p = PULSES[st] || PULSES.healthy;
            pulsebar.className = "pulsebar state-" + ({healthy:"ok",warn:"warn",crit:"crit",flat:"flat",recover:"recover"}[st] || "ok");
            pbPath.setAttribute("d", p.d);
            if (pbStatus) pbStatus.textContent = p.label;
          }
        });
      }, { threshold: 0.4 });
      chapters.forEach(function (c) { ioc.observe(c); });
    }
  }

  /* Home live strip */
  var strip = document.getElementById("live-strip");
  if (strip) {
    var fmt = function (n, d) {
      return Number(n).toLocaleString("en-CA", { maximumFractionDigits: d === undefined ? 0 : d });
    };
    var setTile = function (id, val, sub) {
      var t = document.getElementById(id);
      if (!t) return;
      t.classList.remove("skeleton");
      t.querySelector(".lt-value").innerHTML = val;
      if (sub) t.querySelector(".lt-sub").textContent = sub;
    };
    var fail = function (id) {
      var t = document.getElementById(id);
      if (!t) return;
      t.classList.remove("skeleton");
      t.querySelector(".lt-value").innerHTML = "—";
      t.querySelector(".lt-sub").textContent = "Feed unavailable right now";
    };

    /* Fraser River discharge */
    fetch("https://api.weather.gc.ca/collections/hydrometric-realtime/items?STATION_NUMBER=08MF005&limit=1&sortby=-DATETIME&f=json")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var p = d.features[0].properties;
        var when = new Date(p.DATETIME);
        setTile("lt-fraser",
          fmt(p.DISCHARGE) + ' <span class="unit">m³/s</span>',
          "Measured " + when.toLocaleTimeString("en-CA", { hour: "numeric", minute: "2-digit" }));
      }).catch(function () { fail("lt-fraser"); });

    /* Drought levels summary — B.C. Drought Information Portal live layer */
    fetch("https://services1.arcgis.com/xeMpV7tU1t4KD3Ei/arcgis/rest/services/British_Columbia_Drought_Levels_%28Edit%29_view/FeatureServer/27/query?where=1%3D1&outFields=BasinName,DroughtLevel&returnGeometry=false&f=json")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var lvls = d.features.map(function (f) { return f.attributes.DroughtLevel; })
          .filter(function (v) { return v !== null && v >= 0 && v <= 5; });
        if (!lvls.length) { fail("lt-drought"); return; }
        var worst = Math.max.apply(null, lvls);
        var high = lvls.filter(function (v) { return v >= 3; }).length;
        setTile("lt-drought",
          "Level <b>" + worst + "</b>",
          high + " of " + lvls.length + " basins at drought level 3 or higher");
      }).catch(function () { fail("lt-drought"); });
  }

  /* Year */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
