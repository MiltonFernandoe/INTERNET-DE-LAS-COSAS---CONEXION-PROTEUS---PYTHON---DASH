from flask import Flask, render_template_string, request, jsonify
import serial
import time
import threading
import webbrowser

app = Flask(__name__)

SERIAL_PORT = 'COM11'
BAUD_RATE = 115200

sistema_activo = False
nivel_tanque = 50
ser = None

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"✅ Conectado a {SERIAL_PORT} a {BAUD_RATE} baudios")
except Exception as e:
    print(f"❌ Error al conectar al puerto serial: {e}")
    ser = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SCADA — Control Industrial TK-01</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #f5f4f0;
    --bg2: #eeede8;
    --surface: #ffffff;
    --surface2: #f9f8f5;
    --border: #e2e0d8;
    --border2: #d0cec4;
    --ink: #1a1916;
    --ink2: #3d3b35;
    --ink3: #7a7870;
    --ink4: #b0ae a6;
    --green: #1a7a4a;
    --green-bg: #e8f5ee;
    --green-border: #a8d8bc;
    --green-light: #4caf7d;
    --red: #b91c1c;
    --red-bg: #fef2f2;
    --red-border: #fca5a5;
    --amber: #b45309;
    --amber-bg: #fffbeb;
    --amber-border: #fcd34d;
    --blue: #1d4ed8;
    --blue-bg: #eff6ff;
    --blue-border: #93c5fd;
    --steel: #334155;
    --accent: #e63946;
    --font-display: 'Bebas Neue', sans-serif;
    --font-mono: 'DM Mono', monospace;
    --font-body: 'DM Sans', sans-serif;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    --shadow: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.05);
    --shadow-lg: 0 12px 32px rgba(0,0,0,0.1), 0 4px 8px rgba(0,0,0,0.06);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    font-family: var(--font-body);
    color: var(--ink);
    min-height: 100vh;
    padding: 28px;
  }

  /* ── HEADER ── */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--ink);
    border-radius: 16px;
    padding: 18px 28px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
  }
  .header::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 5px;
    background: var(--accent);
  }
  .header-left { display: flex; align-items: center; gap: 18px; }
  .header-icon {
    width: 48px; height: 48px;
    background: var(--accent);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .header-icon svg { width: 26px; height: 26px; stroke: white; }
  .header h1 {
    font-family: var(--font-display);
    font-size: 28px;
    letter-spacing: 0.08em;
    color: #ffffff;
    line-height: 1;
  }
  .header .sub {
    font-family: var(--font-mono);
    font-size: 10px;
    color: #888;
    letter-spacing: 0.15em;
    margin-top: 4px;
    text-transform: uppercase;
  }
  .header-right { display: flex; align-items: center; gap: 14px; }

  .sys-badge {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 16px;
    border-radius: 50px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    transition: all 0.3s;
  }
  .sys-badge.activo { background: var(--green-bg); color: var(--green); border: 1.5px solid var(--green-border); }
  .sys-badge.parado { background: var(--red-bg); color: var(--red); border: 1.5px solid var(--red-border); }
  .led { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .led-green { background: var(--green-light); box-shadow: 0 0 6px var(--green-light); animation: blink 1.8s ease-in-out infinite; }
  .led-red { background: var(--red); }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }

  .clock {
    font-family: var(--font-mono);
    font-size: 15px;
    font-weight: 500;
    color: #ccc;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 7px 14px;
    letter-spacing: 0.05em;
  }

  /* ── GRID ── */
  .grid {
    display: grid;
    grid-template-columns: 360px 1fr;
    gap: 20px;
    margin-bottom: 20px;
    align-items: start;
  }

  /* ── CARD BASE ── */
  .card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 16px;
    box-shadow: var(--shadow);
    overflow: hidden;
  }
  .card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 22px;
    border-bottom: 1.5px solid var(--border);
    background: var(--surface2);
  }
  .card-label {
    display: flex; align-items: center; gap: 10px;
    font-family: var(--font-display);
    font-size: 18px;
    letter-spacing: 0.1em;
    color: var(--ink2);
  }
  .card-label svg { width: 18px; height: 18px; stroke: var(--ink3); }
  .card-body { padding: 22px; }

  /* ── STATUS BADGE ── */
  .status-pill {
    padding: 4px 12px;
    border-radius: 50px;
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    display: flex; align-items: center; gap: 6px;
  }
  .pill-ok { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
  .pill-warn { background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-border); }
  .pill-danger { background: var(--red-bg); color: var(--red); border: 1px solid var(--red-border); }

  /* ── TANK ── */
  .tank-body {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
  }

  .tank-visual {
    position: relative;
    width: 160px;
    height: 240px;
    flex-shrink: 0;
  }
  .tank-outer {
    position: absolute; inset: 0;
    border: 3px solid #c8c5bc;
    border-radius: 14px;
    background: #f0efe9;
    overflow: hidden;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.06), var(--shadow-sm);
  }
  .tank-water {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(180deg, #60c8e0 0%, #2196b8 100%);
    transition: height 0.6s cubic-bezier(.4,0,.2,1);
    border-radius: 0 0 11px 11px;
  }
  .tank-water::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 6px;
    background: rgba(255,255,255,0.35);
    border-radius: 4px 4px 0 0;
    animation: wave 2s linear infinite;
  }
  @keyframes wave {
    0%,100%{transform:scaleX(1) translateX(0)}
    50%{transform:scaleX(0.96) translateX(4px)}
  }
  .tank-shine {
    position: absolute;
    top: 10px; left: 10px;
    width: 18px; height: 50px;
    background: linear-gradient(180deg, rgba(255,255,255,0.5), rgba(255,255,255,0));
    border-radius: 9px;
    pointer-events: none;
  }
  .tank-marks {
    position: absolute;
    right: -30px;
    top: 0; bottom: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--ink3);
  }
  .tank-label {
    position: absolute;
    bottom: -28px; left: 0; right: 0;
    text-align: center;
    font-family: var(--font-display);
    font-size: 14px;
    letter-spacing: 0.15em;
    color: var(--ink3);
  }

  .tank-metrics { width: 100%; }
  .big-number {
    font-family: var(--font-display);
    font-size: 64px;
    line-height: 1;
    letter-spacing: 0.02em;
    color: var(--ink);
  }
  .big-unit {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--ink3);
    margin-top: 2px;
    letter-spacing: 0.05em;
  }

  .bar-wrap {
    margin: 16px 0;
    background: var(--bg2);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    height: 28px;
    overflow: hidden;
    position: relative;
  }
  .bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #2196b8, #60c8e0);
    transition: width 0.6s cubic-bezier(.4,0,.2,1);
    display: flex; align-items: center; justify-content: flex-end;
    padding-right: 10px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 500;
    color: white;
  }
  .bar-fill.danger { background: linear-gradient(90deg, #b91c1c, #ef4444); }
  .bar-fill.warning { background: linear-gradient(90deg, #b45309, #f59e0b); }

  .meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 4px;
  }
  .meta-item {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
  }
  .meta-key {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--ink3);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .meta-val {
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 500;
    color: var(--ink);
  }

  /* ── BUTTONS ── */
  .btn-row {
    display: flex;
    gap: 12px;
    margin-top: 18px;
  }
  .btn {
    flex: 1;
    padding: 13px 16px;
    border-radius: 10px;
    font-family: var(--font-display);
    font-size: 16px;
    letter-spacing: 0.12em;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s ease;
    display: flex; align-items: center; justify-content: center; gap: 8px;
  }
  .btn-on {
    background: var(--green);
    color: white;
    border-color: var(--green);
    box-shadow: 0 4px 16px rgba(26,122,74,0.25);
  }
  .btn-on:hover { background: #15633c; box-shadow: 0 6px 20px rgba(26,122,74,0.35); transform: translateY(-1px); }
  .btn-off {
    background: white;
    color: var(--red);
    border-color: var(--red-border);
  }
  .btn-off:hover { background: var(--red-bg); transform: translateY(-1px); }
  .btn:active { transform: translateY(0) !important; }

  /* ── CONVEYOR BELT ── */
  .conveyor-card { margin-bottom: 20px; }

  .belt-scene {
    background: var(--surface2);
    border: 1.5px solid var(--border);
    border-radius: 12px;
    padding: 24px 20px;
    position: relative;
    overflow: hidden;
    min-height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    gap: 0;
  }

  /* Rails (top & bottom) */
  .belt-rail {
    position: absolute;
    left: 0; right: 0;
    height: 10px;
    background: linear-gradient(180deg, #c0bdb5, #a8a49c);
    border-radius: 5px;
    z-index: 3;
    box-shadow: 0 2px 4px rgba(0,0,0,0.12);
  }
  .belt-rail-top { top: 52px; }
  .belt-rail-bottom { top: 90px; }

  /* Pulleys */
  .pulley {
    position: absolute;
    width: 40px; height: 40px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #6b6862, #3a3835);
    border: 3px solid #888;
    top: 51px;
    z-index: 5;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }
  .pulley::after {
    content: '';
    position: absolute;
    inset: 6px;
    border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.15);
  }
  .pulley-left { left: 16px; }
  .pulley-right { right: 16px; }
  .pulley.spinning { animation: spin 1s linear infinite; }
  .pulley.spinning-slow { animation: spin 2s linear infinite; }
  @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

  /* Belt surface */
  .belt-surface {
    position: absolute;
    left: 36px; right: 36px;
    top: 57px;
    height: 28px;
    background: repeating-linear-gradient(
      90deg,
      #4a4845 0px, #4a4845 18px,
      #3a3835 18px, #3a3835 20px
    );
    z-index: 2;
    overflow: hidden;
  }
  .belt-surface::after {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      90deg,
      transparent 0px, transparent 18px,
      rgba(255,255,255,0.06) 18px, rgba(255,255,255,0.06) 20px
    );
    animation: belt-move 0.6s linear infinite;
    animation-play-state: paused;
  }
  .belt-surface.running::after { animation-play-state: running; }
  @keyframes belt-move { from{background-position:0 0} to{background-position:-20px 0} }

  /* Packages on belt */
  .packages-track {
    position: absolute;
    left: 36px; right: 36px;
    top: 22px;
    height: 35px;
    overflow: hidden;
    z-index: 4;
    pointer-events: none;
  }
  .package {
    position: absolute;
    width: 34px;
    height: 34px;
    border-radius: 5px;
    top: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    border: 2px solid rgba(0,0,0,0.12);
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    animation-play-state: paused;
  }
  .package.p1 { background: #e8f4f8; border-color: #93c5d8; animation-duration: 6s; animation-name: pkg-move; left: -40px; }
  .package.p2 { background: #fef9e7; border-color: #f0c840; animation-duration: 6s; animation-name: pkg-move; left: -40px; animation-delay: -2s; }
  .package.p3 { background: #f0fdf4; border-color: #86efac; animation-duration: 6s; animation-name: pkg-move; left: -40px; animation-delay: -4s; }
  .package.running { animation-play-state: running; }

  @keyframes pkg-move {
    from { transform: translateX(0); }
    to   { transform: translateX(calc(100% + 80px + 36px)); }
  }

  /* Belt sensors & indicators */
  .belt-info-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    flex-wrap: wrap;
    gap: 8px;
  }
  .sensor {
    display: flex; align-items: center; gap: 7px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--ink3);
  }
  .sensor-dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #ccc;
    transition: all 0.3s;
  }
  .sensor-dot.active { background: var(--green-light); box-shadow: 0 0 6px var(--green-light); }

  .belt-speed {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--ink3);
  }
  .belt-speed span { color: var(--ink); font-weight: 500; }

  /* ── ALERTS ── */
  .alerts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }

  .log-list {
    max-height: 160px;
    overflow-y: auto;
  }
  .log-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 9px 0;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
    animation: fade-in 0.3s ease;
  }
  @keyframes fade-in { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:none} }
  .log-icon { flex-shrink: 0; font-size: 14px; }
  .log-text { color: var(--ink2); line-height: 1.4; }
  .log-time { font-family: var(--font-mono); font-size: 9px; color: var(--ink3); margin-top: 2px; }
  .log-item.danger .log-text { color: var(--red); }
  .log-item.success .log-text { color: var(--green); }
  .log-item.warning .log-text { color: var(--amber); }

  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg2); border-radius: 10px; }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }

  /* ── FOOTER ── */
  .footer {
    text-align: center;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--ink3);
    letter-spacing: 0.1em;
    padding-top: 16px;
    border-top: 1.5px solid var(--border);
  }

  /* Belt structure label */
  .belt-structure {
    position: relative;
    height: 140px;
    margin: 0 0 8px;
  }

  /* Supports */
  .support {
    position: absolute;
    width: 8px;
    background: linear-gradient(180deg, #b0ae a6, #8a8880);
    border-radius: 2px;
    top: 90px;
    z-index: 1;
  }
  .support-l { left: 25px; height: 50px; }
  .support-r { right: 25px; height: 50px; }

  .support-foot {
    position: absolute;
    height: 6px;
    background: #888;
    border-radius: 3px;
    bottom: 0;
    z-index: 1;
  }
  .support-foot-l { left: 14px; width: 30px; }
  .support-foot-r { right: 14px; width: 30px; }
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div class="header-left">
    <div class="header-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2">
        <rect x="2" y="3" width="20" height="14" rx="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
      </svg>
    </div>
    <div>
      <h1>SCADA — Control Industrial</h1>
      <div class="sub">TK-01 / BANDA TRANSPORTADORA / SISTEMA AUTOMÁTICO</div>
    </div>
  </div>
  <div class="header-right">
    <div class="sys-badge activo" id="sys-badge">
      <span class="led led-green" id="sys-led"></span>
      <span id="sys-text">Sistema activo</span>
    </div>
    <div class="clock" id="clock">--:--:--</div>
  </div>
</div>

<!-- MAIN GRID: Tank | Right Panel -->
<div class="grid">

  <!-- ── TANK CARD ── -->
  <div class="card">
    <div class="card-head">
      <div class="card-label">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="3"/><path d="M4 12h16"/></svg>
        Tanque TK-01
      </div>
      <div class="status-pill pill-ok" id="nivel-badge">
        <span class="led led-green" style="width:6px;height:6px"></span>
        <span id="nivel-status">Normal</span>
      </div>
    </div>
    <div class="card-body">
      <div class="tank-body">
        <!-- Visual SVG tank -->
        <div style="position:relative;">
          <div class="tank-visual">
            <div class="tank-outer">
              <div class="tank-water" id="water-fill" style="height:50%"></div>
              <div class="tank-shine"></div>
            </div>
            <div class="tank-marks">
              <span>100%</span>
              <span>75%</span>
              <span>50%</span>
              <span>25%</span>
              <span>0%</span>
            </div>
          </div>
          <div class="tank-label">TK-01</div>
        </div>

        <!-- Metrics -->
        <div class="tank-metrics" style="margin-top:20px">
          <div class="big-number" id="nivel-val">50<span style="font-size:30px;font-family:var(--font-mono);font-weight:300">%</span></div>
          <div class="big-unit">Nivel actual del tanque</div>

          <div class="bar-wrap">
            <div class="bar-fill" id="nivel-bar" style="width:50%">50%</div>
          </div>

          <div class="meta-grid">
            <div class="meta-item">
              <div class="meta-key">Capacidad</div>
              <div class="meta-val">10,000 L</div>
            </div>
            <div class="meta-item">
              <div class="meta-key">Volumen actual</div>
              <div class="meta-val" id="vol-actual">5,000 L</div>
            </div>
            <div class="meta-item">
              <div class="meta-key">Estado</div>
              <div class="meta-val" id="estado-val" style="color:var(--green)">Llenando</div>
            </div>
            <div class="meta-item">
              <div class="meta-key">Comando</div>
              <div class="meta-val" id="cmd-actual">ACTIVO (1)</div>
            </div>
          </div>

          <div class="btn-row">
            <button class="btn btn-on" onclick="enviarComando('1')">▶ LLENAR</button>
            <button class="btn btn-off" onclick="enviarComando('0')">■ DETENER</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── RIGHT COLUMN ── -->
  <div>

    <!-- CONVEYOR CARD -->
    <div class="card conveyor-card">
      <div class="card-head">
        <div class="card-label">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><rect x="2" y="10" width="20" height="4" rx="2"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="12" r="3"/></svg>
          Banda Transportadora BT-01
        </div>
        <div class="status-pill pill-ok" id="belt-badge">
          <span class="led led-green" style="width:6px;height:6px" id="belt-led"></span>
          <span id="belt-status">Activa</span>
        </div>
      </div>
      <div class="card-body">
        <!-- Belt visualization -->
        <div class="belt-scene">

          <div class="belt-structure">
            <!-- Supports -->
            <div class="support support-l"></div>
            <div class="support support-r"></div>
            <div class="support-foot support-foot-l"></div>
            <div class="support-foot support-foot-r"></div>

            <!-- Pulleys -->
            <div class="pulley pulley-left spinning" id="pulley-l"></div>
            <div class="pulley pulley-right spinning" id="pulley-r"></div>

            <!-- Belt surface -->
            <div class="belt-rail belt-rail-top"></div>
            <div class="belt-surface running" id="belt-surface"></div>
            <div class="belt-rail belt-rail-bottom"></div>

            <!-- Packages -->
            <div class="packages-track">
              <div class="package p1 running" id="pkg1">📦</div>
              <div class="package p2 running" id="pkg2">📦</div>
              <div class="package p3 running" id="pkg3">📦</div>
            </div>
          </div>

          <!-- Belt info -->
          <div class="belt-info-row">
            <div class="sensor">
              <div class="sensor-dot active" id="sensor-a"></div>
              Sensor A — Entrada
            </div>
            <div class="sensor">
              <div class="sensor-dot active" id="sensor-b"></div>
              Sensor B — Centro
            </div>
            <div class="sensor">
              <div class="sensor-dot active" id="sensor-c"></div>
              Sensor C — Salida
            </div>
            <div class="belt-speed">Velocidad: <span id="belt-spd">1.2 m/s</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ALERTS GRID -->
    <div class="alerts-grid">
      <div class="card">
        <div class="card-head">
          <div class="card-label" style="font-size:15px">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke="currentColor"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            Alertas
          </div>
        </div>
        <div class="card-body" style="padding:14px 18px">
          <div class="log-list" id="alerts-list">
            <div class="log-item success">
              <span class="log-icon">✅</span>
              <div>
                <div class="log-text">Sistema inicializado correctamente</div>
                <div class="log-time">Ahora</div>
              </div>
            </div>
            <div class="log-item">
              <span class="log-icon">ℹ️</span>
              <div>
                <div class="log-text">Tanque en modo llenado activo</div>
                <div class="log-time">Ahora</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <div class="card-label" style="font-size:15px">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            Historial
          </div>
        </div>
        <div class="card-body" style="padding:14px 18px">
          <div class="log-list" id="history-list">
            <div class="log-item">
              <span class="log-icon">▶</span>
              <div>
                <div class="log-text">Cmd 1 — Sistema ACTIVADO</div>
                <div class="log-time">--:--:--</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div><!-- /right col -->
</div><!-- /grid -->

<div class="footer">
  SCADA v4.0 &nbsp;|&nbsp; TK-01 + BT-01 &nbsp;|&nbsp; Puerto: COM11 @ 115200 baud &nbsp;|&nbsp; 2025
</div>

<script>
let nivel = 50;
let sistemaActivo = true;

// ── Clock ──
function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-ES');
}
setInterval(updateClock, 1000);
updateClock();

