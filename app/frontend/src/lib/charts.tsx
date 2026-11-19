// Hand-rolled SVG charts ported from the V4 mockup (app.js) to keep the exact look.
// Content is built from our own numeric data, so dangerouslySetInnerHTML is safe here.
import React from "react";

export function Raw({ html, className, style }: { html: string; className?: string; style?: React.CSSProperties }) {
  return <div className={className} style={style} dangerouslySetInnerHTML={{ __html: html }} />;
}

export function lineSvg(data: number[], color = "#6e78ed", fill = false, width = 640, height = 180): string {
  if (!data.length) return "";
  const pad = 14, max = Math.max(...data) * 1.13, min = Math.min(...data) * 0.86;
  const pts = data.map((n, i) => [pad + (i * (width - 2 * pad)) / (data.length - 1 || 1), height - pad - ((n - min) / (max - min || 1)) * (height - 2 * pad)]);
  const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(2) + "," + p[1].toFixed(2)).join(" ");
  const area = `${d} L${pts.at(-1)![0]},${height - pad} L${pts[0][0]},${height - pad} Z`;
  const id = color.replace("#", "");
  return `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" style="width:100%;height:${height}px" role="img" aria-label="Trend chart">
    <defs><linearGradient id="fade-${id}" x1="0" y1="0" x2="0" y2="1"><stop stop-color="${color}" stop-opacity=".20"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></linearGradient></defs>
    ${[0.18, 0.48, 0.78].map((y) => `<line x1="0" y1="${height * y}" x2="${width}" y2="${height * y}" stroke="#e6e9f0" stroke-dasharray="4 5"/>`).join("")}
    ${fill ? `<path d="${area}" fill="url(#fade-${id})"/>` : ""}
    <path d="${d}" fill="none" stroke="${color}" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${pts.at(-1)![0]}" cy="${pts.at(-1)![1]}" r="4.5" fill="${color}" stroke="white" stroke-width="2"/></svg>`;
}

export function sparkSvg(data: number[], color: string): string {
  return `<div style="width:85px;height:28px;overflow:hidden">${lineSvg(data, color, false, 85, 27)}</div>`;
}

export function donutSvg(parts: number[], colors: string[], size = 160, centerLabel = "", centerSub = ""): string {
  const total = parts.reduce((a, b) => a + b, 0) || 1;
  let cum = 0;
  const segs = parts.map((p, i) => { const a = (cum / total) * 100; cum += p; return `${colors[i]} ${a}% ${(cum / total) * 100}%`; });
  const big = centerLabel || `${Math.round((parts[0] / total) * 100)}%`;
  return `<div style="height:${size}px;width:${size}px;border-radius:50%;background:conic-gradient(${segs.join(",")});display:grid;place-items:center;margin:auto;position:relative">
    <div style="height:${size * 0.7}px;width:${size * 0.7}px;border-radius:50%;background:var(--panel);display:grid;place-items:center;text-align:center">
    <div><strong style="font-size:${size * 0.14}px;letter-spacing:-1px">${big}</strong><div class="tiny muted">${centerSub || "On-time"}</div></div></div></div>`;
}

/** Two-bar baseline vs scenario comparison (service %). */
export function compareBars(baseline: number, scenario: number, baseLabel = "Baseline", scenLabel = "Scenario"): string {
  const h = (v: number) => Math.max(40, (v / 100) * 170);
  return `<div style="display:flex;align-items:flex-end;gap:18px;justify-content:space-around;height:215px;margin:13px 0 17px;padding:0 15px">
    <div style="width:45%;text-align:center"><div style="font-size:17px;font-weight:800;margin-bottom:9px">${baseline.toFixed(1)}%</div>
      <div style="background:linear-gradient(#818be9,#c1c8ff);height:${h(baseline)}px;max-width:150px;margin:auto;border-radius:9px 9px 3px 3px"></div>
      <div style="font-size:10px;color:#8e94a1;margin-top:9px">${baseLabel} service</div></div>
    <div style="width:45%;text-align:center"><div style="font-size:17px;font-weight:800;margin-bottom:9px">${scenario.toFixed(1)}%</div>
      <div style="background:linear-gradient(#eda98d,#fae0d5);height:${h(scenario)}px;max-width:150px;margin:auto;border-radius:9px 9px 3px 3px"></div>
      <div style="font-size:10px;color:#8e94a1;margin-top:9px">${scenLabel} service</div></div></div>`;
}

export const CHART_COLORS: Record<string, string> = {
  engine: "#6b73eb", gear: "#e5a381", battery: "#7dc4ad", seat: "#c8a8db",
  battery_componment: "#eab5a0", seat_componment: "#9c95ef", car: "#7088ea",
  production: "#7c84eb", transport: "#eab5a0", holding: "#8bcdb1", shortage: "#c8a8db", expedite: "#d8a6e2",
};
