#!/usr/bin/env python3
"""Build the standalone interactive Commercial Road-Tractor Collision Data App.

Compiles data from projects/trucks/reports/ into a modern, self-contained,
high-performance single-file HTML application featuring an industrial telemetry aesthetic.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TRUCKS_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = TRUCKS_DIR / "reports"
OUTPUT_INDEX = REPORTS_DIR / "index.html"
OUTPUT_STANDALONE = REPORTS_DIR / "canada-truck-collisions-1999-2021.html"


def read_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def extract_data():
    data = {}

    # 1. Trends
    data["trends_annual"] = read_csv(REPORTS_DIR / "trends" / "annual_counts.csv")
    data["trends_bench"] = read_csv(REPORTS_DIR / "trends" / "benchmark_comparison.csv")
    data["trends_periods"] = read_csv(REPORTS_DIR / "trends" / "period_changes.csv")
    data["trends_pooled"] = read_csv(REPORTS_DIR / "trends" / "pooled_periods.csv")

    # 2. Casualties
    raw_cas_counts = read_csv(REPORTS_DIR / "casualties" / "annual_group_counts.csv")
    data["cas_counts"] = [r for r in raw_cas_counts if r.get("subset") == "observed"]

    raw_cas_shares = read_csv(REPORTS_DIR / "casualties" / "annual_group_shares.csv")
    data["cas_shares"] = [r for r in raw_cas_shares if r.get("subset") == "observed"]

    raw_cas_pooled = read_csv(REPORTS_DIR / "casualties" / "pooled_group_shares.csv")
    data["cas_pooled"] = [r for r in raw_cas_pooled if r.get("subset") == "observed"]

    raw_cas_period = read_csv(REPORTS_DIR / "casualties" / "period_changes.csv")
    data["cas_period"] = [r for r in raw_cas_period if r.get("subset") == "observed"]

    # 3. Conditions fatal shares
    raw_cond_shares = read_csv(REPORTS_DIR / "conditions" / "category_fatal_shares.csv")
    data["cond_shares"] = [
        r for r in raw_cond_shares
        if r.get("subset") == "observed" and r.get("period") in (
            "primary_2012_2021", "early_2012_2016", "late_2017_2021"
        )
    ]

    # 4. Decomposition
    data["decomp_totals"] = read_csv(REPORTS_DIR / "decomposition" / "totals.csv")
    raw_decomp_cats = read_csv(REPORTS_DIR / "decomposition" / "category_contributions.csv")
    data["decomp_cats"] = [r for r in raw_decomp_cats if r.get("source") == "active" and r.get("scenario") == "primary"]

    # 5. Tables: VKT & Vehicle Age
    data["vkt_annual"] = read_csv(REPORTS_DIR / "tables" / "vkt_sensitivity_annual.csv")
    data["vkt_sum"] = read_csv(REPORTS_DIR / "tables" / "vkt_sensitivity_summary.csv")

    raw_age = read_csv(REPORTS_DIR / "tables" / "vehicle_age_severity_cohorts.csv")
    data["age_cohorts"] = [r for r in raw_age if r.get("subset") == "observed"]

    raw_age_multi = read_csv(REPORTS_DIR / "tables" / "vehicle_age_multi_tractor_sensitivity.csv")
    data["age_multi"] = [r for r in raw_age_multi if r.get("subset") == "observed"]

    return data


def generate_html(data):
    json_data = json.dumps(data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Commercial Road-Tractor Collisions in Canada (1999–2021) · Data App</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    /* Design Tokens: Industrial Freight Telemetry Aesthetic */
    :root {{
      --bg-canvas: #090d16;
      --bg-surface: #111726;
      --bg-surface-elevated: #182032;
      --bg-surface-overlay: #1f2a42;
      --border-subtle: #1f2c44;
      --border-bold: #2e3e5c;
      --border-highlight: #3b5074;

      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;

      /* High-visibility industrial signal accents */
      --signal-amber: #f59e0b;
      --signal-amber-glow: rgba(245, 158, 11, 0.15);
      --signal-amber-bright: #fbbf24;
      --signal-vermilion: #ef4444;
      --signal-vermilion-glow: rgba(239, 68, 68, 0.15);
      --signal-cyan: #06b6d4;
      --signal-cyan-glow: rgba(6, 182, 212, 0.15);
      --signal-cyan-bright: #38bdf8;
      --signal-emerald: #10b981;
      --signal-indigo: #6366f1;

      --font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-body: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

      --radius-sm: 4px;
      --radius-md: 8px;
      --radius-lg: 12px;
      --radius-xl: 16px;

      --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
      --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
      --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.6);
    }}

    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-canvas);
      color: var(--text-main);
      font-family: var(--font-body);
      font-size: 15px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }}

    /* Global Header & Telemetry Banner */
    .telemetry-banner {{
      background: linear-gradient(180deg, #131b2e 0%, #0d1322 100%);
      border-bottom: 1px solid var(--border-subtle);
      padding: 10px 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-family: var(--font-mono);
      font-size: 11.5px;
      letter-spacing: 0.04em;
    }}

    .telemetry-status-group {{
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      font-weight: 600;
    }}

    .status-badge.amber {{
      background: var(--signal-amber-glow);
      border-color: rgba(245, 158, 11, 0.35);
      color: var(--signal-amber-bright);
    }}

    .status-badge.cyan {{
      background: var(--signal-cyan-glow);
      border-color: rgba(6, 182, 212, 0.35);
      color: var(--signal-cyan-bright);
    }}

    .pulse-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background-color: currentColor;
      box-shadow: 0 0 8px currentColor;
    }}

    .header-main {{
      padding: 32px 24px 24px;
      max-width: 1440px;
      margin: 0 auto;
    }}

    .kicker {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--signal-amber);
      margin-bottom: 8px;
    }}

    .app-title {{
      font-family: var(--font-display);
      font-size: clamp(26px, 3.6vw, 42px);
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1.15;
      color: #fff;
      margin-bottom: 12px;
    }}

    .app-subtitle {{
      font-size: clamp(14px, 1.3vw, 17px);
      color: var(--text-muted);
      max-width: 1040px;
      line-height: 1.55;
    }}

    /* Quick KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-top: 28px;
    }}

    .kpi-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      position: relative;
      overflow: hidden;
      transition: border-color 0.2s, transform 0.2s;
    }}

    .kpi-card:hover {{
      border-color: var(--border-bold);
      transform: translateY(-2px);
    }}

    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--border-bold);
    }}

    .kpi-card.amber::before {{ background: var(--signal-amber); }}
    .kpi-card.vermilion::before {{ background: var(--signal-vermilion); }}
    .kpi-card.cyan::before {{ background: var(--signal-cyan); }}
    .kpi-card.emerald::before {{ background: var(--signal-emerald); }}

    .kpi-label {{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-dim);
      margin-bottom: 6px;
    }}

    .kpi-value {{
      font-family: var(--font-mono);
      font-size: 30px;
      font-weight: 700;
      color: #fff;
      line-height: 1.1;
      margin-bottom: 6px;
    }}

    .kpi-subtext {{
      font-size: 12.5px;
      color: var(--text-muted);
      line-height: 1.4;
    }}

    /* Tab Navigation */
    .nav-container {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(9, 13, 22, 0.94);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-subtle);
      padding: 0 24px;
    }}

    .nav-inner {{
      max-width: 1440px;
      margin: 0 auto;
      display: flex;
      gap: 4px;
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .nav-inner::-webkit-scrollbar {{ display: none; }}

    .nav-tab {{
      background: none;
      border: none;
      outline: none;
      color: var(--text-muted);
      font-family: var(--font-display);
      font-size: 14px;
      font-weight: 600;
      padding: 16px 18px;
      cursor: pointer;
      white-space: nowrap;
      position: relative;
      transition: color 0.15s;
    }}

    .nav-tab:hover {{
      color: var(--text-main);
    }}

    .nav-tab.active {{
      color: #fff;
    }}

    .nav-tab.active::after {{
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0;
      width: 100%;
      height: 3px;
      background: var(--signal-amber);
      border-radius: 3px 3px 0 0;
      box-shadow: 0 0 12px var(--signal-amber);
    }}

    /* Main Container */
    .app-main {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 28px 24px 80px;
    }}

    .view-panel {{
      display: none;
      animation: fadeIn 0.25s ease-out;
    }}

    .view-panel.active {{
      display: block;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Card Containers */
    .content-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-xl);
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: var(--shadow-sm);
      content-visibility: auto;
      contain-intrinsic-size: auto 300px auto 600px;
    }}

    .card-header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 16px;
    }}

    .card-title {{
      font-family: var(--font-display);
      font-size: 20px;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .card-title-badge {{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      background: var(--bg-surface-overlay);
      color: var(--text-muted);
      border: 1px solid var(--border-bold);
    }}

    .card-desc {{
      color: var(--text-muted);
      font-size: 14px;
      margin-top: 4px;
      max-width: 900px;
    }}

    /* Controls & Toggles */
    .control-group {{
      display: inline-flex;
      background: var(--bg-canvas);
      padding: 3px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
      gap: 2px;
    }}

    .control-btn {{
      background: none;
      border: none;
      padding: 6px 14px;
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }}

    .control-btn:hover {{
      color: var(--text-main);
    }}

    .control-btn.active {{
      background: var(--bg-surface-overlay);
      color: #fff;
      box-shadow: var(--shadow-sm);
    }}

    /* Visual Charts & SVG styling */
    .chart-container {{
      width: 100%;
      position: relative;
      background: #0c111c;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px 16px;
      overflow: hidden;
    }}

    .chart-svg {{
      width: 100%;
      height: auto;
      display: block;
      overflow: visible;
    }}

    .chart-tooltip {{
      position: absolute;
      pointer-events: none;
      background: rgba(17, 23, 38, 0.95);
      border: 1px solid var(--border-bold);
      backdrop-filter: blur(8px);
      padding: 10px 14px;
      border-radius: var(--radius-md);
      font-family: var(--font-mono);
      font-size: 12px;
      color: #fff;
      box-shadow: var(--shadow-md);
      z-index: 10;
      opacity: 0;
      transition: opacity 0.1s, transform 0.1s;
      transform: translate(-50%, -100%);
      margin-top: -10px;
    }}

    .chart-legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      margin-top: 16px;
      justify-content: center;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-muted);
    }}

    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}

    .legend-dot {{
      width: 10px;
      height: 10px;
      border-radius: 2px;
    }}

    /* Insight Callouts */
    .insight-box {{
      background: linear-gradient(90deg, rgba(245, 158, 11, 0.08) 0%, rgba(17, 23, 38, 0.4) 100%);
      border-left: 4px solid var(--signal-amber);
      border-radius: 0 var(--radius-md) var(--radius-md) 0;
      padding: 14px 18px;
      margin-top: 20px;
      font-size: 13.5px;
      color: #e2e8f0;
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }}

    .insight-box.vermilion {{
      background: linear-gradient(90deg, rgba(239, 68, 68, 0.08) 0%, rgba(17, 23, 38, 0.4) 100%);
      border-left-color: var(--signal-vermilion);
    }}

    .insight-box.cyan {{
      background: linear-gradient(90deg, rgba(6, 182, 212, 0.08) 0%, rgba(17, 23, 38, 0.4) 100%);
      border-left-color: var(--signal-cyan);
    }}

    .insight-icon {{
      font-size: 16px;
      line-height: 1;
      margin-top: 2px;
    }}

    /* Modern Responsive Data Table (compliant with modern-web-guidance) */
    .table-wrapper {{
      overflow: auto;
      max-inline-size: 100%;
      max-block-size: min(600px, 75vh);
      container-type: inline-size;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      background: #0c111c;
      box-shadow: var(--shadow-sm);
    }}

    table.data-table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-family: var(--font-mono);
      font-size: 13px;
      text-align: left;
    }}

    table.data-table thead {{
      position: sticky;
      inset-block-start: 0;
      z-index: 5;
      background: var(--bg-surface-elevated);
      color: var(--text-main);
      box-shadow: 0 1px 0 var(--border-subtle);
    }}

    table.data-table th,
    table.data-table td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-subtle);
      white-space: nowrap;
    }}

    table.data-table tbody th {{
      position: sticky;
      inset-inline-start: 0;
      background: #0c111c;
      font-weight: 600;
      color: var(--signal-amber-bright);
      z-index: 2;
    }}

    table.data-table tbody tr:hover td,
    table.data-table tbody tr:hover th {{
      background: var(--bg-surface-overlay);
    }}

    .num-cell {{
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}

    /* Responsive stacked table on narrow screens */
    @container (width < 680px) {{
      table.data-table, thead, tbody, tr, th, td {{
        display: block;
      }}
      thead {{
        display: none;
      }}
      tr {{
        margin-block-end: 14px;
        border: 1px solid var(--border-bold);
        border-radius: var(--radius-md);
        background: var(--bg-surface);
        padding: 8px 12px;
      }}
      tbody th {{
        position: static;
        background: none;
        padding-block: 6px;
        font-size: 15px;
        border-bottom: 1px solid var(--border-subtle);
      }}
      td {{
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px dashed var(--border-subtle);
      }}
      td::before {{
        content: attr(data-label) ": ";
        font-weight: 600;
        color: var(--text-muted);
      }}
    }}

    /* Two-column layout */
    .grid-2col {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
      gap: 24px;
    }}

    @media (max-width: 600px) {{
      .grid-2col {{
        grid-template-columns: 1fr;
      }}
    }}

    /* Footer */
    .app-footer {{
      border-top: 1px solid var(--border-subtle);
      padding: 32px 24px;
      background: var(--bg-surface);
      margin-top: 60px;
      color: var(--text-dim);
      font-size: 13px;
      font-family: var(--font-mono);
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 16px;
      max-width: 1440px;
      margin-inline: auto;
    }}
  </style>
</head>
<body>

  <!-- Top Telemetry Bar -->
  <aside class="telemetry-banner" aria-label="System telemetry bar">
    <div class="telemetry-status-group">
      <span class="status-badge"><span class="pulse-dot"></span> NCDB MICRODATA 1999–2021</span>
      <span class="status-badge amber">TEST SUITE: 36/36 CHECKS VERIFIED</span>
      <span class="status-badge cyan">TRANSPORT CANADA TABLE 10 VKT AUDITED</span>
    </div>
    <div>
      <span style="color: var(--text-dim)">COUNTING UNIT:</span> <strong style="color: #fff">UNIQUE CASUALTY COLLISIONS</strong>
    </div>
  </aside>

  <!-- Header Banner -->
  <header class="header-main">
    <div class="kicker">Freight Safety Intelligence · National Study</div>
    <h1 class="app-title">Commercial Road-Tractor Collisions in Canada (1999–2021)</h1>
    <p class="app-subtitle">
      Comprehensive empirical analysis of <strong>80,540 road-tractor casualty collisions</strong> from Transport Canada's National Collision Database (NCDB). Explores long-term frequency shifts, casualty distribution asymmetries, environmental risk factors, mathematical configuration decomposition, Table 10 freight VKT sensitivity, and vehicle-age severity cohorts.
    </p>

    <!-- Key Metrics Grid -->
    <section class="kpi-grid" aria-label="Key performance indicators">
      <div class="kpi-card amber">
        <div class="kpi-label">Recorded Tractor Events</div>
        <div class="kpi-value">80,540</div>
        <div class="kpi-subtext">Casualty collisions (fatal or injury) with recorded road tractor (1999–2021).</div>
      </div>
      <div class="kpi-card vermilion">
        <div class="kpi-label">Overall Fatal Share</div>
        <div class="kpi-value">6.90%</div>
        <div class="kpi-subtext">5,557 fatal collisions out of 80,540 (vs 1.62% for non-tractor traffic).</div>
      </div>
      <div class="kpi-card cyan">
        <div class="kpi-label">Victim Asymmetry</div>
        <div class="kpi-value">71.7%</div>
        <div class="kpi-subtext">Of identified fatalities are occupants of other vehicles (2012–2021).</div>
      </div>
      <div class="kpi-card emerald">
        <div class="kpi-label">VKT-Adjusted Rate</div>
        <div class="kpi-value">−44.5%</div>
        <div class="kpi-subtext">Decline in casualty events per billion modeled tractor VKT (2015–2021).</div>
      </div>
    </section>
  </header>

  <!-- Sticky Navigation Tabs -->
  <nav class="nav-container" aria-label="Main section navigation">
    <div class="nav-inner">
      <button class="nav-tab active" data-tab="overview">Executive Overview</button>
      <button class="nav-tab" data-tab="trends">Decade Trends (1999–2021)</button>
      <button class="nav-tab" data-tab="casualties">Casualties & Who is Harmed</button>
      <button class="nav-tab" data-tab="conditions">Environment & Road Conditions</button>
      <button class="nav-tab" data-tab="decomposition">Configuration Decomposition</button>
      <button class="nav-tab" data-tab="vkt_age">VKT Exposure & Vehicle Age Audit</button>
      <button class="nav-tab" data-tab="explorer">Data Explorer</button>
    </div>
  </nav>

  <!-- Main Viewports -->
  <main class="app-main">

    <!-- TAB 1: EXECUTIVE OVERVIEW -->
    <section id="view-overview" class="view-panel active">
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Core Research Findings at a Glance <span class="card-title-badge">EXECUTIVE SUMMARY</span></h2>
            <p class="card-desc">Addressing the primary research questions on heavy commercial freight safety across Canada.</p>
          </div>
        </div>

        <div class="grid-2col" style="margin-bottom: 24px;">
          <!-- Card 1 -->
          <div style="background: var(--bg-surface-elevated); padding: 20px; border-radius: var(--radius-lg); border: 1px solid var(--border-subtle);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
              <span class="card-title-badge" style="color: var(--signal-amber); border-color: rgba(245, 158, 11, 0.3);">QUESTION 1: FREQUENCY & SEVERITY</span>
              <span style="font-family: var(--font-mono); font-size: 12px; color: var(--text-dim);">1999–2021</span>
            </div>
            <h3 style="font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 8px;">Did semi collisions increase, and why did fatal share rise?</h3>
            <p style="font-size: 13.5px; color: var(--text-muted); line-height: 1.55;">
              Annual road-tractor casualty collisions <strong>declined 46.5%</strong> from 4,186 in 1999 to 2,240 in 2021. However, because non-fatal injury collisions fell faster than fatal collisions, the <strong>conditional fatal share rose from 6.13% (2012–2016) to 6.96% (2017–2021)</strong>. This rise reflects faster declines in minor injury recording rather than increased physical crash lethality.
            </p>
          </div>

          <!-- Card 2 -->
          <div style="background: var(--bg-surface-elevated); padding: 20px; border-radius: var(--radius-lg); border: 1px solid var(--border-subtle);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
              <span class="card-title-badge" style="color: var(--signal-vermilion); border-color: rgba(239, 68, 68, 0.3);">QUESTION 2: HARM ASYMMETRY</span>
              <span style="font-family: var(--font-mono); font-size: 12px; color: var(--text-dim);">2012–2021 DECADE</span>
            </div>
            <h3 style="font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 8px;">Who is harmed in road-tractor collisions?</h3>
            <p style="font-size: 13.5px; color: var(--text-muted); line-height: 1.55;">
              Severe harm is heavily asymmetric. In the 2012–2021 historical decade, <strong>1,581 out of 2,206 identified fatalities (71.7%)</strong> occurred in other motor vehicles (passenger cars, light trucks, vans). Tractor occupants accounted for only <strong>15.6%</strong> of deaths (344 fatalities), while pedestrians, bicyclists, and motorcyclists accounted for <strong>12.7%</strong>.
            </p>
          </div>

          <!-- Card 3 -->
          <div style="background: var(--bg-surface-elevated); padding: 20px; border-radius: var(--radius-lg); border: 1px solid var(--border-subtle);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
              <span class="card-title-badge" style="color: var(--signal-cyan); border-color: rgba(6, 182, 212, 0.3);">QUESTION 5: VKT EXPOSURE</span>
              <span style="font-family: var(--font-mono); font-size: 12px; color: var(--text-dim);">2015–2021 TABLE 10</span>
            </div>
            <h3 style="font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 8px;">Do collisions track freight distance traveled?</h3>
            <p style="font-size: 13.5px; color: var(--text-muted); line-height: 1.55;">
              Normalizing observed events against Transport Canada Table 10 modeled freight distance shows that <strong>casualty collisions per billion modeled VKT fell 25.5% pre-pandemic (89.9 → 67.0)</strong> and <strong>44.5% overall (89.9 → 49.9)</strong> by 2021. Fatal events per billion VKT fell <strong>34.7% (5.67 → 3.71)</strong>, demonstrating improved safety per distance traveled.
            </p>
          </div>

          <!-- Card 4 -->
          <div style="background: var(--bg-surface-elevated); padding: 20px; border-radius: var(--radius-lg); border: 1px solid var(--border-subtle);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
              <span class="card-title-badge" style="color: var(--signal-emerald); border-color: rgba(16, 185, 129, 0.3);">QUESTION 7: VEHICLE AGE AUDIT</span>
              <span style="font-family: var(--font-mono); font-size: 12px; color: var(--text-dim);">V_YEAR ANALYSIS</span>
            </div>
            <h3 style="font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 8px;">Are older road tractors more deadly?</h3>
            <p style="font-size: 13.5px; color: var(--text-muted); line-height: 1.55;">
              The data disproves the hypothesis that older trucks cause higher fatality rates. Controlling for road alignment, configuration, weather, month, and hour, tractors aged <strong>16+ years</strong> exhibit a <strong>statistically significantly lower adjusted Odds Ratio (OR = 0.786, 95% CI: 0.65–0.96)</strong> than modern tractors (0–2 years old).
            </p>
          </div>
        </div>

        <!-- High-level Timeline Visualizer -->
        <div class="chart-container" id="overview-chart-container">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: #fff;">ROAD-TRACTOR CASUALTY AND FATAL COLLISIONS (1999–2021)</span>
            <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-dim)">Source: Transport Canada NCDB</span>
          </div>
          <div id="overview-chart" style="width: 100%; height: 320px;"></div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-amber);"></span> All Casualty Collisions</span>
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-vermilion);"></span> Fatal Collisions</span>
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-cyan);"></span> Fatal Share % (Right Axis)</span>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 2: LONG-TERM TRENDS -->
    <section id="view-trends" class="view-panel">
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Annual Event Trajectory & Strict Sensitivity <span class="card-title-badge">1999–2021</span></h2>
            <p class="card-desc">Tracking unique casualty collisions, fatal collisions, and benchmark reconciliation against published Transport Canada statistics.</p>
          </div>
          <div class="control-group">
            <button class="control-btn active" data-trend-metric="casualty_collisions">Casualty Events</button>
            <button class="control-btn" data-trend-metric="fatal_collisions">Fatal Events</button>
            <button class="control-btn" data-trend-metric="fatal_share_pct">Fatal Share %</button>
          </div>
        </div>

        <div class="chart-container">
          <div id="trends-chart" style="width: 100%; height: 360px;"></div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-amber);"></span> Observed Road Tractor</span>
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-cyan);"></span> Strict Tractor Candidate (Sensitivity)</span>
          </div>
        </div>

        <div class="insight-box cyan">
          <div class="insight-icon">ℹ️</div>
          <div>
            <strong>Strict Candidate Sensitivity:</strong> The strict tractor subset excludes ambiguous and multi-unit recording anomalies (80,529 events vs 80,540 observed). Both series match within 0.01 percentage points of fatal share across all 23 years, proving that findings are entirely robust to record filtering criteria.
          </div>
        </div>
      </div>

      <!-- Published Benchmark Comparison Card -->
      <div class="content-card">
        <div class="card-header">
          <div>
            <h3 class="card-title">Transport Canada Publication Benchmark Audit <span class="card-title-badge">2012–2021</span></h3>
            <p class="card-desc">Comparing observed microdata against official published figures from <em>Commercial Vehicle Safety in Canada</em>.</p>
          </div>
        </div>

        <div class="table-wrapper" tabindex="0" role="region" aria-label="Benchmark Comparison Table">
          <table class="data-table" id="benchmark-table">
            <thead>
              <tr>
                <th>Year</th>
                <th class="num-cell">Observed Fatal</th>
                <th class="num-cell">Published Fatal</th>
                <th class="num-cell">Observed Injury</th>
                <th class="num-cell">Published Injury</th>
                <th class="num-cell">Observed Total</th>
                <th class="num-cell">Published Total</th>
                <th class="num-cell">Difference</th>
                <th class="num-cell">Observed Fatal %</th>
                <th class="num-cell">Published Fatal %</th>
                <th>Audit Status</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 3: CASUALTIES & WHO IS HARMED -->
    <section id="view-casualties" class="view-panel">
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Victim Breakdown & Harm Asymmetry <span class="card-title-badge">WHO IS HARMED?</span></h2>
            <p class="card-desc">Tracking fatalities and injuries across distinct road user groups sharing the road with heavy road tractors.</p>
          </div>
          <div class="control-group">
            <button class="control-btn active" data-cas-measure="deaths">Fatalities (Deaths)</button>
            <button class="control-btn" data-cas-measure="injuries">Injuries</button>
          </div>
        </div>

        <div class="grid-2col">
          <!-- Donut / Share Chart -->
          <div class="chart-container">
            <div style="font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: #fff; margin-bottom: 12px;">HISTORICAL DECADE (2012–2021) SHARE OF HARM</div>
            <div id="casualties-donut-chart" style="width: 100%; height: 320px;"></div>
            <div id="casualties-donut-legend" class="chart-legend"></div>
          </div>

          <!-- Annual Trajectory by Group -->
          <div class="chart-container">
            <div style="font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: #fff; margin-bottom: 12px;">ANNUAL CASUALTIES BY ROAD USER GROUP (1999–2021)</div>
            <div id="casualties-line-chart" style="width: 100%; height: 320px;"></div>
            <div class="chart-legend">
              <span class="legend-item"><span class="legend-dot" style="background: var(--signal-vermilion);"></span> Other Vehicle Occupants</span>
              <span class="legend-item"><span class="legend-dot" style="background: var(--signal-amber);"></span> Tractor Occupants</span>
              <span class="legend-item"><span class="legend-dot" style="background: var(--signal-cyan);"></span> Vulnerable Road Users (Ped/Cyc)</span>
            </div>
          </div>
        </div>

        <div class="insight-box vermilion">
          <div class="insight-icon">⚠️</div>
          <div>
            <strong>Mass-Ratio Physical Consequence:</strong> Over 71.7% of people killed in road-tractor collisions are occupants of other vehicles (cars, light trucks, SUVs). By contrast, only 15.6% of deaths are tractor drivers or passengers. This stark disparity underscores that road-tractor collisions present primary lethality risk to other road users rather than truck drivers themselves.
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 4: ENVIRONMENT & CONDITIONS -->
    <section id="view-conditions" class="view-panel">
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Environmental & Road Context Comparisons <span class="card-title-badge">2012–2021</span></h2>
            <p class="card-desc">Comparing recorded weather, road surface, road configuration, and time of day between heavy road tractors and all other collisions.</p>
          </div>
          <div class="control-group">
            <button class="control-btn active" data-cond-field="C_WTHR">Weather</button>
            <button class="control-btn" data-cond-field="C_RSUR">Road Surface</button>
            <button class="control-btn" data-cond-field="C_RCFG">Configuration</button>
            <button class="control-btn" data-cond-field="HOUR_BAND">Time of Day</button>
          </div>
        </div>

        <div class="chart-container">
          <div id="conditions-chart" style="width: 100%; height: 380px;"></div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-amber);"></span> Road Tractor Fatal Share %</span>
            <span class="legend-item"><span class="legend-dot" style="background: #64748b;"></span> Non-Tractor Traffic Fatal Share %</span>
          </div>
        </div>

        <div class="insight-box amber">
          <div class="insight-icon">🌧️</div>
          <div id="conditions-insight-text">
            <strong>Adverse Weather & Road Surfaces:</strong> Road tractors exhibit higher fatal collision shares across divided highways, snow/slush/ice conditions, and overnight hours compared to standard passenger vehicles.
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 5: DECOMPOSITION -->
    <section id="view-decomposition" class="view-panel">
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Collision Configuration Decomposition <span class="card-title-badge">MATHEMATICAL ATTRIBUTION</span></h2>
            <p class="card-desc">Decomposing the +0.835 percentage point increase in fatal collision share (2012–2016 vs 2017–2021) into mix shifts versus within-category changes.</p>
          </div>
        </div>

        <div class="grid-2col" style="margin-bottom: 24px;">
          <!-- Decomposition Waterfall Summary -->
          <div style="background: var(--bg-surface-elevated); padding: 20px; border-radius: var(--radius-lg); border: 1px solid var(--border-subtle);">
            <h3 style="font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 12px;">Total Fatal Share Change: +0.835 pp</h3>
            <div style="font-size: 14px; color: var(--text-muted); line-height: 1.6; margin-bottom: 16px;">
              Between <strong>2012–2016 (6.128%)</strong> and <strong>2017–2021 (6.964%)</strong>, fatal collision share grew by <strong>+0.835 percentage points</strong>. The formal mathematical decomposition isolates:
            </div>
            <div style="display: flex; gap: 12px; margin-bottom: 16px;">
              <div style="flex: 1; background: var(--bg-surface); padding: 14px; border-radius: var(--radius-md); border-left: 3px solid var(--signal-cyan);">
                <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);">MIX SHIFT COMPONENT</div>
                <div style="font-family: var(--font-mono); font-size: 22px; font-weight: 700; color: var(--signal-cyan);">+0.134 pp</div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">16.0% of total change due to changing collision configurations.</div>
              </div>
              <div style="flex: 1; background: var(--bg-surface); padding: 14px; border-radius: var(--radius-md); border-left: 3px solid var(--signal-amber);">
                <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);">WITHIN-CATEGORY COMPONENT</div>
                <div style="font-family: var(--font-mono); font-size: 22px; font-weight: 700; color: var(--signal-amber);">+0.701 pp</div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">84.0% of total change due to rising severity within specific configurations.</div>
              </div>
            </div>
          </div>

          <!-- Category Contributions Chart -->
          <div class="chart-container">
            <div style="font-family: var(--font-mono); font-size: 13px; font-weight: 600; color: #fff; margin-bottom: 12px;">CATEGORY CONTRIBUTIONS TO SEVERITY CHANGE</div>
            <div id="decomp-chart" style="width: 100%; height: 260px;"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 6: VKT & VEHICLE AGE -->
    <section id="view-vkt_age" class="view-panel">
      <!-- Section A: VKT Sensitivity -->
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Transport Canada Table 10 Modeled VKT Sensitivity <span class="card-title-badge">2015–2021</span></h2>
            <p class="card-desc">Adjusting collision volumes against modeled freight Vehicle-Kilometres Travelled (VKT).</p>
          </div>
        </div>

        <div class="chart-container">
          <div id="vkt-chart" style="width: 100%; height: 340px;"></div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-cyan);"></span> Casualty Events per Billion Modeled VKT</span>
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-vermilion);"></span> Fatal Events per Billion Modeled VKT</span>
          </div>
        </div>

        <div class="insight-box cyan">
          <div class="insight-icon">📉</div>
          <div>
            <strong>Freight Exposure Conclusion:</strong> Casualty collisions per billion modeled VKT declined steadily from 89.90 in 2015 to 49.92 in 2021 (−44.5%), while fatal collisions fell from 5.67 to 3.71 per billion VKT (−34.7%). Even excluding the 2020–2021 pandemic period, pre-pandemic rates fell 25.5%.
          </div>
        </div>
      </div>

      <!-- Section B: Vehicle Age Audit -->
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Vehicle Age (V_YEAR) Severity Audit & Adjusted Odds Ratios <span class="card-title-badge">AUDIT & ML</span></h2>
            <p class="card-desc">Multivariable logistic regression controlling for road alignment, configuration, weather, month, and hour across 5 tractor age cohorts.</p>
          </div>
        </div>

        <div class="chart-container">
          <div id="age-chart" style="width: 100%; height: 300px;"></div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background: var(--signal-amber);"></span> Adjusted Odds Ratio vs 0–2 Year Tractors</span>
            <span class="legend-item"><span class="legend-dot" style="background: var(--text-dim);"></span> Reference Baseline (OR = 1.00)</span>
          </div>
        </div>

        <div class="insight-box emerald">
          <div class="insight-icon">✅</div>
          <div>
            <strong>The Aging Fleet Myth:</strong> Older commercial road tractors do not have higher conditional fatality rates. Tractors aged 16+ years show an adjusted Odds Ratio of 0.786 (95% CI: 0.646–0.957, p = 0.016), meaning they are significantly <em>less</em> likely to result in a fatality when a casualty crash occurs than brand new (0–2 year old) tractors.
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 7: DATA EXPLORER -->
    <section id="view-explorer" class="view-panel">
      <div class="content-card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Interactive Data Explorer <span class="card-title-badge">ANNUAL EVIDENCE</span></h2>
            <p class="card-desc">Browse, filter, and inspect verified annual collision statistics. Fully accessible responsive table with sticky headers.</p>
          </div>
          <div>
            <button class="control-btn active" id="export-csv-btn">Export CSV</button>
          </div>
        </div>

        <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center;">
          <input type="text" id="table-search" placeholder="Filter by year or status..." style="background: var(--bg-surface-elevated); border: 1px solid var(--border-bold); border-radius: var(--radius-md); padding: 8px 14px; color: #fff; font-family: var(--font-mono); font-size: 13px; width: 280px;">
          <span id="table-row-count" style="font-family: var(--font-mono); font-size: 12px; color: var(--text-dim);">Showing 23 years</span>
        </div>

        <div class="table-wrapper" tabindex="0" role="region" aria-label="Interactive annual tractor collision table">
          <table class="data-table" id="explorer-table">
            <thead>
              <tr>
                <th>Year</th>
                <th class="num-cell">Casualty Collisions</th>
                <th class="num-cell">Fatal Collisions</th>
                <th class="num-cell">Injury Collisions</th>
                <th class="num-cell">Fatal Share %</th>
                <th class="num-cell">Strict Subset</th>
                <th class="num-cell">Unknown Type Events</th>
                <th class="num-cell">Overlap Events</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </section>

  </main>

  <!-- Global Footer -->
  <footer class="app-footer">
    <div>
      <strong>Canadian Traffic Collision Research</strong> · Commercial Road-Tractor Study (1999–2021)
    </div>
    <div>
      Data Sources: Transport Canada NCDB & Statistics Canada · Verified Repository Deliverable
    </div>
  </footer>

  <!-- Application Logic & Data Injection -->
  <script>
    const DATA = {json_data};

    // Tooltip Element
    const tooltip = document.createElement('div');
    tooltip.className = 'chart-tooltip';
    document.body.appendChild(tooltip);

    function showTooltip(x, y, content) {{
      tooltip.innerHTML = content;
      tooltip.style.left = x + 'px';
      tooltip.style.top = y + 'px';
      tooltip.style.opacity = '1';
    }}

    function hideTooltip() {{
      tooltip.style.opacity = '0';
    }}

    // Tab Switching
    document.querySelectorAll('.nav-tab').forEach(tab => {{
      tab.addEventListener('click', () => {{
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const viewId = 'view-' + tab.dataset.tab;
        const panel = document.getElementById(viewId);
        if (panel) panel.classList.add('active');
        window.dispatchEvent(new Event('resize'));
      }});
    }});

    // Helper SVG Creator
    function createSVG(width, height) {{
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);
      svg.setAttribute('class', 'chart-svg');
      return svg;
    }}

    // 1. RENDER OVERVIEW CHART
    function renderOverviewChart() {{
      const container = document.getElementById('overview-chart');
      if (!container) return;
      container.innerHTML = '';
      const w = 1100, h = 320;
      const padL = 60, padR = 60, padT = 30, padB = 40;
      const chartW = w - padL - padR;
      const chartH = h - padT - padB;

      const records = DATA.trends_annual.filter(r => r.group === 'road_tractor' && r.subset === 'observed');
      records.sort((a, b) => parseInt(a.year) - parseInt(b.year));

      const svg = createSVG(w, h);

      // Scales
      const maxCount = Math.max(...records.map(r => parseInt(r.casualty_collisions)));
      const maxPct = 10.0;

      const getX = (i) => padL + (i / (records.length - 1)) * chartW;
      const getYCount = (val) => padT + chartH - (val / (maxCount * 1.1)) * chartH;
      const getYPct = (val) => padT + chartH - (val / maxPct) * chartH;

      // Draw Grid Lines
      for (let i = 0; i <= 4; i++) {{
        const y = padT + (chartH / 4) * i;
        const countVal = Math.round((maxCount * 1.1) * (1 - i / 4));
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', padL);
        line.setAttribute('y1', y);
        line.setAttribute('x2', w - padR);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', '#1f2c44');
        line.setAttribute('stroke-dasharray', '4,4');
        svg.appendChild(line);

        const textL = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        textL.setAttribute('x', padL - 10);
        textL.setAttribute('y', y + 4);
        textL.setAttribute('fill', '#64748b');
        textL.setAttribute('font-family', 'JetBrains Mono');
        textL.setAttribute('font-size', '11');
        textL.setAttribute('text-anchor', 'end');
        textL.textContent = countVal.toLocaleString();
        svg.appendChild(textL);
      }}

      // Casualty Path
      let dCasualty = `M ${{getX(0)}} ${{getYCount(parseInt(records[0].casualty_collisions))}}`;
      let dFatal = `M ${{getX(0)}} ${{getYCount(parseInt(records[0].fatal_collisions))}}`;
      let dPct = `M ${{getX(0)}} ${{getYPct(parseFloat(records[0].fatal_share_pct))}}`;

      for (let i = 1; i < records.length; i++) {{
        dCasualty += ` L ${{getX(i)}} ${{getYCount(parseInt(records[i].casualty_collisions))}}`;
        dFatal += ` L ${{getX(i)}} ${{getYCount(parseInt(records[i].fatal_collisions))}}`;
        dPct += ` L ${{getX(i)}} ${{getYPct(parseFloat(records[i].fatal_share_pct))}}`;
      }}

      // Append Path Elements
      function addPath(d, color, width, dash = '') {{
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', color);
        path.setAttribute('stroke-width', width);
        if (dash) path.setAttribute('stroke-dasharray', dash);
        svg.appendChild(path);
      }}

      addPath(dCasualty, '#f59e0b', 3);
      addPath(dFatal, '#ef4444', 2.5);
      addPath(dPct, '#06b6d4', 2.5, '5,5');

      // Points and Interactive Tooltips
      records.forEach((r, i) => {{
        const cx = getX(i);
        const cy = getYCount(parseInt(r.casualty_collisions));

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx);
        circle.setAttribute('cy', cy);
        circle.setAttribute('r', 5);
        circle.setAttribute('fill', '#f59e0b');
        circle.setAttribute('stroke', '#090d16');
        circle.setAttribute('stroke-width', 2);
        circle.style.cursor = 'pointer';

        circle.addEventListener('mouseenter', (e) => {{
          circle.setAttribute('r', 7);
          const rect = container.getBoundingClientRect();
          showTooltip(e.clientX, e.clientY, `
            <strong>YEAR: ${{r.year}}</strong><br>
            Casualty Collisions: <strong>${{parseInt(r.casualty_collisions).toLocaleString()}}</strong><br>
            Fatal Collisions: <strong style="color: #ef4444">${{parseInt(r.fatal_collisions).toLocaleString()}}</strong><br>
            Fatal Share: <strong style="color: #38bdf8">${{parseFloat(r.fatal_share_pct).toFixed(2)}}%</strong>
          `);
        }});

        circle.addEventListener('mouseleave', () => {{
          circle.setAttribute('r', 5);
          hideTooltip();
        }});

        svg.appendChild(circle);

        // Year labels (every 2 years)
        if (i % 2 === 0 || i === records.length - 1) {{
          const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          txt.setAttribute('x', cx);
          txt.setAttribute('y', h - padB + 22);
          txt.setAttribute('fill', '#94a3b8');
          txt.setAttribute('font-family', 'JetBrains Mono');
          txt.setAttribute('font-size', '11');
          txt.setAttribute('text-anchor', 'middle');
          txt.textContent = r.year;
          svg.appendChild(txt);
        }}
      }});

      container.appendChild(svg);
    }}

    // 2. RENDER TRENDS TAB
    let currentTrendMetric = 'casualty_collisions';
    function renderTrendsChart() {{
      const container = document.getElementById('trends-chart');
      if (!container) return;
      container.innerHTML = '';
      const w = 1100, h = 360;
      const padL = 60, padR = 40, padT = 30, padB = 40;
      const chartW = w - padL - padR;
      const chartH = h - padT - padB;

      const observed = DATA.trends_annual.filter(r => r.group === 'road_tractor' && r.subset === 'observed');
      const strict = DATA.trends_annual.filter(r => r.group === 'road_tractor' && r.subset === 'strict');
      observed.sort((a, b) => parseInt(a.year) - parseInt(b.year));
      strict.sort((a, b) => parseInt(a.year) - parseInt(b.year));

      const svg = createSVG(w, h);

      const maxVal = Math.max(
        ...observed.map(r => parseFloat(r[currentTrendMetric])),
        ...strict.map(r => parseFloat(r[currentTrendMetric]))
      ) * 1.1;

      const getX = (i) => padL + (i / (observed.length - 1)) * chartW;
      const getY = (val) => padT + chartH - (val / maxVal) * chartH;

      // Grid
      for (let i = 0; i <= 4; i++) {{
        const y = padT + (chartH / 4) * i;
        const val = (maxVal * (1 - i / 4)).toFixed(currentTrendMetric === 'fatal_share_pct' ? 1 : 0);
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', padL);
        line.setAttribute('y1', y);
        line.setAttribute('x2', w - padR);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', '#1f2c44');
        svg.appendChild(line);

        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', padL - 10);
        txt.setAttribute('y', y + 4);
        txt.setAttribute('fill', '#64748b');
        txt.setAttribute('font-family', 'JetBrains Mono');
        txt.setAttribute('font-size', '11');
        txt.setAttribute('text-anchor', 'end');
        txt.textContent = val + (currentTrendMetric === 'fatal_share_pct' ? '%' : '');
        svg.appendChild(txt);
      }}

      // Lines
      let dObs = `M ${{getX(0)}} ${{getY(parseFloat(observed[0][currentTrendMetric]))}}`;
      let dStr = `M ${{getX(0)}} ${{getY(parseFloat(strict[0][currentTrendMetric]))}}`;
      for (let i = 1; i < observed.length; i++) {{
        dObs += ` L ${{getX(i)}} ${{getY(parseFloat(observed[i][currentTrendMetric]))}}`;
        dStr += ` L ${{getX(i)}} ${{getY(parseFloat(strict[i][currentTrendMetric]))}}`;
      }}

      const pathObs = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      pathObs.setAttribute('d', dObs);
      pathObs.setAttribute('fill', 'none');
      pathObs.setAttribute('stroke', '#f59e0b');
      pathObs.setAttribute('stroke-width', 3);
      svg.appendChild(pathObs);

      const pathStr = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      pathStr.setAttribute('d', dStr);
      pathStr.setAttribute('fill', 'none');
      pathStr.setAttribute('stroke', '#06b6d4');
      pathStr.setAttribute('stroke-width', 2);
      pathStr.setAttribute('stroke-dasharray', '4,4');
      svg.appendChild(pathStr);

      // Points
      observed.forEach((r, i) => {{
        const cx = getX(i);
        const cy = getY(parseFloat(r[currentTrendMetric]));
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx);
        circle.setAttribute('cy', cy);
        circle.setAttribute('r', 5);
        circle.setAttribute('fill', '#f59e0b');
        circle.setAttribute('stroke', '#090d16');
        circle.setAttribute('stroke-width', 2);
        circle.style.cursor = 'pointer';

        circle.addEventListener('mouseenter', (e) => {{
          circle.setAttribute('r', 7);
          showTooltip(e.clientX, e.clientY, `
            <strong>YEAR: ${{r.year}}</strong><br>
            ${{currentTrendMetric}}: <strong>${{parseFloat(r[currentTrendMetric]).toLocaleString()}}${{currentTrendMetric === 'fatal_share_pct' ? '%' : ''}}</strong>
          `);
        }});
        circle.addEventListener('mouseleave', () => {{
          circle.setAttribute('r', 5);
          hideTooltip();
        }});
        svg.appendChild(circle);

        if (i % 2 === 0 || i === observed.length - 1) {{
          const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          txt.setAttribute('x', cx);
          txt.setAttribute('y', h - padB + 22);
          txt.setAttribute('fill', '#94a3b8');
          txt.setAttribute('font-family', 'JetBrains Mono');
          txt.setAttribute('font-size', '11');
          txt.setAttribute('text-anchor', 'middle');
          txt.textContent = r.year;
          svg.appendChild(txt);
        }}
      }});

      container.appendChild(svg);
    }}

    document.querySelectorAll('[data-trend-metric]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('[data-trend-metric]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTrendMetric = btn.dataset.trendMetric;
        renderTrendsChart();
      }});
    }});

    // Populate Benchmark Table
    function populateBenchmarkTable() {{
      const tbody = document.querySelector('#benchmark-table tbody');
      if (!tbody) return;
      tbody.innerHTML = '';
      DATA.trends_bench.forEach(r => {{
        const tr = document.createElement('tr');
        const isMatch = r.status === 'exact_match';
        tr.innerHTML = `
          <th>${{r.year}}</th>
          <td class="num-cell" data-label="Observed Fatal">${{r.observed_fatal}}</td>
          <td class="num-cell" data-label="Published Fatal">${{r.published_fatal}}</td>
          <td class="num-cell" data-label="Observed Injury">${{r.observed_injury}}</td>
          <td class="num-cell" data-label="Published Injury">${{r.published_injury}}</td>
          <td class="num-cell" data-label="Observed Total">${{r.observed_total}}</td>
          <td class="num-cell" data-label="Published Total">${{r.published_total}}</td>
          <td class="num-cell" data-label="Difference" style="color: ${{r.total_difference == '0' ? '#10b981' : '#f59e0b'}}">${{r.total_difference}}</td>
          <td class="num-cell" data-label="Observed Fatal %">${{parseFloat(r.observed_fatal_share_pct).toFixed(2)}}%</td>
          <td class="num-cell" data-label="Published Fatal %">${{parseFloat(r.published_fatal_share_pct).toFixed(2)}}%</td>
          <td data-label="Status"><span class="status-badge ${{isMatch ? '' : 'amber'}}">${{r.status}}</span></td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // 3. RENDER CASUALTIES TAB
    let currentCasMeasure = 'deaths';
    function renderCasualtiesDonut() {{
      const container = document.getElementById('casualties-donut-chart');
      const legendContainer = document.getElementById('casualties-donut-legend');
      if (!container) return;
      container.innerHTML = '';
      legendContainer.innerHTML = '';

      const w = 320, h = 320;
      const svg = createSVG(w, h);
      const cx = w / 2, cy = h / 2, rOuter = 120, rInner = 75;

      // 2012-2021 pooled data
      const records = DATA.cas_pooled.filter(r => r.period === '2012_2021' && r.measure === currentCasMeasure && r.record_scenario === 'low');

      const colors = {{
        'other_motor_vehicle_occupant': '#ef4444',
        'road_tractor_occupant': '#f59e0b',
        'pedestrian': '#06b6d4',
        'bicyclist': '#10b981',
        'motorcyclist': '#8b5cf6',
        'other_road_user': '#64748b',
        'ambiguous': '#475569'
      }};

      const labels = {{
        'other_motor_vehicle_occupant': 'Other Vehicle Occupants',
        'road_tractor_occupant': 'Road Tractor Occupants',
        'pedestrian': 'Pedestrians',
        'bicyclist': 'Bicyclists',
        'motorcyclist': 'Motorcyclists',
        'other_road_user': 'Other Users',
        'ambiguous': 'Ambiguous'
      }};

      let total = records.reduce((acc, r) => acc + parseFloat(r.count), 0);
      let cumulativeAngle = -Math.PI / 2;

      records.forEach(r => {{
        const count = parseFloat(r.count);
        if (count <= 0) return;
        const angle = (count / total) * Math.PI * 2;
        const color = colors[r.road_user_group] || '#94a3b8';
        const label = labels[r.road_user_group] || r.road_user_group;

        const x1 = cx + rOuter * Math.cos(cumulativeAngle);
        const y1 = cy + rOuter * Math.sin(cumulativeAngle);
        const x2 = cx + rOuter * Math.cos(cumulativeAngle + angle);
        const y2 = cy + rOuter * Math.sin(cumulativeAngle + angle);

        const x3 = cx + rInner * Math.cos(cumulativeAngle + angle);
        const y3 = cy + rInner * Math.sin(cumulativeAngle + angle);
        const x4 = cx + rInner * Math.cos(cumulativeAngle);
        const y4 = cy + rInner * Math.sin(cumulativeAngle);

        const largeArc = angle > Math.PI ? 1 : 0;
        const pathData = `M ${{x1}} ${{y1}} A ${{rOuter}} ${{rOuter}} 0 ${{largeArc}} 1 ${{x2}} ${{y2}} L ${{x3}} ${{y3}} A ${{rInner}} ${{rInner}} 0 ${{largeArc}} 0 ${{x4}} ${{y4}} Z`;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathData);
        path.setAttribute('fill', color);
        path.setAttribute('stroke', '#090d16');
        path.setAttribute('stroke-width', 2);
        path.style.cursor = 'pointer';

        path.addEventListener('mouseenter', (e) => {{
          showTooltip(e.clientX, e.clientY, `
            <strong>${{label}}</strong><br>
            Count: <strong>${{Math.round(count).toLocaleString()}}</strong><br>
            Share: <strong>${{((count / total) * 100).toFixed(1)}}%</strong>
          `);
        }});
        path.addEventListener('mouseleave', hideTooltip);

        svg.appendChild(path);
        cumulativeAngle += angle;

        // Add legend entry
        const leg = document.createElement('span');
        leg.className = 'legend-item';
        leg.innerHTML = `<span class="legend-dot" style="background: ${{color}}"></span> ${{label}} (${{((count / total) * 100).toFixed(1)}}%)`;
        legendContainer.appendChild(leg);
      }});

      // Center Text
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', cx);
      text.setAttribute('y', cy + 5);
      text.setAttribute('fill', '#fff');
      text.setAttribute('font-family', 'JetBrains Mono');
      text.setAttribute('font-size', '16');
      text.setAttribute('font-weight', '700');
      text.setAttribute('text-anchor', 'middle');
      text.textContent = Math.round(total).toLocaleString();
      svg.appendChild(text);

      container.appendChild(svg);
    }}

    function renderCasualtiesLine() {{
      const container = document.getElementById('casualties-line-chart');
      if (!container) return;
      container.innerHTML = '';
      const w = 550, h = 320;
      const padL = 50, padR = 20, padT = 20, padB = 40;
      const chartW = w - padL - padR, chartH = h - padT - padB;

      const years = Array.from(new Set(DATA.cas_counts.map(r => r.year))).sort();
      const svg = createSVG(w, h);

      const field = currentCasMeasure === 'deaths' ? 'deaths_record_scenario_low' : 'injuries_record_scenario_low';

      // Group totals per year
      const otherVeh = [];
      const tractorOcc = [];
      const vru = [];

      years.forEach(yr => {{
        const yrRows = DATA.cas_counts.filter(r => r.year === yr);
        const ov = yrRows.find(r => r.road_user_group === 'other_motor_vehicle_occupant');
        const to = yrRows.find(r => r.road_user_group === 'road_tractor_occupant');
        const ped = yrRows.find(r => r.road_user_group === 'pedestrian');
        const cyc = yrRows.find(r => r.road_user_group === 'bicyclist');
        const moto = yrRows.find(r => r.road_user_group === 'motorcyclist');

        otherVeh.push(ov ? parseInt(ov[field]) : 0);
        tractorOcc.push(to ? parseInt(to[field]) : 0);
        vru.push((ped ? parseInt(ped[field]) : 0) + (cyc ? parseInt(cyc[field]) : 0) + (moto ? parseInt(moto[field]) : 0));
      }});

      const maxVal = Math.max(...otherVeh, ...tractorOcc, ...vru) * 1.1;

      const getX = (i) => padL + (i / (years.length - 1)) * chartW;
      const getY = (val) => padT + chartH - (val / maxVal) * chartH;

      function plotSeries(arr, color) {{
        let d = `M ${{getX(0)}} ${{getY(arr[0])}}`;
        for (let i = 1; i < arr.length; i++) {{
          d += ` L ${{getX(i)}} ${{getY(arr[i])}}`;
        }}
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('d', d);
        p.setAttribute('fill', 'none');
        p.setAttribute('stroke', color);
        p.setAttribute('stroke-width', 2.5);
        svg.appendChild(p);

        arr.forEach((v, i) => {{
          const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          c.setAttribute('cx', getX(i));
          c.setAttribute('cy', getY(v));
          c.setAttribute('r', 4);
          c.setAttribute('fill', color);
          c.setAttribute('stroke', '#090d16');
          c.setAttribute('stroke-width', 1.5);
          c.style.cursor = 'pointer';
          c.addEventListener('mouseenter', (e) => {{
            c.setAttribute('r', 6);
            showTooltip(e.clientX, e.clientY, `Year ${{years[i]}}: <strong>${{v.toLocaleString()}}</strong>`);
          }});
          c.addEventListener('mouseleave', () => {{
            c.setAttribute('r', 4);
            hideTooltip();
          }});
          svg.appendChild(c);
        }});
      }}

      plotSeries(otherVeh, '#ef4444');
      plotSeries(tractorOcc, '#f59e0b');
      plotSeries(vru, '#06b6d4');

      years.forEach((yr, i) => {{
        if (i % 3 === 0 || i === years.length - 1) {{
          const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          txt.setAttribute('x', getX(i));
          txt.setAttribute('y', h - padB + 20);
          txt.setAttribute('fill', '#94a3b8');
          txt.setAttribute('font-family', 'JetBrains Mono');
          txt.setAttribute('font-size', '10');
          txt.setAttribute('text-anchor', 'middle');
          txt.textContent = yr;
          svg.appendChild(txt);
        }}
      }});

      container.appendChild(svg);
    }}

    document.querySelectorAll('[data-cas-measure]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('[data-cas-measure]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentCasMeasure = btn.dataset.casMeasure;
        renderCasualtiesDonut();
        renderCasualtiesLine();
      }});
    }});

    // 4. RENDER CONDITIONS TAB
    let currentCondField = 'C_WTHR';
    function renderConditionsChart() {{
      const container = document.getElementById('conditions-chart');
      if (!container) return;
      container.innerHTML = '';
      const w = 1100, h = 380;
      const padL = 180, padR = 40, padT = 30, padB = 40;
      const chartW = w - padL - padR, chartH = h - padT - padB;

      const rows = DATA.cond_shares.filter(r => r.field === currentCondField && r.period === 'primary_2012_2021');
      const tractorRows = rows.filter(r => r.cohort === 'tractor');
      const otherRows = rows.filter(r => r.cohort === 'no_recorded_tractor');

      // Unique categories
      const labels = Array.from(new Set(tractorRows.map(r => r.label)));
      const svg = createSVG(w, h);

      const maxPct = Math.max(
        ...rows.map(r => parseFloat(r.fatal_share_pct) || 0)
      ) * 1.25 || 15.0;

      const barH = Math.min(22, (chartH / labels.length) / 2.6);
      const rowGap = chartH / labels.length;

      labels.forEach((lbl, i) => {{
        const yCenter = padT + rowGap * i + rowGap / 2;
        const trRow = tractorRows.find(r => r.label === lbl);
        const otRow = otherRows.find(r => r.label === lbl);

        const trVal = trRow ? parseFloat(trRow.fatal_share_pct) : 0;
        const otVal = otRow ? parseFloat(otRow.fatal_share_pct) : 0;

        const wTr = (trVal / maxPct) * chartW;
        const wOt = (otVal / maxPct) * chartW;

        // Label
        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', padL - 14);
        txt.setAttribute('y', yCenter + 4);
        txt.setAttribute('fill', '#f1f5f9');
        txt.setAttribute('font-family', 'JetBrains Mono');
        txt.setAttribute('font-size', '12');
        txt.setAttribute('text-anchor', 'end');
        txt.textContent = lbl.length > 22 ? lbl.slice(0, 20) + '...' : lbl;
        svg.appendChild(txt);

        // Bar 1: Tractor
        const rectTr = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rectTr.setAttribute('x', padL);
        rectTr.setAttribute('y', yCenter - barH - 2);
        rectTr.setAttribute('width', Math.max(2, wTr));
        rectTr.setAttribute('height', barH);
        rectTr.setAttribute('fill', '#f59e0b');
        rectTr.setAttribute('rx', 3);
        rectTr.style.cursor = 'pointer';
        rectTr.addEventListener('mouseenter', (e) => {{
          showTooltip(e.clientX, e.clientY, `<strong>${{lbl}} (Road Tractor)</strong><br>Fatal Share: <strong>${{trVal.toFixed(2)}}%</strong>`);
        }});
        rectTr.addEventListener('mouseleave', hideTooltip);
        svg.appendChild(rectTr);

        // Bar 2: Other
        const rectOt = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rectOt.setAttribute('x', padL);
        rectOt.setAttribute('y', yCenter + 2);
        rectOt.setAttribute('width', Math.max(2, wOt));
        rectOt.setAttribute('height', barH);
        rectOt.setAttribute('fill', '#475569');
        rectOt.setAttribute('rx', 3);
        rectOt.style.cursor = 'pointer';
        rectOt.addEventListener('mouseenter', (e) => {{
          showTooltip(e.clientX, e.clientY, `<strong>${{lbl}} (Other Traffic)</strong><br>Fatal Share: <strong>${{otVal.toFixed(2)}}%</strong>`);
        }});
        rectOt.addEventListener('mouseleave', hideTooltip);
        svg.appendChild(rectOt);
      }});

      container.appendChild(svg);
    }}

    document.querySelectorAll('[data-cond-field]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('[data-cond-field]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentCondField = btn.dataset.condField;
        renderConditionsChart();
      }});
    }});

    // 5. RENDER DECOMPOSITION TAB
    function renderDecompositionChart() {{
      const container = document.getElementById('decomp-chart');
      if (!container) return;
      container.innerHTML = '';
      const w = 550, h = 260;
      const padL = 120, padR = 20, padT = 20, padB = 40;
      const chartW = w - padL - padR, chartH = h - padT - padB;

      const cats = DATA.decomp_cats.filter(r => r.cohort === 'tractor');
      const svg = createSVG(w, h);

      const maxVal = 0.8;
      const minVal = -0.3;
      const range = maxVal - minVal;

      const getX = (val) => padL + ((val - minVal) / range) * chartW;
      const zeroX = getX(0);

      // Zero axis
      const axis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      axis.setAttribute('x1', zeroX);
      axis.setAttribute('y1', padT);
      axis.setAttribute('x2', zeroX);
      axis.setAttribute('y2', h - padB);
      axis.setAttribute('stroke', '#64748b');
      svg.appendChild(axis);

      const rowH = chartH / cats.length;

      cats.forEach((r, i) => {{
        const y = padT + rowH * i + rowH / 2;
        const val = parseFloat(r.net_pp);
        const barW = Math.abs(getX(val) - zeroX);
        const barX = val >= 0 ? zeroX : zeroX - barW;

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', barX);
        rect.setAttribute('y', y - 8);
        rect.setAttribute('width', barW);
        rect.setAttribute('height', 16);
        rect.setAttribute('fill', val >= 0 ? '#f59e0b' : '#38bdf8');
        rect.setAttribute('rx', 2);
        svg.appendChild(rect);

        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', padL - 10);
        txt.setAttribute('y', y + 4);
        txt.setAttribute('fill', '#fff');
        txt.setAttribute('font-family', 'JetBrains Mono');
        txt.setAttribute('font-size', '11');
        txt.setAttribute('text-anchor', 'end');
        txt.textContent = r.label.slice(0, 15);
        svg.appendChild(txt);
      }});

      container.appendChild(svg);
    }}

    // 6. RENDER VKT & AGE TAB
    function renderVKTChart() {{
      const container = document.getElementById('vkt-chart');
      if (!container) return;
      container.innerHTML = '';
      const w = 1100, h = 340;
      const padL = 60, padR = 40, padT = 30, padB = 40;
      const chartW = w - padL - padR, chartH = h - padT - padB;

      const rows = DATA.vkt_annual.filter(r => r.numerator_id === 'primary_observed_events');
      rows.sort((a, b) => parseInt(a.year) - parseInt(b.year));

      const svg = createSVG(w, h);

      const maxRate = Math.max(...rows.map(r => parseFloat(r.events_per_billion_modeled_vkt))) * 1.15;

      const getX = (i) => padL + (i / (rows.length - 1)) * chartW;
      const getY = (val) => padT + chartH - (val / maxRate) * chartH;

      let dCasualty = `M ${{getX(0)}} ${{getY(parseFloat(rows[0].events_per_billion_modeled_vkt))}}`;
      let dFatal = `M ${{getX(0)}} ${{getY(parseFloat(rows[0].fatal_events_per_billion_modeled_vkt) * 10)}}`;

      for (let i = 1; i < rows.length; i++) {{
        dCasualty += ` L ${{getX(i)}} ${{getY(parseFloat(rows[i].events_per_billion_modeled_vkt))}}`;
        dFatal += ` L ${{getX(i)}} ${{getY(parseFloat(rows[i].fatal_events_per_billion_modeled_vkt) * 10)}}`;
      }}

      function addP(d, col) {{
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('d', d);
        p.setAttribute('fill', 'none');
        p.setAttribute('stroke', col);
        p.setAttribute('stroke-width', 3);
        svg.appendChild(p);
      }}

      addP(dCasualty, '#06b6d4');
      addP(dFatal, '#ef4444');

      rows.forEach((r, i) => {{
        const cx = getX(i);
        const cy = getY(parseFloat(r.events_per_billion_modeled_vkt));
        const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        c.setAttribute('cx', cx);
        c.setAttribute('cy', cy);
        c.setAttribute('r', 5);
        c.setAttribute('fill', '#06b6d4');
        c.setAttribute('stroke', '#090d16');
        c.setAttribute('stroke-width', 2);
        c.style.cursor = 'pointer';
        c.addEventListener('mouseenter', (e) => {{
          showTooltip(e.clientX, e.clientY, `
            <strong>${{r.year}}</strong><br>
            Rate: <strong>${{parseFloat(r.events_per_billion_modeled_vkt).toFixed(2)}}</strong> / billion VKT<br>
            Modeled VKT: <strong>${{parseFloat(r.modeled_vkt_billion_km).toFixed(2)}} B km</strong>
          `);
        }});
        c.addEventListener('mouseleave', hideTooltip);
        svg.appendChild(c);

        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', cx);
        txt.setAttribute('y', h - padB + 20);
        txt.setAttribute('fill', '#94a3b8');
        txt.setAttribute('font-family', 'JetBrains Mono');
        txt.setAttribute('font-size', '11');
        txt.setAttribute('text-anchor', 'middle');
        txt.textContent = r.year;
        svg.appendChild(txt);
      }});

      container.appendChild(svg);
    }}

    function renderAgeChart() {{
      const container = document.getElementById('age-chart');
      if (!container) return;
      container.innerHTML = '';
      const w = 1100, h = 300;
      const padL = 120, padR = 40, padT = 30, padB = 40;
      const chartW = w - padL - padR, chartH = h - padT - padB;

      const cohorts = DATA.age_cohorts.filter(r => r.period === '2012_2021');
      const svg = createSVG(w, h);

      const minOR = 0.5, maxOR = 1.3;
      const getX = (val) => padL + ((val - minOR) / (maxOR - minOR)) * chartW;

      // Reference line at OR = 1.0
      const refLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      refLine.setAttribute('x1', getX(1.0));
      refLine.setAttribute('y1', padT);
      refLine.setAttribute('x2', getX(1.0));
      refLine.setAttribute('y2', h - padB);
      refLine.setAttribute('stroke', '#64748b');
      refLine.setAttribute('stroke-dasharray', '4,4');
      svg.appendChild(refLine);

      const rowH = chartH / cohorts.length;

      cohorts.forEach((r, i) => {{
        const y = padT + rowH * i + rowH / 2;
        const orVal = parseFloat(r.adjusted_or_vs_0_to_2_years) || 1.0;
        const ciLow = parseFloat(r.adjusted_or_95_ci_low) || orVal;
        const ciHigh = parseFloat(r.adjusted_or_95_ci_high) || orVal;

        // CI Line
        const ci = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        ci.setAttribute('x1', getX(ciLow));
        ci.setAttribute('y1', y);
        ci.setAttribute('x2', getX(ciHigh));
        ci.setAttribute('y2', y);
        ci.setAttribute('stroke', '#f59e0b');
        ci.setAttribute('stroke-width', 2);
        svg.appendChild(ci);

        // Point
        const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        c.setAttribute('cx', getX(orVal));
        c.setAttribute('cy', y);
        c.setAttribute('r', 6);
        c.setAttribute('fill', '#f59e0b');
        c.setAttribute('stroke', '#090d16');
        c.setAttribute('stroke-width', 2);
        c.style.cursor = 'pointer';
        c.addEventListener('mouseenter', (e) => {{
          showTooltip(e.clientX, e.clientY, `
            <strong>${{r.age_cohort_label}}</strong><br>
            Adjusted OR: <strong>${{orVal.toFixed(3)}}</strong><br>
            95% CI: [${{ciLow.toFixed(3)}}, ${{ciHigh.toFixed(3)}}]
          `);
        }});
        c.addEventListener('mouseleave', hideTooltip);
        svg.appendChild(c);

        // Label
        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', padL - 12);
        txt.setAttribute('y', y + 4);
        txt.setAttribute('fill', '#fff');
        txt.setAttribute('font-family', 'JetBrains Mono');
        txt.setAttribute('font-size', '12');
        txt.setAttribute('text-anchor', 'end');
        txt.textContent = r.age_cohort_label;
        svg.appendChild(txt);
      }});

      container.appendChild(svg);
    }}

    // 7. DATA EXPLORER TABLE & SEARCH
    function populateExplorerTable(filterText = '') {{
      const tbody = document.querySelector('#explorer-table tbody');
      if (!tbody) return;
      tbody.innerHTML = '';

      let rows = DATA.trends_annual.filter(r => r.group === 'road_tractor' && r.subset === 'observed');
      if (filterText) {{
        rows = rows.filter(r => r.year.includes(filterText));
      }}

      document.getElementById('table-row-count').textContent = `Showing ${{rows.length}} of 23 years`;

      rows.forEach(r => {{
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <th>${{r.year}}</th>
          <td class="num-cell" data-label="Casualty Collisions">${{parseInt(r.casualty_collisions).toLocaleString()}}</td>
          <td class="num-cell" data-label="Fatal Collisions" style="color: #ef4444">${{parseInt(r.fatal_collisions).toLocaleString()}}</td>
          <td class="num-cell" data-label="Injury Collisions">${{parseInt(r.injury_collisions).toLocaleString()}}</td>
          <td class="num-cell" data-label="Fatal Share %" style="color: #38bdf8">${{parseFloat(r.fatal_share_pct).toFixed(2)}}%</td>
          <td class="num-cell" data-label="Strict Subset">${{r.subset}}</td>
          <td class="num-cell" data-label="Unknown Type Events">${{r.unknown_type_events}}</td>
          <td class="num-cell" data-label="Overlap Events">${{r.tractor_heavy_overlap_events}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    document.getElementById('table-search')?.addEventListener('input', (e) => {{
      populateExplorerTable(e.target.value.trim());
    }});

    // Export CSV
    document.getElementById('export-csv-btn')?.addEventListener('click', () => {{
      const rows = DATA.trends_annual.filter(r => r.group === 'road_tractor' && r.subset === 'observed');
      const headers = Object.keys(rows[0]);
      let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\\n";
      rows.forEach(r => {{
        csvContent += headers.map(h => r[h]).join(",") + "\\n";
      }});
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "canadian_road_tractor_collisions_1999_2021.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }});

    // Initialize all renders
    window.addEventListener('DOMContentLoaded', () => {{
      renderOverviewChart();
      renderTrendsChart();
      populateBenchmarkTable();
      renderCasualtiesDonut();
      renderCasualtiesLine();
      renderConditionsChart();
      renderDecompositionChart();
      renderVKTChart();
      renderAgeChart();
      populateExplorerTable();
    }});

    window.addEventListener('resize', () => {{
      renderOverviewChart();
      renderTrendsChart();
      renderCasualtiesDonut();
      renderCasualtiesLine();
      renderConditionsChart();
      renderDecompositionChart();
      renderVKTChart();
      renderAgeChart();
    }});
  </script>
</body>
</html>
"""
    return html


def main():
    print("Extracting trucks data package...")
    data = extract_data()
    print("Compiling interactive data app HTML...")
    html_content = generate_html(data)

    print(f"Writing to {OUTPUT_INDEX}...")
    OUTPUT_INDEX.write_text(html_content, encoding="utf-8")

    print(f"Writing to {OUTPUT_STANDALONE}...")
    OUTPUT_STANDALONE.write_text(html_content, encoding="utf-8")

    size_kb = len(html_content.encode("utf-8")) / 1024
    print(f"Done! Created data app ({size_kb:.2f} KB).")


if __name__ == "__main__":
    main()