// ── Belt control ──
function setBeltState(active) {
  const surface = document.getElementById('belt-surface');
  const pkgs = document.querySelectorAll('.package');
  const pulleys = document.querySelectorAll('.pulley');
  const sensorDots = document.querySelectorAll('.sensor-dot');
  const badge = document.getElementById('belt-badge');
  const beltLed = document.getElementById('belt-led');
  const beltStatus = document.getElementById('belt-status');
  const beltSpd = document.getElementById('belt-spd');

  if (active) {
    surface.classList.add('running');
    pkgs.forEach(p => p.classList.add('running'));
    pulleys.forEach(p => { p.classList.remove('spinning-slow'); p.classList.add('spinning'); });
    sensorDots.forEach(d => d.classList.add('active'));
    badge.className = 'status-pill pill-ok';
    beltLed.className = 'led led-green';
    beltLed.style.width = '6px'; beltLed.style.height = '6px';
    beltStatus.textContent = 'Activa';
    beltSpd.textContent = '1.2 m/s';
  } else {
    surface.classList.remove('running');
    pkgs.forEach(p => p.classList.remove('running'));
    pulleys.forEach(p => { p.classList.remove('spinning'); p.classList.add('spinning-slow'); });
    sensorDots.forEach(d => d.classList.remove('active'));
    badge.className = 'status-pill pill-warn';
    beltLed.className = 'led led-red';
    beltLed.style.width = '6px'; beltLed.style.height = '6px';
    beltStatus.textContent = 'Detenida';
    beltSpd.textContent = '0.0 m/s';
  }
}

