const DATA_URL = "./data/dashboard_data.json";
const CHART_W = 640;
const CHART_H = 280;
const PAD = 28;

function fmtNum(n, digits = 1) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "-";
  return Number(n).toFixed(digits);
}

function paceLabel(minPerKm) {
  if (minPerKm === null || minPerKm === undefined) return "-";
  let m = Math.floor(minPerKm);
  let s = Math.round((minPerKm - m) * 60);
  if (s === 60) {
    m += 1;
    s = 0;
  }
  return `${m}:${String(s).padStart(2, "0")} /km`;
}

function yScale(value, min, max) {
  if (max === min) return CHART_H / 2;
  const pct = (value - min) / (max - min);
  return CHART_H - PAD - pct * (CHART_H - PAD * 2);
}

function xScale(i, total) {
  if (total <= 1) return CHART_W / 2;
  const pct = i / (total - 1);
  return PAD + pct * (CHART_W - PAD * 2);
}

function clearSvg(svg) {
  while (svg.firstChild) svg.removeChild(svg.firstChild);
}

function addAxes(svg) {
  const axis = document.createElementNS("http://www.w3.org/2000/svg", "path");
  axis.setAttribute("d", `M ${PAD} ${PAD} V ${CHART_H - PAD} H ${CHART_W - PAD}`);
  axis.setAttribute("stroke", "#a8b3ac");
  axis.setAttribute("fill", "none");
  axis.setAttribute("stroke-width", "1");
  svg.appendChild(axis);
}

