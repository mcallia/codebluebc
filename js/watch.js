/* CodeBlue BC — Water Watch live dashboard */
(function () {
  "use strict";

  var DROUGHT_URL = "https://services1.arcgis.com/xeMpV7tU1t4KD3Ei/arcgis/rest/services/British_Columbia_Drought_Levels_%28Edit%29_view/FeatureServer/27/query?where=1%3D1&outFields=BasinName,DroughtLevel,Date_Modified&f=geojson";
  var SCARCITY_URL = "https://services1.arcgis.com/xeMpV7tU1t4KD3Ei/arcgis/rest/services/British_Columbia_Water_Scarcity_Levels_%28view%29/FeatureServer/0/query?where=1%3D1&outFields=Watershed,Water_Scarcity_Level,Assessed_By,Date_Modified&returnGeometry=false&f=json";
  var SNOW_URL = "https://services6.arcgis.com/ubm4tcTYICKBpist/arcgis/rest/services/Snow_Basins_Indices_View/FeatureServer/0/query?where=1%3D1&outFields=basinName,Snow_Basin_Index,Date_Calculated_For&returnGeometry=false&f=json";
  var HYDRO = "https://api.weather.gc.ca/collections/hydrometric-realtime/items";

  var LEVELS = {
    0: { c: "#4d9e63", name: "No drought" },
    1: { c: "#d6a63a", name: "Dry conditions" },
    2: { c: "#c67f2b", name: "Very dry" },
    3: { c: "#b05a24", name: "Severely dry — impacts possible" },
    4: { c: "#93381f", name: "Extremely dry — impacts likely" },
    5: { c: "#641717", name: "Exceptionally dry — impacts certain" }
  };
  var GRAY = "#9fb2c4";

  var STATIONS = [
    { id: "08MF005", name: "Fraser River", place: "at Hope", note: "B.C.'s great artery — drains a quarter of the province" },
    { id: "08HA011", name: "Cowichan River", place: "near Duncan", note: "Famous salmon river; ran critically low in recent droughts" },
    { id: "08NM050", name: "Okanagan River", place: "at Penticton", note: "Lifeline of orchard-and-vineyard country" },
    { id: "08LG010", name: "Coldwater River", place: "at Merritt", note: "Flooded Merritt in 2021; now watched for summer lows" },
    { id: "07FD001", name: "Kiskatinaw River", place: "near Farmington", note: "Supplies Dawson Creek — epicentre of northeast drought" },
    { id: "08HB034", name: "Nanaimo River", place: "near Cassidy", note: "Side channels dried in 2026; salmon rescued by hand" }
  ];

  function stamp() {
    var el = document.getElementById("dash-updated");
    if (el) el.textContent = "Updated " + new Date().toLocaleString("en-CA", { dateStyle: "medium", timeStyle: "short" });
  }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  /* ---------- Drought map ---------- */
  var mapBox = document.getElementById("droughtmap");
  if (mapBox && window.L) {
    var map = L.map("droughtmap", { scrollWheelZoom: false, attributionControl: true })
      .setView([54.6, -125.3], 5);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 11
    }).addTo(map);

    fetch(DROUGHT_URL)
      .then(function (r) { return r.json(); })
      .then(function (gj) {
        var counts = {};
        var newest = 0;
        L.geoJSON(gj, {
          style: function (f) {
            var lv = f.properties.DroughtLevel;
            var known = LEVELS[lv];
            return {
              color: "#26406b", weight: 1, fillOpacity: 0.62,
              fillColor: known ? known.c : GRAY
            };
          },
          onEachFeature: function (f, layer) {
            var p = f.properties;
            var lv = p.DroughtLevel;
            var known = LEVELS[lv];
            counts[known ? lv : "na"] = (counts[known ? lv : "na"] || 0) + 1;
            if (p.Date_Modified && p.Date_Modified > newest) newest = p.Date_Modified;
            layer.bindPopup(
              '<strong>' + esc(p.BasinName) + ' basin</strong><br>' +
              (known
                ? 'Drought level <b>' + lv + '</b> — ' + known.name
                : 'Not currently rated') +
              (p.Date_Modified ? '<br><small>Updated ' + new Date(p.Date_Modified).toLocaleDateString("en-CA") + '</small>' : "")
            );
            layer.on("mouseover", function () { layer.setStyle({ weight: 2.4, fillOpacity: 0.78 }); });
            layer.on("mouseout", function () { layer.setStyle({ weight: 1, fillOpacity: 0.62 }); });
          }
        }).addTo(map);

        /* chips */
        var chips = document.getElementById("basin-chips");
        if (chips) {
          var html = "";
          [5, 4, 3, 2, 1, 0].forEach(function (lv) {
            if (counts[lv]) {
              html += '<span class="chip"><i style="display:inline-block;width:.85em;height:.85em;border-radius:50%;background:' + LEVELS[lv].c + ';margin-right:.45em;vertical-align:-1px"></i><b>' + counts[lv] + '</b>&nbsp;basin' + (counts[lv] > 1 ? "s" : "") + ' at Level ' + lv + '</span>';
            }
          });
          if (counts.na) html += '<span class="chip"><b>' + counts.na + '</b>&nbsp;not rated</span>';
          chips.innerHTML = html;
        }
        var src = document.getElementById("drought-stamp");
        if (src && newest) src.textContent = "Provincial assessments last updated " + new Date(newest).toLocaleDateString("en-CA", { dateStyle: "long" });
        stamp();
      })
      .catch(function () {
        mapBox.outerHTML = '<div class="feed-error">The provincial drought feed isn&rsquo;t responding right now. See the <a href="https://droughtportal.gov.bc.ca/">B.C. Drought Information Portal</a> directly.</div>';
      });
  }

  /* ---------- River gauges ---------- */
  var grid = document.getElementById("gauge-grid");
  if (grid) {
    STATIONS.forEach(function (st) {
      var el = document.createElement("article");
      el.className = "card gauge";
      el.id = "g-" + st.id;
      el.innerHTML =
        '<div class="g-name">' + st.name + ' <span style="font-weight:500;color:var(--slate)">' + st.place + '</span></div>' +
        '<div class="g-id">STATION ' + st.id + '</div>' +
        '<div class="g-val">&hellip;</div>' +
        '<div class="g-sub">' + st.note + '</div>' +
        '<svg viewBox="0 0 300 52" preserveAspectRatio="none" aria-hidden="true"></svg>' +
        '<div class="g-sub g-when" style="margin-top:.3rem"></div>';
      grid.appendChild(el);

      fetch(HYDRO + "?STATION_NUMBER=" + st.id + "&limit=300&sortby=-DATETIME&f=json")
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var feats = d.features || [];
          if (!feats.length) throw new Error("no data");
          var pts = feats.map(function (f) {
            return { t: new Date(f.properties.DATETIME).getTime(), q: f.properties.DISCHARGE, h: f.properties.LEVEL };
          }).reverse();
          var latest = pts[pts.length - 1];
          var useQ = latest.q != null;
          var series = pts.map(function (p) { return useQ ? p.q : p.h; }).filter(function (v) { return v != null; });
          var val = useQ ? latest.q : latest.h;
          var unit = useQ ? "m³/s" : "m";
          var vEl = el.querySelector(".g-val");
          vEl.innerHTML = Number(val).toLocaleString("en-CA", { maximumFractionDigits: val < 10 ? 2 : 0 }) + ' <span class="unit">' + unit + (useQ ? " flow" : " level") + '</span>';
          /* trend vs 24h ago */
          if (series.length > 6) {
            var prev = series[0];
            var delta = ((val - prev) / (prev || 1)) * 100;
            var arrow = Math.abs(delta) < 2 ? "→ steady" : (delta > 0 ? "↑ rising" : "↓ falling");
            el.querySelector(".g-when").textContent = arrow + " over the period shown · measured " +
              new Date(latest.t).toLocaleTimeString("en-CA", { hour: "numeric", minute: "2-digit" });
          }
          /* sparkline */
          var svg = el.querySelector("svg");
          var min = Math.min.apply(null, series), max = Math.max.apply(null, series);
          var span = (max - min) || 1;
          var step = 300 / (series.length - 1 || 1);
          var line = series.map(function (v, i) {
            return (i * step).toFixed(1) + "," + (46 - ((v - min) / span) * 40).toFixed(1);
          }).join(" ");
          svg.innerHTML = '<polygon class="spark-fill" points="0,52 ' + line + ' 300,52"></polygon>' +
            '<polyline points="' + line + '"></polyline>';
        })
        .catch(function () {
          el.querySelector(".g-val").textContent = "—";
          el.querySelector(".g-when").textContent = "Feed unavailable right now";
        });
    });
  }

  /* ---------- Local water scarcity assessments ---------- */
  var scarcity = document.getElementById("scarcity-rows");
  if (scarcity) {
    fetch(SCARCITY_URL)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var rows = (d.features || []).map(function (f) { return f.attributes; });
        if (!rows.length) throw new Error("empty");
        var order = { "Extreme": 0, "High": 1, "Moderate": 2, "Low": 3, "Normal": 4 };
        rows.sort(function (a, b) { return (order[a.Water_Scarcity_Level] ?? 9) - (order[b.Water_Scarcity_Level] ?? 9); });
        scarcity.innerHTML = rows.map(function (r) {
          var lv = r.Water_Scarcity_Level || "—";
          var col = { Extreme: "#641717", High: "#93381f", Moderate: "#c67f2b", Low: "#d6a63a", Normal: "#4d9e63" }[lv] || GRAY;
          return "<tr><td><strong>" + esc(r.Watershed) + "</strong></td>" +
            '<td><span style="display:inline-block;width:.8em;height:.8em;border-radius:50%;background:' + col + ';margin-right:.5em;vertical-align:-1px"></span>' + esc(lv) + "</td>" +
            "<td>" + esc(r.Assessed_By || "") + "</td></tr>";
        }).join("");
      })
      .catch(function () {
        var wrap = document.getElementById("scarcity-wrap");
        if (wrap) wrap.style.display = "none";
      });
  }

  /* ---------- Snow basins ---------- */
  var snow = document.getElementById("snow-note");
  if (snow) {
    fetch(SNOW_URL)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var rows = (d.features || []).map(function (f) { return f.attributes; });
        var withIdx = rows.filter(function (r) { return r.Snow_Basin_Index != null; });
        if (!withIdx.length) {
          snow.innerHTML = "It&rsquo;s summer — the River Forecast Centre publishes snow basin indices during the snow season (January&ndash;June). When the snow returns, this panel wakes up automatically.";
          return;
        }
        withIdx.sort(function (a, b) { return a.Snow_Basin_Index - b.Snow_Basin_Index; });
        var when = withIdx[0].Date_Calculated_For ? new Date(withIdx[0].Date_Calculated_For).toLocaleDateString("en-CA", { dateStyle: "long" }) : "";
        snow.innerHTML = "<p class='small'>Snow basin index — percentage of normal snowpack" + (when ? ", as of " + when : "") + ":</p>" +
          '<div class="chip-row">' + withIdx.map(function (r) {
            var pct = Math.round(r.Snow_Basin_Index);
            var col = pct < 60 ? "#93381f" : pct < 80 ? "#c67f2b" : pct < 110 ? "#4d9e63" : "#1467b3";
            return '<span class="chip"><i style="display:inline-block;width:.8em;height:.8em;border-radius:50%;background:' + col + ';margin-right:.45em;vertical-align:-1px"></i>' + esc(r.basinName) + " <b>" + pct + "%</b></span>";
          }).join("") + "</div>";
      })
      .catch(function () {
        snow.textContent = "Snowpack feed unavailable right now.";
      });
  }
})();