// ── Send command ──
async function enviarComando(cmd) {
  const texto = cmd === '1' ? 'LLENAR (ACTIVAR)' : 'VACIAR (DETENER)';
  addLog('history-list', `Enviando cmd ${cmd}…`, 'info', '⏳');

  try {
    const res = await fetch('/comando', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comando: cmd })
    });
    const data = await res.json();

    if (data.status === 'ok') {
      sistemaActivo = (cmd === '1');
      updateSystemUI(cmd);
      setBeltState(sistemaActivo);
      addLog('alerts-list', `Comando ${texto} ejecutado`, 'success', '✅');
      addLog('history-list', `Cmd ${cmd} — ${texto.toUpperCase()}`, 'success', '▶');
    } else {
      addLog('alerts-list', `Error: ${data.message}`, 'danger', '❌');
      addLog('history-list', `Error: ${data.message}`, 'danger', '❌');
    }
  } catch (err) {
    addLog('alerts-list', `Error de conexión: ${err.message}`, 'danger', '❌');
    addLog('history-list', `Error: ${err.message}`, 'danger', '❌');
  }
}

function updateSystemUI(cmd) {
  const badge = document.getElementById('sys-badge');
  const led = document.getElementById('sys-led');
  const txt = document.getElementById('sys-text');
  const estadoVal = document.getElementById('estado-val');
  const cmdActual = document.getElementById('cmd-actual');

  if (cmd === '1') {
    badge.className = 'sys-badge activo';
    led.className = 'led led-green';
    txt.textContent = 'Sistema activo';
    estadoVal.textContent = 'Llenando';
    estadoVal.style.color = 'var(--green)';
    cmdActual.textContent = 'ACTIVO (1)';
  } else {
    badge.className = 'sys-badge parado';
    led.className = 'led led-red';
    txt.textContent = 'Sistema detenido';
    estadoVal.textContent = 'Detenido / Vaciando';
    estadoVal.style.color = 'var(--red)';
    cmdActual.textContent = 'DETENIDO (0)';
  }
}