function renderLine(svgId, points, valueKey, color) {
  const svg = document.getElementById(svgId);
  clearSvg(svg);
  addAxes(svg);
  if (!points.length) return;

  const vals = points.map((p) => Number(p[valueKey])).filter((v) => !Number.isNaN(v));
  const min = Math.min(...vals);
  const max = Math.max(...vals);

  const d = points
    .map((p, i) => {
      const x = xScale(i, points.length);
      const y = yScale(Number(p[valueKey]), min, max);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", d);
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", color);
  path.setAttribute("stroke-width", "2.5");
  svg.appendChild(path);

  points.forEach((p, i) => {
    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    c.setAttribute("cx", xScale(i, points.length));
    c.setAttribute("cy", yScale(Number(p[valueKey]), min, max));
    c.setAttribute("r", "3.5");
    c.setAttribute("fill", color);
    c.setAttribute("opacity", "0.85");
    svg.appendChild(c);
  });
}

function renderBars(svgId, points, valueKey, color) {
  const svg = document.getElementById(svgId);
  clearSvg(svg);
  addAxes(svg);
  if (!points.length) return;

  const vals = points.map((p) => Number(p[valueKey])).filter((v) => !Number.isNaN(v));
  const max = Math.max(...vals, 1);
  const barW = Math.max(2, (CHART_W - PAD * 2) / points.length - 2);

  points.forEach((p, i) => {
    const x = PAD + i * ((CHART_W - PAD * 2) / points.length) + 1;
    const y = yScale(Number(p[valueKey]), 0, max);
    const h = CHART_H - PAD - y;
    const r = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    r.setAttribute("x", x);
    r.setAttribute("y", y);
    r.setAttribute("width", barW);
    r.setAttribute("height", Math.max(h, 1));
    r.setAttribute("fill", color);
    r.setAttribute("opacity", "0.85");
    svg.appendChild(r);
  });
}

function renderScatter(svgId, points) {
  const svg = document.getElementById(svgId);
  clearSvg(svg);
  addAxes(svg);
  if (!points.length) return;

  const xs = points.map((p) => Number(p.avg_hr));
  const ys = points.map((p) => Number(p.avg_pace_min_per_km));
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  points.forEach((p) => {
    const xPct = (Number(p.avg_hr) - minX) / (maxX - minX || 1);
    const x = PAD + xPct * (CHART_W - PAD * 2);

    // Pace chart is inverted (faster pace appears higher).
    const yPct = (Number(p.avg_pace_min_per_km) - minY) / (maxY - minY || 1);
    const y = CHART_H - PAD - yPct * (CHART_H - PAD * 2);

    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    c.setAttribute("cx", x);
    c.setAttribute("cy", y);
    c.setAttribute("r", "4");
    c.setAttribute("fill", "#1f7a63");
    c.setAttribute("opacity", "0.75");
    svg.appendChild(c);
  });
}

function renderKpis(kpis) {
  const wrap = document.getElementById("kpis");
  wrap.innerHTML = "";
  const rows = [
    ["Total Runs", `${kpis.total_runs}`],
    ["Lifetime Distance", `${fmtNum(kpis.lifetime_distance_km, 1)} km`],
    ["Weekly Mileage", `${fmtNum(kpis.weekly_mileage_km, 1)} km`],
    ["7d vs 28d Ratio", `${fmtNum(kpis.training_load_ratio, 2)}`],
    ["Latest Run", `${kpis.latest_run_date}`],
    ["Latest Pace", `${paceLabel(kpis.latest_run_pace)}`],
  ];

  rows.forEach(([label, value]) => {
    const card = document.createElement("article");
    card.className = "kpi";
    card.innerHTML = `<p class="label">${label}</p><p class="value">${value}</p>`;
    wrap.appendChild(card);
  });
}

function renderTable(rows) {
  const tbody = document.querySelector("#runTable tbody");
  tbody.innerHTML = "";

  const sorted = [...rows].sort((a, b) => (a.workout_date < b.workout_date ? 1 : -1));
  sorted.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.workout_date || "-"}</td>
      <td>${fmtNum(r.distance_km, 2)}</td>
      <td>${fmtNum(r.duration_min, 1)}</td>
      <td>${fmtNum(r.avg_hr, 0)}</td>
      <td>${fmtNum(r.max_hr, 0)}</td>
      <td>${fmtNum(r.avg_cadence, 1)}</td>
      <td>${paceLabel(r.avg_pace_min_per_km)}</td>
      <td>${fmtNum(r.hr_efficiency, 4)}</td>
      <td>${fmtNum(r.calories, 0)}</td>
      <td>${fmtNum(r.avg_temperature, 1)}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadDashboard() {
  const generatedAt = document.getElementById("generatedAt");
  const emptyState = document.getElementById("emptyState");
  const content = document.getElementById("content");

  try {
    const resp = await fetch(DATA_URL, { cache: "no-store" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const payload = await resp.json();

    if (!payload.has_data) {
      emptyState.hidden = false;
      content.hidden = true;
      generatedAt.textContent = payload.generated_at
        ? `Generated: ${payload.generated_at}`
        : "No data file found yet.";
      return;
    }

    emptyState.hidden = true;
    content.hidden = false;
    generatedAt.textContent = `Generated: ${payload.generated_at}`;

    renderKpis(payload.kpis);
    renderLine("monthlyChart", payload.series.monthly_mileage, "distance_km", "#b45709");
    renderScatter("scatterChart", payload.series.pace_vs_hr);
    renderLine("cadenceChart", payload.series.cadence_trend, "avg_cadence", "#0c4a3a");
    renderBars("distanceChart", payload.series.distance_trend, "distance_km", "#296f8f");
    renderTable(payload.series.run_table);
  } catch (err) {
    emptyState.hidden = false;
    content.hidden = true;
    generatedAt.textContent = "Could not load dashboard data. Run ./run_pwa.sh first.";
    console.error(err);
  }
}

function setupInstallPrompt() {
  let deferredPrompt = null;
  const installBtn = document.getElementById("installBtn");

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredPrompt = event;
    installBtn.hidden = false;
  });

  installBtn.addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    installBtn.hidden = true;
  });
}

document.getElementById("refreshBtn").addEventListener("click", () => {
  loadDashboard();
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js");
  });
}

setupInstallPrompt();
loadDashboard();