// ── Tank simulation ──
function simularNivel() {
  if (sistemaActivo) {
    nivel = Math.min(100, nivel + 2 + Math.random() * 2);
    if (nivel >= 95) addLog('alerts-list', '⚠️ Nivel crítico — tanque casi lleno', 'warning', '⚠️');
    if (nivel >= 100) addLog('alerts-list', '🚨 MÁXIMO — tanque completamente lleno', 'danger', '❌');
  } else {
    nivel = Math.max(0, nivel - 1.5 - Math.random() * 1.5);
    if (nivel <= 10 && nivel > 0) addLog('alerts-list', '⚠️ Nivel bajo — tanque casi vacío', 'warning', '⚠️');
    if (nivel <= 0) addLog('alerts-list', '🚨 VACÍO — tanque completamente vacío', 'danger', '❌');
  }

  const n = Math.round(nivel);
  document.getElementById('nivel-val').innerHTML = `${n}<span style="font-size:30px;font-family:var(--font-mono);font-weight:300">%</span>`;
  document.getElementById('vol-actual').textContent = `${(n * 100).toLocaleString()} L`;

  // Bar
  const bar = document.getElementById('nivel-bar');
  bar.style.width = `${n}%`;
  bar.textContent = `${n}%`;
  bar.className = 'bar-fill' + (n >= 90 ? ' danger' : n >= 75 ? ' warning' : '');

  // Water visual
  document.getElementById('water-fill').style.height = `${n}%`;

  // Badge
  const badge = document.getElementById('nivel-badge');
  const status = document.getElementById('nivel-status');
  if (n >= 90) { badge.className = 'status-pill pill-danger'; status.textContent = 'Crítico'; }
  else if (n >= 75) { badge.className = 'status-pill pill-warn'; status.textContent = 'Alto'; }
  else if (n <= 15) { badge.className = 'status-pill pill-danger'; status.textContent = 'Bajo crítico'; }
  else if (n <= 30) { badge.className = 'status-pill pill-warn'; status.textContent = 'Bajo'; }
  else { badge.className = 'status-pill pill-ok'; status.textContent = 'Normal'; }
}

setInterval(simularNivel, 1000);

// ── Log helpers ──
function addLog(listId, message, type = 'info', icon = 'ℹ️') {
  const list = document.getElementById(listId);
  const item = document.createElement('div');
  item.className = `log-item ${type}`;
  const time = new Date().toLocaleTimeString('es-ES');
  item.innerHTML = `
    <span class="log-icon">${icon}</span>
    <div>
      <div class="log-text">${message}</div>
      <div class="log-time">${time}</div>
    </div>`;
  list.insertBefore(item, list.firstChild);
  while (list.children.length > 12) list.removeChild(list.lastChild);
}

// ── Init ──
setBeltState(true);
setTimeout(() => {
  addLog('alerts-list', 'SCADA listo — Tanque y banda activos', 'success', '✅');
}, 600);
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/comando', methods=['POST'])
def enviar_comando():
    global sistema_activo, nivel_tanque
    data = request.json
    comando = data.get('comando')

    if not ser:
        return jsonify({'status': 'error', 'message': 'Serial no conectado'})

    try:
        ser.write(comando.encode())
        ser.flush()
        print(f"📤 Comando enviado: {comando}")

        sistema_activo = (comando == '1')

        time.sleep(0.1)
        respuesta = ""
        if ser.in_waiting:
            respuesta = ser.read(ser.in_waiting).decode().strip()
            print(f"📥 Respuesta: {respuesta}")

        return jsonify({
            'status': 'ok',
            'comando': comando,
            'respuesta': respuesta,
            'sistema_activo': sistema_activo
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000')
    print("=" * 55)
    print("🏭 SCADA v4.0 — Tanque TK-01 + Banda BT-01")
    print("=" * 55)
    print(f"🔌 Puerto Serial: {SERIAL_PORT} @ {BAUD_RATE} baud")
    print("🌐 Servidor: http://127.0.0.1:5000")
    print("💡 Botón LLENAR → Activa tanque Y banda")
    print("💡 Botón DETENER → Para tanque Y banda")
    print("=" * 55)
    app.run(debug=False, host='0.0.0.0', port=5000)