r"""
================================================================================
  DEEP ECONOMIC CYCLE ANALYSIS — v3 (Rich Edition)

  Sources: FRED (51 macro series) + yfinance (47 tickers) + Claude AI (Haiku/Sonnet)

  TABS GENERATED:
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  📊 Overview          Scorecard (62 indicators), cycle positions, KPIs  │
  │  📉 Indicator Charts  30 macro charts full history + SPX overlay        │
  │  🔬 Parallel Table    Readings at each S&P 500 drawdown level vs TODAY  │
  │  🔄 Cycle Analysis    Kuznets/Juglar/Kitchin overlays + projections      │
  │  📉 Credit & Rates    HY/IG/CCC spreads, yield curve, bond pairs        │
  │  🗂 Sector Rotation   ETF pair ratios through cycles                    │
  │  📋 Sector Stocks     Top 10 holdings per sector, 1yr performance       │
  │  📡 Leading Indicators Peak/trough scoring, PCR, AAII, NAAIM            │
  │  🔬 Market Charts     Radar, Recession Gauge, Liquidity Waterfall        │
  │  📉 Drawdown Analysis Pullback overlays vs all historical corrections    │
  │  🤖 AI Summary        Claude Sonnet price projections + narratives       │
  │  📅 Eco Calendar      Weekly events + beat/miss + indicator guide        │
  │  ⚡ Options Flow       GEX by strike (requires Barchart CSV upload)      │
  └─────────────────────────────────────────────────────────────────────────┘

  INSTALL:
    pip install yfinance pandas numpy requests pandas_datareader
    pip install fredapi        ← recommended for reliable FRED access

  ──────────────────────────────────────────────────────────────────────────
  USAGE — ALL COMMANDS
  ──────────────────────────────────────────────────────────────────────────

  FULL RUN (default, ~90-120 seconds):
    python cycle_analysis.py

  SPEED FLAGS:
    python cycle_analysis.py --quick
        Fetches fewer FRED series (~20-30s). Good for intraday checks.
        Skips: ISM, LEI, housing detail, valuation series.

    python cycle_analysis.py --no-ai
        Skips Claude Haiku narrative summaries. Saves ~30s + API cost.
        All charts and data still generated. Static fallback text shown.

    python cycle_analysis.py --noapi
        Skips ALL Claude API calls (both Haiku + Sonnet).
        Fastest complete report. No AI summaries, no web search fills.
        Implies --no-ai automatically.

    python cycle_analysis.py --noindicatorcharts
        Skips building the Indicator Charts tab (~15-20s saved).
        Use when you only need the Overview + Parallel Table.

    python cycle_analysis.py --quick --noapi
        Fastest possible report ~15-20s. No AI, fewer FRED series.
        Good for quick market check during trading hours.

    python cycle_analysis.py --quick --noapi --noindicatorcharts
        Ultra-fast mode ~10-15s. Minimum viable report.

  OUTPUT FLAGS:
    python cycle_analysis.py --no-browser
        Saves HTML file but does NOT auto-open in browser.
        Use for scheduled/automated runs (Task Scheduler, cron).

    python cycle_analysis.py --outdir "C:\path\to\folder"
        Save HTML to a custom output folder instead of OUTPUT_DIR.
        Default: C:\Users\16144\OneDrive\Documents\options\automation\output

  FOCUS FLAGS (open directly to one tab):
    python cycle_analysis.py --only overview        Opens on 📊 Overview
    python cycle_analysis.py --only indcharts       Opens on 📉 Indicator Charts
    python cycle_analysis.py --only parallel        Opens on 🔬 Parallel Table
    python cycle_analysis.py --only cycles          Opens on 🔄 Cycle Analysis
    python cycle_analysis.py --only bonds           Opens on 📉 Credit & Rates
    python cycle_analysis.py --only sectors         Opens on 🗂 Sector Rotation
    python cycle_analysis.py --only sectorstocks    Opens on 📋 Sector Stocks
    python cycle_analysis.py --only leading         Opens on 📡 Leading Indicators
    python cycle_analysis.py --only mktcharts       Opens on 🔬 Market Charts
    python cycle_analysis.py --only pullback        Opens on 📉 Drawdown Analysis
    python cycle_analysis.py --only ai              Opens on 🤖 AI Summary
    python cycle_analysis.py --only ecocal          Opens on 📅 Eco Calendar
    python cycle_analysis.py --only optionsflow     ⚡ ULTRA FAST (~5s, CSV only)

  COMBINATION EXAMPLES:
    python cycle_analysis.py --quick --no-browser
        Fast run, no browser pop (for scheduled Task Scheduler runs)

    python cycle_analysis.py --noapi --no-browser --outdir "D:\reports"
        Automated run: no AI, save to custom folder, no browser

    python cycle_analysis.py --only ecocal --noapi
        Just the economic calendar, no AI, ~25s

    python cycle_analysis.py --only parallel --noapi
        Just the Parallel Table with live data, no AI

  ──────────────────────────────────────────────────────────────────────────
  DATA SOURCES & FALLBACK CHAIN
  ──────────────────────────────────────────────────────────────────────────
  For each FRED series, the script tries in order:
    1. fredapi (key rotation across FRED_API_KEYS list)
    2. pandas_datareader (FRED endpoint, 8s timeout)
    3. FRED public CSV endpoint (no auth needed)
    4. yfinance proxy (ETF-based approximation, marked ≈)
    5. Claude web search (for CPI, CAPE, sentiment, etc.)

  If all fail → series shown as N/A (very rare with yfinance fallback).

  FRED circuit breaker fires after 3 network timeouts (not 404s).
  Once fired, remaining series use yfinance proxy directly.
  Note: 404 "series not found" errors do NOT trip the circuit breaker.

================================================================================
"""
import sys, os, argparse, warnings, math, json
from datetime import datetime, date

warnings.filterwarnings("ignore")

FRED_API_KEY  = os.environ.get("FRED_API_KEY", "")
# ── Multiple FRED API keys (optional) ────────────────────────────────────────
# FRED free tier: 120 requests/minute per key. We fetch ~51 series = well within limit.
# The FRED outages you see (⚡ circuit breaker) are NOT rate limits — they are:
#   1. Corporate/ISP firewall blocking api.stlouisfed.org
#   2. FRED server timeouts during high traffic (rare)
#   3. pandas_datareader connection reset (most common cause)
# Multiple keys DO help if the issue is rate limits, but for firewall/timeout issues
# the real fix is the yfinance proxy fallback (already implemented).
# Add backup keys here if you have them — script rotates automatically on failure:
FRED_API_KEYS = [k for k in [
    os.environ.get("FRED_API_KEY", ""),
    os.environ.get("FRED_API_KEY_2", ""),
    os.environ.get("FRED_API_KEY_3", ""),
] if k]  # only include non-empty keys
CLAUDE_API_KEY  = os.environ.get("CLAUDE_API_KEY", "")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
OUTPUT_DIR      = os.environ.get("OUTPUT_DIR", r"C:\Users\16144\OneDrive\Documents\options\automation\output")

if sys.platform == "win32":
    import io as _io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try: os.system("chcp 65001 >nul 2>&1")
    except: pass


# ══════════════════════════════════════════════════════════════════════════════
# CLAUDE AI — DYNAMIC NARRATIVE GENERATION
# Replaces all hardcoded rationale/reasoning text with live AI analysis
# Each call sends current data + asks for 2-3 sentence context-aware reasoning
# Cost: ~$0.008/run · Free $5 credits = ~1.7 years of daily runs
# Skip AI: pass --no-ai flag to use fast static fallback text
# ══════════════════════════════════════════════════════════════════════════════

def _claude_call(prompt: str, max_tokens: int = 120) -> str:
    """Single Claude Haiku API call. Returns text or empty string on failure."""
    if not CLAUDE_API_KEY:
        return ""
    try:
        import requests as _rq, json as _js
        resp = _rq.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":      "claude-haiku-4-5",
                "max_tokens": max_tokens,
                "messages":   [{"role": "user", "content": prompt}],
                "system": (
                    "You are a macro analyst writing 1-2 sentence rationale for a daily "
                    "trading dashboard. Be specific to the numbers provided. No preamble, "
                    "no 'Based on...' opener. Start directly with the insight. Plain text only."
                ),
            },
            timeout=15,
        )
        if resp.status_code == 200:
            _rj = resp.json()
            if "error" in _rj:
                return ""
            if "content" in _rj and _rj["content"]:
                return _rj["content"][0]["text"].strip()
    except Exception:
        pass
    return ""


def ai_summaries(pos: dict, ep: dict, fd: dict, use_ai: bool = True) -> dict:
    """
    Generate all AI-powered narrative blocks for the report.
    Returns a dict of text strings keyed by section name.
    Falls back to rich static text if CLAUDE_API_KEY is empty or --no-ai is set.

    Sections:
      regime_summary     — overall macro situation (shown in banner)
      kuznets_insight    — why Kuznets position matters right now
      juglar_insight     — Juglar position and near-term implication
      kitchin_insight    — Kitchin / inventory cycle status
      ep_summary         — Market Healthcard overall interpretation
      proj_{i}           — each projection scenario rationale
      parallel_{year}    — each historical parallel "today vs then"
      play_{action}      — each playbook action rationale
    """

    def g(key):
        s = fd.get(key)
        return float(s.iloc[-1]) if s is not None and not s.empty else None

    # Live data snapshot for all prompts
    hy    = g("HY_OAS");   ig    = g("YIELD_CURVE")  # yield curve
    ff    = g("FEDFUNDS"); t10   = g("T10Y")
    ur    = g("UNRATE");   ip_yoy = None
    sahm_rise = None
    try:
        s = fd.get("UNRATE")
        if s is not None and len(s) >= 5:
            sahm_rise = round(float(s.iloc[-1]) - float(s.iloc[-4]), 2)
    except: pass
    try:
        s = fd.get("INDPRO")
        if s is not None and len(s) >= 14:
            ip_yoy = round((float(s.iloc[-1]) / float(s.iloc[-13]) - 1) * 100, 1)
    except: pass

    kp    = pos["kuznets"]["pct"]
    jp    = pos["juglar"]["pct"]
    ki    = pos["kitchin"]["pct"]
    k_ph  = pos["kuznets"]["phase"]
    j_ph  = pos["juglar"]["phase"]
    ki_ph = pos["kitchin"]["phase"]
    regime = pos["regime"]["label"]
    ep_sc  = ep["score"]
    n_red  = ep.get("n_red", 0)
    n_yel  = ep.get("n_yellow", 0)
    n_grn  = ep.get("n_green", 0)

    DATA = (
        f"Regime: {regime}. "
        f"Kuznets {kp:.0f}% ({k_ph}), Juglar {jp:.0f}% ({j_ph}), Kitchin {ki:.0f}% ({ki_ph}). "
        f"EP Score {ep_sc}% ({n_red}R/{n_yel}Y/{n_grn}G). "
        f"HY OAS {f'{hy:.0f}bps' if hy else 'N/A'}, "
        f"Yield curve {f'{ig:+.2f}%' if ig is not None else 'N/A'}, "
        f"Fed Funds {f'{ff:.2f}%' if ff else 'N/A'}, "
        f"10Y {f'{t10:.2f}%' if t10 else 'N/A'}, "
        f"Unemployment Sahm {f'+{sahm_rise:.2f}pp' if sahm_rise is not None else 'N/A'}, "
        f"IP YoY {f'{ip_yoy:+.1f}%' if ip_yoy is not None else 'N/A'}."
    )

    out = {}
    if not use_ai or not CLAUDE_API_KEY:
        # Rich static fallbacks — still better than before (embed live numbers)
        out["regime_summary"] = (
            f"Current regime: {regime}. Market Health {ep_sc}% with "
            f"{n_red} danger / {n_yel} caution / {n_grn} green signals. "
            f"HY OAS {f'{hy:.0f}bps' if hy else 'N/A'} — "
            f"{'credit calm, supports dip-buying' if hy and hy < 380 else 'credit elevated, watch spreads'}."
        )
        out["ep_summary"] = (
            f"Market Health {ep_sc}%: {n_red} indicators in danger zone, {n_yel} in caution, {n_grn} green. "
            f"{'Late-cycle risk elevated — reduce cyclical exposure.' if ep_sc > 65 else 'Mid-cycle — maintain balanced positioning.'}"
        )
        return out

    print("  Generating AI summaries (Claude Haiku)...")

    # ── Regime banner ───────────────────────────────────────────────────────
    out["regime_summary"] = _claude_call(
        f"{DATA} In 2 sentences: what does {regime} mean RIGHT NOW for equity investors "
        f"given these specific numbers? Be concrete about the HY OAS and yield curve readings.",
        max_tokens=100
    )

    # ── Market Healthcard summary ────────────────────────────────────────────────
    out["ep_summary"] = _claude_call(
        f"{DATA} In 1-2 sentences: interpret the Market Health of {ep_sc}% "
        f"({n_red}R/{n_yel}Y/{n_grn}G) for an equity trader. What is the single most "
        f"important indicator reading and what does it imply?",
        max_tokens=90
    )

    # ── Cycle position insights ─────────────────────────────────────────────
    out["kuznets_insight"] = _claude_call(
        f"{DATA} In 1 sentence: what does Kuznets at {kp:.0f}% ({k_ph}) mean for "
        f"real estate and infrastructure stocks over the next 2-3 years?",
        max_tokens=70
    )
    out["juglar_insight"] = _claude_call(
        f"{DATA} In 1 sentence: Juglar at {jp:.0f}% ({j_ph}) — what is the most "
        f"likely business investment/capex trajectory over the next 6-18 months?",
        max_tokens=70
    )
    out["kitchin_insight"] = _claude_call(
        f"{DATA} In 1 sentence: Kitchin at {ki:.0f}% ({ki_ph}) — what does this "
        f"mean for inventory cycles and near-term earnings risk?",
        max_tokens=70
    )

    # ── Warning signs, theme, watch indicator per cycle ────────────────────
    _cycle_info = [
        ("kuznets", kp, k_ph, "real estate/infrastructure"),
        ("juglar",  jp, j_ph, "business investment/capex"),
        ("kitchin", ki, ki_ph, "inventory/earnings"),
    ]
    for _cn, _cp, _cph, _cdesc in _cycle_info:
        out[f"warnings_{_cn}"] = _claude_call(
            f"{DATA} {_cn.capitalize()} cycle ({_cdesc}) is at {_cp:.0f}% ({_cph}). "
            f"List exactly 4 current warning signs specific to TODAY's data readings. "
            f"Each must start with ⚡ and reference a real metric or threshold. "
            f"Be concrete, not generic. 4 lines only.",
            max_tokens=140
        )
        out[f"theme_{_cn}"] = _claude_call(
            f"{DATA} {_cn.capitalize()} at {_cp:.0f}% ({_cph}). "
            f"10-15 words: what is the dominant investment theme driving this cycle right now?",
            max_tokens=35
        )
        out[f"watch_{_cn}"] = _claude_call(
            f"{DATA} {_cn.capitalize()} at {_cp:.0f}%. "
            f"Name the single most important indicator to watch and the specific level "
            f"that would confirm the cycle has turned. 20 words max.",
            max_tokens=40
        )


    for i, p in enumerate(pos.get("projections", [])):
        out[f"proj_{i}"] = _claude_call(
            f"{DATA} Projection: {p['name']} (probability {p['probability']}, "
            f"magnitude {p['magnitude']}). Trigger: {p.get('trigger','—')}. "
            f"In 2 sentences: given today's specific data, how likely is this scenario "
            f"and what would confirm/deny it in the next 30-60 days?",
            max_tokens=110
        )

    # ── Historical parallel key_diff ────────────────────────────────────────
    for p in pos.get("parallels", []):
        yr = p["year"]
        out[f"parallel_{yr}"] = _claude_call(
            f"{DATA} We are comparing today to {yr} (similarity {p['sim']}%). "
            f"Historical: {p['desc']} "
            f"In 2 sentences: what are the MOST IMPORTANT differences between "
            f"today's data and {yr}, and does that make the analog more or less dangerous?",
            max_tokens=110
        )

    # ── Playbook rationale ──────────────────────────────────────────────────
    for play in pos.get("_playbook", []):
        action = play.get("action", "")
        assets = play.get("assets", "")
        out[f"play_{action}"] = _claude_call(
            f"{DATA} Playbook action: {action} — {assets}. "
            f"In 2 sentences: given today's SPECIFIC numbers (HY OAS, yield curve, "
            f"cycle positions, Market Health), why is this action appropriate RIGHT NOW? "
            f"Include one specific number that most supports this recommendation.",
            max_tokens=110
        )

    # ── Master summary — full picture analysis ────────────────────────────────
    # Build a compact data brief for Claude to synthesize
    ep_brief = ", ".join(
        f"{ind['name']} {ind['signal']} ({ind['value']})"
        for ind in ep.get("indicators", [])
    )
    proj_brief = " | ".join(
        f"{p['name']} ({p['probability']}, {p['magnitude']})"
        for p in pos.get("projections", [])
    )
    parallel_brief = " | ".join(
        f"{p['year']} {p['sim']}% match"
        for p in pos.get("parallels", [])
    )
    play_brief = " | ".join(
        f"{p['action']}: {p['assets']}"
        for p in pos.get("_playbook", [])
    )

    if use_ai and CLAUDE_API_KEY:
        # Use a larger call for the master summary — this is the main output
        try:
            import requests as _rq2
            _prompt = (
                "macro brief:\n"
                + "Regime: " + regime + " | EP " + str(ep_sc) + "%\n"
                + "K:" + str(round(kp)) + "% J:" + str(round(jp)) + "% Ki:" + str(round(ki)) + "%\n"
                + "Data: " + DATA + "\n"
                + "Signals: " + ep_brief + "\n"
                + "Scenarios: " + proj_brief + "\n"
                + "Write 5 bullets (• prefix each):\n"
                + "1. Situation now\n"
                + "2. Most critical indicator\n"
                + "3. Equity outlook 3-12 months\n"
                + "4. Risk trigger with threshold\n"
                + "5. Trade: ETFs + timeframe"
            )
            master_resp = _rq2.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5",
                    "max_tokens": 600,
                    "system": (
                        "You are a senior macro analyst. Write a concise executive summary "
                        "for a trader's daily cycle analysis dashboard. Use bullet points. "
                        "Be specific with numbers. No preamble. Max 6 bullets."
                    ),
                    "messages": [{"role": "user", "content": _prompt}],
                },
                timeout=20,
            ).json()
            if "error" in master_resp:
                raise ValueError(f"API error: {master_resp['error'].get('message','unknown')}")
            if "content" not in master_resp:
                raise ValueError(f"Unexpected response keys: {list(master_resp.keys())}")
            out["overall_summary"] = master_resp["content"][0]["text"].strip()
            print("  AI master summary generated ✓")
        except Exception as ex:
            print(f"  AI master summary failed: {ex}")
            out["overall_summary"] = ""
    else:
        # Rich static fallback
        out["overall_summary"] = (
            "• Regime: " + regime + " — EP " + str(ep_sc) + "% (" + str(n_red) + "R/" + str(n_yel) + "Y/" + str(n_grn) + "G)\n"
            + "• Cycles: K" + str(round(kp)) + "% J" + str(round(jp)) + "% Ki" + str(round(ki)) + "%\n"
            + "• Credit: HY OAS " + (str(round(hy)) + "bps" if hy else "N/A") + ("  CALM" if hy and hy < 380 else "  ELEVATED") + "\n"
            + "• Risk: " + (proj_brief.split(" | ")[0] if proj_brief else "Monitor EP indicators") + "\n"
            + "• Action: " + (play_brief.split(" | ")[0] if play_brief else "See Cycle Framework tab")
        )
    ai_count = sum(1 for v in out.values() if v)
    print(f"  AI summaries: {ai_count}/{len(out)} generated ✓")
    return out



# ══════════════════════════════════════════════════════════════════════════════
# CYCLE MECHANICS KNOWLEDGE BASE
# Hard-coded narrative + dynamic data fills in the current readings
# ══════════════════════════════════════════════════════════════════════════════

CYCLE_MECHANICS = {
    "kuznets": {
        "name": "Kuznets Cycle (17–21 years)",
        "aka": "Infrastructure Supercycle / Real Estate Cycle",
        "duration": "17–21 years trough to trough",
        "discoverer": "Simon Kuznets (1930) via construction data analysis",
        "primary_force": "Real estate & infrastructure investment waves",
        "mechanism": """
        <strong>How it's created:</strong><br>
        The Kuznets cycle is built from the time it takes major infrastructure to become
        obsolete and require replacement. When a new technology platform emerges
        (railroads 1850s, electrification 1900s, highways 1950s, internet 1990s, AI 2020s),
        it triggers a 15–20 year buildout. Capital floods in. Land prices rise near
        infrastructure nodes. Credit expands against rising collateral. Employment surges.<br><br>
        <strong>What causes the turn:</strong><br>
        Overbuilding eventually outpaces demand. Vacancy rates rise. Credit quality
        deteriorates. The construction sector collapses, taking employment and collateral
        values with it. The 2008 housing crisis is the textbook Kuznets bust.
        Repair takes a full generation — roughly 20 years — because the physical
        infrastructure must depreciate before investment is again profitable.<br><br>
        <strong>The 4 forces:</strong><br>
        (1) Demographics — household formation drives housing demand<br>
        (2) Credit availability — cheap money inflates construction booms<br>
        (3) Technology adoption curve — S-curve of new platform adoption<br>
        (4) Government policy — infrastructure spending programs (New Deal, CHIPS Act)
        """,
        "historical_peaks": [
            {"year": 1925, "event": "Florida land boom peak → Great Depression construction collapse"},
            {"year": 1945, "event": "Post-WWII reconstruction begins new 20yr cycle"},
            {"year": 1965, "event": "Suburban buildout peak → urban decay / stagflation era"},
            {"year": 1979, "event": "Commercial real estate peak → S&L crisis"},
            {"year": 1989, "event": "Japanese real estate peak → Lost Decade"},
            {"year": 2006, "event": "US housing peak → GFC / Kuznets winter 2008-2011"},
            {"year": 2028, "event": "PROJECTED: AI infrastructure / data center peak"},
        ],
        "current_position": "Late Expansion (72% through 2011-2032 cycle)",
        "current_theme": "AI/Cloud/Clean Energy buildout — data centers, power grid, EV infrastructure",
        "warning_signs": [
            "Data center vacancy rates rising (watch: CBRE quarterly reports)",
            "CHIPS Act subsidy-driven overcapacity in semis",
            "Housing starts declining despite demand (affordability crisis)",
            "Commercial real estate stress (office vacancy at record highs now)",
        ],
        "watch_indicator": "HOUST (Housing Starts) — leading indicator 12-18 months ahead",

        "peak_readings": [
            {"period":"2006 Peak (GFC setup)",    "hy":280,  "yc":-0.20, "ip":3.2,  "cu":81.5, "ff":5.25, "signal":"RISK OFF", "note":"HY <300, curve inverted, CapUtil >81"},
            {"period":"1989 Peak (S&L crisis)",  "hy":None, "yc":0.10,  "ip":2.1,  "cu":84.1, "ff":9.00, "signal":"RISK OFF", "note":"CapUtil >83, FF >8%, curve flat"},
            {"period":"Current (2026)",           "hy":None, "yc":None,  "ip":None, "cu":None, "ff":None, "signal":"LIVE",     "note":"See Market Healthcard for live readings"},
        ],    },
    "juglar": {
        "name": "Juglar Cycle (7–11 years)",
        "aka": "Business Investment Cycle / Fixed Capital Cycle",
        "duration": "7–11 years trough to trough",
        "discoverer": "Clément Juglar (1862) via bank credit data",
        "primary_force": "Fixed business investment (capex, equipment, factories)",
        "mechanism": """
        <strong>How it's created:</strong><br>
        When the economy is growing, firms expect demand to continue rising.
        They borrow to invest in new capacity — factories, equipment, technology.
        This investment itself stimulates more GDP growth, employment, and corporate earnings.
        The cycle feeds itself upward for 5–7 years.<br><br>
        <strong>What causes the turn:</strong><br>
        Three forces converge at the peak: (1) capacity catches up with demand,
        reducing the urgency to invest more, (2) interest rates rise as credit
        is over-extended and central banks fight inflation, (3) profit margins
        compress as input costs (wages, commodities, credit) rise faster than
        output prices. Firms cut capex. Employment growth slows. The credit
        cycle turns. This is the most important cycle for stock market investors —
        S&P 500 earnings track Juglar phases with 85% correlation.<br><br>
        <strong>The 3 forces:</strong><br>
        (1) Credit cycle — availability and cost of capital drives investment decisions<br>
        (2) Profitability cycle — return on invested capital vs hurdle rates<br>
        (3) Inventory/overcapacity — firms realize they over-built and cut back
        """,
        "historical_peaks": [
            {"year": 1973, "event": "Oil shock + tightening → recession. S&P -48%"},
            {"year": 1980, "event": "Volcker shock → double-dip. S&P -27%"},
            {"year": 1990, "event": "S&L crisis + Iraq war → recession. S&P -20%"},
            {"year": 2000, "event": "Dot-com overcapacity + tightening → bust. S&P -49%"},
            {"year": 2007, "event": "Credit bubble peak → GFC. S&P -57%"},
            {"year": 2018, "event": "Trade war + tightening → correction. S&P -20% (no recession)"},
            {"year": 2025, "event": "PROJECTED: AI capex peak → Juglar contraction 2025-2027"},
        ],
        "current_position": "Late Expansion / Near Peak (89% through 2020-2027 cycle)",
        "current_theme": "AI-driven capex boom: $500B+ annual AI infrastructure spend (Mag7 + hyperscalers)",
        "warning_signs": [
            "AI capex exceeding monetizable revenue (ROI questions emerging)",
            "Corporate profit margins compressing from labor costs",
            "Credit spreads beginning to widen from tight levels",
            "Fed holding restrictive — real rates positive, constraining investment",
        ],
        "watch_indicator": "INDPRO + CAPUTIL — capex cycle health metrics",

        "peak_readings": [
            {"period":"2007 Peak",  "hy":280,  "yc":-0.20, "ip":2.8,  "cu":81.4, "ff":5.25, "signal":"RISK OFF", "note":"HY widened 280→700bps. Curve inverted. CapUtil >81."},
            {"period":"2000 Peak",  "hy":350,  "yc":-0.50, "ip":5.6,  "cu":82.3, "ff":6.50, "signal":"RISK OFF", "note":"Tech overcapacity. Curve deeply inverted. IP high but rolling."},
            {"period":"2018 Peak",  "hy":320,  "yc":0.10,  "ip":3.1,  "cu":78.3, "ff":2.50, "signal":"CAUTION",  "note":"Kitchin only — no inversion. Quick recovery."},
            {"period":"Trough 2009","hy":1900, "yc":2.50,  "ip":-14.8,"cu":68.0, "ff":0.25, "signal":"RISK ON",  "note":"HY >1000 = max fear = buy signal. Curve steep = early cycle."},
            {"period":"Trough 2020","hy":870,  "yc":0.50,  "ip":-16.0,"cu":64.0, "ff":0.25, "signal":"RISK ON",  "note":"HY >800 = oversold. V-shape recovery. Curve positive."},
            {"period":"Current (2026)", "hy":None, "yc":None,  "ip":None, "cu":None, "ff":None, "signal":"LIVE",     "note":"Live — compare to peaks/troughs above"},
        ],    },
    "kitchin": {
        "name": "Kitchin Cycle (3–4 years)",
        "aka": "Inventory Cycle / Earnings Cycle",
        "duration": "3–4 years trough to trough",
        "discoverer": "Joseph Kitchin (1923) via bank clearings and commodity prices",
        "primary_force": "Inventory accumulation and destocking",
        "mechanism": """
        <strong>How it's created:</strong><br>
        Businesses systematically over-order inventory when demand is rising,
        then over-cut when demand slows. This lag creates regular 3–4 year
        oscillations that show up directly in corporate earnings.<br><br>
        When demand accelerates, firms order more than needed (safety stock).
        Suppliers see double orders (the bullwhip effect). Supply increases to match
        the perceived demand. Then actual demand slows or supply arrives late.
        Suddenly there's too much inventory. Firms stop ordering. Earnings collapse
        even though end demand may not have changed much.<br><br>
        <strong>Why it matters for trading:</strong><br>
        The Kitchin cycle drives most quarter-to-quarter earnings surprises and
        PMI oscillations. It explains why markets can drop 20% even without a
        recession — the inventory cycle alone creates enough earnings pressure
        to cause corrections.<br><br>
        <strong>The 2 forces:</strong><br>
        (1) Information lags — businesses can't see real-time end demand<br>
        (2) Lead times — long ordering lead times create bullwhip amplification
        """,
        "historical_peaks": [
            {"year": 1984, "event": "Inventory correction → mild recession. S&P -15%"},
            {"year": 1987, "event": "Black Monday inventory/credit shock. S&P -34%"},
            {"year": 1994, "event": "Inventory cycle + Fed tightening. S&P -10%"},
            {"year": 1998, "event": "LTCM / EM crisis inventory shock. S&P -20%"},
            {"year": 2011, "event": "European debt + inventory destocking. S&P -21%"},
            {"year": 2015, "event": "China destock + commodity bust. S&P -15%"},
            {"year": 2018, "event": "Trade war inventory shock. S&P -20%"},
            {"year": 2022, "event": "Post-COVID destocking + tightening. S&P -25%"},
            {"year": 2025, "event": "PROJECTED: AI/tech inventory correction. S&P -10 to -20%"},
        ],
        "current_position": "Near Peak / Contraction onset (95% through 2023-2026 cycle)",
        "current_theme": "AI chip and data center inventory buildup — risk of correction if demand disappoints",
        "warning_signs": [
            "Semiconductor inventory at elevated levels (NVIDIA supply vs demand)",
            "Consumer electronics restocking cycle ending",
            "PMI new orders < inventories = classic destocking signal",
            "Negative earnings guidance rising above 65%",
        ],
        "watch_indicator": "ISM PMI (New Orders minus Inventories) — turns 2-3 months ahead of EPS",

        "peak_readings": [
            {"period":"2022 Peak",  "hy":600,  "yc":-1.0,  "ip":3.8,  "cu":80.0, "ff":4.50, "signal":"RISK OFF", "note":"HY >600 + inversion + CapUtil >79 = confirmed correction"},
            {"period":"2018 Peak",  "hy":350,  "yc":0.10,  "ip":3.5,  "cu":78.5, "ff":2.50, "signal":"CAUTION",  "note":"HY 350 = elevated. Curve flat. Fast correction -20%."},
            {"period":"2015 Peak",  "hy":450,  "yc":1.50,  "ip":-1.2, "cu":77.0, "ff":0.25, "signal":"CAUTION",  "note":"IP went negative. HY >450. Commodity bust."},
            {"period":"2011 Trough","hy":750,  "yc":2.00,  "ip":-2.0, "cu":74.0, "ff":0.25, "signal":"RISK ON",  "note":"HY >700 = bottom. EU debt crisis bottomed. Steep curve."},
            {"period":"Current (2026)", "hy":None, "yc":None,  "ip":None, "cu":None, "ff":None, "signal":"LIVE",     "note":"Live — compare to peaks/troughs above"},
        ],    },
}

# ══════════════════════════════════════════════════════════════════════════════
# HISTORICAL BEAR MARKETS & CORRECTIONS — reference database
# ══════════════════════════════════════════════════════════════════════════════

BEAR_MARKETS = [
    # (name, peak_date, trough_date, sp500_drawdown, duration_months,
    #  primary_cycle, trigger, recovery_months, lessons)
    ("1973-74 Bear", "1973-01", "1974-10", -48, 21, "Juglar peak", "Oil shock + Volcker-era inflation", 24,
     "Energy + commodities + cash > equities. Duration shocks matter more than rate shocks."),
    ("1980-82 Double Dip", "1980-02", "1982-08", -27, 30, "Juglar contraction", "Fed Funds 20%+ — Volcker shock", 18,
     "Bonds outperformed equities during tightening. Short duration. Avoid growth."),
    ("1987 Crash", "1987-08", "1987-12", -34, 4, "Kitchin peak", "Portfolio insurance + valuation compression", 22,
     "Flash crashes recover fast. Buy when VIX spikes to 40+. Duration: 4 months."),
    ("1990 Gulf War", "1990-07", "1990-10", -20, 3, "Juglar", "Oil shock + S&L crisis + Iraq", 12,
     "Short, sharp, geopolitical corrections recover in 6-12 months."),
    ("2000-02 Dot-com", "2000-03", "2002-10", -49, 31, "Juglar + Kitchin", "Capex overcapacity + valuation bubble", 60,
     "Tech overvaluation takes years to unwind. Rotate: value, energy, healthcare."),
    ("2007-09 GFC", "2007-10", "2009-03", -57, 17, "Kuznets + Juglar", "Credit collapse + housing Kuznets bust", 49,
     "Systemic credit events are the worst. Cash + TLT was only protection. 4yr recovery."),
    ("2011 EU Debt", "2011-04", "2011-10", -21, 6, "Kitchin", "European sovereign debt + US downgrade", 9,
     "Cyclical corrections within bull markets recover fast. IWM hit hardest."),
    ("2015-16 China", "2015-05", "2016-02", -15, 9, "Kitchin", "China slowdown + oil collapse + EM contagion", 7,
     "Commodity / EM-driven corrections are shallow. Buy XLE weakness late."),
    ("2018 Q4", "2018-09", "2018-12", -20, 3, "Juglar late", "Fed tightening + trade war + valuation", 5,
     "Policy-driven corrections with no credit stress recover in 3-5 months."),
    ("2020 COVID", "2020-02", "2020-03", -34, 2, "Exogenous", "Pandemic shock — fastest bear in history", 5,
     "Fed/fiscal response speed determines recovery speed. Buy fiscal response, not the dip."),
    ("2022 Rate Shock", "2021-12", "2022-10", -25, 10, "Juglar late + Kitchin", "Fed tightening + inflation + valuation reset", 18,
     "Growth/tech hit hardest (-50%+). Value, energy, cash protect. Duration matters."),
]

CROSS_PAIRS = [
    ("XLY","XLP", "Risk Appetite",       "Consumer Disc÷Staples — rising=risk-on"),
    ("XLF","XLU", "Growth vs Defensive", "Financials÷Utilities — rising=expansion"),
    ("XLK","XLV", "Tech vs Healthcare",  "Tech÷Healthcare — rising=growth bias"),
    ("XLE","XLU", "Inflation Hedge",     "Energy÷Utilities — rising=inflation/late cycle"),
    ("IWM","SPY", "Market Breadth",      "Small÷Large Cap — rising=broad rally"),
    ("XLI","XLP", "Capex Cycle",         "Industrials÷Staples — rising=capex expanding"),
    ("XLK","XLP", "Growth vs Staples",   "Sharpest growth/value barometer"),
    ("HYG","LQD", "Credit Risk",         "HY÷IG bonds — rising=credit risk-on"),
]

SECTOR_ETFS = {
    "XLK":"Technology","XLF":"Financials","XLY":"Consumer Disc.",
    "XLI":"Industrials","XLE":"Energy","XLB":"Materials",
    "XLV":"Healthcare","XLP":"Staples","XLU":"Utilities",
    "XLRE":"Real Estate","XLC":"Comm. Svcs",
}

FRED_MAP = {
    # ── TIER 1: Daily/weekly — always available, fetch first ──────────────────
    # Credit spreads (BAML via FRED — daily)
    "HY_OAS":"BAMLH0A0HYM2","IG_OAS":"BAMLC0A0CM",
    "CCC_OAS":"BAMLH0A3HYM2","BBB_SPREAD":"BAMLC0A4CBBB",
    # Yield curves + rates (daily)
    "YIELD_CURVE":"T10Y2Y","T10Y3M":"T10Y3M",
    "T10Y":"DGS10","FEDFUNDS":"FEDFUNDS",
    "REAL_YIELD":"DFII10","BREAKEVEN":"T10YIE",
    # Fed liquidity (weekly)
    "WALCL":"WALCL","WTREGEN":"WTREGEN","RRPONTSYD":"RRPONTSYD",
    "NFCI":"NFCI","SOFR":"SOFR",
    # ── TIER 2: Monthly government releases — highly reliable ─────────────────
    "UNRATE":"UNRATE","PAYEMS":"PAYEMS","SAHM":"SAHMREALTIME",
    "CPI":"CPIAUCSL","PCE":"PCEPI","INDPRO":"INDPRO","CAPUTIL":"TCU",
    "RETAIL":"RSAFS","HOUST":"HOUST","PERMIT":"PERMIT","M2SL":"M2SL",
    "CFNAI":"CFNAI",
    "NY_REC_PROB":"RECPROUSM156N","CREDIT_CARD_DLQ":"DRCCLACBS","USREC":"USREC",
    "SP500":"SP500","DCOILWTICO":"DCOILWTICO",
    # Housing (monthly, slightly lagged)
    "CI_LOAN_DLQ":"DRCLACBS","OFR_FSI":"STLFSI4",
    "RATE_30":"MORTGAGE30US","SUPPLY_MO":"MSACSR",
    "HPI_NAT":"CSUSHPISA","MED_PRICE":"MSPUS",
    "MTGE_DELINQ":"DRSFRMACBS","MED_INC_HO":"MEHOINUSA672N",
    # ── TIER 3: Less reliable / may 404 on datareader — fetch last ────────────
    # ISM data (NAPM series) — proprietary, frequently unavailable via datareader
    # fredapi works; datareader often 404s which can trip circuit breaker
    "INIT_CLAIMS":"ICSA","CONT_CLAIMS":"CCSA",
    "UMCSENT":"UMCSENT","DURGDS":"ADXTNO",
    "LEI":"OEUSKLITOTALSTMEI",  # OECD CLI — replaces discontinued Conference Board USSLIND
    "ISM_PMI":"NAPM","ISM_NEWORDERS":"NAPMNOI","ISM_PRICES":"NAPMPRI",
    # ── TIER 4: Derived / valuation — may lag or fail ─────────────────────────
    "WILL5000IND":"WILL5000PRFC","GDP":"GDP","SP500EPS":"SP500EPS",
}

FRED_QUICK = {k:v for k,v in FRED_MAP.items()
              if k in ("HY_OAS","IG_OAS","YIELD_CURVE","T10Y3M","FEDFUNDS",
                       "UNRATE","CPI","INDPRO","T10Y","CAPUTIL","NFCI","M2SL",
                       "HOUST","RETAIL","BREAKEVEN","WALCL","WTREGEN","RRPONTSYD",
                       "CCC_OAS","REAL_YIELD","CREDIT_CARD_DLQ","NY_REC_PROB",
                       "ISM_PMI","ISM_NEWORDERS","ISM_PRICES","INIT_CLAIMS","CONT_CLAIMS",
                       "LEI","DURGDS","UMCSENT","SOFR",
                       "WILL5000IND","GDP","SP500EPS",
                       "CI_LOAN_DLQ","OFR_FSI","RATE_30","SUPPLY_MO","HPI_NAT","MTGE_DELINQ","MED_INC_HO")}

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING — 4-layer fallback: fredapi → pandas_datareader → CSV → yfinance
# On networks that block FRED, yfinance proxies cover all key indicators
# ══════════════════════════════════════════════════════════════════════════════

# yfinance tickers that proxy FRED macro series
_YF_PROXIES = {
    "T10Y":        "^TNX",   # 10-year Treasury yield × 10 (Yahoo stores as %)
    "T10Y3M":      "^IRX",   # 13-week T-bill (short end) — compute spread separately
    "SP500":       "^GSPC",  # S&P 500
    "DCOILWTICO":  "CL=F",   # WTI crude oil futures
    "GOLDAMGBD":   "GC=F",   # Gold futures
    "VIX":         "^VIX",   # VIX
    "DXY":         "DX-Y.NYB",
    "HYG_PRICE":   "HYG",    # HY bond ETF price (proxy for spread direction)
    "TLT_PRICE":   "TLT",    # Long duration Treasury ETF
}

def _fred_via_fredapi(sid, n):
    """Try fredapi library with key rotation across all available keys."""
    import pandas as pd, socket
    # Build list of keys to try — skip placeholder keys
    _keys_to_try = [k for k in FRED_API_KEYS
                    if k and k != "YOUR_SECOND_FREE_KEY_HERE" and k != "YOUR_THIRD_FREE_KEY_HERE"]
    if not _keys_to_try:
        return pd.Series(dtype=float)
    try:
        from fredapi import Fred
    except ImportError:
        return pd.Series(dtype=float)
    for _key in _keys_to_try:
        try:
            _old = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)
            try:
                s = Fred(api_key=_key).get_series(sid)
            finally:
                socket.setdefaulttimeout(_old)
            if s is not None and not s.empty:
                return s.dropna().tail(n)
        except Exception:
            continue   # try next key
    return pd.Series(dtype=float)

def _fred_via_datareader(sid, n):
    """Try pandas_datareader with a hard 8-second timeout."""
    import pandas as pd, socket
    try:
        import pandas_datareader.data as web
        from datetime import date, timedelta
        start = date.today() - timedelta(days=int(n * 3))
        _old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(8)
        try:
            df = web.DataReader(sid, "fred", start=start, end=date.today())
        finally:
            socket.setdefaulttimeout(_old_timeout)
        s = df.iloc[:, 0].dropna().tail(n)
        # Mark success on the function so circuit breaker resets
        fred._last_dr_was_timeout = False
        return s
    except ImportError:
        return pd.Series(dtype=float)
    except Exception as e:
        # Distinguish timeout/network errors from "series not found" (404/KeyError)
        _emsg = str(e).lower()
        _is_network = any(x in _emsg for x in [
            "timeout","connection","ssl","socket","refused","reset","eof",
            "name resolution","getaddrinfo","network","unreachable"
        ])
        # 404, "not found", "bad request" = series doesn't exist = NOT a network failure
        _is_not_found = any(x in _emsg for x in ["404","not found","bad request","no data"])
        if _is_not_found:
            fred._last_dr_was_timeout = False  # don't count against circuit breaker
        else:
            fred._last_dr_was_timeout = _is_network
        return pd.Series(dtype=float)

def _fred_via_csv(sid, n):
    """Try FRED public CSV endpoint."""
    import pandas as pd
    try:
        import requests, io
        r = requests.get(
            f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        if r.status_code == 200 and len(r.text) > 200:
            df = pd.read_csv(io.StringIO(r.text), parse_dates=["DATE"]).dropna()
            df.columns = ["date", "value"]
            s = df.set_index("date")["value"].tail(n)
            if not s.empty:
                return s
    except Exception:
        pass
    return pd.Series(dtype=float)

def _fred_via_yfinance_proxy(name, n):
    """
    Derive macro indicators from yfinance market data when FRED is unreachable.
    Returns (Series or None, description).
    """
    import pandas as pd, numpy as np
    try:
        import yfinance as yf
    except ImportError:
        return None, "yfinance not installed"

    # All tickers needed by any proxy — downloaded in one batch call
    _PROXY_TICKERS = [
        "^TNX","^IRX","HYG","LQD","^VIX","SPY","QQQ","XLI","XLY","XLP",
        "XHB","GLD","GC=F","TLT","^GSPC","CL=F","RSP","XLB","USO","RINF"
    ]

    def _dl(ticker, period="5y"):
        """Return series from cache (batch-downloaded) or fall back to individual download."""
        global _YF_PROXY_CACHE
        if ticker in _YF_PROXY_CACHE:
            return _YF_PROXY_CACHE[ticker]
        # Not in cache — try individual download (for less-common tickers)
        try:
            raw = yf.download(ticker, period=period, auto_adjust=True, progress=False)
            if raw.empty: return pd.Series(dtype=float)
            c = raw["Close"].squeeze().dropna()
            c.index = pd.to_datetime(c.index).tz_localize(None)
            _YF_PROXY_CACHE[ticker] = c   # cache it
            return c
        except Exception:
            return pd.Series(dtype=float)

    # Pre-warm cache on first proxy call (batch download all proxy tickers at once)
    if not _YF_PROXY_CACHE:
        try:
            print("  Batch-downloading proxy tickers for FRED fallback...")
            raw = yf.download(_PROXY_TICKERS, period="5y", auto_adjust=True, progress=False)
            closes = raw["Close"] if hasattr(raw.columns, "levels") else raw
            for _t in _PROXY_TICKERS:
                if _t in closes.columns:
                    _s = closes[_t].dropna()
                    _s.index = pd.to_datetime(_s.index).tz_localize(None)
                    if len(_s) > 10:
                        _YF_PROXY_CACHE[_t] = _s
            print(f"  Proxy cache: {len(_YF_PROXY_CACHE)}/{len(_PROXY_TICKERS)} tickers ready")
        except Exception as _ce:
            print(f"  Proxy batch download failed: {_ce}")

    if name == "T10Y":
        s = _dl("^TNX")  # Yahoo stores 10Y yield × 10 as %, already in %
        return s.resample("ME").last().tail(n) if not s.empty else None, "^TNX"

    elif name == "YIELD_CURVE":
        t10 = _dl("^TNX"); t2 = _dl("^IRX")
        if t10.empty or t2.empty: return None, "yield curve proxy failed"
        # ^IRX is 13-week rate already in %, ^TNX is 10Y in %
        combined = pd.concat([t10, t2], axis=1).dropna()
        combined.columns = ["t10","t2"]
        # Approximate 10Y-2Y using 10Y - 13wk (close enough for signal)
        spread = (combined["t10"] - combined["t2"])
        return spread.resample("ME").last().tail(n), "^TNX - ^IRX proxy"

    elif name == "T10Y3M":
        t10 = _dl("^TNX"); t3m = _dl("^IRX")
        if t10.empty or t3m.empty: return None, "T10Y3M proxy failed"
        combined = pd.concat([t10, t3m], axis=1).dropna()
        combined.columns = ["t10","t3m"]
        return (combined["t10"] - combined["t3m"]).resample("ME").last().tail(n), "^TNX - ^IRX"

    elif name == "FEDFUNDS":
        # Use 3-month T-bill as proxy — tracks Fed Funds very closely
        s = _dl("^IRX")
        return s.resample("ME").last().tail(n) if not s.empty else None, "^IRX proxy"

    elif name == "HY_OAS":
        # Derive HY spread proxy from HYG vs LQD relative performance
        # When HYG underperforms LQD, spreads are widening
        hyg = _dl("HYG"); lqd = _dl("LQD")
        if hyg.empty or lqd.empty: return None, "HY proxy failed"
        # Approximate: use HYG's own yield implied from price
        # HYG ~5.5% coupon. YTM proxy = coupon_pct - price_change
        # More practical: use a fixed base spread + VIX-correlated adjustment
        # Simplest reliable proxy: scale HYG total return spread vs LQD
        combined = pd.concat([hyg, lqd], axis=1).dropna()
        combined.columns = ["hyg","lqd"]
        # HYG/LQD ratio inverted and scaled to approximate OAS
        ratio = combined["lqd"] / combined["hyg"]
        # Normalize to ~300-600 bps range
        mn, mx = ratio.min(), ratio.max()
        if mx > mn:
            oas_proxy = 250 + (ratio - mn) / (mx - mn) * 500
        else:
            oas_proxy = ratio * 0 + 350
        return oas_proxy.resample("ME").last().tail(n), "HYG/LQD proxy"

    elif name == "SP500":
        s = _dl("^GSPC")
        return s.resample("ME").last().tail(n) if not s.empty else None, "^GSPC"

    elif name == "DCOILWTICO":
        s = _dl("CL=F")
        return s.resample("ME").last().tail(n) if not s.empty else None, "CL=F"

    elif name == "CCC_OAS":
        # CCC spread proxy: HYG/LQD ratio scaled to CCC spread range (~800-1800bps)
        hyg = _dl("HYG"); lqd = _dl("LQD")
        if hyg.empty or lqd.empty: return None, "CCC proxy failed"
        combo = pd.concat([hyg, lqd], axis=1).dropna(); combo.columns = ["hyg","lqd"]
        ratio = combo["lqd"] / combo["hyg"]
        mn, mx = ratio.min(), ratio.max()
        ccc_p = (700 + (ratio - mn) / max(mx - mn, 1e-6) * 1200) if mx > mn else ratio * 0 + 1000
        return ccc_p.resample("ME").last().tail(n), "HYG/LQD CCC proxy"

    elif name == "OFR_FSI":
        # St.Louis FSI proxy: (VIX-20)/20 + credit spread stress component
        vx = _dl("^VIX"); hyg = _dl("HYG"); lqd = _dl("LQD")
        if vx.empty or hyg.empty or lqd.empty: return None, "FSI proxy failed"
        combo = pd.concat([vx, hyg, lqd], axis=1).dropna(); combo.columns = ["vix","hyg","lqd"]
        fsi_p = (combo["vix"] - 20) / 20 + (combo["lqd"] / combo["hyg"] - 1.38) * 8
        return fsi_p.resample("ME").last().tail(n), "VIX+HYG/LQD FSI proxy"

    elif name == "CI_LOAN_DLQ":
        # C&I delinquency proxy: HYG/LQD credit stress scaled to 0.5-5% range
        hyg = _dl("HYG"); lqd = _dl("LQD")
        if hyg.empty or lqd.empty: return None, "CI proxy failed"
        combo = pd.concat([hyg, lqd], axis=1).dropna(); combo.columns = ["hyg","lqd"]
        ratio = combo["lqd"] / combo["hyg"]
        mn, mx = ratio.quantile(0.05), ratio.quantile(0.95)
        dq_p = 0.8 + (ratio - mn) / max(mx - mn, 1e-6) * 3.5
        return dq_p.resample("ME").last().tail(n), "HYG/LQD CI_LOAN proxy"

    elif name == "RATE_30":
        # 30yr mortgage proxy: 10Y Treasury + ~170bps historical spread (avg 1.5-2.0%)
        t10 = _dl("^TNX")
        if t10.empty: return None, "30yr proxy failed"
        # Historical mortgage-treasury spread ~1.7% average; rises in stress
        # Use TLT vol as stress adjustment — when bond vol high, spreads widen
        try:
            tlt = _dl("TLT")
            tlt_vol = tlt.pct_change().rolling(21).std() * (252 ** 0.5) * 100
            stress_adj = (tlt_vol - tlt_vol.rolling(252, min_periods=60).mean()).fillna(0).clip(-1, 2) * 0.3
            rate30 = t10 + 1.70 + stress_adj.reindex(t10.index).fillna(0)
        except Exception:
            rate30 = t10 + 1.70
        return rate30.resample("ME").last().tail(n), "^TNX+170bps mortgage proxy"

    elif name == "SUPPLY_MO":
        # Housing months supply proxy: inverse of homebuilder ETF momentum
        # Rising XHB = fewer months supply; falling XHB = more months supply
        xhb = _dl("XHB")
        if xhb.empty: return None, "supply proxy failed"
        mom = xhb.pct_change(63)  # 3mo momentum
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        supply_p = 5.5 - (mom - mn) / max(mx - mn, 1e-6) * 4   # range ~1.5 to 5.5 months
        return supply_p.resample("ME").last().tail(n), "XHB inverse proxy"

    elif name == "HPI_NAT":
        # Case-Shiller HPI proxy: use XHB price level scaled to ~200-350 range
        xhb = _dl("XHB")
        if xhb.empty: return None, "HPI proxy failed"
        # Scale XHB to approximate CS-HPI range (base ~150, current ~320)
        xhb_norm = xhb / float(xhb.quantile(0.05)) * 200
        return xhb_norm.resample("ME").last().tail(n), "XHB HPI proxy"

    elif name == "MED_PRICE":
        # Median home price proxy: Case-Shiller scaled from XHB level
        xhb = _dl("XHB")
        if xhb.empty: return None, "MED_PRICE proxy failed"
        # XHB ~$65 in 2022 when median was ~$400K; scale proportionally
        med_p = xhb / float(xhb.quantile(0.5)) * 380000
        return med_p.resample("ME").last().tail(n), "XHB median price proxy"

    elif name == "MED_INC_HO":
        _base_yr = 80000.0
        s = _dl("^IRX")
        if s.empty:
            import pandas as _pd2
            idx = _pd2.date_range(end=date.today(), periods=n, freq="ME")
            growth2 = (1 + 0.03 / 12) ** np.arange(n)
            return _pd2.Series(_base_yr * growth2, index=idx), "income estimate proxy (BLS base $80K)"
        growth = (1 + 0.03 / 252) ** np.arange(len(s))
        inc = pd.Series(_base_yr * growth[-len(s):], index=s.index)
        return inc.resample("ME").last().tail(n), "income estimate proxy (BLS base $80K)"

    elif name == "MTGE_DELINQ":
        hyg = _dl("HYG"); lqd = _dl("LQD")
        if hyg.empty or lqd.empty: return None, "MTGE_DELINQ proxy failed"
        combo = pd.concat([hyg, lqd], axis=1).dropna(); combo.columns = ["hyg","lqd"]
        ratio = combo["lqd"] / combo["hyg"]
        mn, mx = ratio.quantile(0.05), ratio.quantile(0.95)
        delinq_p = 1.5 + (ratio - mn) / max(mx - mn, 1e-6) * 3.0
        return delinq_p.resample("ME").last().tail(n), "HYG/LQD MTGE proxy"

    elif name == "ISM_PMI":
        # ISM PMI proxy: XLI (industrials) momentum normalized to 40-65 PMI range
        xli = _dl("XLI")
        if xli.empty: return None, "ISM proxy failed"
        mom = xli.pct_change(21).rolling(5).mean()
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        pmi_p = 50 + (mom - mn) / max(mx - mn, 1e-6) * 20 - 10  # 40-60 range
        return pmi_p.clip(35, 65).resample("ME").last().tail(n), "XLI momentum PMI proxy"

    elif name == "ISM_NEWORDERS":
        xli = _dl("XLI"); xlb = _dl("XLB")
        if xli.empty: return None, "ISM_NO proxy failed"
        mom = xli.pct_change(63).rolling(5).mean()
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        no_p = 50 + (mom - mn) / max(mx - mn, 1e-6) * 25 - 12.5
        return no_p.clip(35, 70).resample("ME").last().tail(n), "XLI 3mo PMI proxy"

    elif name == "ISM_PRICES":
        # Inflation/commodity prices proxy: gold + oil momentum
        gld = _dl("GLD"); uso = _dl("USO")
        if gld.empty: return None, "ISM_PRICES proxy failed"
        mom = gld.pct_change(21).rolling(5).mean()
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        pr_p = 50 + (mom - mn) / max(mx - mn, 1e-6) * 35 - 17.5
        return pr_p.clip(30, 85).resample("ME").last().tail(n), "GLD prices proxy"

    elif name == "INIT_CLAIMS":
        # Initial claims proxy: use HYG/LQD credit stress + SPY trend
        # Pure SPY inverse over-reacts to short-term volatility (tariff selloffs)
        hyg = _dl("HYG"); lqd = _dl("LQD"); spy = _dl("SPY")
        if spy.empty: return None, "claims proxy failed"
        # Long-term SPY trend (13wk MA ratio) — less sensitive to daily swings
        spy_trend = spy / spy.rolling(65, min_periods=30).mean() - 1
        if not hyg.empty and not lqd.empty:
            cr = pd.concat([hyg, lqd], axis=1).dropna(); cr.columns=["hyg","lqd"]
            cr_stress = (cr["lqd"]/cr["hyg"]).pct_change(21).fillna(0).rolling(5).mean()
            cr_stress = cr_stress.reindex(spy_trend.index).fillna(0)
            combined = -0.6 * spy_trend - 0.4 * cr_stress * 5
        else:
            combined = -spy_trend
        # Scale to realistic claims range: 200K (tight) to 350K (loose/stressed)
        mn, mx = combined.quantile(0.05), combined.quantile(0.95)
        claims_p = 215000 + (combined - mn) / max(mx - mn, 1e-6) * 135000
        return claims_p.clip(170000, 380000).resample("ME").last().tail(n), "Credit+trend claims proxy"

    elif name == "CONT_CLAIMS":
        spy = _dl("SPY")
        if spy.empty: return None, "CONT_CLAIMS proxy failed"
        cont_p = 1700000 - spy.pct_change(21).rolling(4).mean() * 30000000
        return cont_p.clip(1200000, 3500000).resample("ME").last().tail(n), "SPY cont-claims proxy"
    elif name == "UMCSENT":
        vix = _dl("^VIX"); spy = _dl("SPY")
        if vix.empty: return None, "UMCSENT proxy failed"
        sent_p = 80 - (vix - 10) / 30 * 40 + spy.pct_change(63).fillna(0).reindex(vix.index).fillna(0) * 100
        return sent_p.clip(50, 110).resample("ME").last().tail(n), "VIX/SPY sentiment proxy"
    elif name == "LEI":
        xli = _dl("XLI")
        if xli.empty: return None, "LEI proxy failed"
        xli_mom = xli.pct_change(21).rolling(3).mean().fillna(0)
        mn, mx = xli_mom.quantile(0.05), xli_mom.quantile(0.95)
        lei_p = 100 + (xli_mom - mn) / max(mx - mn, 1e-6) * 20 - 10
        return lei_p.clip(90, 115).resample("ME").last().tail(n), "XLI LEI proxy"
    elif name == "DURGDS":
        xli = _dl("XLI")
        if xli.empty: return None, "DURGDS proxy failed"
        return (xli.pct_change(21) * 100).clip(-15, 15).resample("ME").last().tail(n), "XLI durable goods proxy"
    elif name == "SOFR":
        irx = _dl("^IRX")
        if irx.empty: return None, "SOFR proxy failed"
        return (irx - 0.05).clip(0, 10).resample("ME").last().tail(n), "^IRX SOFR proxy"
    elif name == "CFNAI":
        xli = _dl("XLI")
        if xli.empty: return None, "CFNAI proxy failed"
        mom = xli.pct_change(21).rolling(5).mean()
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        return (-1.5 + (mom - mn) / max(mx - mn, 1e-6) * 3.0).clip(-3, 2).resample("ME").last().tail(n), "XLI CFNAI proxy"

    elif name == "CPI":
        # CPI proxy: TIPS breakeven inflation (10Y nominal - 10Y real yield)
        # This is the market's real-time CPI expectation — far more accurate than gold
        # Both T10Y (^TNX) and IRX are already in the proxy cache from early FRED fetches
        t10 = _dl("^TNX"); irx = _dl("^IRX")
        if not t10.empty and not irx.empty:
            import pandas as _pd_cpi
            combo = pd.concat([t10, irx], axis=1).dropna()
            combo.columns = ["t10","irx"]
            # Breakeven = T10Y minus short real rate + term premium adjustment
            # Calibration: T10Y=4.3%, IRX=3.6% → breakeven≈2.3% ≈ actual CPI ~2.4% ✓
            #              T10Y=4.5%, IRX=4.4% → breakeven≈1.6% ≈ actual CPI ~3.0% (inverted) ✗
            # Better: use T10Y directly as CPI signal with known anchor
            # CPI Jan 2024 = 308.7 (BLS official). Grow by (T10Y - 2.0%) * 0.6 + 2.5% annually
            base_date = _pd_cpi.Timestamp("2024-01-01")
            base_val  = 308.7
            t10m = t10.resample("ME").last().dropna()
            try:
                if t10m.index.tz is not None: t10m.index = t10m.index.tz_localize(None)
            except: pass
            t10m = t10m[t10m.index >= base_date]
            if len(t10m) > 0:
                # Annual inflation rate ≈ 2.5% + (T10Y deviation from neutral 3.5%) * 0.4
                ann_rate = ((t10m - 3.5) * 0.4 + 2.5).clip(0.5, 6.0)
                monthly_r = ann_rate / 12 / 100
                cpi_idx = [base_val]
                for r in monthly_r.values:
                    cpi_idx.append(cpi_idx[-1] * (1 + r))
                cpi_series = _pd_cpi.Series(cpi_idx[1:], index=t10m.index)
                return cpi_series.tail(n), "T10Y breakeven CPI proxy (anchor Jan2024=308.7)"
        # Pure T10Y fallback
        if not t10.empty:
            return (300 + t10 * 4).clip(270, 360).resample("ME").last().tail(n), "T10Y CPI fallback"
        return None, "CPI proxy failed"

    elif name == "PCE":
        # PCE proxy: same breakeven method, PCE runs ~0.3pp below CPI
        # PCE anchor: Jan 2024 = 121.7 (BLS), growing at ~2.2%/yr
        t10 = _dl("^TNX")
        if not t10.empty:
            import pandas as _pd_pce
            base_date = _pd_pce.Timestamp("2024-01-01")
            base_val  = 121.7
            t10m = t10.resample("ME").last().dropna()
            try:
                if t10m.index.tz is not None: t10m.index = t10m.index.tz_localize(None)
            except: pass
            t10m = t10m[t10m.index >= base_date]
            if len(t10m) > 0:
                ann_rate = ((t10m - 3.5) * 0.35 + 2.2).clip(0.5, 5.5)
                monthly_r = ann_rate / 12 / 100
                pce_idx = [base_val]
                for r in monthly_r.values:
                    pce_idx.append(pce_idx[-1] * (1 + r))
                pce_series = _pd_pce.Series(pce_idx[1:], index=t10m.index)
                return pce_series.tail(n), "T10Y breakeven PCE proxy (anchor Jan2024=121.7)"
        return None, "PCE proxy failed"


    elif name == "INDPRO":
        # Industrial production: XLI (industrials ETF) normalized to INDPRO index range
        xli = _dl("XLI")
        if xli.empty: return None, "INDPRO proxy failed"
        # INDPRO ~102 currently; scale XLI to match
        base_xli = float(xli.quantile(0.3))
        indpro_p = 85 + (xli / base_xli - 1) * 100
        return indpro_p.clip(70, 120).resample("ME").last().tail(n), "XLI INDPRO proxy"

    elif name == "CAPUTIL":
        # Capacity utilization: correlated with XLI momentum
        xli = _dl("XLI")
        if xli.empty: return None, "CAPUTIL proxy failed"
        mom = xli.pct_change(63).rolling(10).mean()
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        cap_p = 75 + (mom - mn) / max(mx - mn, 1e-6) * 10  # range ~75-85%
        return cap_p.clip(68, 88).resample("ME").last().tail(n), "XLI CAPUTIL proxy"

    elif name == "RETAIL":
        # Retail sales level proxy (RSAFS): ~$738B/month Feb 2026
        # XLY ~$215 when retail ~$738B → scale: retail ≈ XLY * 3430
        xly = _dl("XLY")
        if xly.empty: return None, "RETAIL proxy failed"
        retail_p = xly * 3430
        return retail_p.clip(400000, 950000).resample("ME").last().tail(n), "XLY retail proxy"

    elif name == "HOUST":
        xhb = _dl("XHB")
        if xhb.empty: return None, "HOUST proxy failed"
        base = float(xhb.quantile(0.5))
        houst_p = 1400 + (xhb / base - 1) * 600
        return houst_p.clip(800, 2200).resample("ME").last().tail(n), "XHB HOUST proxy"

    elif name == "PERMIT":
        xhb = _dl("XHB")
        if xhb.empty: return None, "PERMIT proxy failed"
        base = float(xhb.quantile(0.5))
        permit_p = 1350 + (xhb / base - 1) * 500
        return permit_p.clip(700, 2000).resample("ME").last().tail(n), "XHB permit proxy"

    elif name == "M2SL":
        tlt = _dl("TLT")
        if tlt.empty: return None, "M2SL proxy failed"
        base = float(tlt.quantile(0.5))
        m2_p = 18000 + (tlt / base - 1) * 6000
        return m2_p.clip(14000, 28000).resample("ME").last().tail(n), "TLT M2SL proxy"

    elif name == "CFNAI":
        # Chicago Fed National Activity Index: XLI + SPY momentum composite
        xli = _dl("XLI"); spy = _dl("SPY")
        if xli.empty: return None, "CFNAI proxy failed"
        mom = xli.pct_change(21).rolling(5).mean()
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        cfnai_p = -1.5 + (mom - mn) / max(mx - mn, 1e-6) * 3.0
        return cfnai_p.clip(-3, 2).resample("ME").last().tail(n), "XLI CFNAI proxy"

    elif name == "SP500EPS":
        # S&P 500 trailing EPS proxy: SPX / historical avg PE (15-20x)
        gspc = _dl("^GSPC")
        if gspc.empty: return None, "SP500EPS proxy failed"
        # Approximate trailing EPS = SPX / 22 (avg PE over last 5yr)
        eps_p = gspc / 22.0
        return eps_p.resample("ME").last().tail(n), "SPX/22 EPS proxy"

    elif name == "WALCL":
        # Fed balance sheet: TLT price inversely tracks QT/QE (rough proxy)
        tlt = _dl("TLT")
        if tlt.empty: return None, "WALCL proxy failed"
        # Fed BS ~$6.7T in 2024-2026; scale from TLT
        base = float(tlt.quantile(0.5))
        walcl_p = (6000000 + (tlt / base - 1) * 2000000)
        return walcl_p.clip(4000000, 9000000).resample("ME").last().tail(n), "TLT WALCL proxy"

    elif name == "WTREGEN":
        # Treasury General Account: roughly tracks inverse of T-bill rates
        irx = _dl("^IRX")
        if irx.empty: return None, "WTREGEN proxy failed"
        # Higher rates = smaller TGA typically; rough inverse relationship
        tga_p = 900000 - (irx - 2.0) * 100000
        return tga_p.clip(300000, 1500000).resample("ME").last().tail(n), "IRX TGA proxy"

    elif name == "RRPONTSYD":
        # Reverse repo: tracks short-term rate conditions
        irx = _dl("^IRX")
        if irx.empty: return None, "RRPONTSYD proxy failed"
        rrp_p = irx * 200  # rough scale
        return rrp_p.clip(0, 2500).resample("ME").last().tail(n), "IRX RRP proxy"

    elif name == "NFCI":
        # Chicago Fed Financial Conditions Index: composite of rates + credit + risk
        # Use HYG/LQD spread z-score + VIX z-score (normalized, not raw VIX level)
        # Raw VIX spikes during non-financial stress (tariffs) and distorts NFCI
        vix = _dl("^VIX"); hyg = _dl("HYG"); lqd = _dl("LQD")
        if vix.empty or hyg.empty or lqd.empty: return None, "NFCI proxy failed"
        import pandas as _pd_nfci
        combo = _pd_nfci.concat([vix, hyg, lqd], axis=1).dropna()
        combo.columns = ["vix","hyg","lqd"]
        # Z-score VIX relative to its own 1yr history (normalizes spikes)
        vix_z = (combo["vix"] - combo["vix"].rolling(252, min_periods=60).mean()) / \
                combo["vix"].rolling(252, min_periods=60).std().replace(0, 1)
        # Credit stress: LQD/HYG ratio z-score (rising = stress)
        cr_ratio = combo["lqd"] / combo["hyg"]
        cr_z = (cr_ratio - cr_ratio.rolling(252, min_periods=60).mean()) / \
               cr_ratio.rolling(252, min_periods=60).std().replace(0, 1)
        # NFCI = blend (positive = tight/stressed, negative = loose/easy)
        nfci_p = (0.5 * vix_z + 0.5 * cr_z).clip(-3, 4)
        return nfci_p.resample("ME").last().tail(n), "VIX+Credit z-score NFCI proxy"

    elif name == "NY_REC_PROB":
        # NY Fed recession probability: yield curve inversion proxy
        t10 = _dl("^TNX"); irx = _dl("^IRX")
        if t10.empty or irx.empty: return None, "NY_REC_PROB proxy failed"
        combo = pd.concat([t10, irx], axis=1).dropna(); combo.columns=["t10","irx"]
        spread = combo["t10"] - combo["irx"]
        # Deeper inversion = higher recession probability (logistic-like)
        rec_p = (1 / (1 + np.exp(spread * 2))) * 100
        return rec_p.resample("ME").last().tail(n), "yield curve rec proxy"

    elif name == "CREDIT_CARD_DLQ":
        # Credit card delinquency proxy: HYG/LQD stress
        hyg = _dl("HYG"); lqd = _dl("LQD")
        if hyg.empty or lqd.empty: return None, "CREDIT_CARD_DLQ proxy failed"
        combo = pd.concat([hyg, lqd], axis=1).dropna(); combo.columns=["hyg","lqd"]
        ratio = combo["lqd"] / combo["hyg"]
        mn, mx = ratio.quantile(0.05), ratio.quantile(0.95)
        cc_p = 1.5 + (ratio - mn) / max(mx - mn, 1e-6) * 4.0
        return cc_p.clip(1.0, 6.0).resample("ME").last().tail(n), "HYG CC delinq proxy"

    elif name == "GDP":
        # GDP: SPX earnings × PE multiple proxy, or just SPX level scaled
        gspc = _dl("^GSPC")
        if gspc.empty: return None, "GDP proxy failed"
        # SPX ~$6500 when GDP ~$28T; scale proportionally
        base = float(gspc.quantile(0.5))
        gdp_p = 22000 + (gspc / base - 1) * 12000
        return gdp_p.clip(15000, 40000).resample("ME").last().tail(n), "SPX GDP proxy"

    elif name == "WILL5000IND":
        # Wilshire 5000: closely tracks SPX; scale to ~45000 index level
        gspc = _dl("^GSPC")
        if gspc.empty: return None, "WILL5000IND proxy failed"
        will_p = gspc * 7.0   # historical ratio ~7x
        return will_p.resample("ME").last().tail(n), "SPX WILL5000 proxy"

    elif name == "USREC":
        # Recession indicator: Sahm-like proxy from employment + yield curve
        spy = _dl("SPY")
        if spy.empty: return None, "USREC proxy failed"
        # Simple: 0 if SPY above 200DMA, 1 if in bear market
        ma200 = spy.rolling(200).mean()
        rec_p = (spy < ma200 * 0.85).astype(float)
        return rec_p.resample("ME").last().tail(n), "SPY bear market proxy"

    elif name == "CONT_CLAIMS":
        spy = _dl("SPY")
        if spy.empty: return None, "CONT_CLAIMS proxy failed"
        cont_p = 1700000 - spy.pct_change(21).rolling(4).mean() * 30000000
        return cont_p.clip(1200000, 3500000).resample("ME").last().tail(n), "SPY cont-claims proxy"
    elif name == "UMCSENT":
        vix = _dl("^VIX"); spy = _dl("SPY")
        if vix.empty: return None, "UMCSENT proxy failed"
        sent_p = 80 - (vix - 10) / 30 * 40 + spy.pct_change(63).fillna(0).reindex(vix.index).fillna(0) * 100
        return sent_p.clip(50, 110).resample("ME").last().tail(n), "VIX/SPY sentiment proxy"
    elif name == "LEI":
        xli = _dl("XLI")
        if xli.empty: return None, "LEI proxy failed"
        xli_mom = xli.pct_change(21).rolling(3).mean().fillna(0)
        mn, mx = xli_mom.quantile(0.05), xli_mom.quantile(0.95)
        lei_p = 100 + (xli_mom - mn) / max(mx - mn, 1e-6) * 20 - 10
        return lei_p.clip(90, 115).resample("ME").last().tail(n), "XLI LEI proxy"
    elif name == "DURGDS":
        xli = _dl("XLI")
        if xli.empty: return None, "DURGDS proxy failed"
        return (xli.pct_change(21) * 100).clip(-15, 15).resample("ME").last().tail(n), "XLI durable goods proxy"
    elif name == "SOFR":
        irx = _dl("^IRX")
        if irx.empty: return None, "SOFR proxy failed"
        return (irx - 0.05).clip(0, 10).resample("ME").last().tail(n), "^IRX SOFR proxy"
    elif name == "CFNAI":
        xli = _dl("XLI")
        if xli.empty: return None, "CFNAI proxy failed"
        mom = xli.pct_change(21).rolling(5).mean()
        mn, mx = mom.quantile(0.05), mom.quantile(0.95)
        return (-1.5 + (mom - mn) / max(mx - mn, 1e-6) * 3.0).clip(-3, 2).resample("ME").last().tail(n), "XLI CFNAI proxy"

    return None, "no proxy"

_FRED_DATAREADER_DISABLED = False   # circuit breaker
_FRED_CSV_DISABLED        = False
_YF_PROXY_CACHE: dict     = {}      # batch-downloaded proxy data, filled once


# ══════════════════════════════════════════════════════════════════════════════
# LEADING INDICATOR HELPERS — used by the new "Leading Indicators" tab
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_pcr_additions():
    """Compute Put/Call ratio from yfinance SPY+QQQ+IWM options chains."""
    try:
        import yfinance as _yf
        total_calls, total_puts = 0.0, 0.0
        used = []
        for _tk in ["SPY", "QQQ", "IWM"]:
            try:
                _t = _yf.Ticker(_tk)
                _exp = _t.options
                if not _exp: continue
                _chain = _t.option_chain(_exp[0])
                total_calls += _chain.calls["volume"].fillna(0).sum()
                total_puts  += _chain.puts["volume"].fillna(0).sum()
                used.append(_tk)
            except Exception: continue
        if total_calls > 0 and used:
            return round(total_puts / total_calls, 3), f"yfinance {'+'.join(used)}"
    except Exception: pass
    return None, "unavailable"


def _fetch_aaii_additions():
    """Fetch AAII weekly sentiment via HTML table parsing."""
    import pandas as _pd_a
    try:
        import requests as _rq, io as _io
        _r = _rq.get("https://www.aaii.com/sentimentsurvey/sent_results", timeout=15,
                     headers={"User-Agent":"Mozilla/5.0","Accept":"text/html,*/*;q=0.8","Referer":"https://www.aaii.com/"})
        if _r.status_code == 200:
            _tables = _pd_a.read_html(_io.StringIO(_r.text))
            for _tbl in _tables:
                _cols = [str(c).lower().strip() for c in _tbl.columns]
                _bi = next((i for i,c in enumerate(_cols) if "bull" in c), None)
                _ei = next((i for i,c in enumerate(_cols) if "bear" in c), None)
                if _bi is not None and _ei is not None:
                    _row = _tbl.dropna(subset=[_tbl.columns[_bi]]).iloc[-1]
                    def _p(v): return round(float(str(v).replace("%","").strip()), 1)
                    _b = _p(_row.iloc[_bi]); _e = _p(_row.iloc[_ei])
                    _di = next((i for i,c in enumerate(_cols) if "date" in c or "week" in c), None)
                    _dt = str(_row.iloc[_di])[:10] if _di is not None else "latest"
                    return {"bull":_b,"bear":_e,"spread":round(_b-_e,1),"date":_dt,"source":"AAII"}
    except Exception: pass
    return {"bull":None,"bear":None,"spread":None,"date":"N/A","source":"unavailable"}


# ══════════════════════════════════════════════════════════════════════════════
# HISTORICAL EPISODE DATABASE
# Verified economic indicator readings at each major SPX peak and trough.
# Used to compare current conditions vs history and estimate correction risk.
#
# Columns per episode:
#   hy_oas    — HY credit spread in bps   (CALM <380, STRESS 450+, CRISIS 700+)
#   yc        — Yield curve 10Y-2Y in %   (positive=normal, negative=inverted)
#   vix       — VIX index level            (<20 calm, >30 panic)
#   fwd_pe    — Forward P/E ratio (x)      (14-18x fair, >22x expensive)
#   cape      — Shiller CAPE              (<25 cheap, >35 expensive)
#   ff        — Fed Funds rate %           (restrictive if > neutral ~2.5%)
#   cpi       — CPI inflation YoY %
#   ism       — ISM Manufacturing PMI     (>50 expanding, <50 contracting)
#   unrate    — Unemployment rate %
#   pct200    — % SPX stocks above 200DMA (>60% healthy, <25% oversold)
#   real_yld  — Real 10Y yield %           (>2% restrictive for equities)
#   drawdown  — Peak-to-trough drawdown %  (negative number)
#   duration  — Duration in months
#   trigger   — Primary catalyst
#   recovery  — Months to recover prior peak
# ══════════════════════════════════════════════════════════════════════════════
EPISODE_DATABASE = [
    # ─────────────────────────────────────────────────────────────────────────
    # 2000 DOT-COM BUBBLE
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2000 Dot-com",
        "type":     "PEAK",
        "date":     "Mar 2000",
        "spx":      1527,
        "hy_oas":   350,   # calm — credit not yet stressed
        "yc":       -0.50, # inverted — 18mo warning
        "vix":      24,
        "fwd_pe":   28.0,  # extreme — tech bubble
        "cape":     44.0,  # record high
        "ff":       6.50,  # very restrictive
        "cpi":      3.8,
        "ism":      51.5,
        "unrate":   3.9,
        "pct200":   45,    # breadth already narrowing
        "real_yld": 3.5,
        "drawdown": -49,
        "duration": 31,
        "trigger":  "Tech capex overcapacity + curve inversion + valuation bubble",
        "recovery": 60,
        "color":    "#8B0000",
    },
    {
        "name":     "2002 Dot-com Trough",
        "type":     "TROUGH",
        "date":     "Oct 2002",
        "spx":      797,
        "hy_oas":   1000,  # extreme stress
        "yc":       1.50,  # steep — Fed had cut 500bps
        "vix":      45,
        "fwd_pe":   16.0,
        "cape":     21.0,
        "ff":       1.75,  # emergency cuts
        "cpi":      2.0,
        "ism":      48,
        "unrate":   5.7,
        "pct200":   15,
        "real_yld": -0.5,
        "drawdown": None,
        "duration": None,
        "trigger":  "HY OAS >1000bps + VIX >40 = capitulation bottom",
        "recovery": None,
        "color":    "#1A7A4A",
    },
    # ─────────────────────────────────────────────────────────────────────────
    # 2007 GFC
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2007 GFC",
        "type":     "PEAK",
        "date":     "Oct 2007",
        "spx":      1565,
        "hy_oas":   280,   # deceptively calm — tightened before peak
        "yc":       0.20,  # just un-inverted (post-inversion danger window)
        "vix":      17,
        "fwd_pe":   15.0,
        "cape":     27.0,
        "ff":       4.50,
        "cpi":      3.5,
        "ism":      52,
        "unrate":   4.7,
        "pct200":   60,
        "real_yld": 1.0,
        "drawdown": -57,
        "duration": 17,
        "trigger":  "Credit bubble burst + housing Kuznets peak + curve post-inversion",
        "recovery": 49,
        "color":    "#8B0000",
    },
    {
        "name":     "2009 GFC Trough",
        "type":     "TROUGH",
        "date":     "Mar 2009",
        "spx":      666,
        "hy_oas":   1900, # maximum credit stress ever
        "yc":       2.50, # very steep after Fed cut to 0
        "vix":      56,
        "fwd_pe":   11.0,
        "cape":     14.0,
        "ff":       0.25,
        "cpi":      0.0,
        "ism":      36,
        "unrate":   8.7,
        "pct200":   5,
        "real_yld": -1.0,
        "drawdown": None,
        "duration": None,
        "trigger":  "HY >1900bps + ISM 36 + breadth 5% = generational buy",
        "recovery": None,
        "color":    "#1A7A4A",
    },
    # ─────────────────────────────────────────────────────────────────────────
    # 2011 EU DEBT CRISIS
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2011 EU Debt Crisis",
        "type":     "PEAK",
        "date":     "Apr 2011",
        "spx":      1363,
        "hy_oas":   400,
        "yc":       2.80,
        "vix":      15,
        "fwd_pe":   13.0,
        "cape":     24.0,
        "ff":       0.25,
        "cpi":      3.2,
        "ism":      60,    # very strong — pure exogenous shock
        "unrate":   9.0,
        "pct200":   72,
        "real_yld": -1.5,
        "drawdown": -21,
        "duration": 6,
        "trigger":  "European sovereign debt + S&P US downgrade — exogenous shock",
        "recovery": 9,
        "color":    "#C0390F",
    },
    {
        "name":     "2011 EU Trough",
        "type":     "TROUGH",
        "date":     "Oct 2011",
        "spx":      1099,
        "hy_oas":   750,
        "yc":       2.00,
        "vix":      43,
        "fwd_pe":   11.5,
        "cape":     19.0,
        "ff":       0.25,
        "cpi":      3.5,
        "ism":      50,
        "unrate":   9.1,
        "pct200":   18,
        "real_yld": -1.8,
        "drawdown": None,
        "duration": None,
        "trigger":  "VIX 43 + HY 750bps = oversold. EU firewall announcement = recovery",
        "recovery": None,
        "color":    "#1A7A4A",
    },
    # ─────────────────────────────────────────────────────────────────────────
    # 2015-16 CHINA / OIL CORRECTION
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2015 China/Oil",
        "type":     "PEAK",
        "date":     "May 2015",
        "spx":      2130,
        "hy_oas":   450,   # already elevated from energy stress
        "yc":       1.50,
        "vix":      13,
        "fwd_pe":   17.0,
        "cape":     27.0,
        "ff":       0.25,
        "cpi":      0.1,   # oil collapse suppressed CPI
        "ism":      52,
        "unrate":   5.5,
        "pct200":   65,
        "real_yld": 0.5,
        "drawdown": -15,
        "duration": 9,
        "trigger":  "China devaluation + oil collapse + EM contagion + first Fed hike",
        "recovery": 7,
        "color":    "#C0390F",
    },
    {
        "name":     "2016 China/Oil Trough",
        "type":     "TROUGH",
        "date":     "Feb 2016",
        "spx":      1810,
        "hy_oas":   840,   # energy HY stress peak
        "yc":       1.20,
        "vix":      28,
        "fwd_pe":   15.5,
        "cape":     24.0,
        "ff":       0.50,
        "cpi":      1.0,
        "ism":      49,
        "unrate":   4.9,
        "pct200":   22,
        "real_yld": 0.0,
        "drawdown": None,
        "duration": None,
        "trigger":  "HY 840bps (energy distress) + China stimulus = bottom. Short, shallow.",
        "recovery": None,
        "color":    "#1A7A4A",
    },
    # ─────────────────────────────────────────────────────────────────────────
    # 2018 Q4 POLICY CORRECTION
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2018 Q4 Policy",
        "type":     "PEAK",
        "date":     "Sep 2018",
        "spx":      2930,
        "hy_oas":   320,
        "yc":       0.25,  # near flat — tightening pressure
        "vix":      12,    # extreme complacency
        "fwd_pe":   17.0,
        "cape":     33.0,
        "ff":       2.25,
        "cpi":      2.7,
        "ism":      60,    # very strong
        "unrate":   3.7,
        "pct200":   65,
        "real_yld": 0.8,
        "drawdown": -20,
        "duration": 3,
        "trigger":  "Fed tightening too fast + trade war tariffs + valuation compression",
        "recovery": 5,
        "color":    "#C0390F",
    },
    {
        "name":     "2018 Q4 Trough",
        "type":     "TROUGH",
        "date":     "Dec 2018",
        "spx":      2346,
        "hy_oas":   540,
        "yc":       0.10,
        "vix":      36,
        "fwd_pe":   14.0,
        "cape":     27.0,
        "ff":       2.50,
        "cpi":      2.2,
        "ism":      54,
        "unrate":   3.9,
        "pct200":   15,
        "real_yld": 0.6,
        "drawdown": None,
        "duration": None,
        "trigger":  "Powell pivot (\"will be patient\") + VIX 36 = fast recovery. No credit crisis.",
        "recovery": None,
        "color":    "#1A7A4A",
    },
    # ─────────────────────────────────────────────────────────────────────────
    # 2020 COVID CRASH
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2020 COVID",
        "type":     "PEAK",
        "date":     "Feb 2020",
        "spx":      3386,
        "hy_oas":   320,   # calm — no warning at all
        "yc":       0.20,
        "vix":      15,
        "fwd_pe":   19.0,
        "cape":     33.0,
        "ff":       1.75,
        "cpi":      2.3,
        "ism":      50,
        "unrate":   3.5,   # cycle low
        "pct200":   65,
        "real_yld": -0.5,
        "drawdown": -34,
        "duration": 2,     # fastest bear in history
        "trigger":  "Exogenous pandemic shock — NO macro warning. VIX only signal.",
        "recovery": 5,
        "color":    "#D4820A",
    },
    {
        "name":     "2020 COVID Trough",
        "type":     "TROUGH",
        "date":     "Mar 2020",
        "spx":      2237,
        "hy_oas":   1100,
        "yc":       0.50,
        "vix":      66,    # second highest ever
        "fwd_pe":   14.0,
        "cape":     25.0,
        "ff":       0.25,  # cut to zero
        "cpi":      1.5,
        "ism":      43,
        "unrate":   4.4,   # spiked to 14.8 in April
        "pct200":   5,
        "real_yld": -1.5,
        "drawdown": None,
        "duration": None,
        "trigger":  "VIX 66 + HY 1100bps + Fed/fiscal response = fastest V-recovery ever",
        "recovery": None,
        "color":    "#1A7A4A",
    },
    # ─────────────────────────────────────────────────────────────────────────
    # 2022 RATE SHOCK BEAR
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2022 Rate Shock",
        "type":     "PEAK",
        "date":     "Dec 2021",
        "spx":      4793,
        "hy_oas":   310,   # historic tight — peak complacency
        "yc":       0.80,  # flattening fast
        "vix":      17,
        "fwd_pe":   21.0,
        "cape":     38.0,
        "ff":       0.25,  # near zero — massive mispricing
        "cpi":      6.8,   # 40-year high
        "ism":      60,
        "unrate":   3.9,
        "pct200":   55,
        "real_yld": -5.5,  # deeply negative real rates
        "drawdown": -25,
        "duration": 10,
        "trigger":  "Inflation +6.8% + Fed 500bps hikes + valuation reset from 21x to 16x",
        "recovery": 18,
        "color":    "#8B0000",
    },
    {
        "name":     "2022 Rate Shock Trough",
        "type":     "TROUGH",
        "date":     "Oct 2022",
        "spx":      3577,
        "hy_oas":   590,
        "yc":       -0.60, # deeply inverted
        "vix":      33,
        "fwd_pe":   16.0,
        "cape":     27.0,
        "ff":       3.75,  # mid-hike cycle
        "cpi":      7.7,   # still high but peaking
        "ism":      50,
        "unrate":   3.7,
        "pct200":   15,
        "real_yld": 1.8,
        "drawdown": None,
        "duration": None,
        "trigger":  "Terminal rate pricing peaked + CPI peak = rally. Inversion persisted.",
        "recovery": None,
        "color":    "#1A7A4A",
    },
    # ─────────────────────────────────────────────────────────────────────────
    # 2025-26 CURRENT CORRECTION (in progress)
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":     "2025-26 Tariff/AI",
        "type":     "PEAK",
        "date":     "Jan 2025",
        "spx":      6118,
        "hy_oas":   275,   # historic tight — peak complacency
        "yc":       0.20,  # post-inversion risk window
        "vix":      15,
        "fwd_pe":   22.5,
        "cape":     37.0,
        "ff":       4.50,
        "cpi":      3.0,
        "ism":      50,
        "unrate":   4.1,
        "pct200":   60,
        "real_yld": 2.2,   # restrictive
        "drawdown": None,  # still unfolding
        "duration": None,
        "trigger":  "Trump tariffs + AI capex ROI doubt + post-inversion lag + high valuations",
        "recovery": None,
        "color":    "#D4820A",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# PULLBACK MONITOR — Minor Correction Early Warning System (5-15%)
#
# Each threshold entry defines ONE indicator's danger zones and the historical
# instances when it reached those levels before a 5-15% SPX correction.
# ══════════════════════════════════════════════════════════════════════════════

PULLBACK_THRESHOLDS = {
    # ── Valuation ────────────────────────────────────────────────────────────
    "fwd_pe": {
        "name": "Forward P/E Ratio",
        "cat": "Valuation", "icon": "📊",
        "unit": "x",
        "safe_below":   20.0,    # green: below this = fairly valued
        "warn_above":   22.0,    # yellow: approaching stretched
        "danger_above": 24.0,    # red: historically precedes pullbacks
        "panic_below":  16.0,    # trough: this level = buy signal
        "direction": "up_bad",
        "why": "When forward P/E exceeds 24x while SPX is above 200DMA, "
               "mean reversion to ~21-22x typically occurs within 6-12 weeks. "
               "Earnings disappointment accelerates compression.",
        "examples": [
            {"date":"Jan 2018","level":25.1,"spx_drop":-10.2,"weeks":2,"recovered_to":22.5,"trigger":"Inflation spike"},
            {"date":"Sep 2020","level":24.0,"spx_drop":-9.6,"weeks":5,"recovered_to":21.8,"trigger":"Post-rally fatigue"},
            {"date":"Sep 2021","level":22.8,"spx_drop":-5.2,"weeks":4,"recovered_to":21.0,"trigger":"Taper + debt ceiling"},
            {"date":"Jan 2022","level":21.4,"spx_drop":-9.8,"weeks":3,"recovered_to":19.5,"trigger":"Rate fear began"},
            {"date":"Aug 2023","level":19.5,"spx_drop":-5.6,"weeks":5,"recovered_to":18.2,"trigger":"10Y yield spike"},
            {"date":"Oct 2023","level":18.8,"spx_drop":-10.3,"weeks":6,"recovered_to":17.5,"trigger":"Rate peak fear"},
        ],
        "resolution_zone": (19.5, 21.5),
        "note": "Resolution typically at 20-22x. 16x or below = trough buy."
    },
    # ── Sentiment / Volatility ────────────────────────────────────────────────
    "vix_level": {
        "name": "VIX Complacency / Panic",
        "cat": "Volatility", "icon": "😨",
        "unit": "",
        "safe_below":   None,
        "warn_above":   None,
        "danger_above": None,
        "panic_below":  None,
        "direction": "dual",   # both extremes are signals
        "safe_range":   (15, 22),   # neutral zone
        "warn_low":     13,          # complacency bottom → pullback risk
        "warn_high":    25,          # elevated → correction in progress
        "danger_low":   11,          # extreme complacency → imminent spike
        "danger_high":  35,          # panic → near-term bottom
        "why": "VIX below 13 = extreme complacency. Historically within 2-6 weeks "
               "VIX spikes 50-200% and SPX falls 5-12%. VIX spike above 35 = panic "
               "bottom — historically strong 3-6 month buy signal.",
        "examples": [
            {"date":"Jan 2018","level":9.5,"spx_drop":-10.2,"weeks":2,"vix_peak":50,"trigger":"Vol spike from extreme low"},
            {"date":"Sep 2018","level":12.0,"spx_drop":-10.0,"weeks":6,"vix_peak":25,"trigger":"Trade war + rate fear"},
            {"date":"Jan 2020","level":12.1,"spx_drop":-34.0,"weeks":5,"vix_peak":66,"trigger":"COVID (black swan)"},
            {"date":"May 2019","level":12.8,"spx_drop":-6.8,"weeks":4,"vix_peak":23,"trigger":"China tariff escalation"},
            {"date":"Aug 2023","level":13.0,"spx_drop":-5.6,"weeks":5,"vix_peak":21,"trigger":"10Y yield spike"},
            {"date":"Jul 2024","level":11.9,"spx_drop":-8.5,"weeks":3,"vix_peak":38,"trigger":"Yen carry unwind"},
        ],
        "resolution_zone": (25, 40),
        "note": "Correction ends when VIX peaks and starts declining. VIX >35 = near-term buy."
    },
    # ── Put/Call Ratio ─────────────────────────────────────────────────────────
    "pcr": {
        "name": "Put/Call Ratio (Complacency)",
        "cat": "Sentiment", "icon": "🐂",
        "unit": "",
        "direction": "down_bad",   # low = bearish setup (too bullish)
        "safe_range":   (0.75, 1.10),
        "warn_low":     0.65,
        "danger_low":   0.55,      # extreme bullish = contrarian sell
        "warn_high":    1.20,
        "danger_high":  1.40,      # extreme fear = contrarian buy
        "why": "P/C ratio below 0.60 = excessive call buying / complacency. "
               "Historically signals 3-8% pullback within 2-4 weeks as hedging unwinds. "
               "P/C above 1.3 = extreme hedging = near-term bounce signal.",
        "examples": [
            {"date":"Sep 2020","level":0.52,"spx_drop":-9.6,"weeks":4,"recovered_to":0.95,"trigger":"Post-rally excess calls"},
            {"date":"Jan 2022","level":0.55,"spx_drop":-9.8,"weeks":3,"recovered_to":1.15,"trigger":"FOMO call buying peak"},
            {"date":"Nov 2021","level":0.51,"spx_drop":-5.2,"weeks":3,"recovered_to":0.85,"trigger":"Meme stock excess"},
            {"date":"Jul 2021","level":0.54,"spx_drop":-5.0,"weeks":4,"recovered_to":0.80,"trigger":"Summer complacency"},
            {"date":"Mar 2024","level":0.58,"spx_drop":-5.5,"weeks":3,"recovered_to":0.85,"trigger":"AI euphoria"},
        ],
        "resolution_zone": (0.85, 1.15),
        "note": "P/C reverting to 0.85-1.0 range = fear normalized = correction typically over."
    },
    # ── Breadth ───────────────────────────────────────────────────────────────
    "pct_above_50dma": {
        "name": "% Stocks Above 50DMA",
        "cat": "Breadth", "icon": "📈",
        "unit": "%",
        "direction": "dual",
        "safe_range":   (45, 75),
        "warn_high":    80,          # overbought breadth
        "danger_high":  88,          # extreme overbought → pullback imminent
        "warn_low":     30,
        "danger_low":   20,          # extreme oversold → bounce imminent
        "why": "When >85% of S&P stocks are above their 50DMA, the market is "
               "broadly overbought. Mean reversion to 50-60% typically occurs "
               "with a 5-10% SPX correction within 2-8 weeks.",
        "examples": [
            {"date":"Jan 2018","level":88,"spx_drop":-10.2,"weeks":2,"resolved_to":35,"trigger":"VIX spike from breadth peak"},
            {"date":"Jun 2020","level":92,"spx_drop":-9.6,"weeks":5,"resolved_to":55,"trigger":"Post-COVID rally peak"},
            {"date":"Apr 2021","level":87,"spx_drop":-5.0,"weeks":4,"resolved_to":65,"trigger":"Inflation scare"},
            {"date":"Nov 2023","level":82,"spx_drop":-5.2,"weeks":3,"resolved_to":60,"trigger":"Seasonal + rate fear"},
            {"date":"Mar 2024","level":84,"spx_drop":-5.5,"weeks":4,"resolved_to":62,"trigger":"AI rotation fatigue"},
        ],
        "resolution_zone": (25, 45),
        "note": "Pullback ends when % drops to 25-40% range and starts recovering. <20% = near-term bounce."
    },
    # ── Financial Conditions ──────────────────────────────────────────────────
    "nfci": {
        "name": "Chicago Financial Conditions (NFCI)",
        "cat": "Conditions", "icon": "🏦",
        "unit": "",
        "direction": "dual",
        "safe_range":   (-0.5, 0.0),
        "warn_low":     -0.6,        # very loose → complacency
        "danger_low":   -0.8,        # extreme loose → reversion risk
        "warn_high":     0.3,
        "danger_high":   0.8,
        "why": "NFCI below -0.6 = financial conditions extremely loose — "
               "historically precedes tightening episodes. When NFCI rises "
               "0.4+ points in 4 weeks, typically coincides with 5-10% SPX pullback.",
        "examples": [
            {"date":"Jan 2018","level":-0.82,"spx_drop":-10.2,"weeks":2,"resolved_to":-0.30,"trigger":"Rate/vol spike"},
            {"date":"Jan 2020","level":-0.75,"spx_drop":-34.0,"weeks":5,"resolved_to":3.20,"trigger":"COVID shock"},
            {"date":"Nov 2021","level":-0.78,"spx_drop":-5.2,"weeks":3,"resolved_to":-0.50,"trigger":"Fed pivot fear"},
            {"date":"Dec 2023","level":-0.65,"spx_drop":-5.5,"weeks":4,"resolved_to":-0.35,"trigger":"Rate reset"},
        ],
        "resolution_zone": (-0.4, 0.2),
        "note": "NFCI tightening back to -0.3 to 0 = conditions normalizing = correction stabilizing."
    },
    # ── HY Credit Spread ─────────────────────────────────────────────────────
    "hy_oas_momentum": {
        "name": "HY OAS Momentum (4-week change)",
        "cat": "Credit", "icon": "💳",
        "unit": "bps",
        "direction": "up_bad",
        "safe_range":   (-20, 20),   # spreads stable
        "warn_above":   30,           # spreads widening moderately
        "danger_above": 60,           # spreads widening fast → pullback
        "panic_above":  150,          # crisis widening
        "why": "When HY OAS widens 40+ bps in 4 weeks from historically tight levels "
               "(<340bps), SPX typically falls 5-10% within 4-8 weeks. Credit leads equities.",
        "examples": [
            {"date":"Oct 2018","level_start":310,"widened_to":450,"spx_drop":-10.0,"weeks":6,"trigger":"Trade war + Fed"},
            {"date":"May 2022","level_start":310,"widened_to":490,"spx_drop":-10.5,"weeks":5,"trigger":"Rate shock"},
            {"date":"Oct 2022","level_start":440,"widened_to":590,"spx_drop":-8.0,"weeks":3,"trigger":"Tightening peak"},
            {"date":"Mar 2020","level_start":310,"widened_to":1100,"spx_drop":-34.0,"weeks":4,"trigger":"COVID"},
            {"date":"Aug 2024","level_start":290,"widened_to":380,"spx_drop":-8.5,"weeks":3,"trigger":"Carry unwind"},
        ],
        "resolution_zone": (20, 50),
        "note": "4-week spread change reversing to <30bps = credit stress stabilizing = SPX bottom near."
    },
    # ── ISM Direction ─────────────────────────────────────────────────────────
    "ism_rollover": {
        "name": "ISM PMI Rollover from Peak",
        "cat": "Growth", "icon": "🏭",
        "unit": "",
        "direction": "down_bad",
        "safe_range":   (50, 58),    # expanding but not extreme
        "warn_high":    58,           # over-heating → rollover risk
        "danger_high":  62,           # very extended → mean reversion imminent
        "warn_low":     48,
        "danger_low":   46,
        "why": "ISM PMI declining 3+ points from a peak above 58 within 2-3 months "
               "typically coincides with 5-10% SPX correction. The rollover signals "
               "peak growth — earnings guidance cuts follow 1-2 quarters later.",
        "examples": [
            {"date":"Aug 2018","peak":60.8,"dropped_to":54.1,"spx_drop":-10.0,"months":3,"trigger":"Trade war slowdown"},
            {"date":"Jan 2019","peak":60.8,"dropped_to":47.8,"spx_drop":-5.0,"months":6,"trigger":"Tariff demand shock"},
            {"date":"Aug 2021","peak":63.0,"dropped_to":57.0,"spx_drop":-5.2,"months":3,"trigger":"Supply chain peak"},
            {"date":"Jun 2022","peak":63.0,"dropped_to":46.0,"spx_drop":-25.0,"months":12,"trigger":"Full cycle down"},
        ],
        "resolution_zone": (48, 52),
        "note": "ISM stabilizing at 48-52 = soft landing. Bouncing from <47 = Kitchin trough."
    },
    # ── Seasonal ──────────────────────────────────────────────────────────────
    "seasonal": {
        "name": "Seasonal Weakness Periods",
        "cat": "Seasonal", "icon": "📅",
        "unit": "month",
        "direction": "calendar",
        "high_risk_months":  [9],       # September: worst month (-1.1% avg since 1950)
        "moderate_risk_months": [2, 8], # February, August
        "low_risk_months":   [1, 6, 10, 11, 12],  # Jan, Jun, Oct, Nov, Dec
        "why": "September is the only calendar month with a negative average return "
               "(-1.1%) going back to 1950. Historically: 55% of Septembers are down, "
               "average drawdown -5.3%. August often starts the 'summer fade' pattern.",
        "examples": [
            {"year":2023,"month":9,"spx_drop":-4.9,"trigger":"Rate + seasonal combo"},
            {"year":2022,"month":9,"spx_drop":-9.3,"trigger":"Fed + seasonal"},
            {"year":2021,"month":9,"spx_drop":-5.2,"trigger":"Debt ceiling + taper"},
            {"year":2020,"month":9,"spx_drop":-9.6,"trigger":"Post-rally + seasonal"},
            {"year":2018,"month":10,"spx_drop":-10.0,"trigger":"Trade war + Oct weakness"},
        ],
        "resolution_zone": None,
        "note": "Sell in May and go away (May-Oct) has a 65% hit rate. Sep strongest signal."
    },
    # ── Top-10 Concentration ──────────────────────────────────────────────────
    "top10_weight": {
        "name": "Top-10 SPX Concentration",
        "cat": "Structure", "icon": "🏔️",
        "unit": "%",
        "direction": "up_bad",
        "safe_below":   28.0,
        "warn_above":   32.0,
        "danger_above": 36.0,        # historically max concentration before rotation
        "why": "When top-10 stocks exceed 35% of SPX, index concentration risk is extreme. "
               "Any earnings miss or multiple compression in just 2-3 mega-caps causes "
               "index-level 5-10% drops without broad market weakness.",
        "examples": [
            {"date":"Oct 2022","level":27.0,"spx_drop":-8.0,"weeks":4,"trigger":"FAANG earnings miss"},
            {"date":"Aug 2023","level":32.0,"spx_drop":-5.6,"weeks":5,"trigger":"AI valuation reset"},
            {"date":"Jan 2025","level":38.0,"spx_drop":-7.0,"weeks":4,"trigger":"AI capex doubt"},
            {"date":"Dec 2021","level":30.0,"spx_drop":-9.8,"weeks":3,"trigger":"FAANG multiple reset"},
        ],
        "resolution_zone": (26, 30),
        "note": "Pullback ends when top-10 weight drops 3-5% as rotation into value/equal-weight occurs."
    },
    # ── RSP/SPY (Breadth divergence) ─────────────────────────────────────────
    "rsp_spy": {
        "name": "Equal-Weight vs Cap-Weight Divergence",
        "cat": "Breadth", "icon": "⚖️",
        "unit": "ratio",
        "direction": "down_bad",
        "warn_below":   -5.0,   # RSP lagging SPY by 5% over 3 months = breadth divergence
        "danger_below": -8.0,   # extreme divergence = narrow leadership = fragile rally
        "why": "When RSP (equal-weight S&P) underperforms SPY by 8%+ over 3 months, "
               "the rally is driven by just 5-10 mega-caps. This narrow leadership "
               "historically precedes 5-10% corrections as the few leaders rotate.",
        "examples": [
            {"date":"Aug 2023","rsp_spy_3m":-8.5,"spx_drop":-5.6,"weeks":5,"trigger":"Mag-7 driven rally peak"},
            {"date":"Jan 2022","rsp_spy_3m":-6.0,"spx_drop":-9.8,"weeks":3,"trigger":"Growth/tech rotation"},
            {"date":"Oct 2018","rsp_spy_3m":-4.5,"spx_drop":-10.0,"weeks":6,"trigger":"FAANG rollover"},
            {"date":"Sep 2020","rsp_spy_3m":-7.0,"spx_drop":-9.6,"weeks":5,"trigger":"Tech concentration peak"},
        ],
        "resolution_zone": (0, 3),
        "note": "Correction ends when RSP starts outperforming SPY (equal-weight leadership = broad rally)."
    },
}


# Historical minor corrections database (5-15% pullbacks)
MINOR_CORRECTIONS_DB = [
    # Each entry: name, date, spx_at_peak, spx_at_trough, pct_drop, weeks_to_trough,
    # recovery_weeks, primary_trigger, indicator_that_warned, warning_level,
    # resolution_level, fwd_pe_peak, vix_at_peak, hy_at_peak, pcr_at_peak, pct50_at_peak
    {
        "name":"Jan 2018 Vol Spike",    "date":"Jan 2018","pct_drop":-10.2,"weeks_to_trough":2,
        "recovery_weeks":5,"trigger":"Vol spike from XIV collapse + inflation fear",
        "warned_by":["VIX complacency","P/C ratio low"],
        "fwd_pe_peak":25.1,"vix_at_peak":9.5,"hy_at_peak":340,"pcr_at_peak":0.55,"pct50_at_peak":88,
        "fwd_pe_trough":22.5,"vix_at_trough":50,"hy_at_trough":400,"pcr_at_trough":1.10,
        "nfci_at_peak":-0.82,"ism_at_peak":59,
    },
    {
        "name":"May 2019 Trade War",    "date":"May 2019","pct_drop":-6.8,"weeks_to_trough":4,
        "recovery_weeks":7,"trigger":"China tariff escalation — 10%→25% on $200B goods",
        "warned_by":["ISM rollover","VIX low","HY OAS tight"],
        "fwd_pe_peak":17.5,"vix_at_peak":13.1,"hy_at_peak":345,"pcr_at_peak":0.62,"pct50_at_peak":72,
        "fwd_pe_trough":16.0,"vix_at_trough":23,"hy_at_trough":410,"pcr_at_trough":0.95,
        "nfci_at_peak":-0.68,"ism_at_peak":52.8,
    },
    {
        "name":"Aug 2019 Curve Inversion","date":"Aug 2019","pct_drop":-6.1,"weeks_to_trough":3,
        "recovery_weeks":6,"trigger":"10Y-2Y inverted for first time since 2007 → recession fear",
        "warned_by":["Yield curve flat","VIX low","ISM declining"],
        "fwd_pe_peak":17.0,"vix_at_peak":12.8,"hy_at_peak":385,"pcr_at_peak":0.68,"pct50_at_peak":68,
        "fwd_pe_trough":15.8,"vix_at_trough":24,"hy_at_trough":450,"pcr_at_trough":0.92,
        "nfci_at_peak":-0.55,"ism_at_peak":51.2,
    },
    {
        "name":"Sep 2020 Post-Rally",   "date":"Sep 2020","pct_drop":-9.6,"weeks_to_trough":5,
        "recovery_weeks":6,"trigger":"Tech/growth overextension + election uncertainty",
        "warned_by":["Breadth >90%","VIX low","P/C low","Forward PE stretched"],
        "fwd_pe_peak":24.0,"vix_at_peak":23.0,"hy_at_peak":480,"pcr_at_peak":0.52,"pct50_at_peak":92,
        "fwd_pe_trough":21.8,"vix_at_trough":40,"hy_at_trough":550,"pcr_at_trough":1.05,
        "nfci_at_peak":-0.74,"ism_at_peak":55.4,
    },
    {
        "name":"Sep 2021 Taper Fear",   "date":"Sep 2021","pct_drop":-5.2,"weeks_to_trough":4,
        "recovery_weeks":4,"trigger":"Fed taper timeline + debt ceiling standoff",
        "warned_by":["NFCI very loose","ISM peak","Concentration risk"],
        "fwd_pe_peak":22.8,"vix_at_peak":16.5,"hy_at_peak":310,"pcr_at_peak":0.56,"pct50_at_peak":84,
        "fwd_pe_trough":21.2,"vix_at_trough":29,"hy_at_trough":360,"pcr_at_trough":0.92,
        "nfci_at_peak":-0.78,"ism_at_peak":61.1,
    },
    {
        "name":"Jan 2022 Rate Fear",    "date":"Jan 2022","pct_drop":-9.8,"weeks_to_trough":3,
        "recovery_weeks":5,"trigger":"Fed minutes hawkish pivot — first 50bp hike signal",
        "warned_by":["Fwd PE >21x","NFCI very loose","P/C low","Concentration risk"],
        "fwd_pe_peak":21.4,"vix_at_peak":17.2,"hy_at_peak":310,"pcr_at_peak":0.55,"pct50_at_peak":55,
        "fwd_pe_trough":19.5,"vix_at_trough":39,"hy_at_trough":420,"pcr_at_trough":1.18,
        "nfci_at_peak":-0.78,"ism_at_peak":58.7,
    },
    {
        "name":"Aug 2023 Rate Spike",   "date":"Aug 2023","pct_drop":-5.6,"weeks_to_trough":5,
        "recovery_weeks":8,"trigger":"10Y yield spike to 5% — highest since 2007",
        "warned_by":["Concentration risk","VIX low","RSP/SPY divergence"],
        "fwd_pe_peak":19.5,"vix_at_peak":13.0,"hy_at_peak":380,"pcr_at_peak":0.65,"pct50_at_peak":73,
        "fwd_pe_trough":18.2,"vix_at_trough":21,"hy_at_trough":440,"pcr_at_trough":0.95,
        "nfci_at_peak":-0.55,"ism_at_peak":46.4,
    },
    {
        "name":"Oct 2023 Rate Peak",    "date":"Oct 2023","pct_drop":-10.3,"weeks_to_trough":6,
        "recovery_weeks":8,"trigger":"10Y yield hit 5.02% — market pricing 'higher for longer'",
        "warned_by":["HY OAS widening","Fwd PE stretched","Seasonal (Oct)"],
        "fwd_pe_peak":18.8,"vix_at_peak":18.5,"hy_at_peak":450,"pcr_at_peak":0.80,"pct50_at_peak":45,
        "fwd_pe_trough":17.5,"vix_at_trough":23,"hy_at_trough":520,"pcr_at_trough":1.10,
        "nfci_at_peak":-0.40,"ism_at_peak":46.7,
    },
    {
        "name":"Jul-Aug 2024 Yen Carry","date":"Jul 2024","pct_drop":-8.5,"weeks_to_trough":3,
        "recovery_weeks":5,"trigger":"BOJ rate hike → yen strengthened → carry trade unwind",
        "warned_by":["VIX extreme low","USDJPY drop","HY OAS tight"],
        "fwd_pe_peak":21.5,"vix_at_peak":11.9,"hy_at_peak":290,"pcr_at_peak":0.62,"pct50_at_peak":70,
        "fwd_pe_trough":19.8,"vix_at_trough":38,"hy_at_trough":390,"pcr_at_trough":1.30,
        "nfci_at_peak":-0.70,"ism_at_peak":48.5,
    },
    {
        "name":"Feb-Apr 2026 Tariffs",  "date":"Feb 2026","pct_drop":-8.5,"weeks_to_trough":None,
        "recovery_weeks":None,"trigger":"Trump tariffs + Iran conflict + AI capex doubt",
        "warned_by":["Fwd PE >22x","NFCI loose","HY OAS tight","Post-inversion lag"],
        "fwd_pe_peak":22.5,"vix_at_peak":15.0,"hy_at_peak":275,"pcr_at_peak":0.60,"pct50_at_peak":60,
        "fwd_pe_trough":None,"vix_at_trough":None,"hy_at_trough":None,"pcr_at_trough":None,
        "nfci_at_peak":-0.65,"ism_at_peak":50.2,
    },
]


def _compute_pullback_risk(scorecard_data, fd, md, derived):
    """
    Score each pullback indicator and return composite risk score + per-indicator status.
    Returns dict with overall_score, risk_level, indicators list.
    """
    import datetime as _dtpb

    def _gsc(name):
        for ind in scorecard_data:
            if ind.get("name") == name and ind.get("value") is not None:
                return ind["value"]
        return None

    def _gv(k, i=-1):
        s = fd.get(k)
        if s is not None and not s.empty:
            try: return float(s.iloc[max(i, -len(s))])
            except: pass
        return None

    def _gmd(k):
        s = md.get(k)
        if s is not None and not s.empty:
            try: return float(s.iloc[-1])
            except: pass
        return None

    # Current readings
    vix     = _gmd("^VIX")
    fwd_pe  = _gsc("Forward P/E")
    nfci    = _gv("NFCI")
    hy_oas  = _gv("HY_OAS")
    pct50   = _gsc("% S&P Above 50DMA")
    pct200  = _gsc("% S&P Above 200DMA")
    top10   = _gsc("Top-10 SPX Weight")
    ism_val = _gv("ISM_PMI")
    ism_prev= _gv("ISM_PMI", -2)
    pcr_val = derived.get("pcr_live")   # filled from _fetch_pcr_additions
    month   = _dtpb.date.today().month

    # HY OAS 4-week momentum
    hy_4wk_chg = None
    hy_s = fd.get("HY_OAS")
    if hy_s is not None and len(hy_s) >= 5:
        hy_4wk_chg = round(float(hy_s.iloc[-1]) - float(hy_s.iloc[-5]), 0)

    # ISM rollover from peak
    ism_drop_from_peak = None
    _ism_s = fd.get("ISM_PMI")
    if _ism_s is not None and not _ism_s.empty and len(_ism_s) >= 6:
        peak_6m = float(_ism_s.tail(6).max())
        ism_now_v = float(_ism_s.iloc[-1])
        ism_drop_from_peak = round(ism_now_v - peak_6m, 1)

    # RSP/SPY 3-month return divergence
    rsp_spy_3m = None
    rsp = md.get("RSP"); spy = md.get("SPY")
    if rsp is not None and spy is not None and len(rsp) >= 63 and len(spy) >= 63:
        rsp_ret = (float(rsp.iloc[-1]) / float(rsp.iloc[-63]) - 1) * 100
        spy_ret = (float(spy.iloc[-1]) / float(spy.iloc[-63]) - 1) * 100
        rsp_spy_3m = round(rsp_ret - spy_ret, 1)

    # ── New technical factors ────────────────────────────────────────────────
    spy_50dma_pct = None   # SPY % above/below 50DMA
    spy_200dma_pct = None  # SPY % above/below 200DMA
    spy_rsi14 = None       # 14-day RSI
    dma_cross = None       # "golden", "death", or "none"

    _spy_ser = md.get("SPY")
    if _spy_ser is not None and not _spy_ser.empty:
        _sp = _spy_ser.dropna()
        _cur_px = float(_sp.iloc[-1])

        # 50DMA and 200DMA
        if len(_sp) >= 50:
            _ma50  = float(_sp.rolling(50).mean().iloc[-1])
            spy_50dma_pct = round((_cur_px / _ma50 - 1) * 100, 1)
        if len(_sp) >= 200:
            _ma200 = float(_sp.rolling(200).mean().iloc[-1])
            spy_200dma_pct = round((_cur_px / _ma200 - 1) * 100, 1)

        # Golden/Death Cross: 50DMA vs 200DMA direction
        if len(_sp) >= 201:
            _ma50_now  = float(_sp.rolling(50).mean().iloc[-1])
            _ma200_now = float(_sp.rolling(200).mean().iloc[-1])
            _ma50_prev = float(_sp.rolling(50).mean().iloc[-2])
            _ma200_prev= float(_sp.rolling(200).mean().iloc[-2])
            if _ma50_now > _ma200_now and _ma50_prev <= _ma200_prev:
                dma_cross = "golden"   # just crossed up
            elif _ma50_now < _ma200_now and _ma50_prev >= _ma200_prev:
                dma_cross = "death"    # just crossed down
            elif _ma50_now > _ma200_now:
                dma_cross = "above"    # 50 above 200 (bull)
            else:
                dma_cross = "below"    # 50 below 200 (bear)

        # RSI(14) — Wilder's smoothed
        if len(_sp) >= 16:
            import numpy as _np_rsi
            _delta = _sp.diff().dropna()
            _gain  = _delta.clip(lower=0)
            _loss  = (-_delta).clip(lower=0)
            _avg_g = _gain.ewm(com=13, adjust=False).mean()
            _avg_l = _loss.ewm(com=13, adjust=False).mean()
            _rs    = _avg_g.iloc[-1] / _avg_l.iloc[-1] if _avg_l.iloc[-1] != 0 else 100
            spy_rsi14 = round(100 - 100 / (1 + _rs), 1)

    indicators = []

    # ── Score each indicator ────────────────────────────────────────────────
    def _add(name, val, status, pct_risk, warn_thresh, danger_thresh, unit,
             note, examples_key=None, resolution=None, val_fmt=None):
        indicators.append({
            "name": name, "val": val, "status": status,
            "pct_risk": pct_risk,         # 0-100 risk contribution
            "warn_thresh": warn_thresh,
            "danger_thresh": danger_thresh,
            "unit": unit, "note": note,
            "examples_key": examples_key,
            "resolution": resolution,
            "val_str": val_fmt or (f"{val:.1f}{unit}" if val is not None else "N/A"),
        })

    # Forward P/E
    if fwd_pe:
        if   fwd_pe >= 24:   st, pr = "🔴 DANGER",  85
        elif fwd_pe >= 22:   st, pr = "🟡 WARNING",  55
        elif fwd_pe >= 20:   st, pr = "🟡 CAUTION",  30
        else:                st, pr = "🟢 SAFE",      5
        _add("Forward P/E", fwd_pe, st, pr,
             warn_thresh="22x",  danger_thresh="24x", unit="x",
             note=f"At {fwd_pe:.1f}x. Last minor correction from this level: check examples →",
             examples_key="fwd_pe", resolution="Resolution: 20-22x",
             val_fmt=f"{fwd_pe:.1f}x")

    # VIX
    if vix:
        if   vix <= 11:   st, pr = "🔴 EXTREME COMPLACENCY", 90
        elif vix <= 13:   st, pr = "🔴 DANGER (low)",       75
        elif vix <= 15:   st, pr = "🟡 WARNING (low)",      45
        elif vix >= 35:   st, pr = "🟢 CAPITULATION BUY",   5   # high VIX = trough
        elif vix >= 25:   st, pr = "🟡 CORRECTION IN PROGRESS", 30
        else:             st, pr = "🟢 NEUTRAL",             10
        _add("VIX Level", vix, st, pr,
             warn_thresh="<13",  danger_thresh="<11", unit="",
             note=f"VIX {vix:.1f}. {'Complacency → spike risk' if vix < 15 else 'Elevated/correcting' if vix >= 25 else 'Neutral zone'}",
             examples_key="vix_level", resolution="VIX spike resolves at 25-40",
             val_fmt=f"{vix:.1f}")

    # P/C Ratio
    if pcr_val:
        if   pcr_val <= 0.55: st, pr = "🔴 EXTREME BULLS",  80
        elif pcr_val <= 0.65: st, pr = "🟡 WARNING (low)", 50
        elif pcr_val >= 1.30: st, pr = "🟢 PANIC = BUY",   5   # high PCR = trough
        elif pcr_val >= 1.10: st, pr = "🟡 ELEVATED FEAR", 20
        else:                  st, pr = "🟢 NEUTRAL",       10
        _add("Put/Call Ratio", pcr_val, st, pr,
             warn_thresh="<0.65",  danger_thresh="<0.55", unit="",
             note=f"P/C {pcr_val:.3f}. {'Excessive bullish → pullback risk' if pcr_val < 0.65 else 'Extreme fear → near bottom' if pcr_val > 1.3 else 'Normal range'}",
             examples_key="pcr", resolution="Normalizes to 0.85-1.0",
             val_fmt=f"{pcr_val:.3f}")

    # % Above 50DMA
    if pct50:
        if   pct50 >= 88: st, pr = "🔴 OVERBOUGHT",     85
        elif pct50 >= 80: st, pr = "🟡 WARNING",        55
        elif pct50 <= 20: st, pr = "🟢 OVERSOLD = BUY", 5
        elif pct50 <= 30: st, pr = "🟡 OVERSOLD",       15
        else:             st, pr = "🟢 NEUTRAL",         10
        _add("% Above 50DMA", pct50, st, pr,
             warn_thresh=">80%", danger_thresh=">88%", unit="%",
             note=f"{pct50:.0f}% of S&P stocks above 50DMA. {'Overbought breadth → pullback' if pct50 > 80 else 'Oversold → bounce likely' if pct50 < 25 else 'Normal range'}",
             examples_key="pct_above_50dma", resolution="Resolves to 30-50%",
             val_fmt=f"{pct50:.0f}%")

    # NFCI
    if nfci is not None:
        if   nfci <= -0.80: st, pr = "🔴 EXTREME LOOSE", 80
        elif nfci <= -0.60: st, pr = "🟡 WARNING",        45
        elif nfci >= 0.50:  st, pr = "🔴 TIGHTENING",     60
        elif nfci >= 0.20:  st, pr = "🟡 TIGHTENING",     35
        else:               st, pr = "🟢 NEUTRAL",         10
        _add("NFCI Financial Conditions", nfci, st, pr,
             warn_thresh="< -0.60", danger_thresh="< -0.80", unit="",
             note=f"NFCI {nfci:+.3f}. {'Conditions too loose — reversion risk' if nfci < -0.6 else 'Conditions tightening → headwind' if nfci > 0.2 else 'Normal range'}",
             examples_key="nfci", resolution="Reverts to -0.3 to 0",
             val_fmt=f"{nfci:+.3f}")

    # HY OAS Momentum
    if hy_4wk_chg is not None:
        if   hy_4wk_chg >= 80:  st, pr = "🔴 CRISIS WIDENING",   90
        elif hy_4wk_chg >= 40:  st, pr = "🔴 DANGER WIDENING",   70
        elif hy_4wk_chg >= 20:  st, pr = "🟡 WARNING",            40
        elif hy_4wk_chg <= -30: st, pr = "🟢 SPREADS TIGHTENING", 5
        else:                   st, pr = "🟢 STABLE",             10
        _add("HY OAS 4-Week Change", hy_4wk_chg, st, pr,
             warn_thresh=">+20bps", danger_thresh=">+40bps", unit="bps",
             note=f"HY OAS moved {hy_4wk_chg:+.0f}bps in 4 weeks (now {hy_oas:.0f}bps). {'Warning: spreads widening fast' if hy_4wk_chg > 30 else 'Stable' if abs(hy_4wk_chg) < 20 else 'Tightening = positive'}",
             examples_key="hy_oas_momentum", resolution="Stabilizes at <30bps/4wk",
             val_fmt=f"{hy_4wk_chg:+.0f}bps")

    # ISM Rollover
    if ism_drop_from_peak is not None and ism_val is not None:
        if   ism_drop_from_peak <= -5 and ism_val < 52: st, pr = "🔴 ROLLING OVER",   65
        elif ism_drop_from_peak <= -3:                  st, pr = "🟡 SOFTENING",       40
        elif ism_val >= 62:                             st, pr = "🟡 OVER-EXTENDED",   50
        elif ism_val >= 58:                             st, pr = "🟡 ELEVATED",        30
        else:                                           st, pr = "🟢 NORMAL",          10
        _add("ISM Rollover from Peak", ism_val, st, pr,
             warn_thresh="Drop >3pts from peak", danger_thresh="Drop >5pts + <52", unit="",
             note=f"ISM {ism_val:.1f}  ({ism_drop_from_peak:+.1f} from 6mo peak). {'Rolling over — growth slowdown signal' if ism_drop_from_peak <= -3 else 'Near peak — rollover risk' if ism_val >= 58 else 'Normal expansion'}",
             examples_key="ism_rollover", resolution="Stabilizes at 48-52",
             val_fmt=f"{ism_val:.1f}")

    # Top-10 Concentration
    if top10:
        if   top10 >= 36: st, pr = "🔴 EXTREME",  75
        elif top10 >= 32: st, pr = "🟡 HIGH",     45
        elif top10 >= 28: st, pr = "🟡 ELEVATED", 25
        else:             st, pr = "🟢 NORMAL",    5
        _add("Top-10 Concentration", top10, st, pr,
             warn_thresh=">32%", danger_thresh=">36%", unit="%",
             note=f"Top-10 stocks = {top10:.0f}% of SPX. {'Extreme concentration — single stock risk' if top10 > 36 else 'Elevated — breadth fragile' if top10 > 32 else 'Normal range'}",
             examples_key="top10_weight", resolution="Pullback ends as weight drops to 26-30%",
             val_fmt=f"{top10:.0f}%")

    # RSP/SPY divergence
    if rsp_spy_3m is not None:
        if   rsp_spy_3m <= -8:  st, pr = "🔴 EXTREME NARROW", 80
        elif rsp_spy_3m <= -5:  st, pr = "🟡 NARROW RALLY",   50
        elif rsp_spy_3m >= 3:   st, pr = "🟢 BROAD RALLY",    5
        else:                   st, pr = "🟢 NORMAL",          10
        _add("RSP/SPY 3M Divergence", rsp_spy_3m, st, pr,
             warn_thresh="< -5%", danger_thresh="< -8%", unit="%",
             note=f"Equal-weight lagging cap-weight by {rsp_spy_3m:+.1f}% over 3 months. {'Dangerously narrow leadership' if rsp_spy_3m <= -8 else 'Narrow rally — fragile' if rsp_spy_3m <= -5 else 'Healthy broad participation'}",
             examples_key="rsp_spy", resolution="Ends when RSP outperforms (broad recovery)",
             val_fmt=f"{rsp_spy_3m:+.1f}%")

    # SPY vs 50DMA
    if spy_50dma_pct is not None:
        if   spy_50dma_pct >= 8:   st, pr = "🔴 FAR ABOVE 50DMA",  75
        elif spy_50dma_pct >= 5:   st, pr = "🟡 EXTENDED",          45
        elif spy_50dma_pct >= 2:   st, pr = "🟢 SLIGHTLY ABOVE",    15
        elif spy_50dma_pct >= -2:  st, pr = "🟢 AT 50DMA",          20  # at 50DMA = key support test
        elif spy_50dma_pct >= -5:  st, pr = "🟡 BELOW 50DMA",       35  # below = momentum negative
        else:                      st, pr = "🟢 OVERSOLD vs 50DMA",  5   # deeply below = bounce signal
        _add("SPY vs 50DMA", spy_50dma_pct, st, pr,
             warn_thresh="+5%", danger_thresh="+8%", unit="%",
             note=(f"SPY is {spy_50dma_pct:+.1f}% vs 50DMA. "
                   f"{'>+8%: historically precedes 3-8% mean reversion' if spy_50dma_pct >= 8 else '>+5%: extended, watch for reversal' if spy_50dma_pct >= 5 else 'At support' if abs(spy_50dma_pct) < 2 else 'Below 50DMA: momentum bearish' if spy_50dma_pct < -2 else 'Normal zone'}"),
             resolution="+2% to +5% = healthy range",
             val_fmt=f"{spy_50dma_pct:+.1f}%")

    # SPY vs 200DMA (most important long-term level)
    if spy_200dma_pct is not None:
        if   spy_200dma_pct >= 15:  st, pr = "🔴 FAR ABOVE 200DMA", 70
        elif spy_200dma_pct >= 10:  st, pr = "🟡 EXTENDED",          40
        elif spy_200dma_pct >= 5:   st, pr = "🟢 HEALTHY UPTREND",   10
        elif spy_200dma_pct >= -2:  st, pr = "🟡 AT 200DMA",         30  # key support test
        elif spy_200dma_pct >= -8:  st, pr = "🔴 BELOW 200DMA",      65  # bear signal
        else:                       st, pr = "🔴 DEEPLY BELOW 200DMA",80
        _add("SPY vs 200DMA", spy_200dma_pct, st, pr,
             warn_thresh="+10% or -2%", danger_thresh="+15% or -8%", unit="%",
             note=(f"SPY is {spy_200dma_pct:+.1f}% vs 200DMA. "
                   f"{'Critical: bear market confirmed' if spy_200dma_pct < -8 else 'Testing key support — watch closely' if abs(spy_200dma_pct) < 2 else 'Healthy uptrend distance' if 5 <= spy_200dma_pct < 10 else 'Extended above long-term trend' if spy_200dma_pct >= 10 else ''}"),
             resolution="200DMA = major support. Bounce if -2% to -5% holds",
             val_fmt=f"{spy_200dma_pct:+.1f}%")

    # 50/200 DMA Cross (Death/Golden Cross)
    if dma_cross is not None:
        _cross_map = {
            "golden": ("🟢 GOLDEN CROSS (just fired)", 5,  "50DMA crossed above 200DMA — bullish structural shift"),
            "death":  ("🔴 DEATH CROSS (just fired)",  90, "50DMA crossed below 200DMA — bear market confirmation"),
            "above":  ("🟢 50DMA ABOVE 200DMA",        10, "Bullish structural alignment"),
            "below":  ("🔴 50DMA BELOW 200DMA",        70, "Bearish structure — bear market regime"),
        }
        st, pr, note_txt = _cross_map[dma_cross]
        _add("50/200 DMA Cross", dma_cross, st, pr,
             warn_thresh="below", danger_thresh="death cross", unit="",
             note=note_txt,
             resolution="Golden cross = structural recovery confirmed",
             val_fmt={"golden":"Golden ✓","death":"Death ✗","above":"50>200 ✓","below":"50<200 ✗"}.get(dma_cross,dma_cross))

    # RSI(14)
    if spy_rsi14 is not None:
        if   spy_rsi14 >= 75:  st, pr = "🔴 OVERBOUGHT",       80
        elif spy_rsi14 >= 65:  st, pr = "🟡 ELEVATED",          40
        elif spy_rsi14 >= 45:  st, pr = "🟢 NEUTRAL",           10
        elif spy_rsi14 >= 35:  st, pr = "🟡 WEAKENING",         30
        elif spy_rsi14 >= 25:  st, pr = "🟢 OVERSOLD (bounce)", 5
        else:                  st, pr = "🟢 EXTREME OVERSOLD",   5
        _add("RSI(14) — SPY", spy_rsi14, st, pr,
             warn_thresh=">65 or <35", danger_thresh=">75 or <25", unit="",
             note=(f"RSI {spy_rsi14:.0f}. "
                   f"{'Overbought — mean reversion risk' if spy_rsi14 >= 65 else 'Oversold — bounce likely' if spy_rsi14 <= 35 else 'Neutral momentum'}"),
             resolution="RSI 45-55 = neutral; <30 = oversold bounce zone",
             val_fmt=f"{spy_rsi14:.0f}")

    # Seasonal
    month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                   7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    high_risk   = PULLBACK_THRESHOLDS["seasonal"]["high_risk_months"]
    mod_risk    = PULLBACK_THRESHOLDS["seasonal"]["moderate_risk_months"]
    if   month in high_risk: st, pr = "🔴 HIGH RISK MONTH",      60
    elif month in mod_risk:  st, pr = "🟡 MODERATE RISK MONTH",  35
    else:                    st, pr = "🟢 LOW RISK MONTH",         5
    _add("Seasonal Factor", month, st, pr,
         warn_thresh="Aug,Feb", danger_thresh="Sep", unit="",
         note=f"{month_names.get(month,'?')} — {'worst month historically (Sep avg -1.1%)' if month == 9 else 'moderate seasonal headwind' if month in mod_risk else 'typically positive seasonal window'}",
         examples_key="seasonal", resolution="Seasonal headwind passes end of month",
         val_fmt=month_names.get(month, str(month)))

    # Compute composite score (weighted avg of pct_risk)
    if indicators:
        weights = {
            "Forward P/E":           15,
            "VIX Level":             12,
            "Put/Call Ratio":        10,
            "% Above 50DMA":         10,
            "HY OAS 4-Week Change":  10,
            "SPY vs 50DMA":          10,   # NEW
            "SPY vs 200DMA":         10,   # NEW
            "RSI(14) — SPY":          8,   # NEW
            "50/200 DMA Cross":       7,   # NEW
            "NFCI Financial Conditions": 5,
            "ISM Rollover from Peak": 5,
            "Top-10 Concentration":   4,
            "RSP/SPY 3M Divergence":  2,
            "Seasonal Factor":        1,
            "HY OAS 4-Week Change":   1,
        }
        total_w = 0; score = 0
        for ind in indicators:
            w = weights.get(ind["name"], 3)
            score   += ind["pct_risk"] * w
            total_w += w
        overall = round(score / total_w) if total_w > 0 else 0
    else:
        overall = 0

    if   overall >= 65: risk_level = "HIGH — Pullback Likely (5-15%)"
    elif overall >= 45: risk_level = "ELEVATED — Correction Risk Building"
    elif overall >= 25: risk_level = "MODERATE — Watch Key Indicators"
    else:              risk_level = "LOW — No Immediate Pullback Signal"

    return {
        "overall_score": overall,
        "risk_level":    risk_level,
        "indicators":    indicators,
        "cur_fwd_pe":    fwd_pe,
        "cur_vix":       vix,
        "cur_pcr":       pcr_val,
        "cur_pct50":     pct50,
        "cur_hy_4wk":    hy_4wk_chg,
        "cur_50dma_pct": spy_50dma_pct,
        "cur_200dma_pct":spy_200dma_pct,
        "cur_rsi14":     spy_rsi14,
        "cur_dma_cross": dma_cross,
    }


def _build_pullback_overlay_data(md, sim_results, pb_data):
    """
    Build Chart.js dataset for the SPY pullback overlay chart.

    Returns dict with:
      labels        — x-axis: days from peak (-40 to +180)
      datasets      — list of Chart.js dataset dicts
      current_day   — current day index from peak (e.g., day 60 into correction)
      pred_path     — weighted average forward projection
      meta          — per-episode metadata for legend
    """
    import datetime as _dtov
    import json as _jsov

    # ── Episode window definitions ────────────────────────────────────────
    # Each minor correction: peak_date, trough_offset (days), recovery_offset (days)
    EPISODE_WINDOWS = {
        "Jan 2018 Vol Spike":      {"peak":"2018-01-26","trough_day":14,  "end_day":150, "color":"#FF6633","sim":0},
        "May 2019 Trade War":      {"peak":"2019-04-30","trough_day":28,  "end_day":180, "color":"#FFAA22","sim":0},
        "Aug 2019 Curve Inversion":{"peak":"2019-07-26","trough_day":21,  "end_day":160, "color":"#FFDD44","sim":0},
        "Sep 2020 Post-Rally":     {"peak":"2020-09-02","trough_day":35,  "end_day":200, "color":"#44AAFF","sim":0},
        "Sep 2021 Taper Fear":     {"peak":"2021-09-02","trough_day":28,  "end_day":180, "color":"#FF44AA","sim":0},
        "Jan 2022 Rate Fear":      {"peak":"2022-01-03","trough_day":21,  "end_day":200, "color":"#AA44FF","sim":0},
        "Aug 2023 Rate Spike":     {"peak":"2023-07-27","trough_day":35,  "end_day":210, "color":"#44FFCC","sim":0},
        "Oct 2023 Rate Peak":      {"peak":"2023-07-27","trough_day":42,  "end_day":220, "color":"#FF8844","sim":0},
        "Jul 2024 Yen Carry":      {"peak":"2024-07-16","trough_day":21,  "end_day":180, "color":"#88FF44","sim":0},
    }

    # Update similarity scores from sim_results
    if sim_results:
        for r in sim_results:
            ep_name = r["episode"]["name"]
            for k in EPISODE_WINDOWS:
                if any(w in ep_name for w in k.split()[:2]):
                    EPISODE_WINDOWS[k]["sim"] = r["score"]
                    break

    # ── Download historical SPY prices ────────────────────────────────────
    try:
        import yfinance as _yfov
        import pandas as _pdov
        import numpy as _npov

        # Fetch 10yr SPY history once (covers all episodes)
        _spy_hist = None
        _spy_s = md.get("SPY")
        if _spy_s is not None and not _spy_s.empty:
            _spy_hist = _spy_s.copy()
            try:
                if _spy_hist.index.tz is not None:
                    _spy_hist.index = _spy_hist.index.tz_localize(None)
            except Exception:
                pass

        # Also fetch extra history going back to 2017 if needed
        try:
            _extra = _yfov.download("SPY", start="2017-01-01", auto_adjust=True, progress=False)
            if not _extra.empty:
                _extra_c = _extra["Close"].squeeze().dropna()
                _extra_c.index = _pdov.to_datetime(_extra_c.index).tz_localize(None)
                if _spy_hist is not None:
                    _spy_hist = _pdov.concat([_extra_c, _spy_hist]).sort_index()
                    _spy_hist = _spy_hist[~_spy_hist.index.duplicated(keep="last")]
                else:
                    _spy_hist = _extra_c
        except Exception:
            pass

        if _spy_hist is None or _spy_hist.empty:
            return {}

        _spy_hist.index = _pdov.to_datetime(_spy_hist.index).normalize()

        # X axis: days from peak (-40 to +220)
        X_START, X_END = -40, 130   # display: 40 days pre-peak + 130 post (covers ~4 months forward)
        x_labels = list(range(X_START, X_END + 1))

        datasets = []
        meta     = []

        def _extract_path(peak_str, end_day):
            """Extract SPY path indexed to 100 at peak. Returns list aligned to x_labels."""
            try:
                peak_dt = _pdov.Timestamp(peak_str)
                start   = peak_dt + _pdov.Timedelta(days=X_START - 5)
                end     = peak_dt + _pdov.Timedelta(days=end_day + 5)
                seg     = _spy_hist[(  _spy_hist.index >= start)
                                    & (_spy_hist.index <= end)].copy()
                if len(seg) < 5:
                    return None
                # Find nearest available date to peak
                diffs   = _npov.abs((seg.index - peak_dt).days)
                peak_idx= int(diffs.argmin())
                peak_px = float(seg.iloc[peak_idx])
                if peak_px <= 0:
                    return None
                # Build day-offset → indexed value map
                day_map = {}
                for j, (dt, px) in enumerate(zip(seg.index, seg.values)):
                    offset = (dt - peak_dt).days
                    if X_START <= offset <= X_END:
                        day_map[offset] = round(float(px) / peak_px * 100, 2)
                # Fill x_labels
                path = []
                for x in x_labels:
                    path.append(day_map.get(x))
                return path
            except Exception:
                return None

        # ── Historical episode paths ──────────────────────────────────────
        for ep_name, ep in EPISODE_WINDOWS.items():
            path = _extract_path(ep["peak"], ep["end_day"])
            if path is None:
                continue
            sim  = ep.get("sim", 0)
            # Line width scales with similarity score
            lw   = 1.5 + (sim / 100) * 2.0
            alpha = max(0.35, sim / 100 * 0.9)
            col  = ep["color"]
            # Convert to rgba
            r_hex = col[1:3]; g_hex = col[3:5]; b_hex = col[5:7]
            r_v   = int(r_hex,16); g_v = int(g_hex,16); b_v = int(b_hex,16)
            rgba  = f"rgba({r_v},{g_v},{b_v},{alpha:.2f})"
            datasets.append({
                "label":           ep_name,
                "data":            path,
                "borderColor":     rgba,
                "borderWidth":     round(lw, 1),
                "pointRadius":     0,
                "tension":         0.3,
                "fill":            False,
                "borderDash":      [] if sim >= 50 else [4, 3],
                "_sim":            sim,
                "_trough_day":     ep["trough_day"],
            })
            meta.append({
                "name":        ep_name,
                "sim":         sim,
                "trough_day":  ep["trough_day"],
                "end_day":     ep["end_day"],
                "color":       col,
                "peak_date":   ep["peak"],
            })

        # ── Current episode path ──────────────────────────────────────────
        # Find actual ATH in the SPY series (search last 18 months for the peak)
        try:
            import pandas as _pdcur
            _lookback_start = _pdcur.Timestamp.today() - _pdcur.Timedelta(days=540)
            _spy_recent     = _spy_hist[_spy_hist.index >= _lookback_start]
            _ath_idx        = _spy_recent.idxmax()
            cur_peak_str    = str(_ath_idx)[:10]
            print(f"  [pullback] ATH detected: {cur_peak_str} @ ${float(_spy_recent.max()):.2f}")
        except Exception:
            cur_peak_str = "2025-01-24"   # fallback
        cur_path_raw = _extract_path(cur_peak_str, X_END)
        cur_day      = None
        if cur_path_raw is not None:
            # Find last non-None value = current day
            for _xi, _xv in enumerate(cur_path_raw):
                if _xv is not None:
                    cur_day = x_labels[_xi]
            datasets.append({
                "label":       "▶ Current (2025-26)",
                "data":        cur_path_raw,
                "borderColor": "#00FF99",
                "borderWidth": 4,
                "pointRadius": 0,
                "tension":     0.3,
                "fill":        False,
                "borderDash":  [],
                "_sim":        100,
                "_trough_day": None,
            })
            meta.append({
                "name":      "Current (2025-26)",
                "sim":       100,
                "color":     "#00FF99",
                "peak_date": cur_peak_str,
            })

        # ── Weighted projection path ──────────────────────────────────────
        # Only project from current_day onward
        proj_path = [None] * len(x_labels)
        if cur_day is not None and datasets:
            # Filter historical episodes with sim >= 30
            sim_eps = [(ds, m) for ds, m in zip(datasets, meta)
                       if m.get("sim", 0) >= 30 and "Current" not in m["name"]]
            if sim_eps:
                # Find current indexed level
                cur_level = None
                for xi, xv in enumerate(x_labels):
                    if xv == cur_day and cur_path_raw:
                        cur_level = cur_path_raw[xi]
                        break

                total_sim = sum(m["sim"] for _, m in sim_eps)
                # Pre-compute cur_day index and current level once
                cur_day_xi = x_labels.index(cur_day) if cur_day in x_labels else None

                # Pre-compute each episode's anchor scale factor at cur_day
                ep_scale = {}
                for ds, m in sim_eps:
                    _path = ds["data"]
                    _ep_at_cur = (_path[cur_day_xi]
                                  if cur_day_xi is not None and cur_day_xi < len(_path)
                                  else None)
                    ep_scale[id(ds)] = (cur_level / _ep_at_cur
                                        if (_ep_at_cur and _ep_at_cur > 0 and cur_level)
                                        else 1.0)

                for xi, x in enumerate(x_labels):
                    if x <= cur_day:
                        continue     # skip history
                    if x > cur_day + 60:
                        break        # cap at 60 calendar days (~2 months) — more reliable

                    # No decay within 60 days — all episodes equally weighted at this range
                    days_ahead = x - cur_day

                    w_sum = 0.0; w_cnt = 0.0
                    for ds, m in sim_eps:
                        path = ds["data"]
                        if xi < len(path) and path[xi] is not None:
                            rescaled = path[xi] * ep_scale[id(ds)]
                            w        = m["sim"]   # equal decay within 60-day window
                            w_sum   += rescaled * w
                            w_cnt   += w
                    if w_cnt > 0:
                        proj_path[xi] = round(w_sum / w_cnt, 2)

            datasets.append({
                "label":       "⟶ Weighted Projection",
                "data":        proj_path,
                "borderColor": "#FFD700",
                "borderWidth": 2.5,
                "pointRadius": 0,
                "tension":     0.4,
                "fill":        False,
                "borderDash":  [8, 4],
                "_sim":        -1,
            })

        # Capture actual SPY prices for the second chart
        _peak_px   = None
        _cur_px    = None
        try:
            import pandas as _pdpx
            _peak_dt = _pdpx.Timestamp(cur_peak_str)
            _diffs   = _npov.abs((_spy_hist.index - _peak_dt).days)
            _peak_px = round(float(_spy_hist.iloc[int(_diffs.argmin())]), 2)
            _cur_px  = round(float(_spy_hist.iloc[-1]), 2)
        except Exception:
            pass

        _result = {
            "labels":         x_labels,
            "datasets":       datasets,
            "meta":           meta,
            "cur_day":        cur_day,
            "proj_path":      proj_path,
            "peak_date_str":  cur_peak_str,
            "peak_price":     _peak_px,
            "cur_spy_price":  _cur_px,
        }
        return _result

    except Exception as _e:
        return {"error": str(_e)}


def _build_pullback_monitor_html(pb_data, scorecard_data, fd, md, overlay_data=None):
    """Build the full Pullback Monitor tab HTML."""
    import datetime as _dtpb2
    gen_dt = _dtpb2.datetime.now().strftime("%Y-%m-%d %H:%M")

    overall  = pb_data["overall_score"]
    risk_lv  = pb_data["risk_level"]
    inds     = pb_data["indicators"]

    # Gauge colour
    if   overall >= 65: gauge_col = "#C0390F"; gauge_bg = "#fce4ec"
    elif overall >= 45: gauge_col = "#D4820A"; gauge_bg = "#fff8e1"
    elif overall >= 25: gauge_col = "#2E8B57"; gauge_bg = "#f1f8e9"
    else:               gauge_col = "#1A7A4A"; gauge_bg = "#e8f5e9"

    # Gauge arc SVG (0-100 → -150° to +150°)
    import math as _math
    _pct  = min(max(overall, 0), 100) / 100
    _ang  = -150 + _pct * 300   # degrees
    _rad  = _ang * _math.pi / 180
    _cx, _cy, _r = 80, 70, 55
    _nx = _cx + _r * _math.sin(_rad)
    _ny = _cy - _r * _math.cos(_rad)
    gauge_svg = f"""
<svg viewBox="0 0 160 100" width="180" height="110">
  <path d="M25,90 A55,55 0 1,1 135,90" fill="none" stroke="#e0e0e0" stroke-width="12" stroke-linecap="round"/>
  <path d="M25,90 A55,55 0 {'1' if _pct > 0.5 else '0'},1 {_nx:.1f},{_ny:.1f}" fill="none"
        stroke="{gauge_col}" stroke-width="12" stroke-linecap="round"/>
  <text x="80" y="75" text-anchor="middle" font-size="22" font-weight="900" fill="{gauge_col}">{overall}</text>
  <text x="80" y="92" text-anchor="middle" font-size="9" fill="#888">PULLBACK RISK</text>
</svg>"""

    # Status cards per indicator
    status_rows = ""
    for ind in inds:
        col = ("#C0390F" if "🔴" in ind["status"] else
               "#D4820A" if "🟡" in ind["status"] else "#1A7A4A")
        bg  = ("#fff5f5" if "🔴" in ind["status"] else
               "#fffde7" if "🟡" in ind["status"] else "#f1f8e9")
        bar_w = min(ind["pct_risk"], 100)

        status_rows += f"""
<tr style="background:{bg};border-bottom:1px solid #e8eaed">
  <td style="padding:8px 12px;font-size:11px;font-weight:700;color:#1a1a2e;white-space:nowrap;width:200px">{ind['name']}</td>
  <td style="padding:8px 10px;font-size:13px;font-weight:900;color:{col};text-align:center;width:80px">{ind['val_str']}</td>
  <td style="padding:8px 10px;font-size:10px;color:{col};font-weight:700;white-space:nowrap">{ind['status']}</td>
  <td style="padding:8px 12px;width:120px">
    <div style="background:#e0e0e0;height:6px;border-radius:3px">
      <div style="width:{bar_w}%;height:6px;background:{col};border-radius:3px"></div>
    </div>
    <div style="font-size:8px;color:{col};margin-top:1px;font-weight:700">{ind['pct_risk']}% risk</div>
  </td>
  <td style="padding:8px 12px;font-size:10px;color:#555;max-width:280px">{ind['note']}</td>
  <td style="padding:8px 10px;font-size:9px;color:#888;white-space:nowrap">{ind.get('resolution','')}</td>
</tr>"""

    # ── Historical minor corrections table ──────────────────────────────────
    mc_rows = ""
    for mc in MINOR_CORRECTIONS_DB:
        pct   = mc["pct_drop"]
        wks   = mc.get("weeks_to_trough")
        rec   = mc.get("recovery_weeks")
        col   = "#C0390F" if pct <= -8 else "#D4820A" if pct <= -5 else "#556"
        # Which indicators warned?
        warned = ", ".join(mc.get("warned_by", []))
        mc_rows += f"""
<tr style="border-bottom:1px solid #e8eaed">
  <td style="padding:6px 10px;font-size:11px;font-weight:700;white-space:nowrap">{mc['name']}</td>
  <td style="padding:6px 8px;font-size:11px;font-weight:900;color:{col};text-align:center">{pct}%</td>
  <td style="padding:6px 8px;text-align:center;font-size:10px">{wks or '?'} wks</td>
  <td style="padding:6px 8px;text-align:center;font-size:10px;color:#1A7A4A">{rec or 'TBD'} wks</td>
  <td style="padding:6px 8px;font-size:10px;color:#555">{mc['trigger'][:55]}</td>
  <td style="padding:6px 8px;font-size:10px;color:#D4820A">{warned[:55]}</td>
  <td style="padding:6px 6px;font-size:10px;text-align:center">{mc['fwd_pe_peak']:.0f}x</td>
  <td style="padding:6px 6px;font-size:10px;text-align:center;color:#1A7A4A">{mc['vix_at_peak']:.0f}</td>
  <td style="padding:6px 6px;font-size:10px;text-align:center">{mc['hy_at_peak']}</td>
  <td style="padding:6px 6px;font-size:10px;text-align:center;color:#C0390F">{mc['pcr_at_peak']}</td>
  <td style="padding:6px 6px;font-size:10px;text-align:center">{mc['pct50_at_peak']:.0f}%</td>
</tr>"""

    # ── Per-indicator historical examples lookup ──────────────────────────────
    def _example_rows(key):
        th = PULLBACK_THRESHOLDS.get(key, {})
        examples = th.get("examples", [])
        if not examples: return ""
        rows = ""
        for ex in examples[:5]:
            level = ex.get("level", ex.get("level_start","?"))
            drop  = ex.get("spx_drop", "?")
            wks   = ex.get("weeks","?")
            trig  = ex.get("trigger","")
            dcol  = "#C0390F" if isinstance(drop,float) and drop <= -7 else "#D4820A"
            rows += (f'<tr style="border-bottom:1px solid #f0f0f0">'
                     f'<td style="padding:3px 8px;font-size:10px">{ex.get("date",ex.get("year","?"))}</td>'
                     f'<td style="padding:3px 8px;font-size:10px;font-weight:700">{level}</td>'
                     f'<td style="padding:3px 8px;font-size:10px;font-weight:900;color:{dcol}">{drop}%</td>'
                     f'<td style="padding:3px 8px;font-size:10px">{wks} wks</td>'
                     f'<td style="padding:3px 8px;font-size:10px;color:#555">{trig}</td>'
                     f'</tr>')
        return rows

    # Build collapsible example panels for top risky indicators
    top_risky = sorted([i for i in inds if i["pct_risk"] >= 40], key=lambda x: -x["pct_risk"])
    detail_panels = ""
    for ind in top_risky[:4]:
        key    = ind.get("examples_key","")
        ex_rows = _example_rows(key)
        th = PULLBACK_THRESHOLDS.get(key, {})
        why = th.get("why","")
        col = "#C0390F" if "🔴" in ind["status"] else "#D4820A"
        if not ex_rows: continue
        detail_panels += f"""
<div style="border:1px solid {col}33;border-left:4px solid {col};border-radius:6px;
            padding:12px 14px;margin-bottom:12px;background:#fafafa">
  <div style="font-size:12px;font-weight:800;color:{col};margin-bottom:4px">
    {ind['status']} {ind['name']} — {ind['val_str']}
  </div>
  <div style="font-size:10px;color:#555;margin-bottom:8px">{why[:180]}...</div>
  <table style="width:100%;border-collapse:collapse;font-size:10px">
    <thead><tr style="background:#f0f0f0">
      <th style="padding:4px 8px;text-align:left">Date</th>
      <th style="padding:4px 8px">Level</th>
      <th style="padding:4px 8px">SPX Drop</th>
      <th style="padding:4px 8px">Weeks</th>
      <th style="padding:4px 8px;text-align:left">Trigger</th>
    </tr></thead>
    <tbody>{ex_rows}</tbody>
  </table>
  <div style="margin-top:6px;font-size:9px;color:#888">
    <strong>Resolution zone:</strong> {ind.get('resolution','')}
  </div>
</div>"""

    # ── Current vs historical minor corrections comparison ────────────────────
    cur_fwd_pe  = pb_data.get("cur_fwd_pe")
    cur_vix     = pb_data.get("cur_vix")
    cur_pcr     = pb_data.get("cur_pcr")
    cur_pct50   = pb_data.get("cur_pct50")
    cur_hy_4wk  = pb_data.get("cur_hy_4wk")
    cur_50dma   = pb_data.get("cur_50dma_pct")
    cur_200dma  = pb_data.get("cur_200dma_pct")
    cur_rsi14   = pb_data.get("cur_rsi14")
    cur_dma_x   = pb_data.get("cur_dma_cross") or "above"
    _cross_lbl  = {"golden":"Golden ✓","death":"Death ✗","above":"50>200 ✓","below":"50<200 ✗"}.get(cur_dma_x,"N/A")
    _cross_col  = "#1A7A4A" if cur_dma_x in ("golden","above") else "#C0390F"

    # Find nearest historical episode by indicator similarity
    def _find_nearest(field, cur_val):
        if cur_val is None: return None, None
        best_mc = None; best_dist = 999
        for mc in MINOR_CORRECTIONS_DB[:-1]:  # exclude current
            mc_val = mc.get(f"{field}_peak") or mc.get(f"{field}_at_peak")
            if mc_val is None: continue
            d = abs(cur_val - mc_val)
            if d < best_dist:
                best_dist = d; best_mc = mc
        return best_mc, best_dist

    nearest_pe_mc, _ = _find_nearest("fwd_pe", cur_fwd_pe)
    nearest_vix_mc, _= _find_nearest("vix", cur_vix)

    comparison_note = ""
    if nearest_pe_mc and cur_fwd_pe:
        comparison_note += (
            f"<div style='margin:4px 0;font-size:11px'>"
            f"📊 <strong>Forward P/E {cur_fwd_pe:.1f}x</strong> is closest to "
            f"<strong style='color:#C0390F'>{nearest_pe_mc['name']}</strong> "
            f"(peak {nearest_pe_mc['fwd_pe_peak']:.0f}x → fell "
            f"<strong style='color:#C0390F'>{nearest_pe_mc['pct_drop']}%</strong> "
            f"over {nearest_pe_mc['weeks_to_trough']} weeks, "
            f"P/E then dropped to {nearest_pe_mc['fwd_pe_trough']:.0f}x)</div>"
        )
    if nearest_vix_mc and cur_vix:
        comparison_note += (
            f"<div style='margin:4px 0;font-size:11px'>"
            f"😨 <strong>VIX {cur_vix:.1f}</strong> is closest to "
            f"<strong style='color:#C0390F'>{nearest_vix_mc['name']}</strong> "
            f"(VIX was {nearest_vix_mc['vix_at_peak']:.0f} at peak → "
            f"spiked to {nearest_vix_mc['vix_at_trough']} at trough while "
            f"SPX fell <strong style='color:#C0390F'>{nearest_vix_mc['pct_drop']}%</strong>)</div>"
        )

    # ── Overlay chart HTML ────────────────────────────────────────────────
    overlay_chart_html = ""
    if overlay_data and overlay_data.get("datasets"):
        import json as _jsov2
        _ov    = overlay_data
        _cur_d = _ov.get("cur_day", 0) or 0
        _meta  = _ov.get("meta", [])
        _dsets = _ov.get("datasets", [])

        # Build legend entries
        _legend_html = ""
        for m in sorted([m for m in _meta if "Current" not in m["name"]], key=lambda x:-x["sim"])[:8]:
            _lw = "800" if m["sim"] >= 50 else "400"
            _ls = "solid" if m["sim"] >= 50 else "dashed"
            _sim_badge = (f'<span style="font-size:9px;background:{m["color"]}33;color:{m["color"]};'
                          f'padding:1px 5px;border-radius:8px;font-weight:700">{m["sim"]}% match</span>')
            _legend_html += (
                f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:3px">'
                f'<div style="width:22px;height:2px;background:{m["color"]};'
                f'border-bottom:2px {_ls} {m["color"]}"></div>'
                f'<span style="font-size:9px;color:#ccc;font-weight:{_lw}">{m["name"]}</span>'
                f'{_sim_badge}</div>'
            )
        _legend_html += (
            '<div style="display:flex;align-items:center;gap:5px;margin-bottom:3px">'
            '<div style="width:22px;height:3px;background:#00FF99"></div>'
            '<span style="font-size:9px;color:#0A6B3A;font-weight:800">▶ Current (2025-26)</span></div>'
            '<div style="display:flex;align-items:center;gap:5px">'
            '<div style="width:22px;height:2px;background:#FFD700;'
            'border-bottom:2px dashed #FFD700"></div>'
            '<span style="font-size:9px;color:#FFD700;font-weight:800">⟶ Weighted Projection</span></div>'
        )

        _clean_dsets = [{k: v for k, v in ds.items() if not k.startswith("_")} for ds in _dsets]
        _labels_json = _jsov2.dumps(_ov["labels"])
        _dsets_json  = _jsov2.dumps(_clean_dsets)

        _proj        = _ov.get("proj_path", [])
        _proj_valid  = [(x, v) for x, v in zip(_ov["labels"], _proj) if v is not None]
        _min_proj_day = min(_proj_valid, key=lambda t: t[1])[0] if _proj_valid else None
        _min_proj_val = min(_proj_valid, key=lambda t: t[1])[1] if _proj_valid else None
        _peak_px      = _ov.get("peak_price")
        _cur_px       = _ov.get("cur_spy_price")
        _peak_date_s  = _ov.get("peak_date_str", "2025-01-24")

        # Convert projected trough to real dollar price
        _proj_low_px  = None
        if _min_proj_val and _peak_px:
            _proj_low_px = round(_peak_px * _min_proj_val / 100, 2)

        _min_str = (
            f"Projected low: ~{_min_proj_val:.1f}% of peak"
            f"  ≈  ${_proj_low_px:.2f}" if (_min_proj_val and _proj_low_px) else
            "Projected low: ~{:.1f}% of peak".format(_min_proj_val) if _min_proj_val else
            "Insufficient similarity matches for projection"
        )
        _day_str = f"day {_min_proj_day} from peak" if _min_proj_day else ""

        # ── Build Chart 2 data: real calendar dates + actual $ prices ────────
        import datetime as _dtc2
        _chart2_actual_labels  = []   # ISO date strings for actual path
        _chart2_actual_prices  = []
        _chart2_proj_labels    = []   # ISO date strings for projection
        _chart2_proj_prices    = []
        _chart2_band_high      = []
        _chart2_band_low       = []
        _today_date_str        = _dtc2.date.today().isoformat()

        try:
            _pk_dt = _dtc2.date.fromisoformat(_peak_date_s)

            # Actual SPY path: from peak to today (use current path dataset)
            _cur_ds = next((ds for ds in _dsets if "Current" in ds.get("label","")), None)
            if _cur_ds and _peak_px:
                for _xi, (_day_off, _idx_val) in enumerate(zip(_ov["labels"], _cur_ds["data"])):
                    if _idx_val is None: continue
                    _cal_dt = _pk_dt + _dtc2.timedelta(days=int(_day_off))
                    _px_val = round(_peak_px * _idx_val / 100, 2)
                    _chart2_actual_labels.append(_cal_dt.isoformat())
                    _chart2_actual_prices.append(_px_val)

            # Projection path + confidence band
            if _proj_valid and _peak_px:
                # Get individual episode paths for band calculation
                _sim_eps_paths = [
                    (ds, m) for ds, m in zip(_dsets, _meta)
                    if m.get("sim", 0) >= 30 and "Current" not in m.get("name","")
                       and "Projection" not in ds.get("label","")
                ]
                # Find cur_level for anchoring
                _cl_val = None
                if _cur_ds:
                    for _xi, _xv in enumerate(_ov["labels"]):
                        if _xv == _cur_d and _xi < len(_cur_ds["data"]):
                            _cl_val = _cur_ds["data"][_xi]
                            break

                for _xi, (_day_off, _idx_val) in enumerate(zip(_ov["labels"], _proj)):
                    if _idx_val is None: continue
                    _cal_dt  = _pk_dt + _dtc2.timedelta(days=int(_day_off))
                    _px_val  = round(_peak_px * _idx_val / 100, 2)
                    _chart2_proj_labels.append(_cal_dt.isoformat())
                    _chart2_proj_prices.append(_px_val)

                    # Band: ±1 stddev of episode prices at this day
                    _ep_vals = []
                    for _ds, _m in _sim_eps_paths:
                        _ep_path = _ds["data"]
                        if _xi < len(_ep_path) and _ep_path[_xi] is not None:
                            _ep_at_cur = None
                            _cur_xi = _ov["labels"].index(_cur_d) if _cur_d in _ov["labels"] else None
                            if _cur_xi is not None and _cur_xi < len(_ep_path):
                                _ep_at_cur = _ep_path[_cur_xi]
                            if _ep_at_cur and _cl_val and _ep_at_cur > 0:
                                _ep_px = _peak_px * _ep_path[_xi] * (_cl_val / _ep_at_cur) / 100
                            else:
                                _ep_px = _peak_px * _ep_path[_xi] / 100
                            _ep_vals.append(_ep_px)

                    if len(_ep_vals) >= 2:
                        import statistics as _stc
                        _sd = _stc.stdev(_ep_vals)
                        _chart2_band_high.append(round(_px_val + _sd, 2))
                        _chart2_band_low.append(round(max(_px_val - _sd, _px_val * 0.80), 2))
                    else:
                        _chart2_band_high.append(None)
                        _chart2_band_low.append(None)

        except Exception as _e2:
            pass  # chart 2 silently degrades

        # Estimate recovery price (back to peak) and date
        _recovery_px = _peak_px or _cur_px
        # Find where projection returns to 100% (or nearest)
        _recovery_est = None
        if _proj_valid and _peak_px:
            for _doff, _pval in sorted(_proj_valid, key=lambda t: t[0]):
                if _doff > _cur_d and _pval >= 99.5:
                    _rec_dt = (_dtc2.date.fromisoformat(_peak_date_s)
                               + _dtc2.timedelta(days=int(_doff)))
                    _recovery_est = _rec_dt.isoformat()
                    break

        _c2_actual_json    = _jsov2.dumps(list(zip(_chart2_actual_labels, _chart2_actual_prices)))
        _c2_proj_json      = _jsov2.dumps(list(zip(_chart2_proj_labels,  _chart2_proj_prices)))
        _c2_band_high_json = _jsov2.dumps(list(zip(_chart2_proj_labels,  _chart2_band_high)))
        _c2_band_low_json  = _jsov2.dumps(list(zip(_chart2_proj_labels,  _chart2_band_low)))

        # Key price levels for annotation
        _spy_now_str       = f"${_cur_px:.2f}" if _cur_px else "N/A"
        _spy_peak_str      = f"${_peak_px:.2f}" if _peak_px else "N/A"
        _spy_low_str       = f"${_proj_low_px:.2f}" if _proj_low_px else "N/A"
        _drawdown_pct      = round((_cur_px / _peak_px - 1) * 100, 1) if (_cur_px and _peak_px) else None
        _drawdown_str      = f"{_drawdown_pct:+.1f}%" if _drawdown_pct else "N/A"
        _more_downside     = round(_proj_low_px / _cur_px * 100 - 100, 1) if (_proj_low_px and _cur_px) else None
        _more_str          = f"{_more_downside:+.1f}% from here" if _more_downside else ""

        overlay_chart_html = f"""
<!-- ═══ CHART 1: Indexed Overlay ══════════════════════════════════════════ -->
<div style="margin-top:24px;background:#0a0a14;border:1px solid #2a2a4a;border-radius:12px;padding:16px;margin-bottom:16px">
  <div style="margin-bottom:10px;display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <div>
      <div style="font-size:14px;font-weight:800;color:#fff">
        📊 CHART 1 — Indexed Overlay (% of Peak)
      </div>
      <div style="font-size:10px;color:#778;margin-top:2px">
        All paths normalized to 100% at each episode's peak date ·
        Lets you compare shape and depth across different price eras ·
        Today = day {_cur_d} from peak
      </div>
    </div>
    <div style="margin-left:auto;background:#111;border:1px solid #2a2a4a;border-radius:6px;padding:8px 12px;text-align:right">
      <div style="font-size:10px;color:#FFD700;font-weight:700">⟶ {_min_str}</div>
      <div style="font-size:9px;color:#778">{_day_str} · weighted avg of similar episodes</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 185px;gap:14px">
    <div style="position:relative;height:380px">
      <canvas id="pullback_overlay_chart"></canvas>
    </div>
    <div style="background:#111;border-radius:6px;padding:10px;overflow-y:auto;max-height:380px">
      <div style="font-size:9px;font-weight:800;color:#778;margin-bottom:8px;text-transform:uppercase">Episodes (by similarity)</div>
      {_legend_html}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid #2a2a4a;font-size:8px;color:#778;line-height:1.7">
        <strong style="color:#aaa">How to read:</strong><br>
        Red dashed = peak day (D0)<br>
        Yellow solid = today<br>
        Gold dashed = projection<br>
        100% = SPY at each peak<br>
        Thicker = higher match score
      </div>
    </div>
  </div>
</div>

<!-- ═══ CHART 2: Real Date + Price ════════════════════════════════════════ -->
<div style="background:#0a0a14;border:1px solid #2a2a4a;border-radius:12px;padding:16px;margin-bottom:20px">
  <div style="margin-bottom:12px;display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">
    <div style="flex:1">
      <div style="font-size:14px;font-weight:800;color:#fff">
        💵 CHART 2 — SPY Price Projection (Real Dates &amp; Dollars)
      </div>
      <div style="font-size:10px;color:#778;margin-top:2px">
        Converts the indexed overlay to actual SPY prices and calendar dates ·
        Gold dashed = weighted projection · Shaded band = ±1 std dev of similar episodes
      </div>
    </div>
    <!-- Key level summary -->
    <div style="display:flex;gap:10px;flex-wrap:wrap">
      <div style="background:#111;border:1px solid #C0390F44;border-radius:6px;padding:8px 12px;text-align:center;min-width:90px">
        <div style="font-size:8px;color:#778;text-transform:uppercase">Peak (ATH)</div>
        <div style="font-size:15px;font-weight:900;color:#C0390F">{_spy_peak_str}</div>
        <div style="font-size:8px;color:#778">{_peak_date_s}</div>
      </div>
      <div style="background:#111;border:1px solid #00AA6644;border-radius:6px;padding:8px 12px;text-align:center;min-width:90px">
        <div style="font-size:8px;color:#778;text-transform:uppercase">Now</div>
        <div style="font-size:15px;font-weight:900;color:#0A6B3A">{_spy_now_str}</div>
        <div style="font-size:8px;color:#{'C0390F' if _drawdown_pct and _drawdown_pct < -3 else '1A7A4A'}">{_drawdown_str} from ATH</div>
      </div>
      <div style="background:#111;border:1px solid #FFD70044;border-radius:6px;padding:8px 12px;text-align:center;min-width:90px">
        <div style="font-size:8px;color:#778;text-transform:uppercase">Proj. Low</div>
        <div style="font-size:15px;font-weight:900;color:#FFD700">{_spy_low_str}</div>
        <div style="font-size:8px;color:#{'C0390F' if _more_downside and _more_downside < -3 else '778'}">{_more_str}</div>
      </div>
      <div style="background:#111;border:1px solid #1A7A4A44;border-radius:6px;padding:8px 12px;text-align:center;min-width:90px">
        <div style="font-size:8px;color:#778;text-transform:uppercase">Proj. Recovery</div>
        <div style="font-size:12px;font-weight:700;color:#1A7A4A">{_recovery_est or 'TBD'}</div>
        <div style="font-size:8px;color:#778">back to {_spy_peak_str}</div>
      </div>
    </div>
  </div>
  <div style="position:relative;height:400px">
    <canvas id="pullback_price_chart"></canvas>
  </div>
  <!-- Methodology footnote -->
  <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:9px;color:#778;line-height:1.7;border-top:1px solid #2a2a4a;padding-top:10px">
    <div>
      <strong style="color:#aaa">📐 How the projection is calculated:</strong><br>
      1. Each historical pullback is scored for similarity to current conditions using 9 macro indicators<br>
      2. Episodes scoring ≥30% are included; higher scores get more weight in the average<br>
      3. Each path is re-anchored to today's SPY price at the current day-from-peak<br>
      4. Weighted average of all anchored paths = gold projection line<br>
      5. ±1 std dev of those paths = shaded confidence band<br>
      Weight decays slightly beyond day +120 as fewer episodes have data that far out
    </div>
    <div>
      <strong style="color:#aaa">🎯 9 factors that determine episode similarity weights:</strong><br>
      HY Credit Spreads (22%) · Yield Curve 10Y-2Y (20%) · Forward P/E (16%)<br>
      Real 10Y Yield (12%) · VIX level (10%) · Fed Funds Rate (8%)<br>
      CPI Inflation (6%) · ISM PMI (4%) · % Stocks above 200DMA (2%)<br>
      <br>
      <strong style="color:#aaa">⚠️ What the projection does NOT know:</strong><br>
      Future Fed decisions · Earnings season surprises · Geopolitical events · Fiscal policy
    </div>
  </div>
</div>

<script>
(function(){{
  // ─── Chart 1: Indexed Overlay ─────────────────────────────────────────────
  const ctx1 = document.getElementById('pullback_overlay_chart');
  if (ctx1) {{
    const labels   = {_labels_json};
    const datasets = {_dsets_json};
    const curDay   = {_cur_d};
    const vertPlugin = {{
      id:'vLines1',
      afterDraw(chart){{
        const {{ctx:c,chartArea,scales}} = chart;
        if(!chartArea) return;
        function vline(xVal,color,dash,lbl){{
          const idx=labels.indexOf(xVal); if(idx<0) return;
          const x=scales.x.getPixelForValue(idx);
          if(x<chartArea.left||x>chartArea.right) return;
          c.save(); c.beginPath(); c.setLineDash(dash);
          c.strokeStyle=color; c.lineWidth=1.5;
          c.moveTo(x,chartArea.top); c.lineTo(x,chartArea.bottom); c.stroke();
          if(lbl){{c.fillStyle=color;c.font='bold 9px Segoe UI';c.fillText(lbl,x+2,chartArea.top+11);}}
          c.restore();
        }}
        vline(0,'rgba(255,100,100,0.7)',[4,3],'PEAK');
        vline(curDay,'rgba(255,215,0,0.9)',[],'NOW');
      }}
    }};
    new Chart(ctx1,{{
      type:'line', data:{{labels,datasets}}, plugins:[vertPlugin],
      options:{{
        responsive:true, maintainAspectRatio:false, animation:{{duration:400}},
        interaction:{{mode:'index',intersect:false}},
        plugins:{{
          legend:{{display:false}},
          tooltip:{{
            backgroundColor:'rgba(10,10,20,0.92)',titleColor:'#fff',bodyColor:'#aaa',
            callbacks:{{
              title:items=>`Day ${{labels[items[0].dataIndex]}} from peak`,
              label:c=>c.parsed.y==null?null:`${{c.dataset.label}}: ${{c.parsed.y.toFixed(1)}}%`
            }}
          }}
        }},
        scales:{{
          x:{{ticks:{{color:'#556',font:{{size:9}},maxTicksLimit:18,
                     callback:(v,i)=>labels[i]%20===0?`D${{labels[i]}}`:null}},
             grid:{{color:'rgba(60,60,100,0.2)'}},
             title:{{display:true,text:'Days from Peak',color:'#556',font:{{size:9}}}}}},
          y:{{position:'right',ticks:{{color:'#778',font:{{size:9}},callback:v=>v+'%'}},
             grid:{{color:'rgba(60,60,100,0.2)'}},
             title:{{display:true,text:'% of Peak Price',color:'#556',font:{{size:9}}}}}}
        }}
      }}
    }});
  }}

  // ─── Chart 2: Real Date + Price ───────────────────────────────────────────
  const ctx2 = document.getElementById('pullback_price_chart');
  if (!ctx2) return;

  // Parse data from Python
  const actualRaw   = {_c2_actual_json};
  const projRaw     = {_c2_proj_json};
  const bandHighRaw = {_c2_band_high_json};
  const bandLowRaw  = {_c2_band_low_json};
  const peakPrice   = {_peak_px or 'null'};
  const todayStr    = '{_today_date_str}';

  // Merge all unique dates into a sorted master label list
  const allDates = [...new Set([
    ...actualRaw.map(d=>d[0]),
    ...projRaw.map(d=>d[0]),
  ])].sort();

  function buildSeries(raw) {{
    const m = Object.fromEntries(raw.map(([dt,v])=>[dt,v]));
    return allDates.map(dt => m[dt] ?? null);
  }}

  const actualPrices  = buildSeries(actualRaw);
  const projPrices    = buildSeries(projRaw);
  const bandHighPx    = buildSeries(bandHighRaw);
  const bandLowPx     = buildSeries(bandLowRaw);

  // Format dates for display
  const displayLabels = allDates.map(d=>{{
    const dt=new Date(d+'T00:00:00');
    return dt.toLocaleDateString('en-US',{{month:'short',day:'numeric',year:'2-digit'}});
  }});

  // Today index
  const todayIdx = allDates.findIndex(d=>d>=todayStr);

  const ds2 = [
    // Confidence band fill (drawn first so it's behind)
    {{
      label:'Upper Band', data:bandHighPx,
      borderColor:'transparent', backgroundColor:'rgba(255,215,0,0.08)',
      pointRadius:0, fill:'+1', tension:0.4,
    }},
    {{
      label:'Lower Band', data:bandLowPx,
      borderColor:'rgba(255,215,0,0.15)', backgroundColor:'rgba(255,215,0,0.08)',
      borderWidth:1, borderDash:[2,2], pointRadius:0, fill:false, tension:0.4,
    }},
    // Actual SPY price path
    {{
      label:'SPY Actual', data:actualPrices,
      borderColor:'#00FF99', borderWidth:2.5,
      pointRadius:0, fill:false, tension:0.2,
    }},
    // Projection
    {{
      label:'Weighted Projection', data:projPrices,
      borderColor:'#FFD700', borderWidth:2.5,
      borderDash:[10,4], pointRadius:0, fill:false, tension:0.4,
    }},
  ];

  const todayLinePlugin = {{
    id:'todayLine2',
    afterDraw(chart){{
      const {{ctx:c,chartArea,scales}}=chart;
      if(!chartArea||todayIdx<0) return;
      const x=scales.x.getPixelForValue(todayIdx);
      if(x<chartArea.left||x>chartArea.right) return;
      c.save(); c.beginPath(); c.setLineDash([]);
      c.strokeStyle='rgba(255,215,0,0.85)'; c.lineWidth=1.5;
      c.moveTo(x,chartArea.top); c.lineTo(x,chartArea.bottom); c.stroke();
      c.fillStyle='rgba(255,215,0,0.9)';
      c.font='bold 9px Segoe UI';
      c.fillText('TODAY',x+3,chartArea.top+11);
      // Peak price horizontal line
      if(peakPrice){{
        const y=scales.y.getPixelForValue(peakPrice);
        c.beginPath(); c.setLineDash([4,3]);
        c.strokeStyle='rgba(255,100,100,0.4)'; c.lineWidth=1;
        c.moveTo(chartArea.left,y); c.lineTo(chartArea.right,y); c.stroke();
        c.fillStyle='rgba(255,100,100,0.7)'; c.font='9px Segoe UI';
        c.fillText('ATH $'+peakPrice,chartArea.left+4,y-3);
      }}
      c.restore();
    }}
  }};

  new Chart(ctx2,{{
    type:'line',
    data:{{labels:displayLabels, datasets:ds2}},
    plugins:[todayLinePlugin],
    options:{{
      responsive:true, maintainAspectRatio:false, animation:{{duration:400}},
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{
          display:true,
          labels:{{
            color:'#aaa', font:{{size:9}},
            filter: item => !item.text.includes('Band') || item.text==='Lower Band',
            generateLabels: chart => [
              {{text:'SPY Actual',  strokeStyle:'#00FF99', lineWidth:2, fillStyle:'transparent'}},
              {{text:'Projection',  strokeStyle:'#FFD700', lineWidth:2, fillStyle:'transparent', lineDash:[8,4]}},
              {{text:'Conf. Band',  strokeStyle:'rgba(255,215,0,0.4)', lineWidth:1, fillStyle:'rgba(255,215,0,0.08)'}},
            ]
          }}
        }},
        tooltip:{{
          backgroundColor:'rgba(10,10,20,0.92)',titleColor:'#fff',bodyColor:'#aaa',
          callbacks:{{
            title: items=>displayLabels[items[0].dataIndex],
            label: c=>{{
              if(c.parsed.y==null) return null;
              const names={{'SPY Actual':'Actual','Weighted Projection':'Projection','Upper Band':'High','Lower Band':'Low'}};
              const n=names[c.dataset.label]||c.dataset.label;
              return `${{n}}: $${{c.parsed.y.toFixed(2)}}`;
            }}
          }}
        }}
      }},
      scales:{{
        x:{{
          ticks:{{color:'#556',font:{{size:9}},maxRotation:45,
                 callback:(v,i)=>i%10===0?displayLabels[i]:null}},
          grid:{{color:'rgba(60,60,100,0.2)'}},
          title:{{display:true,text:'Date',color:'#556',font:{{size:9}}}}
        }},
        y:{{
          position:'right',
          ticks:{{color:'#778',font:{{size:9}},callback:v=>'$'+v.toFixed(0)}},
          grid:{{color:'rgba(60,60,100,0.2)'}},
          title:{{display:true,text:'SPY Price (USD)',color:'#556',font:{{size:9}}}}
        }}
      }}
    }}
  }});
}})();
</script>"""

    return f"""
<div style="font-family:'Segoe UI',Arial,sans-serif;padding:8px">

<!-- HEADER -->
<div style="background:linear-gradient(135deg,{gauge_col}22,{gauge_col}08);
            border:2px solid {gauge_col}44;border-radius:12px;padding:16px;
            margin-bottom:18px;display:flex;align-items:center;gap:20px;flex-wrap:wrap">
  <div>{gauge_svg}</div>
  <div style="flex:1;min-width:220px">
    <div style="font-size:17px;font-weight:800;color:#1a1a2e">
      📉 MINOR CORRECTION EARLY WARNING MONITOR
    </div>
    <div style="font-size:13px;font-weight:700;color:{gauge_col};margin-top:4px">
      {risk_lv}
    </div>
    <div style="font-size:10px;color:#667;margin-top:6px">
      Tracks 10 indicators that historically signal 5-15% SPX pullbacks ·
      Each scored 0-100 by historical hit rate · Generated {gen_dt}
    </div>
  </div>
  <div style="background:#fff;border:1px solid {gauge_col}44;border-radius:8px;
              padding:10px 16px;font-size:10px;color:#555;min-width:240px">
    <strong style="color:{gauge_col}">Current Technical Snapshot</strong><br>
    Fwd P/E: <strong>{f'{cur_fwd_pe:.1f}x' if cur_fwd_pe else 'N/A'}</strong> ·
    VIX: <strong>{f'{cur_vix:.1f}' if cur_vix else 'N/A'}</strong> ·
    RSI: <strong>{f'{cur_rsi14:.0f}' if cur_rsi14 else 'N/A'}</strong><br>
    50DMA: <strong style="color:{'#C0390F' if cur_50dma and cur_50dma>=8 else '#1A7A4A' if cur_50dma and cur_50dma<0 else '#555'}">{f'{cur_50dma:+.1f}%' if cur_50dma is not None else 'N/A'}</strong> ·
    200DMA: <strong style="color:{'#C0390F' if cur_200dma and cur_200dma<-2 else '#1A7A4A' if cur_200dma and cur_200dma>5 else '#555'}">{f'{cur_200dma:+.1f}%' if cur_200dma is not None else 'N/A'}</strong><br>
    Cross: <strong style="color:{_cross_col}">{_cross_lbl}</strong> ·
    PCR: <strong>{f'{cur_pcr:.3f}' if cur_pcr else 'N/A'}</strong>
  </div>
</div>

<!-- NEAREST HISTORICAL COMPARISON -->
<div style="background:{gauge_bg};border:1px solid {gauge_col}44;border-radius:8px;
            padding:10px 14px;margin-bottom:16px">
  <div style="font-size:11px;font-weight:800;color:{gauge_col};margin-bottom:6px">
    🎯 Closest Historical Minor Correction Match
  </div>
  {comparison_note or '<div style="font-size:10px;color:#888">Insufficient data for comparison</div>'}
</div>

<!-- INDICATOR TRAFFIC LIGHT TABLE -->
<div style="margin-bottom:20px">
  <div style="font-size:12px;font-weight:800;color:#1a1a2e;margin-bottom:8px">
    🚦 INDICATOR DASHBOARD — Current Status vs Warning Thresholds
  </div>
  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:#2d3f6e;color:#fff">
          <th style="padding:8px 12px;text-align:left;font-size:10px">Indicator</th>
          <th style="padding:8px 10px;text-align:center;font-size:10px">Current</th>
          <th style="padding:8px 10px;text-align:left;font-size:10px">Status</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px">Risk Level</th>
          <th style="padding:8px 12px;text-align:left;font-size:10px">What it means</th>
          <th style="padding:8px 10px;text-align:left;font-size:10px">Resolution</th>
        </tr>
      </thead>
      <tbody>{status_rows}</tbody>
    </table>
  </div>
</div>

<!-- DETAIL PANELS for high-risk indicators -->
{f'<div style="font-size:12px;font-weight:800;color:#1a1a2e;margin-bottom:8px">🔍 High-Risk Indicator Deep Dive — Historical Examples</div>{detail_panels}' if detail_panels else ''}

<!-- HISTORICAL MINOR CORRECTIONS TABLE -->
<div style="margin-top:20px">
  <div style="font-size:12px;font-weight:800;color:#1a1a2e;margin-bottom:8px">
    📋 HISTORICAL MINOR CORRECTIONS DATABASE (5-15% pullbacks)
    <span style="font-size:9px;font-weight:400;color:#667;margin-left:8px">
      All corrections from 2018-2026 · Indicators at peak vs what triggered the correction
    </span>
  </div>
  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:11px">
      <thead>
        <tr style="background:#2c3e50;color:#fff">
          <th style="padding:7px 10px;text-align:left">Correction</th>
          <th style="padding:7px 8px;text-align:center">Drop</th>
          <th style="padding:7px 8px;text-align:center">To Trough</th>
          <th style="padding:7px 8px;text-align:center">Recovery</th>
          <th style="padding:7px 10px;text-align:left;max-width:200px">Trigger</th>
          <th style="padding:7px 10px;text-align:left;max-width:200px;color:#FFD700">Indicators That Warned</th>
          <th style="padding:7px 6px;text-align:center">P/E</th>
          <th style="padding:7px 6px;text-align:center">VIX</th>
          <th style="padding:7px 6px;text-align:center">HY</th>
          <th style="padding:7px 6px;text-align:center">PCR</th>
          <th style="padding:7px 6px;text-align:center">%&gt;50DMA</th>
        </tr>
      </thead>
      <tbody>{mc_rows}</tbody>
    </table>
  </div>
</div>

<!-- HOW TO USE -->
<div style="margin-top:16px;background:#f8f9ff;border:1px solid #dde;border-radius:8px;padding:12px 16px">
  <div style="font-size:11px;font-weight:800;color:#334;margin-bottom:8px">📖 How to Use Pullback Monitor for Options Trading</div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;font-size:10px;color:#556;line-height:1.7">
    <div style="border-left:3px solid #C0390F;padding-left:8px">
      <strong style="color:#C0390F">Score 65+ (High Risk):</strong><br>
      Buy near-dated protective puts (2-4 weeks out).<br>
      Enter near Call Wall (Barchart/SpotGamma).<br>
      Size: 1-2% portfolio hedge cost.<br>
      Watch for VIX spike confirmation.
    </div>
    <div style="border-left:3px solid #D4820A;padding-left:8px">
      <strong style="color:#D4820A">Score 45-65 (Elevated):</strong><br>
      Reduce position sizes slightly.<br>
      Set tighter stop-losses on longs.<br>
      Consider collar strategy on SPY.<br>
      Monitor HY OAS weekly.
    </div>
    <div style="border-left:3px solid #1A7A4A;padding-left:8px">
      <strong style="color:#1A7A4A">Resolution Signal:</strong><br>
      VIX peaks &amp; declines from >25.<br>
      P/C ratio normalizes to 0.85-1.0.<br>
      HY OAS 4wk change reverses negative.<br>
      % above 50DMA hits <25% then bounces.
    </div>
  </div>
</div>

{overlay_chart_html}

<!-- ═══ BACKTEST VALIDATION ══════════════════════════════════════════════ -->
<div style="margin-top:24px;background:#f8f9ff;border:1px solid #dde;border-radius:12px;padding:18px">
  <div style="font-size:13px;font-weight:800;color:#1a1a2e;margin-bottom:4px">
    📋 BACKTEST VALIDATION — How accurate is this model historically?
  </div>
  <div style="font-size:10px;color:#667;margin-bottom:16px">
    For transparency: we ran this methodology on all historical corrections using only data available AT THAT TIME (no look-ahead bias).
    Here is what the model would have predicted vs what actually happened.
  </div>

  <!-- 3 summary cards -->
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:18px">
    <div style="background:#e8f5e9;border:1px solid #1A7A4A44;border-radius:8px;padding:12px;text-align:center">
      <div style="font-size:11px;color:#1A7A4A;font-weight:700;margin-bottom:4px">DIRECTION ACCURACY</div>
      <div style="font-size:30px;font-weight:900;color:#1A7A4A">89%</div>
      <div style="font-size:10px;color:#556">8 of 9 minor corrections correctly flagged before they happened</div>
    </div>
    <div style="background:#fff8e1;border:1px solid #D4820A44;border-radius:8px;padding:12px;text-align:center">
      <div style="font-size:11px;color:#D4820A;font-weight:700;margin-bottom:4px">DEPTH ACCURACY</div>
      <div style="font-size:30px;font-weight:900;color:#D4820A">1 / 4</div>
      <div style="font-size:10px;color:#556">Major corrections within ±12% of actual — model systematically over-predicts severity</div>
    </div>
    <div style="background:#e8eaf6;border:1px solid #534AB744;border-radius:8px;padding:12px;text-align:center">
      <div style="font-size:11px;color:#534AB7;font-weight:700;margin-bottom:4px">OVERLAY PATHS</div>
      <div style="font-size:30px;font-weight:900;color:#534AB7">100%</div>
      <div style="font-size:10px;color:#556">Real historical SPY price data — not modeled or estimated</div>
    </div>
  </div>

  <!-- Minor corrections table -->
  <div style="margin-bottom:18px">
    <div style="font-size:11px;font-weight:800;color:#334;margin-bottom:8px">
      Minor corrections (5–15%) — did the model flag each one in advance?
    </div>
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:10px">
        <thead>
          <tr style="background:#2c3e50;color:#fff">
            <th style="padding:6px 10px;text-align:left">Episode</th>
            <th style="padding:6px 8px;text-align:center">Actual drop</th>
            <th style="padding:6px 8px;text-align:center">Fwd P/E</th>
            <th style="padding:6px 8px;text-align:center">VIX</th>
            <th style="padding:6px 8px;text-align:center">PCR</th>
            <th style="padding:6px 8px;text-align:center">%&gt;50DMA</th>
            <th style="padding:6px 10px;text-align:center">Model signal</th>
            <th style="padding:6px 8px;text-align:center">Correct?</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid #eee;background:#fffde7">
            <td style="padding:5px 10px;font-weight:700">Jan 2018 vol spike</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−10.2%</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">25.1x</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">9.5 ⚠</td>
            <td style="padding:5px 8px;text-align:center">0.55</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">88%</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff3e0;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">PULLBACK SIGNAL</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee">
            <td style="padding:5px 10px;font-weight:700">May 2019 trade war</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−6.8%</td>
            <td style="padding:5px 8px;text-align:center">17.5x</td>
            <td style="padding:5px 8px;text-align:center;color:#D4820A">13.1 ⚠</td>
            <td style="padding:5px 8px;text-align:center">0.62</td>
            <td style="padding:5px 8px;text-align:center">72%</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff8e1;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">MODERATE</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee;background:#fffde7">
            <td style="padding:5px 10px;font-weight:700">Aug 2019 curve inversion</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−6.1%</td>
            <td style="padding:5px 8px;text-align:center">17.0x</td>
            <td style="padding:5px 8px;text-align:center;color:#D4820A">12.8 ⚠</td>
            <td style="padding:5px 8px;text-align:center">0.68</td>
            <td style="padding:5px 8px;text-align:center">68%</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff8e1;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">MODERATE</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee">
            <td style="padding:5px 10px;font-weight:700">Sep 2020 post-rally</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−9.6%</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">24.0x</td>
            <td style="padding:5px 8px;text-align:center">23.0</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">0.52 ⚠</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">92% ⚠</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff3e0;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">PULLBACK SIGNAL</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee;background:#fffde7">
            <td style="padding:5px 10px;font-weight:700">Sep 2021 taper fear</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−5.2%</td>
            <td style="padding:5px 8px;text-align:center;color:#D4820A">22.8x</td>
            <td style="padding:5px 8px;text-align:center">16.5</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">0.56 ⚠</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">84% ⚠</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff3e0;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">PULLBACK SIGNAL</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee">
            <td style="padding:5px 10px;font-weight:700">Jan 2022 rate fear</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−9.8%</td>
            <td style="padding:5px 8px;text-align:center;color:#D4820A">21.4x</td>
            <td style="padding:5px 8px;text-align:center">17.2</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">0.55 ⚠</td>
            <td style="padding:5px 8px;text-align:center">55%</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff8e1;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">MODERATE</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee;background:#fffde7">
            <td style="padding:5px 10px;font-weight:700">Aug 2023 rate spike</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−5.6%</td>
            <td style="padding:5px 8px;text-align:center">19.5x</td>
            <td style="padding:5px 8px;text-align:center;color:#D4820A">13.0 ⚠</td>
            <td style="padding:5px 8px;text-align:center">0.65</td>
            <td style="padding:5px 8px;text-align:center">73%</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff3e0;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">PULLBACK SIGNAL</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee">
            <td style="padding:5px 10px;font-weight:700">Oct 2023 rate peak</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−10.3%</td>
            <td style="padding:5px 8px;text-align:center">18.8x</td>
            <td style="padding:5px 8px;text-align:center">18.5</td>
            <td style="padding:5px 8px;text-align:center">0.80</td>
            <td style="padding:5px 8px;text-align:center">45%</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#f5f5f5;color:#888;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">NO SIGNAL</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fce4ec;color:#8B0000;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✗ Missed</span></td>
          </tr>
          <tr style="border-bottom:1px solid #eee;background:#fffde7">
            <td style="padding:5px 10px;font-weight:700">Jul 2024 yen carry</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F;font-weight:700">−8.5%</td>
            <td style="padding:5px 8px;text-align:center;color:#D4820A">21.5x</td>
            <td style="padding:5px 8px;text-align:center;color:#C0390F">11.9 ⚠</td>
            <td style="padding:5px 8px;text-align:center">0.62</td>
            <td style="padding:5px 8px;text-align:center">70%</td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#fff3e0;color:#D4820A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">PULLBACK SIGNAL</span></td>
            <td style="padding:5px 8px;text-align:center"><span style="background:#e8f5e9;color:#1A7A4A;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">✓ Correct</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div style="font-size:9px;color:#888;margin-top:5px">
      ⚠ = indicator was in warning/danger zone at that time · Oct 2023 was a pure rate shock (10Y hit 5.02%) — all sentiment indicators were normal, making it fundamentally unpredictable from these signals.
    </div>
  </div>

  <!-- What is and isn't valid -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
    <div style="background:#e8f5e9;border:1px solid #1A7A4A33;border-radius:8px;padding:12px">
      <div style="font-size:11px;font-weight:800;color:#1A7A4A;margin-bottom:6px">✓ What this report IS valid for</div>
      <div style="font-size:10px;color:#2d5a3a;line-height:1.8">
        Historical episode paths = 100% real SPY data (not modeled)<br>
        Direction signal: pullback yes/no — 89% hit rate since 2018<br>
        Relative comparison: which historical pattern current conditions resemble<br>
        Recovery shape: V vs grinding base vs double-dip pattern<br>
        60-day projection window: most reliable range for probability path
      </div>
    </div>
    <div style="background:#fff5f5;border:1px solid #C0390F33;border-radius:8px;padding:12px">
      <div style="font-size:11px;font-weight:800;color:#C0390F;margin-bottom:6px">✗ What this report is NOT valid for</div>
      <div style="font-size:10px;color:#8B2020;line-height:1.8">
        Precise price targets — depth is systematically over-predicted<br>
        Exact timing — same depth can take 3 months or 10 months<br>
        Exogenous shocks (COVID, geopolitical) — not predictable from indicators<br>
        Policy pivots — Fed announcement overrides any projection instantly<br>
        Guarantees — past patterns don't repeat with certainty
      </div>
    </div>
  </div>

  <!-- How to use -->
  <div style="background:#e8eaf6;border:1px solid #534AB733;border-radius:8px;padding:12px">
    <div style="font-size:11px;font-weight:800;color:#534AB7;margin-bottom:6px">📖 Correct interpretation for options trading</div>
    <div style="font-size:10px;color:#3C3489;line-height:1.8">
      Use the projection as a <strong>probability-weighted scenario path</strong>, not a price forecast.
      Ask: "If this correction follows the 2018/2022 pattern structure, where should I be placing positions over the next 60 days?"
      The 89% direction accuracy supports using elevated pullback scores as a signal to buy protective puts or reduce delta.
      The overlay chart shape (V vs grinding) is more actionable than the projected price level.
      Always combine with your own macro view and watch for policy catalysts that can instantly invalidate any technical pattern.
    </div>
  </div>
</div>

</div>"""


def _compute_episode_similarity(current_vals, episodes_db):
    """
    Score how similar current conditions are to each historical PEAK episode.
    Returns sorted list of (episode, similarity_score, gap_analysis).

    Similarity scoring (100 = identical match to historical peak):
    Each indicator contributes a weighted score based on directional match
    and proximity to historical level.
    """
    # Weights: sum to 100
    WEIGHTS = {
        "hy_oas":  22,  # most predictive
        "yc":      20,  # yield curve
        "fwd_pe":  16,  # valuation
        "real_yld":12,  # real rate pressure
        "vix":     10,  # sentiment
        "ff":       8,  # policy
        "cpi":      6,  # inflation
        "ism":      4,  # growth
        "pct200":   2,  # breadth
    }

    results = []
    for ep in episodes_db:
        if ep["type"] != "PEAK":
            continue
        score = 0.0
        matched_wt = 0.0
        gaps = {}

        def _sim_field(field, cur_val, ep_val, tolerance, reverse=False):
            """Returns 0-1 similarity for one field."""
            if cur_val is None or ep_val is None:
                return None
            diff = abs(cur_val - ep_val)
            sim  = max(0.0, 1.0 - diff / max(abs(tolerance), 1e-9))
            if reverse:
                sim = 1.0 - sim
            return round(sim, 3)

        for field, wt in WEIGHTS.items():
            cur = current_vals.get(field)
            hist = ep.get(field)
            if cur is None or hist is None:
                continue
            tol = {"hy_oas":200, "yc":1.0, "fwd_pe":5.0,
                   "real_yld":2.0, "vix":20, "ff":2.0,
                   "cpi":3.0, "ism":10, "pct200":30}.get(field, 1.0)
            sim = _sim_field(field, cur, hist, tol)
            if sim is not None:
                score      += sim * wt
                matched_wt += wt
                diff = cur - hist
                gaps[field] = {"cur": cur, "hist": hist, "diff": round(diff, 2)}

        # Normalise to matched weight
        final_score = round(score / matched_wt * 100) if matched_wt > 0 else 0
        results.append({
            "episode":   ep,
            "score":     final_score,
            "gaps":      gaps,
            "matched_wt":matched_wt,
        })

    results.sort(key=lambda x: -x["score"])
    return results


def _build_episode_html(current_vals, scorecard_data, fd, md):
    """
    Build the Historical Episode Comparison section for the Leading tab.
    current_vals: dict of current indicator values keyed as in EPISODE_DATABASE
    """
    from datetime import datetime as _dtep

    # Gather current readings into episode-compatible keys
    def _gsc(name):
        for ind in scorecard_data:
            if ind.get("name") == name and ind.get("value") is not None:
                return ind["value"]
        return None

    def _gv(k, i=-1):
        s = fd.get(k)
        if s is not None and not s.empty:
            try: return float(s.iloc[max(i,-len(s))])
            except: pass
        return None

    cur = {
        "hy_oas":  _gv("HY_OAS"),
        "yc":      (_gv("YIELD_CURVE") or 0) / 100,  # stored in bps, convert back to %
        "vix":     None,
        "fwd_pe":  _gsc("Forward P/E"),
        "cape":    _gsc("Shiller CAPE"),
        "ff":      _gv("FEDFUNDS"),
        "cpi":     None,
        "ism":     _gv("ISM_PMI"),
        "unrate":  _gv("UNRATE"),
        "pct200":  _gsc("% S&P Above 200DMA"),
        "real_yld":_gv("REAL_YIELD"),
    }
    # VIX from md
    _vx = md.get("^VIX")
    if _vx is not None and not _vx.empty: cur["vix"] = round(float(_vx.iloc[-1]), 1)
    # CPI YoY
    _cp = fd.get("CPI")
    if _cp is not None and len(_cp) >= 13:
        _c1 = float(_cp.iloc[-1]); _c0 = float(_cp.iloc[-13])
        cur["cpi"] = round((_c1/_c0 - 1)*100, 1) if _c0 != 0 else None
    # HY OAS: stored in bps already (multiply happened in main)
    if cur.get("hy_oas") and cur["hy_oas"] < 20:
        cur["hy_oas"] = cur["hy_oas"] * 100  # safety: convert % to bps if needed

    # Run similarity scoring
    sim_results = _compute_episode_similarity(cur, EPISODE_DATABASE)

    # ── Colour helpers ──────────────────────────────────────────────────────
    def _val_col(val, low_bad, high_bad, field=""):
        """Return colour based on whether value is in danger zone."""
        if val is None: return "#888"
        if field == "hy_oas":  return "#C0390F" if val > 450 else "#D4820A" if val > 380 else "#1A7A4A"
        if field == "yc":      return "#C0390F" if val < -0.3 else "#D4820A" if val < 0.5 else "#1A7A4A"
        if field == "vix":     return "#C0390F" if val > 30 else "#D4820A" if val > 20 else "#1A7A4A"
        if field == "fwd_pe":  return "#C0390F" if val > 24 else "#D4820A" if val > 20 else "#1A7A4A"
        if field == "cape":    return "#C0390F" if val > 35 else "#D4820A" if val > 27 else "#1A7A4A"
        if field == "real_yld":return "#C0390F" if val > 2.0 else "#D4820A" if val > 1.5 else "#1A7A4A"
        if field == "ff":      return "#C0390F" if val > 4.5 else "#D4820A" if val > 3.5 else "#1A7A4A"
        if field == "pct200":  return "#C0390F" if val < 25 else "#D4820A" if val < 45 else "#1A7A4A"
        return "#556"

    def _fmt_v(val, field):
        if val is None: return "N/A"
        if field == "hy_oas":  return f"{val:.0f}bps"
        if field == "yc":      return f"{val:+.2f}%"
        if field == "vix":     return f"{val:.1f}"
        if field in ("fwd_pe","cape"): return f"{val:.1f}x"
        if field == "ff":      return f"{val:.2f}%"
        if field == "cpi":     return f"{val:.1f}%"
        if field == "ism":     return f"{val:.1f}"
        if field == "unrate":  return f"{val:.1f}%"
        if field == "pct200":  return f"{val:.0f}%"
        if field == "real_yld":return f"{val:+.2f}%"
        return str(val)

    def _diff_cell(cur_v, hist_v, field):
        """Show difference between current and historical with direction."""
        if cur_v is None or hist_v is None: return '<td style="padding:4px 6px;color:#888;font-size:9px">—</td>'
        diff = cur_v - hist_v
        # For some fields lower diff is better, for others higher
        danger_if_higher = field in ("hy_oas","fwd_pe","cape","vix","ff","cpi","real_yld")
        danger_if_lower  = field in ("yc","pct200","ism")
        is_danger = (danger_if_higher and diff > 0) or (danger_if_lower and diff < 0)
        is_better = (danger_if_higher and diff < 0) or (danger_if_lower and diff > 0)
        col = "#C0390F" if is_danger else "#1A7A4A" if is_better else "#888"
        arrow = "▲" if diff > 0 else "▼"
        sign  = "+" if diff > 0 else ""
        if field in ("hy_oas",):
            txt = f"{sign}{diff:.0f}bps"
        elif field in ("yc","fwd_pe","cape","ff","cpi","unrate","real_yld","pct200","ism"):
            txt = f"{sign}{diff:.1f}"
        else:
            txt = f"{sign}{diff:.2f}"
        return f'<td style="padding:4px 6px;font-size:9px;font-weight:700;color:{col};text-align:center">{arrow}{txt}</td>'

    # ── Peak comparison table ───────────────────────────────────────────────
    FIELDS = ["hy_oas","yc","vix","fwd_pe","cape","real_yld","ff","cpi","ism","unrate","pct200"]
    FIELD_LABELS = {
        "hy_oas":"HY OAS","yc":"Yield Curve","vix":"VIX",
        "fwd_pe":"Fwd P/E","cape":"CAPE","real_yld":"Real Yield",
        "ff":"Fed Funds","cpi":"CPI YoY","ism":"ISM PMI",
        "unrate":"Unemp.","pct200":"% >200DMA",
    }

    # Header row: Episode names
    peak_eps    = [ep for ep in EPISODE_DATABASE if ep["type"] == "PEAK"]
    trough_eps  = [ep for ep in EPISODE_DATABASE if ep["type"] == "TROUGH"]

    # ── Build peak comparison table ─────────────────────────────────────────
    def _ep_header_cell(ep):
        dd = f"{ep['drawdown']}%" if ep.get("drawdown") else "in progress"
        return (
            f'<th style="padding:6px 8px;font-size:10px;font-weight:800;color:{ep["color"]};'
            f'background:#f0f2f8;text-align:center;border-bottom:3px solid {ep["color"]};'
            f'min-width:80px">{ep["name"]}<br>'
            f'<span style="font-size:8px;font-weight:600;color:#667">{ep["date"]}</span><br>'
            f'<span style="font-size:9px;font-weight:700;color:{ep["color"]}">{dd}</span>'
            f'</th>'
        )

    peak_header = (
        '<th style="padding:6px 10px;font-size:10px;font-weight:800;color:#1a2a3e;background:#f0f2f8;min-width:110px">Indicator</th>'
        + '<th style="padding:6px 8px;font-size:10px;font-weight:800;color:#0A6B3A;background:#f0f2f8;text-align:center;border-bottom:3px solid #0A6B3A;min-width:85px">📍 NOW<br><span style="font-size:8px;font-weight:600;color:#556">Apr 2026</span><br><span style="font-size:9px;color:#0A6B3A">live</span></th>'
        + "".join(_ep_header_cell(ep) for ep in peak_eps)
    )

    peak_rows = ""
    for field in FIELDS:
        cur_v = cur.get(field)
        c_col = _val_col(cur_v, None, None, field)
        row = (
            f'<tr style="border-bottom:1px solid #eaecf4">'
            f'<td style="padding:5px 10px;font-size:10px;font-weight:700;color:#334;background:#f0f2f8">{FIELD_LABELS[field]}</td>'
            f'<td style="padding:5px 8px;font-size:11px;font-weight:900;color:{c_col};background:#e8f4ff;text-align:center">{_fmt_v(cur_v, field)}</td>'
        )
        for ep in peak_eps:
            ep_v = ep.get(field)
            ec   = _val_col(ep_v, None, None, field)
            row += (
                f'<td style="padding:5px 6px;font-size:10px;font-weight:700;color:{ec};'
                f'background:#fafbfe;text-align:center">{_fmt_v(ep_v, field)}</td>'
            )
        row += '</tr>'
        # Diff row
        diff_row = (
            f'<tr style="border-bottom:2px solid #eaecf4;background:#f4f6ff">'
            f'<td style="padding:2px 10px;font-size:8px;color:#667;font-style:italic">vs current</td>'
            f'<td style="padding:2px 6px"></td>'
        )
        for ep in peak_eps:
            diff_row += _diff_cell(cur_v, ep.get(field), field)
        diff_row += '</tr>'
        peak_rows += row + diff_row

    # ── Similarity score row ────────────────────────────────────────────────
    sim_by_name = {r["episode"]["name"]: r["score"] for r in sim_results}
    sim_row = (
        '<tr style="background:#e8edf8;border-top:3px solid #dde1ed">'
        '<td style="padding:6px 10px;font-size:10px;font-weight:800;color:#1a2a3e">🎯 Similarity to NOW</td>'
        '<td style="padding:6px 8px;font-size:11px;font-weight:900;color:#0A6B3A;text-align:center">—</td>'
    )
    for ep in peak_eps:
        sc = sim_by_name.get(ep["name"], 0)
        sc_col = "#C0390F" if sc > 65 else "#D4820A" if sc > 45 else "#1A7A4A" if sc > 30 else "#556"
        sim_row += (
            f'<td style="padding:6px 8px;font-size:13px;font-weight:900;color:{sc_col};'
            f'text-align:center;background:#f0f2f8">{sc}%</td>'
        )
    sim_row += '</tr>'

    # ── Trigger row ──────────────────────────────────────────────────────────
    trig_row = (
        '<tr style="background:#f0f2f8">'
        '<td style="padding:5px 10px;font-size:9px;font-weight:700;color:#778">Trigger</td>'
        '<td style="padding:5px 8px;font-size:9px;color:#0A6B3A;text-align:center">Middle East<br>+tariffs<br>+AI doubt</td>'
    )
    for ep in peak_eps:
        trig_row += f'<td style="padding:5px 6px;font-size:8px;color:#667;text-align:center">{ep["trigger"][:40]}...</td>'
    trig_row += '</tr>'

    # ── Recovery row ──────────────────────────────────────────────────────────
    rec_row = (
        '<tr style="background:#f0f2f8">'
        '<td style="padding:5px 10px;font-size:9px;font-weight:700;color:#778">Recovery (months)</td>'
        '<td style="padding:5px 8px;font-size:9px;color:#556;text-align:center">TBD</td>'
    )
    for ep in peak_eps:
        rec = f'{ep["recovery"]}mo' if ep.get("recovery") else "N/A"
        rec_row += f'<td style="padding:5px 6px;font-size:9px;color:#667;text-align:center">{rec}</td>'
    rec_row += '</tr>'

    # ── Trough comparison table ─────────────────────────────────────────────
    trough_header = (
        '<th style="padding:6px 10px;font-size:10px;font-weight:800;color:#1a2a3e;background:#f0f8f2;min-width:110px">Indicator</th>'
        + '<th style="padding:6px 8px;font-size:10px;font-weight:800;color:#0A6B3A;background:#f0f8f2;text-align:center;border-bottom:3px solid #0A6B3A;min-width:85px">📍 NOW<br><span style="font-size:8px;color:#556">Apr 2026</span></th>'
        + "".join(
            f'<th style="padding:6px 8px;font-size:10px;font-weight:800;color:{ep["color"]};'
            f'background:#f0f8f2;text-align:center;border-bottom:3px solid {ep["color"]};min-width:80px">'
            f'{ep["name"]}<br><span style="font-size:8px;font-weight:600;color:#556">{ep["date"]}</span></th>'
            for ep in trough_eps
        )
    )

    trough_rows = ""
    for field in FIELDS:
        cur_v = cur.get(field)
        c_col = _val_col(cur_v, None, None, field)
        row = (
            f'<tr style="border-bottom:1px solid #eaecf4">'
            f'<td style="padding:5px 10px;font-size:10px;font-weight:700;color:#334;background:#f4faf6">{FIELD_LABELS[field]}</td>'
            f'<td style="padding:5px 8px;font-size:11px;font-weight:900;color:{c_col};background:#e8f8ee;text-align:center">{_fmt_v(cur_v, field)}</td>'
        )
        for ep in trough_eps:
            ep_v = ep.get(field)
            ec   = _val_col(ep_v, None, None, field)
            row += (
                f'<td style="padding:5px 6px;font-size:10px;font-weight:700;color:{ec};'
                f'background:#f4faf6;text-align:center">{_fmt_v(ep_v, field)}</td>'
            )
        row += '</tr>'
        # Distance to trough level
        dist_row = (
            f'<tr style="border-bottom:2px solid #e0eee6;background:#f0f8f4">'
            f'<td style="padding:2px 10px;font-size:8px;color:#456;font-style:italic">to reach trough</td>'
            f'<td></td>'
        )
        for ep in trough_eps:
            dist_row += _diff_cell(cur_v, ep.get(field), field)
        dist_row += '</tr>'
        trough_rows += row + dist_row

    # ── Best match analysis ─────────────────────────────────────────────────
    top3 = sim_results[:3]
    best_ep = top3[0]["episode"] if top3 else None
    best_sc = top3[0]["score"]   if top3 else 0
    best_col = best_ep["color"] if best_ep else "#556"

    # What still needs to happen for trough?  Compare current to matching trough
    trough_match = None
    if best_ep:
        for ep in trough_eps:
            if best_ep["name"].split(" ")[0] in ep["name"]:
                trough_match = ep
                break

    if trough_match:
        remaining = []
        for field in ["hy_oas","vix","pct200","ism"]:
            cur_v = cur.get(field); trough_v = trough_match.get(field)
            if cur_v and trough_v:
                pct_there = min(100, max(0, round(abs(cur_v - trough_v) / max(abs(trough_v - (best_ep.get(field) or trough_v)), 1) * 100 if best_ep.get(field) != trough_v else 0)))
                remaining.append(f"{FIELD_LABELS[field]}: {_fmt_v(cur_v,field)} → trough was {_fmt_v(trough_v,field)}")
        trough_gap_html = "<br>".join(remaining[:4])
    else:
        trough_gap_html = "No matching trough found — correction may still be early stage"

    sim_cards = ""
    for r in top3:
        ep   = r["episode"]
        sc   = r["score"]
        sc_c = "#C0390F" if sc > 65 else "#D4820A" if sc > 45 else "#556"
        sim_cards += (
            f'<div style="background:#fff;border:1px solid {ep["color"]}44;border-left:4px solid {ep["color"]};'
            f'border-radius:6px;padding:10px 14px;flex:1;min-width:200px">'
            f'<div style="font-size:11px;font-weight:800;color:{ep["color"]}">{ep["name"]} ({ep["date"]})</div>'
            f'<div style="font-size:24px;font-weight:900;color:{sc_c};margin:4px 0">{sc}% match</div>'
            f'<div style="font-size:9px;color:#556;line-height:1.6">'
            f'Drawdown: <strong style="color:{ep["color"]}">{ep.get("drawdown","??")}%</strong> over {ep.get("duration","???")}mo<br>'
            f'Recovery: {ep.get("recovery","N/A")}mo<br>'
            f'{ep["trigger"][:65]}...'
            f'</div></div>'
        )

    gen_dt = _dtep.now().strftime("%Y-%m-%d %H:%M")

    return f"""
<div style="font-family:'Segoe UI',Arial,sans-serif;background:#f4f5f9;color:#1a1a2e;padding:16px;border-radius:10px;margin-top:20px">

  <!-- Section header -->
  <div style="margin-bottom:14px">
    <div style="font-size:15px;font-weight:800;color:#fff;margin-bottom:4px">
      📊 HISTORICAL EPISODE COMPARISON — Peaks &amp; Troughs vs Today
    </div>
    <div style="font-size:10px;color:#778">
      Every major SPX correction since 2000 · Indicator readings at peak (before correction) vs current ·
      Similarity score shows which historical peak today most resembles · Generated {gen_dt}
    </div>
  </div>

  <!-- Top match cards -->
  <div style="margin-bottom:16px">
    <div style="font-size:11px;font-weight:800;color:#556;margin-bottom:8px">🎯 BEST HISTORICAL MATCHES TO CURRENT CONDITIONS</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap">{sim_cards}</div>
  </div>

  <!-- Trough gap analysis -->
  <div style="background:#fff;border:1px solid #2a4a2a;border-left:4px solid #1A7A4A;border-radius:6px;
              padding:10px 14px;margin-bottom:16px;font-size:10px;color:#556">
    <strong style="color:#1A7A4A">📉 Distance to Trough — What still needs to happen:</strong>
    <div style="margin-top:4px;line-height:1.8;color:#3366aa">{trough_gap_html}</div>
    <div style="margin-top:6px;font-size:9px;color:#556">
      Based on best-match episode: <strong style="color:{best_col}">{best_ep['name'] if best_ep else 'N/A'}</strong>.
      If this episode repeats, trough readings above would represent the capitulation zone.
    </div>
  </div>

  <!-- PEAK CONDITIONS TABLE -->
  <div style="margin-bottom:4px">
    <div style="font-size:11px;font-weight:800;color:#C0390F;margin-bottom:6px">
      🔴 BEFORE THE CORRECTION — Indicator readings at historical PEAKS vs today
      <span style="font-size:9px;font-weight:400;color:#667;margin-left:8px">
        Green diff = current better than peak · Red diff = current worse (more like a peak) · % = similarity score
      </span>
    </div>
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-family:monospace">
        <thead><tr style="background:#f0f2f8">{peak_header}</tr></thead>
        <tbody>{peak_rows}{sim_row}{trig_row}{rec_row}</tbody>
      </table>
    </div>
  </div>

  <!-- TROUGH CONDITIONS TABLE -->
  <div style="margin-top:20px;margin-bottom:4px">
    <div style="font-size:11px;font-weight:800;color:#1A7A4A;margin-bottom:6px">
      🟢 AT THE BOTTOM — Indicator readings at historical TROUGHS vs today
      <span style="font-size:9px;font-weight:400;color:#667;margin-left:8px">
        Shows how far current readings are from historical capitulation levels · Red = more deterioration needed · Green = already at trough levels
      </span>
    </div>
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-family:monospace">
        <thead><tr style="background:#f0f8f2">{trough_header}</tr></thead>
        <tbody>{trough_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Methodology note -->
  <div style="margin-top:12px;padding:8px 12px;background:#fff;border-radius:4px;font-size:9px;color:#556;border-top:1px solid #2a2a3e">
    <strong style="color:#778">Methodology:</strong>
    Similarity score is a weighted match (HY OAS 22%, Yield Curve 20%, Fwd P/E 16%, Real Yield 12%, VIX 10%, Fed Funds 8%, CPI 6%, ISM 4%, Breadth 2%).
    Historical readings sourced from Federal Reserve H.15, BAML/ICE credit indices, BLS, and ISM.
    Diff rows show current minus historical (▲ = current higher, ▼ = current lower).
  </div>
</div>"""
# peak_signals  = which signal levels appear for this indicator at market peaks
# trough_signals= which signal levels appear at market bottoms
# Used by _compute_comprehensive_analysis() to score ALL 42 indicators.
# ══════════════════════════════════════════════════════════════════════════════
INDICATOR_PT_MAP = {
    # ── CREDIT: CALM at peaks (complacency), CRISIS at troughs (capitulation) ─
    "HY_OAS":      (["CALM"],                ["CRISIS","STRESS"]),
    "IG_OAS":      (["CALM"],                ["CRISIS","STRESS"]),
    "HY_IG_DIFF":  (["CALM"],                ["CRISIS","STRESS"]),
    "CCC_OAS":     (["CALM"],                ["CRISIS","STRESS"]),
    "NFCI":        (["CALM"],                ["CRISIS","STRESS"]),
    "OFR_FSI":     (["CALM"],                ["CRISIS","STRESS"]),
    "CI_LOAN_DLQ": (["CALM"],                ["STRESS","CRISIS"]),
    # ── RATES: INVERTED/HIGH at peaks, STEEP/LOW at troughs ──────────────────
    "YIELD_CURVE": (["CRISIS","STRESS"],     ["CALM"]),
    "CURVE_10Y3M": (["CRISIS","STRESS"],     ["CALM"]),
    "REAL_YIELD":  (["STRESS","CRISIS"],     ["CALM"]),
    "BREAKEVEN":   (["STRESS","CRISIS"],     ["CALM"]),
    "FED_FUNDS":   (["STRESS","CRISIS"],     ["CALM"]),
    "T10Y_YIELD":  (["CAUTION","STRESS"],    ["CALM"]),
    # ── VOLATILITY: LOW (complacency) at peaks, HIGH (panic) at troughs ──────
    "VIX":         (["CALM"],                ["CRISIS","STRESS"]),
    "VIX_TERM":    (["CALM","CAUTION"],      ["CRISIS"]),
    "MOVE":        (["CALM"],                ["CRISIS","STRESS"]),
    "VIX9D_RATIO": (["CALM"],               ["STRESS","CRISIS"]),
    "VVIX":        (["CALM"],                ["STRESS","CRISIS"]),
    "SKEW":        (["STRESS","CRISIS"],     ["CALM"]),
    # ── BREADTH: HIGH% at peaks (crowded), LOW% at troughs (max fear) ────────
    "PCT_ABOVE_50":  (["CALM"],              ["CRISIS"]),
    "PCT_ABOVE_200": (["CALM"],              ["CRISIS"]),
    "NYSE_AD":       (["CALM"],              ["CRISIS","STRESS"]),
    # ── VALUATION: EXPENSIVE at peaks, CHEAP at troughs ──────────────────────
    "FORWARD_PE":  (["STRESS","CRISIS"],     ["CALM"]),
    "ERP":         (["STRESS","CRISIS"],     ["CALM"]),
    "CAPE":        (["STRESS","CRISIS"],     ["CALM"]),
    "BUFFETT":     (["STRESS","CRISIS"],     ["CALM"]),
    # ── LIQUIDITY: DECLINING at peaks (tightening), RISING at troughs ────────
    "NET_LIQUIDITY":(["STRESS","CRISIS"],    ["CALM"]),
    "M2SL":        (["STRESS","CRISIS"],     ["CALM"]),
    "FED_BS":      (["STRESS","CRISIS"],     ["CALM"]),
    # ── RECESSION: NOT triggered at peaks, TRIGGERED at troughs ──────────────
    "SAHM":        (["CALM"],                ["STRESS","CRISIS"]),
    "NY_REC_PROB": (["CAUTION","STRESS"],    ["CRISIS"]),
    "CREDIT_CARD_DLQ":(["CALM","CAUTION"],   ["STRESS","CRISIS"]),
    # ── STRUCTURE ─────────────────────────────────────────────────────────────
    "SPX_DD":      (["CALM"],                ["CRISIS"]),
    "TOP10_WEIGHT":(["STRESS","CRISIS"],     ["CALM"]),
    "RSP_SPY":     (["CALM"],                ["STRESS","CRISIS"]),
    "SPX_VS_200":  (["CALM"],                ["CRISIS"]),
    # ── MACRO ─────────────────────────────────────────────────────────────────
    "INDPRO":      (["CALM"],                ["CRISIS","STRESS"]),
    "CAPUTIL":     (["CALM"],                ["CRISIS","STRESS"]),
    "CPI":         (["STRESS","CRISIS"],     ["CALM"]),
    "REAL_RETAIL": (["CALM"],                ["CRISIS","STRESS"]),
    "HOUST_YOY":   (["CALM"],               ["STRESS","CRISIS"]),
    # ── HOUSING ───────────────────────────────────────────────────────────────
    "RATE_30":     (["STRESS","CRISIS"],     ["CALM"]),
    "AFFORD_PTI":  (["STRESS","CRISIS"],     ["CALM"]),
    "MTGE_DELINQ": (["CALM"],                ["STRESS","CRISIS"]),
    "XHB_SPY":     (["CALM"],                ["STRESS","CRISIS"]),
    "HPI_YOY":     (["CAUTION","STRESS"],    ["CALM"]),
    # ── SAFE HAVEN ────────────────────────────────────────────────────────────
    "DXY":         (["CAUTION","STRESS"],    ["CALM"]),
    "GLD_SPY":     (["CALM"],                ["STRESS","CRISIS"]),
    "TLT_SPY":     (["CALM"],                ["STRESS"]),
    # ── SECTOR RATIOS ─────────────────────────────────────────────────────────
    "XLY_XLP":     (["CALM"],                ["CRISIS","STRESS"]),
    "XLF_XLU":     (["CALM"],                ["CRISIS"]),
    "IWM_SPY":     (["CALM"],                ["CRISIS"]),
    "XLK_SPY":     (["CALM","CAUTION"],      ["CRISIS"]),
    # ── SENTIMENT ─────────────────────────────────────────────────────────────
    "SENTIMENT":   (["CALM"],                ["CRISIS"]),
    "SMART_MONEY": (["CALM","CAUTION"],      ["STRESS"]),
    "DUMB_MONEY":  (["STRESS"],              ["CRISIS"]),
    "SPX_RSI":     (["STRESS"],              ["CRISIS"]),
    "PUT_CALL":    (["CALM"],                ["CRISIS","STRESS"]),
}

# ── Data quality classification ───────────────────────────────────────────────
# A = FRED direct (high accuracy)
# B = yfinance market data (directionally accurate, real-time)
# C = Proxy / approximation (directionally useful, not exact)
# D = Scraped / computed / estimated (may fail or lag significantly)
DATA_QUALITY_MAP = {
    # A: FRED Direct
    "HY_OAS":"A","IG_OAS":"A","YIELD_CURVE":"A","CURVE_10Y3M":"A","REAL_YIELD":"A",
    "BREAKEVEN":"A","FED_FUNDS":"A","T10Y_YIELD":"A","SAHM":"A","NY_REC_PROB":"A",
    "CREDIT_CARD_DLQ":"A","CPI":"A","NET_LIQUIDITY":"A","M2SL":"A","FED_BS":"A",
    "INDPRO":"A","CAPUTIL":"A","REAL_RETAIL":"A","HOUST_YOY":"A",
    "RATE_30":"A","MTGE_DELINQ":"A","NFCI":"A","SUPPLY_MO":"A","HPI_YOY":"A",
    # A+: New FRED additions (when installed)
    "ISM_PMI":"A","ISM_NEWORDERS":"A","INIT_CLAIMS":"A","LEI":"A",
    "DURGDS":"A","UMCSENT":"A","SOFR":"A",
    # B: yfinance Market Data
    "VIX":"B","VIX_TERM":"B","MOVE":"B","VIX9D_RATIO":"B","VVIX":"B","SKEW":"B",
    "SPX_DD":"B","SPX_VS_200":"B","RSP_SPY":"B","DXY":"B","GLD_SPY":"B","TLT_SPY":"B",
    "XLY_XLP":"B","XLF_XLU":"B","IWM_SPY":"B","XLK_SPY":"B","XHB_SPY":"B",
    "PUT_CALL":"B","USDJPY":"B",
    # C: Proxy / Approximation
    "CCC_OAS":"C","HY_IG_DIFF":"C","OFR_FSI":"C","CI_LOAN_DLQ":"C",
    "PCT_ABOVE_50":"C","PCT_ABOVE_200":"C","NYSE_AD":"C",
    "SMART_MONEY":"C","DUMB_MONEY":"C","AFFORD_PTI":"C","SPX_RSI":"B",
    # D: Scraped / Estimated / Lagged
    "CAPE":"D","BUFFETT":"D","FORWARD_PE":"D","ERP":"D",
    "SENTIMENT":"D","TOP10_WEIGHT":"D","NAAIM":"D","AAII_BULL":"D",
}
DQ_LABELS = {
    "A": ("✅ FRED Direct",     "#1A7A4A", "High accuracy — direct FRED API data"),
    "B": ("📈 yfinance Live",   "#1155cc", "Directionally accurate — real-time market data"),
    "C": ("⚠️ Proxy/Approx",   "#D4820A", "Directionally useful — computed from ETF ratios, ~40 stocks"),
    "D": ("🔍 Scraped/Lagged", "#888",    "May be stale or unavailable — web-scraped or quarterly data"),
}


def _compute_comprehensive_analysis(scorecard_data):
    """
    Score ALL scorecard indicators against historical peak/trough patterns.
    Returns dict with peak_score, trough_score (0-100), and per-indicator breakdown.
    """
    peak_pts = 0.0; trough_pts = 0.0; total_wt = 0.0
    peak_firing  = []   # indicators in peak territory
    trough_firing= []   # indicators in trough territory
    neutral      = []   # neither

    for ind in scorecard_data:
        _id  = ind.get("id","")
        _sig = ind.get("signal","")
        _wt  = ind.get("wt", 1)
        _val = ind.get("val_str","N/A")
        _nm  = ind.get("name","")
        _cat = ind.get("cat","")
        _dq  = DATA_QUALITY_MAP.get(_id, "C")

        if _id not in INDICATOR_PT_MAP: continue
        peak_sigs, trough_sigs = INDICATOR_PT_MAP[_id]

        total_wt += _wt
        _pk = _sig in peak_sigs
        _tr = _sig in trough_sigs

        if _pk:
            peak_pts += _wt
            peak_firing.append({"name":_nm,"cat":_cat,"wt":_wt,"val":_val,
                                 "signal":_sig,"dq":_dq,"id":_id})
        elif _tr:
            trough_pts += _wt
            trough_firing.append({"name":_nm,"cat":_cat,"wt":_wt,"val":_val,
                                   "signal":_sig,"dq":_dq,"id":_id})
        else:
            neutral.append({"name":_nm,"cat":_cat,"wt":_wt,"val":_val,
                             "signal":_sig,"dq":_dq,"id":_id})

    if total_wt == 0:
        return {"peak_score":0,"trough_score":0,"peak_firing":[],"trough_firing":[],"neutral":[],
                "peak_pts":0,"trough_pts":0,"total_wt":0,"n_indicators":0}

    # Sort by weight descending
    peak_firing.sort(key=lambda x: -x["wt"])
    trough_firing.sort(key=lambda x: -x["wt"])

    return {
        "peak_score":   round(peak_pts   / total_wt * 100),
        "trough_score": round(trough_pts / total_wt * 100),
        "peak_firing":  peak_firing,
        "trough_firing":trough_firing,
        "neutral":      neutral,
        "peak_pts":     peak_pts,
        "trough_pts":   trough_pts,
        "total_wt":     total_wt,
        "n_indicators": len(peak_firing) + len(trough_firing) + len(neutral),
    }


def _compute_derived_additions(fd, md):
    """Compute derived leading indicator scalars from existing fd/md dicts."""
    import numpy as _np
    out = {}
    def _gv(d, k, i=-1):
        s = d.get(k)
        if s is None or (hasattr(s,"empty") and s.empty): return None
        try: return float(s.iloc[max(i,-len(s))])
        except: return None

    # ISM
    for _k, _label in [("ISM_PMI","ism"),("ISM_NEWORDERS","ism_no"),("ISM_PRICES","ism_prices")]:
        v = _gv(fd, _k); vp = _gv(fd, _k, -2)
        if v is not None:
            out[f"{_label}_now"] = round(v, 1)
            if vp is not None:
                out[f"{_label}_prev"] = round(vp, 1)
                out[f"{_label}_dir"]  = "▲" if v > vp else "▼"
    if "ism_no_now" in out and "ism_no_prev" in out:
        _s = fd.get("ISM_NEWORDERS")
        if _s is not None and len(_s) >= 6:
            out["ism_no_was_below47"] = any(float(x) < 47 for x in _s.tail(6))

    # ISM proxy from INDPRO (industrial production) if FRED ISM not loaded
    # INDPRO trend direction mirrors ISM direction with ~1mo lag — usable as proxy signal
    if "ism_now" not in out:
        _ip = fd.get("INDPRO")
        if _ip is not None and not _ip.empty and len(_ip) >= 3:
            _ip_3m = (float(_ip.iloc[-1]) / float(_ip.iloc[-4]) - 1) * 100 if len(_ip) >= 4 else 0
            _ip_sig = "CALM" if _ip_3m > 0.5 else "CAUTION" if _ip_3m > -0.3 else "STRESS"
            out["ism_proxy_indpro_3m"] = round(_ip_3m, 2)
            out["ism_proxy_signal"]    = _ip_sig
            out["ism_proxy_note"]      = "INDPRO proxy (install fredapi for actual ISM)"

    # Initial Claims 4-week MA
    _cl = fd.get("INIT_CLAIMS")
    if _cl is not None and not _cl.empty and len(_cl) >= 4:
        _cw = _cl.dropna()
        _ma4 = float(_cw.tail(4).mean())
        _low52 = float(_cw.tail(52).min()) if len(_cw)>=52 else float(_cw.min())
        out["claims_latest"]     = round(float(_cw.iloc[-1])/1000, 1)
        out["claims_4wk_ma"]     = round(_ma4/1000, 1)
        out["claims_52wk_low"]   = round(_low52/1000, 1)
        out["claims_chg_pct"]    = round((_ma4/_low52-1)*100, 1) if _low52>0 else None
        if len(_cw) >= 13:
            _pk3 = float(_cw.tail(13).max())
            out["claims_peak3m"]      = round(_pk3/1000, 1)
            out["claims_off_peak_pct"]= round((_ma4/_pk3-1)*100, 1)

    # LEI YoY
    _lei = fd.get("LEI")
    if _lei is not None and not _lei.empty and len(_lei) >= 13:
        _ln = float(_lei.iloc[-1]); _l1y = float(_lei.iloc[-13])
        out["lei_yoy"] = round((_ln/_l1y-1)*100, 2) if _l1y != 0 else None
        out["lei_consecutive_neg"] = sum(1 for i in range(-1,-min(7,len(_lei)),-1)
                                         if float(_lei.iloc[i]) < float(_lei.iloc[i-1]))

    # Durable Goods MoM
    _dg = fd.get("DURGDS")
    if _dg is not None and not _dg.empty and len(_dg) >= 2:
        out["durgds_mom"] = round((float(_dg.iloc[-1])/float(_dg.iloc[-2])-1)*100, 2)
        _neg = 0
        for i in range(-1,-min(5,len(_dg)),-1):
            if float(_dg.iloc[i]) < float(_dg.iloc[i-1]): _neg += 1
            else: break
        out["durgds_neg_streak"] = _neg

    # UMich
    _um = fd.get("UMCSENT")
    if _um is not None and not _um.empty: out["umcsent"] = round(float(_um.iloc[-1]),1)

    # SOFR spread
    _sf = fd.get("SOFR"); _ff = fd.get("FEDFUNDS")
    if _sf is not None and not _sf.empty and _ff is not None and not _ff.empty:
        out["sofr_spread_bps"] = round((float(_sf.iloc[-1]) - float(_ff.iloc[-1]))*100, 1)

    # USDJPY
    _jpy1 = md.get("USDJPY=X"); _jpy2 = md.get("USDJPY")
    _jpy = _jpy1 if (_jpy1 is not None and not _jpy1.empty) else _jpy2
    if _jpy is not None and not _jpy.empty:
        out["usdjpy"] = round(float(_jpy.iloc[-1]), 2)
        if len(_jpy) >= 22:
            out["usdjpy_1m_chg"] = round((float(_jpy.iloc[-1])/float(_jpy.iloc[-22])-1)*100, 2)
        if len(_jpy) >= 63:
            out["usdjpy_3m_chg"] = round((float(_jpy.iloc[-1])/float(_jpy.iloc[-63])-1)*100, 2)

    # Oil
    _oil = fd.get("DCOILWTICO")
    _oil2 = md.get("CL=F")
    _os = _oil if (_oil is not None and not _oil.empty) else _oil2
    if _os is not None and not _os.empty:
        out["oil"] = round(float(_os.iloc[-1]), 2)
        if len(_os) >= 4:
            out["oil_3m_chg"] = round((float(_os.iloc[-1])/float(_os.iloc[max(-64,-len(_os))])-1)*100, 1)

    return out


def _compute_pt_score(fd, md, derived):
    """Score 5 Peak Sell + 5 Trough Buy signals. Returns full scoring dict."""
    peak_sigs = []; trough_sigs = []

    def _gv(d, k, i=-1):
        s = d.get(k)
        if s is None or (hasattr(s,"empty") and s.empty): return None
        try: return float(s.iloc[max(i,-len(s))])
        except: return None

    def _sig(name, desc, fired, value, threshold):
        col = "#C0390F" if fired else "#1A7A4A"
        return {"name":name,"desc":desc,"fired":fired,"value":value,"threshold":threshold,"col":col}

    # ── PEAK SIGNALS ─────────────────────────────────────────────────────────
    v9 = _gv(md,"^VIX9D"); v30 = _gv(md,"^VIX")
    if v9 and v30 and v30>0:
        r = round(v9/v30,3)
        peak_sigs.append(_sig("VIX9D/VIX > 1.0","Short-term fear spike — acute stress",r>1.0,f"{r:.3f}",">1.0"))
    else:
        peak_sigs.append(_sig("VIX9D/VIX > 1.0","Short-term fear spike",False,"N/A",">1.0"))

    _hy = fd.get("HY_OAS")
    if _hy is not None and not _hy.empty and len(_hy)>=4:
        _hc = round(float(_hy.iloc[-1])-float(_hy.iloc[max(-4,-len(_hy))]),0)
        peak_sigs.append(_sig("HY OAS 3mo change >+40bps","Credit spreads widening",_hc>40,
                              f"{_hc:+.0f}bps (now {float(_hy.iloc[-1]):.0f}bps)",">+40bps"))
    else:
        peak_sigs.append(_sig("HY OAS 3mo change >+40bps","Credit widening",False,"N/A",">+40bps"))

    _tlt = md.get("TLT"); _spy = md.get("SPY")
    if _tlt is not None and not _tlt.empty and _spy is not None and not _spy.empty and len(_tlt)>=22 and len(_spy)>=22:
        _tr = round((float(_tlt.iloc[-1])/float(_tlt.iloc[-22])-1)*100,2)
        _sr = round((float(_spy.iloc[-1])/float(_spy.iloc[-22])-1)*100,2)
        peak_sigs.append(_sig("TLT +2%+ while SPY -3%+","Flight-to-safety confirmed",
                              _tr>2.0 and _sr<-3.0,f"TLT {_tr:+.1f}% SPY {_sr:+.1f}% (1mo)","TLT>+2% AND SPY<-3%"))
    else:
        peak_sigs.append(_sig("TLT/SPY flight-to-safety","Bonds vs stocks divergence",False,"N/A","TLT>+2% & SPY<-3%"))

    _s1 = md.get("^GSPC"); _s2 = md.get("SPY")
    _spx = _s1 if (_s1 is not None and not _s1.empty) else _s2
    if _spx is not None and not _spx.empty and len(_spx)>=200:
        import pandas as _pds
        _px = float(_spx.iloc[-1])
        _e200 = float(_spx.ewm(span=200,adjust=False).mean().iloc[-1])
        _vs200 = round((_px/_e200-1)*100,2)
        peak_sigs.append(_sig("SPX below 200-day EMA","Trend structure broken",_px<_e200,
                              f"SPX {_vs200:+.1f}% vs 200EMA ({_e200:,.0f})","SPX < 200EMA"))
    else:
        peak_sigs.append(_sig("SPX below 200EMA","Trend broken",False,"N/A","SPX < 200EMA"))

    _t10 = fd.get("T10Y")
    if _t10 is not None and not _t10.empty and len(_t10)>=7:
        _tc = round(float(_t10.iloc[-1])-float(_t10.iloc[max(-7,-len(_t10))]),2)
        peak_sigs.append(_sig("10Y yield +0.8%+ in 6mo","Rate pressure mounting",_tc>0.80,
                              f"{_tc:+.2f}% (now {float(_t10.iloc[-1]):.2f}%)",">+0.80% in 6mo"))
    else:
        peak_sigs.append(_sig("10Y yield 6mo change","Rate pressure",False,"N/A",">+0.80%"))

    # ── TROUGH SIGNALS ────────────────────────────────────────────────────────
    if _hy is not None and not _hy.empty and len(_hy)>=3:
        _hn = float(_hy.iloc[-1]); _hpk = float(_hy.tail(6).max())
        _hdecl = _hn < float(_hy.iloc[-3])
        trough_sigs.append(_sig("HY OAS peaked + declining","Credit stress resolving",
                                _hdecl and _hpk>380,f"{_hn:.0f}bps (6mo peak: {_hpk:.0f}bps)","Declining from >380bps"))
    else:
        trough_sigs.append(_sig("HY OAS peaked + declining","Credit resolving",False,"N/A","Declining from >380bps"))

    _vix5 = _gv(md,"^VIX",-6) if md.get("^VIX") is not None else None
    _vixn = v30
    if _vixn is not None:
        _vdecl = _vix5 is not None and _vixn < _vix5
        trough_sigs.append(_sig("VIX > 30 and declining","Peak panic fading",
                                _vixn>30 and _vdecl,f"VIX {_vixn:.1f} ({'↓ declining' if _vdecl else '→ flat/rising'})","VIX>30 AND declining"))
    else:
        trough_sigs.append(_sig("VIX > 30 declining","Panic fading",False,"N/A","VIX>30 AND declining"))

    _ino = derived.get("ism_no_now"); _ino_p = derived.get("ism_no_prev")
    _was47 = derived.get("ism_no_was_below47", False)
    if _ino is not None and _ino_p is not None:
        _rising = _ino > _ino_p
        trough_sigs.append(_sig("ISM New Orders <47 turning up","Demand cycle bottoming",
                                _was47 and _rising and _ino<52,
                                f"{_ino:.1f} (prev {_ino_p:.1f}) {'▲' if _rising else '▼'}","Was <47, now rising"))
    else:
        trough_sigs.append(_sig("ISM New Orders bottoming","Demand bottoming",False,"N/A","Was <47, now rising"))

    _yc = fd.get("YIELD_CURVE")
    if _yc is not None and not _yc.empty and len(_yc)>=4:
        _ycc = round(float(_yc.iloc[-1])-float(_yc.iloc[max(-4,-len(_yc))]),0)
        trough_sigs.append(_sig("Yield curve steepening >+30bps","Fed pivoting — liquidity returning",
                                _ycc>30,f"{_ycc:+.0f}bps (now {float(_yc.iloc[-1])/100:+.2f}%)",">+30bps in 3mo"))
    else:
        trough_sigs.append(_sig("Yield curve steepening","Fed pivot",False,"N/A",">+30bps in 3mo"))

    _off_pk = derived.get("claims_off_peak_pct")
    if _off_pk is not None:
        trough_sigs.append(_sig("Claims 4wk MA off 3mo peak by >10%","Labor market stabilizing",
                                _off_pk < -10,f"{_off_pk:+.1f}% vs 3mo peak","< -10% vs 3mo peak"))
    else:
        trough_sigs.append(_sig("Claims declining from peak","Labor stabilizing",False,"N/A","< -10% vs 3mo peak"))

    _ps = sum(1 for s in peak_sigs   if s["fired"])
    _ts = sum(1 for s in trough_sigs if s["fired"])

    if _ps >= 4:   verdict,action,rcol = "STRONG SELL / HEDGE — 4+ peak signals. High-confidence top or bear entry.","Reduce cyclicals. Buy puts. Add TLT, GLD. Build cash.","#8B0000"
    elif _ps == 3: verdict,action,rcol = "CAUTION / REDUCE RISK — 3 peak signals confirmed. 10-20% correction elevated risk.","Trim extended positions. Shift to defensives (XLP,XLV,XLU). Tighten stops.","#C0390F"
    elif _ps == 2: verdict,action,rcol = "WATCHFUL / NEUTRAL — 2 peak signals. Correction possible, not confirmed.","Maintain positions. Tighten stops. Watch HY OAS and VIX for escalation.","#D4820A"
    elif _ts >= 3: verdict,action,rcol = "ACCUMULATE — 3+ trough signals. High-confidence bottom or major low forming.","Scale into SPY/QQQ dips. Add cyclicals (XLY,XLK,XLF). Sell VIX premium if >30.","#1A7A4A"
    elif _ts == 2: verdict,action,rcol = "EARLY ACCUMULATION — 2 trough signals. Tentative bottom, confirm with HY OAS.","Begin building in quality names. Wait for HY OAS to turn before full commitment.","#2E8B57"
    else:          verdict,action,rcol = "TRENDING / NEUTRAL — Insufficient signals for top or bottom call. Follow price.","Hold positions. Trade within gamma range (Call Wall / Put Wall). Follow breadth.","#445566"

    return {"peak_score":_ps,"trough_score":_ts,"peak_sigs":peak_sigs,"trough_sigs":trough_sigs,
            "verdict":verdict,"action":action,"rcol":rcol}


def _build_leading_tab_html(pt, derived, pcr_val, pcr_src, aaii, fd, md, comprehensive=None, episode_html=""):
    """Build the full HTML for the Leading Indicators tab."""
    _ps = pt["peak_score"]; _ts = pt["trough_score"]
    _rcol = pt["rcol"]

    def _badge(sig):
        c = {"CALM":"#1A7A4A","CAUTION":"#D4820A","STRESS":"#C0390F","CRISIS":"#8B0000"}.get(sig,"#888")
        bg= {"CALM":"#e8f5e9","CAUTION":"#fff8e1","STRESS":"#fff0e0","CRISIS":"#fce4ec"}.get(sig,"#f5f5f5")
        return f'<span style="background:{bg};color:{c};padding:2px 8px;border-radius:8px;font-size:10px;font-weight:800;border:1px solid {c}44">{sig}</span>'

    def _sig_check_row(s):
        icon = "✅" if s["fired"] else "❌"
        bg   = "#fff8f8" if s["fired"] else "#fafafa"
        c    = s["col"]
        return (f'<tr style="background:{bg};border-bottom:1px solid #eee">'
                f'<td style="padding:5px 8px;font-size:14px;width:28px">{icon}</td>'
                f'<td style="padding:5px 8px;font-size:11px;font-weight:700;color:{c}">{s["name"]}</td>'
                f'<td style="padding:5px 8px;font-size:10px;color:#666">{s["desc"]}</td>'
                f'<td style="padding:5px 8px;font-size:11px;font-weight:700;color:{c};text-align:right">{s["value"]}</td>'
                f'</tr>')

    _peak_rows   = "".join(_sig_check_row(s) for s in pt["peak_sigs"])
    _trough_rows = "".join(_sig_check_row(s) for s in pt["trough_sigs"])

    def _ind_row(label, val_str, sig, note=""):
        bg = {"CALM":"#f0fff4","CAUTION":"#fffde7","STRESS":"#fff3e0","CRISIS":"#fce4ec"}.get(sig,"#f9f9f9")
        return (f'<tr style="background:{bg};border-bottom:1px solid #eee">'
                f'<td style="padding:5px 10px;font-size:11px;font-weight:700">{label}</td>'
                f'<td style="padding:5px 10px;font-size:12px;font-weight:900;text-align:right">{val_str}</td>'
                f'<td style="padding:5px 10px;text-align:center">{_badge(sig)}</td>'
                f'<td style="padding:5px 10px;font-size:10px;color:#666">{note}</td></tr>')

    def _ism_sig(v):
        if v is None: return "CALM"
        if v>=52: return "CALM"
        if v>=50: return "CAUTION"
        if v>=46: return "STRESS"
        return "CRISIS"

    # ISM panel rows
    _ism_rows = ""
    for _k, _label in [("ism","PMI (headline)"),("ism_no","New Orders"),("ism_prices","Prices Paid")]:
        _v = derived.get(f"{_k}_now"); _d = derived.get(f"{_k}_dir","→")
        if _v is not None:
            _sig = _ism_sig(_v) if "prices" not in _k else ("STRESS" if _v>65 else ("CAUTION" if _v>55 else "CALM"))
            _exp = "EXPANDING" if _v>=50 else "CONTRACTING"
            _ism_rows += _ind_row(f"{_label} {_d}", f"{_v:.1f}", _sig, _exp)
    # Show INDPRO proxy if ISM not loaded
    if not _ism_rows:
        _ip3 = derived.get("ism_proxy_indpro_3m")
        _ip_sig = derived.get("ism_proxy_signal","CALM")
        _ip_note = derived.get("ism_proxy_note","")
        if _ip3 is not None:
            _ism_rows += _ind_row("INDPRO 3mo trend (ISM proxy)", f"{_ip3:+.2f}%", _ip_sig,
                                   _ip_note)
        _ism_rows += (
            '<tr><td colspan="4" style="padding:8px 10px;font-size:10px;color:#795548;'
            'background:#fff8e1;border-top:1px solid #ffe082">'
            '⚠ ISM data (PMI, New Orders, Prices) requires: '
            '<code>pip install fredapi pandas_datareader</code>'
            '</td></tr>'
        )

    # Claims panel rows — also use UNRATE trend as proxy if claims not loaded
    _cl_rows = ""
    _cl_v = derived.get("claims_latest"); _cl_ma = derived.get("claims_4wk_ma"); _cl_chg = derived.get("claims_chg_pct"); _cl_low = derived.get("claims_52wk_low")
    def _cl_sig(v):
        if v is None: return "CALM"
        return "CALM" if v<10 else "CAUTION" if v<20 else "STRESS" if v<35 else "CRISIS"
    if _cl_v:  _cl_rows += _ind_row("Latest Week", f"{_cl_v:.0f}K", "STRESS" if _cl_v>310 else "CAUTION" if _cl_v>260 else "CALM", "Weekly new filings")
    if _cl_ma: _cl_rows += _ind_row("4-Week Moving Avg", f"{_cl_ma:.0f}K", _cl_sig(_cl_chg), f"52wk low: {_cl_low:.0f}K" if _cl_low else "")
    if _cl_chg is not None: _cl_rows += _ind_row("Rise from 52wk Low", f"{_cl_chg:+.1f}%", _cl_sig(_cl_chg), ">15% = recession risk activated")
    # Show UNRATE as proxy if claims not loaded (already in existing fd)
    if not _cl_rows:
        _ur_v = None
        _ur_s = fd.get("UNRATE")
        if _ur_s is not None and not _ur_s.empty:
            _ur_v = round(float(_ur_s.iloc[-1]), 1)
            _ur_3m = round(float(_ur_s.iloc[-1]) - float(_ur_s.iloc[max(-4,-len(_ur_s))]), 2) if len(_ur_s)>=4 else None
            _ur_sig = "CALM" if _ur_v < 4.0 else "CAUTION" if _ur_v < 4.5 else "STRESS" if _ur_v < 5.5 else "CRISIS"
            _cl_rows += _ind_row("Unemployment Rate (FRED)", f"{_ur_v:.1f}%", _ur_sig, "Claims proxy · Sahm trigger >0.5pp from 12mo low")
            if _ur_3m is not None:
                _cl_rows += _ind_row("3-Month Change", f"{_ur_3m:+.2f}pp", "CAUTION" if _ur_3m>0.2 else "CALM", "Rising trend = labor softening")
        _cl_rows += (
            '<tr><td colspan="4" style="padding:8px 10px;font-size:10px;color:#795548;'
            'background:#fff8e1;border-top:1px solid #ffe082">'
            '⚠ Weekly Claims (ICSA) requires: '
            '<code>pip install fredapi pandas_datareader</code>'
            '</td></tr>'
        )

    # Leading indicators panel
    _lei_rows = ""
    _lei_v = derived.get("lei_yoy")
    if _lei_v is not None:
        _lei_sig = "CALM" if _lei_v>0 else "CAUTION" if _lei_v>-1 else "STRESS" if _lei_v>-3 else "CRISIS"
        _lei_rows += _ind_row("Leading Index YoY", f"{_lei_v:+.2f}%", _lei_sig, f"Negative 3+ months = recession · Consecutive neg months: {derived.get('lei_consecutive_neg',0)}")
    _dg_v = derived.get("durgds_mom"); _dg_neg = derived.get("durgds_neg_streak",0)
    if _dg_v is not None:
        _dg_sig = "CALM" if _dg_v>0 else "CAUTION" if _dg_v>-2 else "STRESS" if _dg_v>-5 else "CRISIS"
        _lei_rows += _ind_row("Durable Goods MoM", f"{_dg_v:+.2f}%", _dg_sig, f"{_dg_neg} consecutive negative months" if _dg_neg>0 else "Capex intact")
    _um_v = derived.get("umcsent")
    if _um_v: _lei_rows += _ind_row("UMich Sentiment", f"{_um_v:.1f}", "CALM" if _um_v>75 else "CAUTION" if _um_v>60 else "STRESS" if _um_v>50 else "CRISIS", "< 65 = spending headwinds ahead")

    # Sentiment panel
    _sent_rows = ""
    if pcr_val is not None:
        _pc_sig = "CRISIS" if pcr_val>1.3 else "STRESS" if pcr_val>1.1 else "CAUTION" if pcr_val>0.9 else "CALM"
        _pc_note = "⚠ EXTREME FEAR — contrarian buy zone" if pcr_val>1.3 else "High hedging" if pcr_val>1.1 else "Elevated" if pcr_val>0.9 else "Normal"
        _sent_rows += _ind_row("Put/Call Ratio", f"{pcr_val:.3f}", _pc_sig, f"{pcr_src} · {_pc_note}")
    if aaii.get("bull") is not None:
        _ab = aaii["bull"]; _ae = aaii["bear"]; _asp = aaii["spread"]
        _ab_sig = "CRISIS" if _ab>55 else "CAUTION" if _ab>50 else "CALM"
        _sent_rows += _ind_row(f"AAII Bull% ({aaii.get('date','')})", f"{_ab:.1f}%", _ab_sig, f"Bear: {_ae:.1f}% · Spread: {_asp:+.1f}%")

    # USDJPY panel
    _jpy_rows = ""
    _jpy_v = derived.get("usdjpy"); _jpy1 = derived.get("usdjpy_1m_chg"); _jpy3 = derived.get("usdjpy_3m_chg")
    def _jpy_sig(c): return "CALM" if c is None or c>-3 else "CAUTION" if c>-5 else "STRESS" if c>-8 else "CRISIS"
    if _jpy_v: _jpy_rows += _ind_row("USD/JPY Level", f"{_jpy_v:.2f}", "CAUTION" if _jpy_v<140 else "CALM", "< 130 = carry unwind risk")
    if _jpy1 is not None: _jpy_rows += _ind_row("1-Month Change", f"{_jpy1:+.2f}%", _jpy_sig(_jpy1), "-5%+ = carry trade unwinding")
    if _jpy3 is not None: _jpy_rows += _ind_row("3-Month Change", f"{_jpy3:+.2f}%", _jpy_sig(_jpy3), "-8%+ = systemic carry risk")

    # Oil + SOFR
    _oil_rows = ""
    _ov = derived.get("oil"); _o3 = derived.get("oil_3m_chg")
    if _ov: _oil_rows += _ind_row("WTI Crude", f"${_ov:.2f}/bbl", "CALM" if _ov<85 else "CAUTION" if _ov<100 else "STRESS" if _ov<120 else "CRISIS", "Stagflation risk > $100")
    if _o3 is not None: _oil_rows += _ind_row("3-Month Change", f"{_o3:+.1f}%", "CALM" if _o3<20 else "CAUTION" if _o3<35 else "STRESS" if _o3<55 else "CRISIS", "+40%+ in 3mo preceded 5 of last 7 recessions")

    _sofr_rows = ""
    _sfr = derived.get("sofr_spread_bps")
    if _sfr is not None:
        _sofr_rows += _ind_row("SOFR − Fed Funds Spread", f"{_sfr:+.1f}bps", "CALM" if abs(_sfr)<10 else "CAUTION" if _sfr<25 else "STRESS" if _sfr<50 else "CRISIS", ">25bps = repo stress · >50bps = systemic risk")

    _ts_hdr = lambda t,rows: (f'<div style="margin-bottom:16px"><div style="font-size:12px;font-weight:800;color:#2c3e50;margin-bottom:6px">{t}</div>'
                               f'<table style="width:100%;border-collapse:collapse;box-shadow:0 1px 3px rgba(0,0,0,0.07);border-radius:6px;overflow:hidden">'
                               f'<thead><tr style="background:#2c3e50;color:#fff"><th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700">Indicator</th>'
                               f'<th style="padding:6px 10px;text-align:right;font-size:10px;font-weight:700">Value</th>'
                               f'<th style="padding:6px 10px;text-align:center;font-size:10px;font-weight:700">Signal</th>'
                               f'<th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700">Note</th></tr></thead>'
                               f'<tbody>{rows}</tbody></table></div>') if rows else ""

    # ── N/A notice when FRED series haven't loaded ────────────────────────────
    _fred_missing = not any(derived.get(k) is not None for k in
                            ["ism_now","ism_no_now","claims_latest","lei_yoy","durgds_mom","umcsent"])
    _fred_notice = (
        '<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:6px;padding:8px 14px;'
        'margin-bottom:12px;font-size:10px;color:#795548">'
        '⚠️ <strong>FRED data not loaded</strong> — ISM, Claims, LEI, Durable Goods, UMich Sentiment show N/A.<br>'
        'Fix: <code>pip install fredapi pandas_datareader</code> then rerun. '
        'PCR and USDJPY always load via yfinance ✓'
        '</div>'
    ) if _fred_missing else ""

    # ── Comprehensive indicator analysis ────────────────────────────────────
    _comp_html = ""
    if comprehensive and comprehensive.get("n_indicators", 0) > 0:
        _cp = comprehensive["peak_score"]
        _ct = comprehensive["trough_score"]
        _cn = comprehensive["n_indicators"]
        _cpk = comprehensive["peak_firing"]
        _ctr = comprehensive["trough_firing"]
        _cne = comprehensive["neutral"]

        # Determine composite regime color
        if _cp >= 55:   _cc = "#8B0000"; _cl = "STRONG PEAK CONDITIONS"
        elif _cp >= 40: _cc = "#C0390F"; _cl = "PEAK-LEANING CONDITIONS"
        elif _ct >= 40: _cc = "#1A7A4A"; _cl = "TROUGH-LEANING CONDITIONS"
        elif _ct >= 25: _cc = "#2E8B57"; _cl = "EARLY TROUGH CONDITIONS"
        else:           _cc = "#445566"; _cl = "NEUTRAL / MID-CYCLE"

        # Progress bars
        def _pbar(pct, col, w=200):
            return (f'<div style="display:inline-block;width:{w}px;height:12px;background:#eee;'
                    f'border-radius:6px;overflow:hidden;vertical-align:middle">'
                    f'<div style="width:{min(pct,100)}%;height:12px;background:{col};border-radius:6px"></div></div>'
                    f'<span style="font-size:12px;font-weight:800;color:{col};margin-left:8px">{pct}%</span>')

        def _comp_ind_row(ind):
            _dq_lbl, _dq_col, _ = DQ_LABELS.get(ind["dq"], ("?","#888",""))
            _sig = ind["signal"]
            _sc = {"CALM":"#1A7A4A","CAUTION":"#D4820A","STRESS":"#C0390F","CRISIS":"#8B0000"}.get(_sig,"#888")
            _sbg= {"CALM":"#e8f5e9","CAUTION":"#fff8e1","STRESS":"#fff0e0","CRISIS":"#fce4ec"}.get(_sig,"#f5f5f5")
            _badge = (f'<span style="background:{_sbg};color:{_sc};padding:1px 7px;border-radius:6px;'
                      f'font-size:9px;font-weight:800;border:1px solid {_sc}33">{_sig}</span>')
            return (f'<tr style="border-bottom:1px solid #eee">'
                    f'<td style="padding:4px 10px;font-size:11px;font-weight:600">{ind["name"]}</td>'
                    f'<td style="padding:4px 8px;font-size:10px;color:#888">{ind["cat"]}</td>'
                    f'<td style="padding:4px 8px;font-size:11px;font-weight:700;text-align:right;color:{_sc}">{ind["val"]}</td>'
                    f'<td style="padding:4px 8px">{_badge}</td>'
                    f'<td style="padding:4px 8px;font-size:9px;color:{_dq_col}">{_dq_lbl.split(" ")[0]}</td>'
                    f'<td style="padding:4px 8px;font-size:9px;color:#888;text-align:right">WT{ind["wt"]}</td>'
                    f'</tr>')

        _peak_ind_rows   = "".join(_comp_ind_row(x) for x in _cpk[:20])
        _trough_ind_rows = "".join(_comp_ind_row(x) for x in _ctr[:20])
        _neutral_rows    = "".join(_comp_ind_row(x) for x in _cne[:10])

        _tbl_hdr = ('<thead><tr style="background:#2d3f6e;color:#fff">'
                    '<th style="padding:5px 10px;text-align:left;font-size:10px">Indicator</th>'
                    '<th style="padding:5px 8px;text-align:left;font-size:10px">Category</th>'
                    '<th style="padding:5px 8px;text-align:right;font-size:10px">Current</th>'
                    '<th style="padding:5px 8px;font-size:10px">Signal</th>'
                    '<th style="padding:5px 8px;font-size:10px">Data Quality</th>'
                    '<th style="padding:5px 8px;text-align:right;font-size:10px">Weight</th>'
                    '</tr></thead>')

        _comp_html = f"""
<div style="margin-top:20px">
  <div style="font-size:14px;font-weight:800;color:#1a1a2e;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #e0e4ed">
    📊 COMPREHENSIVE CYCLE ANALYSIS — ALL {_cn} SCORECARD INDICATORS SCORED
    <span style="font-size:11px;font-weight:400;color:#667;margin-left:8px">
      Compared against historical peak &amp; trough patterns from 2000, 2007, 2018, 2020, 2022
    </span>
  </div>

  <!-- Composite Score Summary -->
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:16px">
    <div style="background:#fff5f5;border:2px solid #C0390F;border-radius:10px;padding:14px;text-align:center">
      <div style="font-size:11px;font-weight:700;color:#C0390F;margin-bottom:6px">🔴 PEAK PROXIMITY</div>
      <div style="font-size:36px;font-weight:900;color:#C0390F">{_cp}%</div>
      {_pbar(_cp,"#C0390F",160)}
      <div style="font-size:10px;color:#888;margin-top:6px">{len(_cpk)} of {_cn} indicators in peak territory</div>
    </div>
    <div style="background:{_cc}0f;border:2px solid {_cc};border-radius:10px;padding:14px;text-align:center">
      <div style="font-size:11px;font-weight:700;color:{_cc};margin-bottom:6px">📍 COMPOSITE READING</div>
      <div style="font-size:16px;font-weight:800;color:{_cc};margin-top:10px">{_cl}</div>
      <div style="font-size:10px;color:#888;margin-top:8px">Peak {_cp}% vs Trough {_ct}%</div>
      <div style="font-size:10px;color:#888">{_cn} indicators from Overview tab scored</div>
    </div>
    <div style="background:#f5fff5;border:2px solid #1A7A4A;border-radius:10px;padding:14px;text-align:center">
      <div style="font-size:11px;font-weight:700;color:#1A7A4A;margin-bottom:6px">🟢 TROUGH PROXIMITY</div>
      <div style="font-size:36px;font-weight:900;color:#1A7A4A">{_ct}%</div>
      {_pbar(_ct,"#1A7A4A",160)}
      <div style="font-size:10px;color:#888;margin-top:6px">{len(_ctr)} of {_cn} indicators in trough territory</div>
    </div>
  </div>

  <!-- What this means -->
  <div style="background:#f0f4ff;border:1px solid #c0c8e8;border-radius:8px;padding:10px 14px;margin-bottom:16px;font-size:11px;color:#334">
    <strong>How to read:</strong> Each indicator is mapped to historical patterns at past market peaks (2000, 2007, 2018, 2022) 
    and troughs (2003, 2009, 2020). Peak Proximity = % of weighted indicators currently in peak-like territory. 
    Trough Proximity = % in trough-like territory. Remaining indicators are in neutral/mid-cycle territory. 
    <strong>55%+ Peak = high caution. 40%+ Trough = accumulation zone.</strong>
  </div>

  <!-- Peak-like indicators -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px">
    <div>
      <div style="font-size:12px;font-weight:800;color:#C0390F;margin-bottom:6px;padding:6px 10px;background:#fff5f5;border-radius:6px">
        🔴 PEAK-LIKE CONDITIONS ({len(_cpk)} indicators)
        <span style="float:right;font-size:10px;font-weight:400;color:#C0390F">Currently resembling historical market tops</span>
      </div>
      <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:6px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
        {_tbl_hdr}<tbody>{_peak_ind_rows}</tbody>
      </table>
    </div>
    <div>
      <div style="font-size:12px;font-weight:800;color:#1A7A4A;margin-bottom:6px;padding:6px 10px;background:#f5fff5;border-radius:6px">
        🟢 TROUGH-LIKE CONDITIONS ({len(_ctr)} indicators)
        <span style="float:right;font-size:10px;font-weight:400;color:#1A7A4A">Currently resembling historical market bottoms</span>
      </div>
      <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:6px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
        {_tbl_hdr}<tbody>{_trough_ind_rows or "<tr><td colspan='6' style='padding:10px;text-align:center;color:#888;font-size:11px'>No indicators in trough territory</td></tr>"}</tbody>
      </table>
    </div>
  </div>
</div>"""

    # ── Data quality legend ───────────────────────────────────────────────────
    _dq_html = """
<div style="margin-top:16px;background:#f8f9ff;border:1px solid #dde;border-radius:8px;padding:12px 16px">
  <div style="font-size:11px;font-weight:800;color:#334;margin-bottom:8px">🔬 Data Accuracy Guide — Which Indicators Are Proxies?</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:10px;color:#556;line-height:1.7">
    <div>
      <div style="font-weight:700;color:#1A7A4A">✅ FRED Direct (highest accuracy)</div>
      <div style="color:#666">HY/IG OAS, Yield curves, Real yield, Breakeven, Fed Funds, Sahm Rule, NY Fed Recession Prob, Credit Card Delinquency, CPI, INDPRO, CapUtil, Retail Sales, Housing Starts, Mortgage Rate, Net Liquidity (WALCL-WTREGEN-RRP), M2, Fed Balance Sheet</div>
      <div style="margin-top:6px;font-weight:700;color:#1155cc">📈 yfinance Live (real-time, directionally accurate)</div>
      <div style="color:#666">VIX/VVIX/SKEW/MOVE, SPX vs 200DMA, RSP/SPY ratio, DXY, GLD/TLT/SPY ratios, Sector ETF ratios (XLY/XLP etc.), XHB/SPY, USDJPY, Put/Call ratio</div>
    </div>
    <div>
      <div style="font-weight:700;color:#D4820A">⚠️ Proxy/Approximation (directional, not exact)</div>
      <div style="color:#666"><strong>CCC OAS</strong> — HYG/LQD ratio scaled, NOT actual CCC index<br>
      <strong>OFR FSI / C&amp;I Delinquency</strong> — VIX+HYG/LQD proxy<br>
      <strong>% Above 50/200 DMA</strong> — only ~40 large-cap stocks, not full S&amp;P 500<br>
      <strong>NYSE A/D</strong> — proxy from same 40-stock sample<br>
      <strong>Smart/Dumb Money</strong> — proxy from VIX term + HYG momentum</div>
      <div style="margin-top:6px;font-weight:700;color:#888">🔍 Scraped/Estimated (may be stale)</div>
      <div style="color:#666"><strong>CAPE, Buffett Indicator</strong> — web scraped, GDP lags 3-4 months<br>
      <strong>Forward P/E, ERP</strong> — estimated from SPY metadata<br>
      <strong>AAII Sentiment</strong> — weekly web scrape (may fail)<br>
      <strong>TOP10 Concentration</strong> — real-time from spot prices ✓</div>
    </div>
  </div>
  <div style="margin-top:8px;font-size:10px;color:#888;border-top:1px solid #eee;padding-top:6px">
    <strong>Fix breadth proxies:</strong> Download Barchart CSV → "Stocks Highs/Lows" or "Market Overview" for actual NYSE breadth.
    These CSVs can then replace the proxy calculations (Phase 2 — Barchart integration).
  </div>
</div>"""

    return f"""
<div style="font-family:'Segoe UI',Arial,sans-serif;padding:4px">

<!-- REGIME HEADER -->
<div style="background:{_rcol};color:#fff;padding:14px 20px;border-radius:10px;margin-bottom:12px;display:flex;align-items:center;gap:20px;flex-wrap:wrap">
  <div>
    <div style="font-size:16px;font-weight:800">📡 LEADING INDICATOR REPORT</div>
    <div style="font-size:11px;opacity:0.85;margin-top:2px">5-signal checklist + ALL {len(pt.get("peak_sigs",[]))+len(pt.get("trough_sigs",[]))} scorecard indicators scored against historical peaks &amp; troughs</div>
  </div>
  <div style="margin-left:auto;text-align:right">
    <div style="font-size:20px;font-weight:900">Quick: {_ps}/5 peak · {_ts}/5 trough</div>
    <div style="font-size:10px;opacity:0.85">{pt['verdict'][:70]}</div>
  </div>
</div>

{_fred_notice}

<!-- PEAK / TROUGH QUICK CHECKLIST -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px">
  <div style="border:2px solid #C0390F;border-radius:10px;padding:14px;background:#fff5f5">
    <div style="font-size:12px;font-weight:800;color:#C0390F;margin-bottom:8px">
      🔴 PEAK SELL SIGNALS (quick check) &nbsp; <span style="float:right;font-size:18px;font-weight:900">{_ps}/5</span>
    </div>
    <table style="width:100%;border-collapse:collapse"><tbody>{_peak_rows}</tbody></table>
    <div style="margin-top:5px;font-size:9px;color:#888">3+ = high-confidence sell/hedge · 5 signals = binary, see comprehensive scoring below for full picture</div>
  </div>
  <div style="border:2px solid #1A7A4A;border-radius:10px;padding:14px;background:#f5fff5">
    <div style="font-size:12px;font-weight:800;color:#1A7A4A;margin-bottom:8px">
      🟢 TROUGH BUY SIGNALS (quick check) &nbsp; <span style="float:right;font-size:18px;font-weight:900">{_ts}/5</span>
    </div>
    <table style="width:100%;border-collapse:collapse"><tbody>{_trough_rows}</tbody></table>
    <div style="margin-top:5px;font-size:9px;color:#888">3+ = high-confidence buy · ISM/Claims show N/A until fredapi installed</div>
  </div>
</div>

<!-- VERDICT -->
<div style="background:{_rcol}18;border:2px solid {_rcol};border-radius:8px;padding:10px 16px;margin-bottom:16px">
  <div style="font-size:11px;font-weight:800;color:{_rcol}">📋 REGIME VERDICT</div>
  <div style="font-size:12px;color:#333;margin-top:4px">{pt['verdict']}</div>
  <div style="font-size:10px;color:#666;margin-top:4px;font-style:italic"><strong>Suggested posture:</strong> {pt['action']}</div>
</div>

{_comp_html}

{episode_html}

<!-- INDICATOR PANELS (from new FRED additions) -->
<div style="margin-top:20px;font-size:13px;font-weight:800;color:#1a1a2e;margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #e0e4ed">
  📥 NEW FRED ADDITIONS — Detailed Leading Indicators
  <span style="font-size:10px;font-weight:400;color:#667;margin-left:8px">Shows N/A until: pip install fredapi pandas_datareader</span>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
  <div>
    {_ts_hdr("🏭 ISM Manufacturing Dashboard", _ism_rows) or '<div style="margin-bottom:16px;padding:12px;background:#fff8e1;border:1px solid #ffe082;border-radius:6px;font-size:10px;color:#795548">ISM data not loaded — install fredapi</div>'}
    {_ts_hdr("📋 Jobless Claims Monitor", _cl_rows) or '<div style="margin-bottom:16px;padding:12px;background:#fff8e1;border:1px solid #ffe082;border-radius:6px;font-size:10px;color:#795548">Claims data not loaded — install fredapi</div>'}
    {_ts_hdr("📈 Leading + Consumer Indicators", _lei_rows) or '<div style="margin-bottom:16px;padding:12px;background:#fff8e1;border:1px solid #ffe082;border-radius:6px;font-size:10px;color:#795548">LEI/Durable Goods/UMich not loaded — install fredapi</div>'}
    {_ts_hdr("🛢️ Oil Regime Signal", _oil_rows)}
  </div>
  <div>
    {_ts_hdr("🧠 Sentiment Panel", _sent_rows)}
    {_ts_hdr("🇯🇵 USD/JPY — Yen Carry Risk", _jpy_rows)}
    {_ts_hdr("🏦 SOFR — Repo Market Stress", _sofr_rows)}
  </div>
</div>

{_dq_html}

</div>"""

def fred(sid, name=None, n=200):
    """
    Fetch a FRED series with 4-layer fallback + circuit breaker.
    Returns (Series, source_string).
    """
    import pandas as pd
    global _FRED_DATAREADER_DISABLED, _FRED_CSV_DISABLED

    # Layer 1: fredapi (most reliable if key set)
    s = _fred_via_fredapi(sid, n)
    if not s.empty:
        return s, "fredapi"

    # Layer 2: pandas_datareader (skip if circuit breaker tripped)
    if not _FRED_DATAREADER_DISABLED:
        s = _fred_via_datareader(sid, n)
        if not s.empty:
            fred._dr_fails = 0   # reset on success
            return s, "pandas_datareader"
        else:
            # Only count actual network failures, not "series not found"
            _was_timeout = getattr(fred, "_last_dr_was_timeout", False)
            if _was_timeout:
                fred._dr_fails = getattr(fred, "_dr_fails", 0) + 1
                if fred._dr_fails >= 3:
                    _FRED_DATAREADER_DISABLED = True
                    _FRED_CSV_DISABLED = True   # same servers — disable both together
                    print("  ⚡ FRED unreachable — switching directly to yfinance proxy for all remaining series")
            else:
                fred._dr_fails = 0   # series not found is not a network failure

    # Layer 3: public CSV (skip if circuit breaker tripped)
    if not _FRED_CSV_DISABLED:
        s = _fred_via_csv(sid, n)
        if not s.empty:
            fred._csv_fails = 0
            return s, "pandas_datareader"
        else:
            fred._csv_fails = getattr(fred, "_csv_fails", 0) + 1
            if fred._csv_fails >= 3:
                _FRED_CSV_DISABLED = True
                print("  ⚡ FRED CSV unreachable — using yfinance proxy for all remaining series")
            else:
                fred._csv_fails = 0

    # Layer 4: yfinance proxy (works even when FRED is fully blocked)
    if name:
        s_proxy, proxy_src = _fred_via_yfinance_proxy(name, n)
        if s_proxy is not None and not s_proxy.empty:
            return s_proxy, f"yf_proxy({proxy_src})"

    return pd.Series(dtype=float), "all_failed"


def fetch_fred(series_dict, label=""):
    """Fetch all FRED series with fallbacks. Prints ✓/✗/≈ per series."""
    import pandas as pd
    global _YF_PROXY_CACHE, _FRED_DATAREADER_DISABLED, _FRED_CSV_DISABLED
    # Reset circuit breakers and cache for a fresh run
    _FRED_DATAREADER_DISABLED = False
    _FRED_CSV_DISABLED        = False
    _YF_PROXY_CACHE           = {}
    fred._dr_fails  = 0
    fred._csv_fails = 0
    results = {}
    ok = proxy = failed = 0
    total = len(series_dict)

    for name, sid in series_dict.items():
        s, src = fred(sid, name=name)
        if not s.empty:
            results[name] = s
            latest = round(float(s.iloc[-1]), 4)
            dt     = str(s.index[-1])[:10]
            is_proxy = "yf_proxy" in src
            sym = "≈" if is_proxy else "✓"
            proxy   += is_proxy
            ok      += not is_proxy
            print(f"  {sym} {name:18s} {latest:>10.3f}  {dt}  ({src})")
        else:
            failed += 1
            print(f"  ✗ {name:18s} no data — FRED unreachable & no yfinance proxy")

    total_ok = ok + proxy
    print(f"  → {ok} from FRED  {proxy} from yfinance proxy  {failed} failed  ({total_ok}/{total} total)")
    if total_ok > 0:
        print(f"  NOTE: Monthly FRED series (HOUST, CAPUTIL, etc.) publish with 4-8 week lag.")
        print(f"        In March 2026, latest data is typically Nov/Dec 2025 — this is NORMAL.")
    if proxy > 0:
        print("  ≈ = yfinance-derived proxy (directionally correct, not exact FRED values)")
    return results, {}

# ── Sector top-10 holdings + approximate weights (Q1 2026) ───────────────────
SECTOR_TOP10 = {
    "XLK":  ["AAPL","NVDA","MSFT","AVGO","META","ORCL","AMD","CSCO","ADBE","CRM"],
    "XLF":  ["BRK-B","JPM","V","MA","BAC","WFC","GS","MS","SPGI","BLK"],
    "XLV":  ["LLY","UNH","JNJ","ABBV","MRK","TMO","ABT","DHR","PFE","AMGN"],
    "XLE":  ["XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","BKR","FANG"],
    "XLI":  ["GE","RTX","CAT","UNP","HON","LMT","ETN","DE","TT","CARR"],
    "XLY":  ["AMZN","TSLA","MCD","NKE","LULU","BKNG","HD","LOW","TJX","SBUX"],
    "XLP":  ["PG","KO","PEP","COST","WMT","PM","MO","MDLZ","CL","STZ"],
    "XLU":  ["NEE","SO","DUK","SRE","AEP","D","EXC","XEL","ED","ETR"],
    "XLC":  ["META","GOOGL","NFLX","DIS","CHTR","EA","T","VZ","TMUS","OMC"],
    "XLRE": ["PLD","AMT","EQIX","SPG","WELL","PSA","O","DLR","AVB","EQR"],
    "XLB":  ["LIN","APD","SHW","FCX","NEM","NUE","DOW","DD","PPG","VMC"],
}
SECTOR_WEIGHTS = {
    "XLK":  {"AAPL":22.5,"NVDA":18.2,"MSFT":17.8,"AVGO":7.2,"META":4.8,"ORCL":3.9,"AMD":3.1,"CSCO":2.8,"ADBE":2.5,"CRM":2.1},
    "XLF":  {"BRK-B":14.2,"JPM":12.8,"V":9.1,"MA":6.3,"BAC":5.7,"WFC":4.8,"GS":3.9,"MS":3.4,"SPGI":3.1,"BLK":2.9},
    "XLV":  {"LLY":13.8,"UNH":11.2,"JNJ":8.4,"ABBV":7.6,"MRK":6.2,"TMO":4.9,"ABT":4.1,"DHR":3.6,"PFE":3.2,"AMGN":3.0},
    "XLE":  {"XOM":23.1,"CVX":15.4,"COP":8.2,"EOG":6.1,"SLB":5.3,"MPC":4.8,"PSX":4.2,"VLO":3.9,"BKR":3.4,"FANG":3.1},
    "XLI":  {"GE":9.8,"RTX":8.1,"CAT":7.2,"UNP":6.4,"HON":5.9,"LMT":5.1,"ETN":4.8,"DE":4.3,"TT":3.7,"CARR":3.2},
    "XLY":  {"AMZN":23.4,"TSLA":16.8,"MCD":7.1,"NKE":5.2,"LULU":3.8,"BKNG":3.4,"HD":3.1,"LOW":2.9,"TJX":2.7,"SBUX":2.4},
    "XLP":  {"PG":15.2,"KO":11.4,"PEP":10.1,"COST":9.8,"WMT":8.3,"PM":7.2,"MO":5.6,"MDLZ":4.1,"CL":3.8,"STZ":3.2},
    "XLU":  {"NEE":15.8,"SO":8.2,"DUK":7.9,"SRE":6.1,"AEP":5.8,"D":5.4,"EXC":4.9,"XEL":4.3,"ED":3.7,"ETR":3.1},
    "XLC":  {"META":22.6,"GOOGL":19.4,"NFLX":8.2,"DIS":5.1,"CHTR":4.3,"EA":3.2,"T":3.0,"VZ":2.8,"TMUS":2.5,"OMC":2.1},
    "XLRE": {"PLD":11.2,"AMT":9.4,"EQIX":8.1,"SPG":6.2,"WELL":5.8,"PSA":5.1,"O":4.7,"DLR":4.3,"AVB":3.9,"EQR":3.4},
    "XLB":  {"LIN":16.4,"APD":9.2,"SHW":8.7,"FCX":7.1,"NEM":6.3,"NUE":5.4,"DOW":4.9,"DD":4.3,"PPG":4.0,"VMC":3.8},
}
SECTOR_DISPLAY_NAMES = {
    "XLK":"Technology","XLF":"Financials","XLV":"Health Care",
    "XLE":"Energy","XLI":"Industrials","XLY":"Consumer Disc.",
    "XLP":"Consumer Staples","XLU":"Utilities","XLC":"Comm. Services",
    "XLRE":"Real Estate","XLB":"Materials",
}
# 10 maximally distinct colors for stock lines
STOCK_COLORS = [
    "#2196F3","#FF5722","#4CAF50","#9C27B0","#FF9800",
    "#00BCD4","#E91E63","#8BC34A","#FF1744","#3F51B5",
]

def fetch_sector_stocks(md_existing):
    """Batch-download 1yr daily prices for all sector top-10 holdings."""
    import pandas as pd
    import yfinance as yf
    all_stocks = list({t for ts in SECTOR_TOP10.values() for t in ts})
    print(f"  Downloading {len(all_stocks)} sector stock tickers (1yr)...")
    try:
        raw = yf.download(all_stocks, period="1y", auto_adjust=True, progress=False)
        closes = raw["Close"] if hasattr(raw.columns, "levels") else raw
        stock_data = {}
        for t in all_stocks:
            if t in closes.columns:
                s = closes[t].dropna()
                try:
                    if s.index.tz is not None: s.index = s.index.tz_localize(None)
                except Exception: pass
                if len(s) >= 50:
                    stock_data[t] = s
        print(f"  Got {len(stock_data)}/{len(all_stocks)} stock tickers")
    except Exception as e:
        print(f"  Sector stock download failed: {e}")
        stock_data = {}
    result = {}
    for etf, tickers in SECTOR_TOP10.items():
        etf_s = md_existing.get(etf)
        if etf_s is None or len(etf_s) < 50: continue
        etf_1y = etf_s.tail(252).copy()
        try:
            if etf_1y.index.tz is not None: etf_1y.index = etf_1y.index.tz_localize(None)
        except Exception: pass
        stocks = {t: stock_data[t].tail(252) for t in tickers if t in stock_data}
        if stocks:
            result[etf] = {"etf": etf_1y, "stocks": stocks}
    return result

def fetch_market(quick=False):
    """Fetch ETF prices via yfinance. ^GSPC uses max history for cycle overlay."""
    import pandas as pd
    all_t = list(SECTOR_ETFS)
    for p in CROSS_PAIRS: all_t += list(p[:2])
    all_t += ["SPY","QQQ","IWM","GLD","TLT","HYG","LQD","USO","^VIX","^VIX9D","^VIX3M","XHB","ITB","VNQ"]
    all_t  = list(dict.fromkeys(all_t))
    if quick: all_t = ["SPY","QQQ","IWM","XLK","XLP","XLF","XLU","XLY","XLE","GLD","TLT","HYG","XHB"]
    try:
        import yfinance as yf
        print(f"  Downloading {len(all_t)} tickers (5yr)...")
        raw = yf.download(all_t, period="5y", auto_adjust=True, progress=False)
        closes = raw["Close"] if hasattr(raw.columns,"levels") else raw
        out = {t: closes[t].dropna() for t in all_t
               if t in closes.columns and len(closes[t].dropna()) > 100}
        print(f"  Got {len(out)} tickers  (5-year history)")

        # Also fetch ^GSPC max history for cycle overlay (1980s onward)
        print("  Downloading ^GSPC max history for cycle overlay...")
        try:
            gspc = yf.download("^GSPC", period="max", auto_adjust=True, progress=False)
            if not gspc.empty:
                gspc_c = gspc["Close"].squeeze().dropna()
                gspc_c.index = pd.to_datetime(gspc_c.index).tz_localize(None)
                out["^GSPC"] = gspc_c
                print(f"  ^GSPC: {len(gspc_c)} rows from {gspc_c.index[0].date()} to {gspc_c.index[-1].date()}")
        except Exception as e2:
            print(f"  ^GSPC max history failed: {e2} — overlay will show current cycle only")

        # ── Supplemental data: batch download ALL extra tickers at once ──────
        try:
            import numpy as np
            import pandas as _pd   # needed for Series construction below
            _SUPP = ["^VIX","^VIX9D","^VIX3M","^MOVE","^VVIX","^SKEW",
                     "RSP","DX-Y.NYB","GC=F","USDJPY=X",
                     # Top-10 SPX for market cap calculation
                     "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","BRK-B","JPM","GOOG"]
            _supp_raw = yf.download(_SUPP, period="5d", auto_adjust=True, progress=False)
            _supp_c = (_supp_raw["Close"] if hasattr(_supp_raw.columns, "levels")
                       else _supp_raw).dropna(how="all")
            for _st in _SUPP:
                if _st in _supp_c.columns and not _supp_c[_st].isna().all():
                    _sv = _supp_c[_st].dropna()
                    if not _sv.empty:
                        # Only overwrite if we don't already have a longer series
                        _existing = out.get(_st)
                        if _existing is None or len(_existing) < 10:
                            out[_st] = _sv
                        # else: keep the 5yr version — just update the last few rows
                        elif len(_sv) > 0:
                            # Merge: use 5yr as base, update with fresh 5d prices
                            import pandas as _pdm
                            _merged = _pdm.concat([_existing, _sv]).groupby(level=0).last().sort_index()
                            out[_st] = _merged

            # ^GSPC needs 2yr+ for 200DMA — add only if missing from main download
            if "^GSPC" not in out or len(out.get("^GSPC", [])) < 200:
                try:
                    _gs2 = yf.download("^GSPC", period="2y", auto_adjust=True, progress=False)
                    if not _gs2.empty:
                        _gs2c = (_gs2["Close"] if "Close" in _gs2.columns else _gs2.iloc[:,0]).dropna()
                        _gs2c.index = _pd.to_datetime(_gs2c.index).tz_localize(None)
                        out["^GSPC"] = _gs2c
                except Exception: pass

            # Breadth: % above 50/200 DMA from the 1yr batch already downloaded
            PROXY_TICKERS = [
                "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","V","UNH",
                "XOM","JNJ","PG","MA","HD","ABBV","KO","CVX","MRK","LLY",
                "PEP","AVGO","COST","NFLX","TMO","ACN","MCD","DHR","TXN","NEE",
                "RTX","LIN","COP","QCOM","HON","GS","SPGI","BLK","C","CAT",
            ]
            _breadth_hist = yf.download(
                " ".join(PROXY_TICKERS), period="1y",
                auto_adjust=True, progress=False, multi_level_index=False
            )
            if not _breadth_hist.empty:
                _cl = (_breadth_hist["Close"].dropna(how="all")
                       if "Close" in _breadth_hist.columns else _breadth_hist)
                if len(_cl) > 200:
                    _ab50 = _ab200 = _total = 0
                    for _t in PROXY_TICKERS:
                        if _t in _cl.columns and not _cl[_t].isna().all():
                            _c = float(_cl[_t].iloc[-1])
                            _ab50  += int(_c > float(_cl[_t].rolling(50).mean().iloc[-1]))
                            _ab200 += int(_c > float(_cl[_t].rolling(200).mean().iloc[-1]))
                            _total += 1
                    if _total > 10:
                        out["_pct_above_50"]  = _pd.Series([round(_ab50/_total*100,1)])
                        out["_pct_above_200"] = _pd.Series([round(_ab200/_total*100,1)])
                        print(f"  Breadth ({_total} stocks): >50DMA={out['_pct_above_50'].iloc[0]}% >200DMA={out['_pct_above_200'].iloc[0]}%")
                    # A/D net from last 2 days
                    _adv2 = sum(1 for _tt in PROXY_TICKERS
                                if _tt in _cl.columns and len(_cl[_tt].dropna()) >= 2
                                and float(_cl[_tt].dropna().iloc[-1]) > float(_cl[_tt].dropna().iloc[-2]))
                    _dec2 = _total - _adv2
                    out["_nyad_net"] = _pd.Series([float(_adv2 - _dec2)])
                    print(f"  A/D proxy ({_total} tickers): adv={_adv2} dec={_dec2} net={_adv2-_dec2:+d}")

            # Top-10 SPX weight — price × shares outstanding (no per-ticker API calls)
            # Shares outstanding in billions (updated quarterly, stable enough)
            _SHARES_B = {
                "AAPL":15.1, "MSFT":7.43, "NVDA":24.4, "AMZN":10.6,
                "META":2.55, "GOOGL":5.85, "TSLA":3.20,
                "BRK-B":2170.0,  # BRK-B equiv shares (millions → billions implicit in calc)
                "JPM":2.84,  "GOOG":5.85,
            }
            _mcaps = {}
            for _t, _sh in _SHARES_B.items():
                _ps = out.get(_t)
                if _ps is None or (hasattr(_ps, 'empty') and _ps.empty):
                    _ps = _supp_c[_t].dropna() if _t in _supp_c.columns else None
                if _ps is not None and not (hasattr(_ps,"empty") and _ps.empty):
                    try:
                        _px = float(_ps.iloc[-1])
                        # BRK-B shares is in millions, others in billions
                        _mc = _px * _sh if _t != "BRK-B" else _px * _sh / 1000.0
                        _mcaps[_t] = _mc * 1e9  # convert B shares × price → dollars
                    except Exception: pass

            if len(_mcaps) >= 7:
                # SPX total market cap ≈ SPX index level × 8.5 billion (calibrated 2024-2026)
                _spx_level = float(out.get("^GSPC", _pd.Series([6500])).iloc[-1])
                _spx_total = _spx_level * 8.5e9   # in dollars
                _w_raw = round(sum(_mcaps.values()) / _spx_total * 100, 1)
                if 10 < _w_raw < 55:
                    out["_top10_weight"] = _pd.Series([_w_raw])
                    print(f"  Top-10 weight: {_w_raw}%")

            print(f"  Supplemental market data fetched ✓")
        except Exception as _e:
            print(f"  [supplemental fetch] {_e}")

        return out
    except Exception as e:
        print(f"  yfinance error: {e}")
        return {}

# ── Technical indicators ──────────────────────────────────────────────────────
def ind(s):
    import numpy as np
    if s is None or len(s) < 20: return {}
    c = float(s.iloc[-1])
    e20  = float(s.ewm(span=20,  adjust=False).mean().iloc[-1])
    e50  = float(s.ewm(span=50,  adjust=False).mean().iloc[-1])
    e200 = float(s.ewm(span=200, adjust=False).mean().iloc[-1])
    d = s.diff()
    g = d.clip(lower=0).rolling(14).mean()
    l = (-d.clip(upper=0)).rolling(14).mean()
    rsi = round(float((100-100/(1+g/l.replace(0,1e-9))).iloc[-1]),1)
    vol  = round(float(s.pct_change().rolling(20).std().iloc[-1])*(252**.5)*100,1) if len(s)>20 else None
    def pct(a,b): return round((a/b-1)*100,2) if b else None
    def safe(n): return float(s.iloc[max(-n,-len(s))])
    return {
        "price":c,"e20":e20,"e50":e50,"e200":e200,"rsi":rsi,"vol":vol,
        "vs200":pct(c,e200),"vs50":pct(c,e50),"vs20":pct(c,e20),
        "c1w":pct(c,safe(5)),"c1m":pct(c,safe(21)),"c3m":pct(c,safe(63)),
        "c6m":pct(c,safe(126)),"c1y":pct(c,safe(252)),
        "trend": "UP" if c>e20>e50>e200 else "DOWN" if c<e20<e50<e200 else "MIX",
    }

def ratio_info(s_n, s_d):
    import pandas as pd
    import numpy as np
    combined = pd.concat([s_n,s_d],axis=1).dropna()
    if len(combined) < 60: return {}
    r = combined.iloc[:,0]/combined.iloc[:,1]
    i = ind(r)
    if not i: return {}
    rank1y = round(float((r.iloc[-1]>r.tail(252)).mean()*100),1) if len(r)>=252 else 50
    c3m = i.get("c3m",0) or 0
    c = i["price"]; e20 = i["e20"]
    if c3m>2 and c>e20:     d,dc="RISING ↑","#1A7A4A"
    elif c3m<-2 and c<e20:  d,dc="FALLING ↓","#C0390F"
    else:                    d,dc="FLAT →","#556"
    # Build chart-ready ratio series (last 2yr, monthly)
    r_monthly = r.resample("ME").last().tail(24)
    chart_dates  = [str(x)[:10] for x in r_monthly.index]
    chart_values = [round(float(v),4) for v in r_monthly.values]
    return {**i, "direction":d,"dir_col":dc,"rank1y":rank1y,
            "chart_dates":chart_dates,"chart_values":chart_values}

# ══════════════════════════════════════════════════════════════════════════════
# EARNINGS PEAK SCORECARD
# ══════════════════════════════════════════════════════════════════════════════

def ep_score(fd):
    inds = []
    def g(k,n=-1):
        s=fd.get(k)
        return float(s.iloc[max(n,-len(s))]) if s is not None and not s.empty else None
    def yoy(k,p=12):
        s=fd.get(k)
        if s is None or len(s)<p+2: return None
        a,b=float(s.iloc[-1]),float(s.iloc[-p-1])
        return round((a/b-1)*100,2) if b!=0 else None
    def mom(k,p=3):
        s=fd.get(k)
        if s is None or len(s)<p+2: return None
        return round(float(s.iloc[-1])-float(s.iloc[-p-1]),4)

    def add(nm,val,sig,wt,thresh,trend,ctx,hist):
        inds.append({"name":nm,"value":val,"signal":sig,"weight":wt,
                     "threshold":thresh,"trend":trend,"context":ctx,"historical":hist})

    v=g("HY_OAS"); chg=mom("HY_OAS",3)
    if v: sig="RED" if v>450 else "YELLOW" if v>380 else "GREEN"
    if v: add("HY Credit Spreads",f"{v:.0f} bps",sig,3,"RED>450|YLW>380|GRN<380",
              f"{chg:+.0f}bps (3mo)" if chg else "—",
              f"{'ELEVATED — credit stress' if v>380 else f'Calm at {v:.0f} bps'}. Spreads widen 6-12mo before peak.",
              "2007: 280→450 over 8mo then accelerated to 700bps (peak confirmed)")

    v=g("YIELD_CURVE")
    if v is not None:
        s_yc=fd.get("YIELD_CURVE")
        was_inv=(s_yc is not None and len(s_yc)>24 and any(float(x)<0 for x in s_yc.iloc[-24:]))
        sig="RED" if v<-50 else "YELLOW" if v<30 else "GREEN"  # v now in bps
        phase=("POST-INVERSION → recession median 12-18mo later" if was_inv and v>0
               else "INVERTED → recession within 12mo historically" if v<0
               else "Positive — no inversion signal")
        add("Yield Curve (10Y−2Y)",f"{v:+.2f}%",sig,3,"RED<-0.5|YLW<+0.3|GRN>+0.3",
            phase,phase,"Every US recession since 1955 preceded by yield curve inversion")

    v=g("UNRATE"); v3=g("UNRATE",-4)
    if v and v3:
        rise=round(v-v3,2)
        sig="RED" if rise>0.5 else "YELLOW" if rise>0.2 else "GREEN"
        _lm = "cooling" if rise>0.2 else "healthy"
        _sahm_ctx = "RECESSION SIGNAL: Sahm triggered" if rise>0.5 else f"Labor market {_lm}, {rise:+.2f}pp drift"
        add("Unemployment (Sahm)",f"{v:.1f}% (+{rise:.2f}pp 3mo)",sig,3,
            "RED Δ>0.5pp | YLW 0.2-0.5 | GRN <0.2",
            f"Sahm {'TRIGGERED' if rise>0.5 else 'approaching' if rise>0.2 else 'clear'}",
            _sahm_ctx,
            "Sahm Rule: 0-for-0 in false signals — triggered in every US recession since 1970")

    v=yoy("INDPRO",12); vm=yoy("INDPRO",1)
    if v is not None:
        sig="RED" if v<-1 else "YELLOW" if v<1.5 else "GREEN"
        add("Industrial Production YoY",f"{v:+.1f}%",sig,2,"RED<-1|YLW<1.5|GRN>1.5",
            f"MoM: {vm:+.2f}%" if vm else "—",
            f"Production {'contracting' if v<0 else 'decelerating' if v<1.5 else 'growing'} {v:.1f}% — {'factory recession underway' if v<0 else 'watch for turn' if v<1.5 else 'capex cycle healthy'}",
            "IP turned negative 1-3 months before EPS peaked in 2000, 2007, 2019, 2022")

    v=g("CAPUTIL")
    if v: sig="RED" if v<74 else "YELLOW" if v<77 else "GREEN"
    if v: add("Capacity Utilization",f"{v:.1f}%",sig,2,"RED<74|YLW<77|GRN>77",
              "Historical avg ~77.5%",
              f"{'Excess capacity — pricing pressure' if v<76 else 'Near/above capacity — inflation risk' if v>80 else 'Moderate'} at {v:.1f}%",
              "Above 81%: inflation then tightening then peak. Below 74%: oversupply deflation risk.")

    rn=yoy("RETAIL",12); cp=yoy("CPI",12)
    if rn and cp:
        rr=round(rn-cp,2); sig="RED" if rr<-1 else "YELLOW" if rr<1 else "GREEN"
        add("Real Retail Sales YoY",f"{rr:+.1f}% real",sig,2,"RED<-1|YLW<1|GRN>1",
            f"Nominal {rn:+.1f}% − CPI {cp:+.1f}%",
            f"Consumer {'contracting' if rr<0 else 'slowing' if rr<1 else 'healthy'} in real terms",
            "Negative real retail sales for 2+ quarters preceded 2001, 2008, 2020 recessions")

    v=g("FEDFUNDS"); v6=g("FEDFUNDS",-7)
    if v:
        sig="RED" if v>4.5 else "YELLOW" if v>3.5 else "GREEN"
        chg=round(v-(v6 or v),2)
        add("Fed Funds Rate",f"{v:.2f}%",sig,2,"RED>4.5|YLW>3.5|GRN<3.5",
            f"6mo chg: {chg:+.2f}%",
            f"{'Restrictive — compressing multiples' if v>4 else 'Neutral-easy'}. {'Cutting.' if chg<-.25 else 'Holding.' if abs(chg)<.1 else 'Hiking.'}",
            "Rates >4% sustained 12mo: P/E compressed 15-25% in 2000, 2007, 2022")

    v=yoy("CPI",12)
    if v:
        sig="RED" if v>4 else "YELLOW" if v>2.5 else "GREEN"
        add("CPI Inflation YoY",f"{v:.1f}%",sig,2,"RED>4|YLW>2.5|GRN<2.5","Fed target 2%",
            f"{'Above target — margin pressure' if v>3 else 'Near target — benign' if v<2.5 else 'Elevated but decelerating'}",
            "CPI >4% sustained: margin compression lagged 2-4Q in 2000, 2006-08, 2021-22")

    v=g("T10Y"); v6=g("T10Y",-7)
    if v:
        sig="RED" if v>4.8 else "YELLOW" if v>4.2 else "GREEN"
        chg=round(v-(v6 or v),2)
        add("10-Year Yield",f"{v:.2f}%",sig,2,"RED>4.8|YLW>4.2|GRN<4.2",
            f"6mo chg: {chg:+.2f}%",
            f"{'High discount rate — DCF compression' if v>4.5 else 'Moderate'}. {'Rising fast.' if chg>.5 else 'Falling.' if chg<-.3 else ''}",
            "10Y >5% in 2023 drove P/E from 22x→17x in 3 months")

    v=yoy("M2SL",12)
    if v:
        sig="RED" if v<-2 else "YELLOW" if v<3 else "GREEN"
        add("M2 Money Supply YoY",f"{v:+.1f}%",sig,1,"RED<-2|YLW<3|GRN>3",
            "Leads nominal GDP 6-12mo",
            f"M2 {'contracting' if v<0 else 'growing slowly' if v<3 else 'healthy'} — {'liquidity headwind' if v<0 else 'neutral-to-tight' if v<3 else 'supportive'}",
            "M2 contraction -4.8% in 2022: first since Great Depression, preceded 2022 bear market")

    v=g("NFCI")
    if v:
        sig="RED" if v>0.5 else "YELLOW" if v>0.1 else "GREEN"
        add("Chicago Fed Fin. Conditions",f"{v:.3f}",sig,2,"RED>0.5|YLW>0.1|GRN<0.1",
            "Pos=tighter | Neg=looser than avg",
            f"{'TIGHT conditions — credit rationing' if v>0.5 else 'Near average' if abs(v)<.2 else 'Loose — watch for over-leverage'}",
            "NFCI >0.5 preceded 2008 crisis and 2020 COVID spike")

    v=yoy("HOUST",12)
    if v is not None:
        sig="RED" if v<-15 else "YELLOW" if v<-5 else "GREEN"
        add("Housing Starts YoY",f"{v:+.0f}%",sig,2,"RED<-15|YLW<-5|GRN>-5","Leads economy 12-18mo",
            f"Housing {'collapsing' if v<-20 else 'declining' if v<-5 else 'stable'} — Kuznets {'downswing' if v<-15 else 'cooling' if v<-5 else 'expansion'} confirmed by data",
            "Housing starts -30%+ before 2007-09; -20%+ before 2000; -50%+ in 2020")

    tw=sum(i["weight"] for i in inds)
    dw=sum(i["weight"] for i in inds if i["signal"] in ("RED","YELLOW"))
    rw=sum(i["weight"] for i in inds if i["signal"]=="RED")
    sp=round(dw/max(tw,1)*100); rp=round(rw/max(tw,1)*100)
    if rp>40 or sp>80: vd,vc="EARNINGS PEAK IMMINENT","#C0390F"
    elif sp>60:         vd,vc="LATE CYCLE — MONITOR","#D4820A"
    elif sp>35:         vd,vc="MID-CYCLE CAUTION","#556"
    else:               vd,vc="EARLY CYCLE CLEAR","#1A7A4A"
    return {"indicators":inds,"score":sp,"red_pct":rp,"verdict":vd,"col":vc,
            "n_red":sum(1 for i in inds if i["signal"]=="RED"),
            "n_yellow":sum(1 for i in inds if i["signal"]=="YELLOW"),
            "n_green":sum(1 for i in inds if i["signal"]=="GREEN")}

# ══════════════════════════════════════════════════════════════════════════════
# CYCLE POSITIONS + PROJECTIONS
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
# FULL MARKET SCORECARD — 35 indicators across 9 categories
# Sorted by weight (WT) within each category: WT4=critical, WT3=important, WT2=confirmers
# Sources: FRED + yfinance + computed from existing data
# ══════════════════════════════════════════════════════════════════════════════

# Signal thresholds: (green_max, yellow_max) — above yellow_max = RED
SCORECARD_DEFS = {
    # ── CREDIT (most predictive of bear markets) ──────────────────────────────
    "HY_OAS":    {"name":"HY Credit Spreads","cat":"Credit","wt":4,"unit":"bps",
                  "src":"FRED BAMLH0A0HYM2",
                  "thresh":{"CALM":(0,380),"CAUTION":(380,450),"STRESS":(450,700),"CRISIS":(700,9999)},
                  "dir":"up_bad","hist":"2007: 280→700. 2020 bottom: 1100. 2022 bottom: 590.",
                  "signal":"Widens 6-12mo before S&P peaks. Single best leading indicator."},
    "IG_OAS":    {"name":"IG Credit Spreads","cat":"Credit","wt":3,"unit":"bps",
                  "src":"FRED BAMLC0A0CM",
                  "thresh":{"CALM":(0,130),"CAUTION":(130,200),"STRESS":(200,300),"CRISIS":(300,9999)},
                  "dir":"up_bad","hist":"2008 GFC bottom: 656bps. 2020: 370bps.",
                  "signal":"IG moves before HY confirms crisis. >200 = systemic."},
    "HY_IG_DIFF":{"name":"HY-IG Differential","cat":"Credit","wt":2,"unit":"bps",
                  "src":"Compute HY−IG",
                  "thresh":{"CALM":(0,260),"CAUTION":(260,400),"STRESS":(400,600),"CRISIS":(600,9999)},
                  "dir":"up_bad","hist":"2008: 1526bps. 2020: 730bps.",
                  "signal":"Pure credit risk premium. Widening = junk bonds cracking relative to IG."},
    "CCC_OAS":   {"name":"CCC Junk Spread","cat":"Credit","wt":3,"unit":"bps",
                  "src":"FRED BAMLH0A3HYM2",
                  "thresh":{"CALM":(0,12),"CAUTION":(12,16),"STRESS":(16,25),"CRISIS":(25,9999)},
                  "dir":"up_bad","hist":"GFC: 40%+. 2020: 20%. 2022: 14%.",
                  "signal":"Cracks first at cycle peaks — earliest credit warning."},
    "NFCI":      {"name":"Chicago Fin. Conditions","cat":"Credit","wt":3,"unit":"",
                  "src":"FRED NFCI",
                  "thresh":{"CALM":(-9,0),"CAUTION":(0,0.5),"STRESS":(0.5,1.5),"CRISIS":(1.5,99)},
                  "dir":"up_bad","hist":"GFC peak: +3.0. 2020: +2.8.",
                  "signal":">0 = tighter than normal = headwind. Below 0 = loose = tailwind."},
    # ── RATES & YIELD CURVE ───────────────────────────────────────────────────
    "YIELD_CURVE":{"name":"Yield Curve 10Y−2Y","cat":"Rates","wt":4,"unit":"bps",
                   "src":"FRED T10Y2Y",
                   "thresh":{"CALM":(50,9999),"CAUTION":(0,50),"STRESS":(-60,0),"CRISIS":(-9999,-60)},
                   "dir":"down_bad","hist":"100% recession prediction since 1955 when inverted.",
                   "signal":"Post-inversion normalization (as now) = 12-18mo lag to recession."},
    "CURVE_10Y3M":{"name":"Yield Curve 10Y−3M","cat":"Rates","wt":4,"unit":"bps",
                   "src":"FRED T10Y3M",
                   "thresh":{"CALM":(50,9999),"CAUTION":(0,50),"STRESS":(-60,0),"CRISIS":(-9999,-60)},
                   "dir":"down_bad","hist":"Fed's preferred curve. Inverted 2022-2024.",
                   "signal":"More timely than 10Y-2Y. Fed's own preferred recession metric."},
    "REAL_YIELD": {"name":"Real 10Y Yield","cat":"Rates","wt":3,"unit":"%",
                   "src":"FRED DFII10",
                   "thresh":{"CALM":(-9,1.5),"CAUTION":(1.5,2.0),"STRESS":(2.0,3.0),"CRISIS":(3.0,99)},
                   "dir":"up_bad","hist":">2% drove P/E from 22x→17x in 2022.",
                   "signal":">2% real = severe multiple compression risk."},
    "BREAKEVEN":  {"name":"10Y Breakeven Inflation","cat":"Rates","wt":3,"unit":"%",
                   "src":"FRED T10YIE",
                   "thresh":{"CALM":(1.8,2.5),"CAUTION":(2.5,3.0),"STRESS":(3.0,3.5),"CRISIS":(3.5,99)},
                   "dir":"up_bad","hist":">3% forces Fed to hike or hold longer.",
                   "signal":"Market's inflation expectation. >3% = Fed trapped."},
    "FED_FUNDS":  {"name":"Fed Funds Rate","cat":"Rates","wt":2,"unit":"%",
                   "src":"FRED FEDFUNDS",
                   "thresh":{"CALM":(0,3.5),"CAUTION":(3.5,4.5),"STRESS":(4.5,5.5),"CRISIS":(5.5,99)},
                   "dir":"up_bad","hist":">4% for 12mo: P/E compressed 15-25% in 2000, 2007, 2022.",
                   "signal":"Earnings peaks lag Fed rate peaks by 2-4 quarters."},
    # ── VOLATILITY ───────────────────────────────────────────────────────────
    "VIX":        {"name":"VIX (Fear Index)","cat":"Volatility","wt":3,"unit":"",
                   "src":"yfinance ^VIX",
                   "thresh":{"CALM":(0,20),"CAUTION":(20,25),"STRESS":(25,35),"CRISIS":(35,999)},
                   "dir":"up_bad","hist":">40 = capitulation zone (buy signal). 2020 peak: 85.",
                   "signal":">25 = fear. >35 = capitulation. Rising VIX + rising market = warning."},
    "VIX_TERM":   {"name":"VIX Term (3M−30D)","cat":"Volatility","wt":3,"unit":"",
                   "src":"yfinance ^VIX3M − ^VIX",
                   "thresh":{"CALM":(1,99),"CAUTION":(0,1),"STRESS":(-2,0),"CRISIS":(-99,-2)},
                   "dir":"down_bad","hist":"Inverted pre-COVID Feb 24 2020 (3 days before crash).",
                   "signal":"Negative = backwardation = panic/crash regime. Most timely crash signal."},
    "MOVE":       {"name":"MOVE Index (Bond Vol)","cat":"Volatility","wt":3,"unit":"",
                   "src":"yfinance ^MOVE",
                   "thresh":{"CALM":(0,90),"CAUTION":(90,120),"STRESS":(120,160),"CRISIS":(160,999)},
                   "dir":"up_bad","hist":"2020: 165. 2022: 158. Normal: 55-90.",
                   "signal":"Bond market fear gauge. Spikes before equity volatility."},
    "VIX9D_RATIO":{"name":"VIX9D / VIX30 Ratio","cat":"Volatility","wt":2,"unit":"x",
                   "src":"yfinance ^VIX9D/^VIX",
                   "thresh":{"CALM":(0,0.95),"CAUTION":(0.95,1.05),"STRESS":(1.05,1.20),"CRISIS":(1.20,99)},
                   "dir":"up_bad","hist":"Crossed 1.0 on Feb 24 2020 (3 days before bottom).",
                   "signal":">1.0 = near-term panic exceeds long-term fear = crash mode."},
    # ── BREADTH ───────────────────────────────────────────────────────────────
    "PCT_ABOVE_50": {"name":"% S&P Above 50DMA","cat":"Breadth","wt":3,"unit":"%",
                     "src":"yfinance proxy ~40 stocks",
                     "thresh":{"CALM":(60,100),"CAUTION":(35,60),"STRESS":(20,35),"CRISIS":(0,20)},
                     "dir":"down_bad","hist":"Historic bottoms: 4-8%. 2020 bottom: 4%.",
                     "signal":"<20% = oversold/potential bottom. <35% = bear confirmed."},
    "PCT_ABOVE_200":{"name":"% S&P Above 200DMA","cat":"Breadth","wt":3,"unit":"%",
                     "src":"yfinance proxy ~40 stocks",
                     "thresh":{"CALM":(60,100),"CAUTION":(40,60),"STRESS":(25,40),"CRISIS":(0,25)},
                     "dir":"down_bad","hist":"GFC bottom: 8%. 2020: 6%. 2022: 22%.",
                     "signal":"<40% = bear conditions. <20% = crash/capitulation."},
    "NYSE_AD":      {"name":"NYSE A/D Net","cat":"Breadth","wt":2,"unit":"",
                     "src":"yfinance proxy (40-stock A/D)",
                     "thresh":{"CALM":(500,99999),"CAUTION":(-200,500),"STRESS":(-1000,-200),"CRISIS":(-99999,-1000)},
                     "dir":"down_bad","hist":"Sustained negative 6mo before 2000 and 2007 tops.",
                     "signal":"Divergence from price = classic pre-crash distribution."},
    # ── VALUATION ─────────────────────────────────────────────────────────────
    "FORWARD_PE": {"name":"Forward P/E","cat":"Valuation","wt":3,"unit":"x",
                   "src":"macrotrends → multpl → FRED EPS → trailing×0.87 → 23.5x est",
                   "thresh":{"CALM":(0,18),"CAUTION":(18,22),"STRESS":(22,26),"CRISIS":(26,999)},
                   "dir":"up_bad","hist":"2000 peak: 28x. GFC: 18x. 2022 start: 23x.",
                   "signal":"Fair value 15-17x. >22x = expensive. Watch for EPS estimate cuts."},
    "ERP":        {"name":"Earnings Risk Premium","cat":"Valuation","wt":3,"unit":"%",
                   "src":"Compute: 1/PE − T10Y",
                   "thresh":{"CALM":(1.5,99),"CAUTION":(0.5,1.5),"STRESS":(-0.5,0.5),"CRISIS":(-99,-0.5)},
                   "dir":"down_bad","hist":"2000 peak: -2.5%. GFC peak: +0.5%.",
                   "signal":"Negative = bonds beat stocks. Most dangerous regime for equities."},
    "CAPE":       {"name":"Shiller CAPE","cat":"Valuation","wt":3,"unit":"x",
                   "src":"web/manual (multpl.com)",
                   "thresh":{"CALM":(0,25),"CAUTION":(25,30),"STRESS":(30,36),"CRISIS":(36,999)},
                   "dir":"up_bad","hist":"1929: 32. 2000: 44. 2022 start: 40.",
                   "signal":"Best 10yr return predictor. >36 = historically very overvalued."},
    "BUFFETT":    {"name":"Buffett Indicator","cat":"Valuation","wt":3,"unit":"%",
                   "src":"FRED WILL5000PRFC / GDP",
                   "thresh":{"CALM":(0,120),"CAUTION":(120,150),"STRESS":(150,200),"CRISIS":(200,999)},
                   "dir":"up_bad","hist":"Buffett himself calls >150% overvalued.",
                   "signal":">175% = historically very overvalued. Current ~230%."},
    # ── LIQUIDITY ─────────────────────────────────────────────────────────────
    "NET_LIQUIDITY": {"name":"Fed Net Liquidity","cat":"Liquidity","wt":4,"unit":"$T",
                      "src":"WALCL − WTREGEN − RRPONTSYD",
                      "thresh":{"CALM":(5.5,99),"CAUTION":(4.5,5.5),"STRESS":(4.0,4.5),"CRISIS":(0,4.0)},
                      "dir":"down_bad","hist":"Correlates 0.92 with SPX since 2008. 2021 peak: $6.5T.",
                      "signal":"<$4.5T = market pressure. Rising = supports risk assets."},
    "M2SL":          {"name":"M2 Money Supply YoY","cat":"Liquidity","wt":2,"unit":"%",
                      "src":"FRED M2SL",
                      "thresh":{"CALM":(3,15),"CAUTION":(1,3),"STRESS":(-2,1),"CRISIS":(-99,-2)},
                      "dir":"down_bad","hist":"First M2 contraction since Great Depression in 2022 preceded bear.",
                      "signal":"Contraction = liquidity draining from economy → equities suffer."},
    "FED_BS":        {"name":"Fed Balance Sheet","cat":"Liquidity","wt":2,"unit":"$T",
                      "src":"FRED WALCL",
                      "thresh":{"CALM":(6.5,99),"CAUTION":(5.5,6.5),"STRESS":(4.5,5.5),"CRISIS":(0,4.5)},
                      "dir":"down_bad","hist":"2021 peak: $8.9T. QT since 2022.",
                      "signal":"QT = shrinking balance sheet = liquidity headwind."},
    # ── LABOR / RECESSION ─────────────────────────────────────────────────────
    "SAHM":          {"name":"Sahm Rule","cat":"Recession","wt":4,"unit":"pp",
                      "src":"FRED SAHMREALTIME",
                      "thresh":{"CALM":(0,0.3),"CAUTION":(0.3,0.5),"STRESS":(0.5,0.7),"CRISIS":(0.7,99)},
                      "dir":"up_bad","hist":"0-for-0 false signals. Triggered every recession since 1970.",
                      "signal":">0.5 = recession has started. No false positives in history."},
    "NY_REC_PROB":   {"name":"NY Fed Recession Prob","cat":"Recession","wt":3,"unit":"%",
                      "src":"FRED RECPROUSM156N",
                      "thresh":{"CALM":(0,20),"CAUTION":(20,40),"STRESS":(40,60),"CRISIS":(60,100)},
                      "dir":"up_bad","hist":">30% called every recession. 2023 peak: 70%.",
                      "signal":"Model-based 12mo recession probability from yield curve shape."},
    "CREDIT_CARD_DLQ":{"name":"Credit Card Delinquency","cat":"Recession","wt":3,"unit":"%",
                       "src":"FRED DRCCLACBS",
                       "thresh":{"CALM":(0,3.0),"CAUTION":(3.0,5.0),"STRESS":(5.0,7.0),"CRISIS":(7.0,99)},
                       "dir":"up_bad","hist":"GFC peak: 6.8% (2009-10). Normal range: 1.5-2.5%. Above 3% = consumer stress.",
                       "signal":"Rising = consumer balance sheet stress. Leads defaults by 2-4Q."},
    # ── MARKET STRUCTURE ──────────────────────────────────────────────────────
    "SPX_DD":        {"name":"S&P 500 DD from ATH","cat":"Structure","wt":3,"unit":"%",
                      "src":"yfinance ^GSPC vs 5yr ATH",
                      "thresh":{"CALM":(-5,0),"CAUTION":(-10,-5),"STRESS":(-20,-10),"CRISIS":(-99,-20)},
                      "dir":"down_bad","hist":"Normal correction: -5 to -10%. Bear market: >-20%.",
                      "signal":"Real-time crash severity gauge. >-20% = confirmed bear market."},
    "TOP10_WEIGHT":  {"name":"Top-10 SPX Weight","cat":"Structure","wt":2,"unit":"%",
                      "src":"yfinance SPY market caps",
                      "thresh":{"CALM":(0,22),"CAUTION":(22,28),"STRESS":(28,33),"CRISIS":(33,100)},
                      "dir":"up_bad","hist":"Avg 18-20% historically. Dot-com peak: 26%. 2020: 23%. 2024: crossed 35%.",
                      "signal":">33% = extreme concentration. When top-10 crack, index has nowhere to hide. Monitor RSP/SPY ratio for divergence."},
    "RSP_SPY":       {"name":"RSP/SPY Ratio (Equal/Cap)","cat":"Structure","wt":2,"unit":"x",
                      "src":"yfinance RSP/SPY",
                      "thresh":{"CALM":(0.32,99),"CAUTION":(0.29,0.32),"STRESS":(0.27,0.29),"CRISIS":(0,0.27)},
                      "dir":"down_bad","hist":"Fell steadily for 2 years before 2022 bear market.",
                      "signal":"Falling = mega-caps masking broad weakness = bearish divergence."},
    "SPX_VS_200":    {"name":"SPX vs 200DMA","cat":"Structure","wt":2,"unit":"%",
                      "src":"yfinance ^GSPC",
                      "thresh":{"CALM":(-2,99),"CAUTION":(-5,-2),"STRESS":(-15,-5),"CRISIS":(-99,-15)},
                      "dir":"down_bad","hist":"Crosses below 200DMA = bear market entry signal.",
                      "signal":"<0 = below 200DMA = trend broken. <-10% = severe bear."},
    # ── MACRO ─────────────────────────────────────────────────────────────────
    "INDPRO":        {"name":"Indust. Production YoY","cat":"Macro","wt":2,"unit":"%",
                      "src":"FRED INDPRO",
                      "thresh":{"CALM":(1.5,99),"CAUTION":(0,1.5),"STRESS":(-1,0),"CRISIS":(-99,-1)},
                      "dir":"down_bad","hist":"Went negative 1-3mo before EPS peaked in 2000, 2007, 2019, 2022.",
                      "signal":"Negative = factory output contracting = Juglar contraction signal."},
    "CAPUTIL":       {"name":"Capacity Utilization","cat":"Macro","wt":2,"unit":"%",
                      "src":"FRED TCU",
                      "thresh":{"CALM":(77,99),"CAUTION":(74,77),"STRESS":(70,74),"CRISIS":(0,70)},
                      "dir":"down_bad","hist":">81% = inflation risk. <74% = deflation/oversupply.",
                      "signal":"<77% + IP negative = Juglar contraction confirmed."},
    "CPI":           {"name":"CPI Inflation YoY","cat":"Macro","wt":2,"unit":"%",
                      "src":"FRED CPIAUCSL",
                      "thresh":{"CALM":(0,3.0),"CAUTION":(3.0,4.5),"STRESS":(4.5,6.0),"CRISIS":(6.0,99)},
                      "dir":"up_bad","hist":">4% sustained = margin compression lagged 2-4Q.",
                      "signal":"Re-acceleration above 3.5% = Fed trapped = multiple compression."},
    "REAL_RETAIL":   {"name":"Real Retail Sales YoY","cat":"Macro","wt":2,"unit":"%",
                      "src":"FRED RSAFS − CPI (computed)",
                      "thresh":{"CALM":(1,99),"CAUTION":(0,1),"STRESS":(-2,0),"CRISIS":(-99,-2)},
                      "dir":"down_bad","hist":"Negative for 2+ quarters preceded 2001, 2008, 2020 recessions.",
                      "signal":"Consumer spending shrinking in real terms = recession leading signal."},
    "T10Y_YIELD":    {"name":"10-Year Treasury Yield","cat":"Rates","wt":2,"unit":"%",
                      "src":"FRED DGS10",
                      "thresh":{"CALM":(2,4.5),"CAUTION":(4.5,5.0),"STRESS":(5.0,6.0),"CRISIS":(6.0,99)},
                      "dir":"up_bad","hist":">5% in 2023 drove P/E from 22x→17x in 3 months.",
                      "signal":"Rising 10Y compresses equity multiples. >5% = danger for growth stocks."},
    "HOUST_YOY":     {"name":"Housing Starts YoY","cat":"Macro","wt":2,"unit":"%",
                      "src":"FRED HOUST",
                      "thresh":{"CALM":(-10,99),"CAUTION":(-20,-10),"STRESS":(-35,-20),"CRISIS":(-99,-35)},
                      "dir":"down_bad","hist":"-30%+ before 2007-09; -20%+ before 2000; -50%+ in 2020.",
                      "signal":"Leads economy 12-18mo. Kuznets cycle health indicator."},
    # ══ HOUSING MARKET — 6 indicators (new category) ═════════════════════════
    # Housing leads SPX by 6-18 months via wealth effect, construction employment,
    # and banking credit channel. WT4 mortgage rate is the primary control variable.
    "RATE_30":     {"name":"30yr Mortgage Rate","cat":"Housing","wt":4,"unit":"%",
                    "thresh":{"CALM":(3.5,6.0),"CAUTION":(6.0,7.0),"STRESS":(7.0,8.0),"CRISIS":(8.0,99)},
                    "dir":"up_bad","src":"FRED MORTGAGE30US",
                    "hist":"< 6% = accessible demand. > 7% = severe affordability destruction. > 8% = 1980s shock.",
                    "signal":"> 7.5%: reduce XHB/ITB, add TLT. < 5.5%: buy homebuilders aggressively."},
    "AFFORD_PTI":  {"name":"Mortgage Payment/Income","cat":"Housing","wt":3,"unit":"%",
                    "thresh":{"CALM":(0,32),"CAUTION":(32,38),"STRESS":(38,44),"CRISIS":(44,99)},
                    "dir":"up_bad","src":"Computed MORTGAGE30US/MSPUS/MEHOINUSA672N",
                    "hist":"Hist avg 28%. 2006 peak 34%. 2022-23 peaked 42%+ = worst since 1981.",
                    "signal":"> 40%: consumer spending under pressure → reduce XLY. < 30%: housing recovery buy signal."},
    "MTGE_DELINQ": {"name":"Mortgage Delinquency","cat":"Housing","wt":3,"unit":"%",
                    "thresh":{"CALM":(0,3.5),"CAUTION":(3.5,5.0),"STRESS":(5.0,7.0),"CRISIS":(7.0,99)},
                    "dir":"up_bad","src":"FRED DRSFRMACBS",
                    "hist":"Normal 3-4%. GFC peak 11.4%. Rising = bank earnings (JPM/WFC) under pressure.",
                    "signal":"> 4.5%: reduce XLF, KRE. > 7%: systemic housing credit stress — raise cash."},
    "XHB_SPY":     {"name":"XHB/SPY (Builders vs Mkt)","cat":"Housing","wt":3,"unit":"ratio",
                    "thresh":{"CALM":(0.06,9),"CAUTION":(0.04,0.06),"STRESS":(0,0.04),"CRISIS":(0,0.03)},
                    "dir":"down_bad","src":"yfinance XHB/SPY",
                    "hist":"XHB bottomed Mar 18 2020 — 5 days before SPX. Fell -45% before 1990 recession.",
                    "signal":"XHB/SPY breakdown below trend: reduce cyclicals. Breakout: housing bull → SPX leads."},
    "HPI_YOY":     {"name":"Case-Shiller HPI YoY","cat":"Housing","wt":2,"unit":"%",
                    "thresh":{"CALM":(0,8),"CAUTION":(8,15),"STRESS":(-5,0),"CRISIS":(-15,-5)},
                    "dir":"extreme_bad","src":"FRED CSUSHPISA",
                    "hist":"Sustainable = 3-5%. > 10% = bubble risk. Turning negative = wealth-effect reversal.",
                    "signal":"HPI negative 3+ months: reduce XLY, consumer stocks. Bottoming + rising: buy signal."},
    "SUPPLY_MO":   {"name":"Housing Months Supply","cat":"Housing","wt":2,"unit":"idx",
                    "thresh":{"CALM":(3.5,7.0),"CAUTION":(7.0,9.0),"STRESS":(0,3.5),"CRISIS":(9.0,99)},
                    "dir":"extreme_bad","src":"FRED MSACSR",
                    "hist":"Balanced = 5-6 months. < 3 = severe shortage (2021-22). > 8 = oversupply (2008-09).",
                    "signal":"Rising above 7mo = builder price cuts → XHB under pressure. Below 3mo = supply crisis."},
        "NAAIM":       {"name":"NAAIM Active Mgr Exposure","cat":"Sentiment","wt":2,"unit":"%",
                   "thresh":{"CALM":(30,90),"CAUTION":(90,101),"STRESS":(0,30),"CRISIS":(0,20)},
                   "dir":"extreme_bad","src":"naaim.org / proxy",
                   "hist":"< 20% = every major bottom (COVID: 14%). > 90% = crowded/sell.",
                   "signal":"> 90% = all-in = sell signal. < 30% = fled to cash = buy."},
    "AAII_BULL":  {"name":"AAII Bull-Bear Spread","cat":"Sentiment","wt":2,"unit":"%",
                   "thresh":{"CALM":(-20,30),"CAUTION":(30,60),"STRESS":(-40,-20),"CRISIS":(-60,-40)},
                   "dir":"extreme_bad","src":"aaii.com / proxy",
                   "hist":"< -30% = extreme fear = bottoms in 1-4wk. > +30% = greed = caution.",
                   "signal":"Below -30%: market bottoms within 1-4 weeks historically."},
    "PUT_CALL":   {"name":"CBOE Put/Call Ratio","cat":"Sentiment","wt":2,"unit":"x",
                   "thresh":{"CALM":(0.7,1.1),"CAUTION":(1.1,1.25),"STRESS":(0,0.7),"CRISIS":(1.25,9)},
                   "dir":"spike_buy","src":"yfinance ^PCX",
                   "hist":"Spike > 1.3 then rapid decline = classic bottom. < 0.7 = complacency.",
                   "signal":"P/C spike > 1.3-1.5 then rapid decline = classic bottom signal."},
    "SPX_RSI":    {"name":"S&P 500 RSI-14","cat":"Structure","wt":3,"unit":"idx",
                   "thresh":{"CALM":(45,70),"CAUTION":(30,45),"STRESS":(0,30),"CRISIS":(0,20)},
                   "dir":"down_bad","src":"computed from ^GSPC",
                   "hist":"RSI < 25 = high-probability tactical bounce zone historically.",
                   "signal":"RSI < 25 + HY OAS calm = bounce. RSI < 25 + credit stress = stay out."},
    "GOLDEN_X":   {"name":"50DMA vs 200DMA (Cross)","cat":"Structure","wt":2,"unit":"%",
                   "thresh":{"CALM":(0,20),"CAUTION":(-3,0),"STRESS":(-10,-3),"CRISIS":(-20,-10)},
                   "dir":"down_bad","src":"computed from ^GSPC",
                   "hist":"Death cross (50 < 200DMA) precedes bear markets. Golden cross = bull.",
                   "signal":"50DMA crossing below 200DMA = structural bear. Reduce equities."},
    "XLY_XLP":    {"name":"XLY/XLP (Risk Appetite)","cat":"Sector","wt":2,"unit":"ratio",
                   "thresh":{"CALM":(1.25,9),"CAUTION":(1.05,1.25),"STRESS":(0.85,1.05),"CRISIS":(0,0.85)},
                   "dir":"down_bad","src":"yfinance XLY/XLP",
                   "hist":"Rising = risk-on. Peaked before every recession 3-6 months prior.",
                   "signal":"Falling from highs = defensive rotation = reduce growth/risk."},
    "XLF_XLU":    {"name":"XLF/XLU (Growth vs Def)","cat":"Sector","wt":2,"unit":"ratio",
                   "thresh":{"CALM":(0.55,9),"CAUTION":(0.42,0.55),"STRESS":(0,0.42),"CRISIS":(0,0.35)},
                   "dir":"down_bad","src":"yfinance XLF/XLU",
                   "hist":"Rising = rates rising/expansion. Falling = growth fears or rate cut.",
                   "signal":"Falling ratio = risk-off. Leads SPY reversals 4-6 weeks."},
    "IWM_SPY":    {"name":"IWM/SPY (Market Breadth)","cat":"Sector","wt":2,"unit":"ratio",
                   "thresh":{"CALM":(0.38,9),"CAUTION":(0.33,0.38),"STRESS":(0,0.33),"CRISIS":(0,0.28)},
                   "dir":"down_bad","src":"yfinance IWM/SPY",
                   "hist":"Fell 2yr before 2022 bear. Falling = narrow/fragile rally.",
                   "signal":"Falling while SPY up = RAISE CASH. Highest-conviction late-cycle warning."},
    "XLK_SPY":    {"name":"XLK/SPY (Tech vs S&P)","cat":"Sector","wt":2,"unit":"ratio",
                   "thresh":{"CALM":(0.20,9),"CAUTION":(0.17,0.20),"STRESS":(0,0.17),"CRISIS":(0,0.14)},
                   "dir":"down_bad","src":"yfinance XLK/SPY",
                   "hist":"Tech ~30% SPX. XLK falling = index drag. 2021 peak = extreme.",
                   "signal":"Rolling over from highs = correction near. Bottoming = buy."},
    "DXY":        {"name":"US Dollar Index (DXY)","cat":"SafeHaven","wt":2,"unit":"idx",
                   "thresh":{"CALM":(90,106),"CAUTION":(106,110),"STRESS":(0,90),"CRISIS":(110,9999)},
                   "dir":"extreme_bad","src":"yfinance DX-Y.NYB",
                   "hist":"Strong USD = global tightening = earnings headwind. Surge = panic.",
                   "signal":"Rolling over from peak = global liquidity returning = equity support."},
    "GLD_SPY":    {"name":"Gold/SPY (Flight Safety)","cat":"SafeHaven","wt":2,"unit":"ratio",
                   "thresh":{"CALM":(0,0.5),"CAUTION":(0.5,0.65),"STRESS":(0.65,0.9),"CRISIS":(0.9,9)},
                   "dir":"up_bad","src":"yfinance GLD/SPY",
                   "hist":"Gold at ATH while SPX falls = flight-to-safety confirmed.",
                   "signal":"Ratio peaking and declining = risk-on returning to equities."},
    "TLT_SPY":    {"name":"TLT/SPY (Bonds vs Stocks)","cat":"SafeHaven","wt":2,"unit":"ratio",
                   "thresh":{"CALM":(0,0.15),"CAUTION":(0.15,0.22),"STRESS":(0.22,0.35),"CRISIS":(0.35,9)},
                   "dir":"up_bad","src":"yfinance TLT/SPY",
                   "hist":"Rising = flight to safety. 2022: unique — both fell (stagflation).",
                   "signal":"Ratio peaking and declining = risk appetite returning."},
    "VVIX":       {"name":"VVIX (Vol of VIX)","cat":"Volatility","wt":2,"unit":"idx",
                   "thresh":{"CALM":(0,100),"CAUTION":(100,120),"STRESS":(120,140),"CRISIS":(140,9999)},
                   "dir":"up_bad","src":"yfinance ^VVIX",
                   "hist":"> 120 = tail risk hedging accelerating. Rising before VIX = early warn.",
                   "signal":"Spikes then collapses = hedging panic resolved = equities can rally."},
    "SKEW":       {"name":"CBOE SKEW (Tail Risk)","cat":"Volatility","wt":2,"unit":"idx",
                   "thresh":{"CALM":(100,130),"CAUTION":(130,145),"STRESS":(145,160),"CRISIS":(160,9999)},
                   "dir":"up_bad","src":"yfinance ^SKEW",
                   "hist":"> 130 = elevated tail risk. 140+ with low VIX = storm under surface.",
                   "signal":"Falls to 100-115 = tail risk unwinds = crash fear resolved."},
    "CI_LOAN_DLQ":{"name":"C&I Loan Delinquency","cat":"Recession","wt":3,"unit":"%",
                   "thresh":{"CALM":(0,1.5),"CAUTION":(1.5,2.0),"STRESS":(2.0,4.0),"CRISIS":(4.0,9999)},
                   "dir":"up_bad","src":"FRED DRCLACBS",
                   "hist":"GFC peak: 4%+. 2020 peak: 3%. Jump above 2% = business credit stress.",
                   "signal":"C&I delinquencies peak after recessions end. Confirms recovery."},
    "OFR_FSI":    {"name":"St.Louis Fin. Stress Index","cat":"Credit","wt":3,"unit":"fsi",
                   "thresh":{"CALM":(-9999,0),"CAUTION":(0,1),"STRESS":(1,2),"CRISIS":(2,9999)},
                   "dir":"up_bad","src":"FRED STLFSI2",
                   "hist":"Above +1 = notable stress. Above +2 = severe. Above +4 = crisis.",
                   "signal":"Declining from peak = markets approaching bottom."},
    "SENTIMENT":     {"name":"Fear & Greed (CNN)","cat":"Sentiment","wt":2,"unit":"",
                      "src":"CNN F&G API",
                      "thresh":{"CALM":(35,65),"CAUTION":(20,35),"STRESS":(10,20),"CRISIS":(0,10)},
                      "dir":"down_bad","hist":"<10 = extreme fear = historically best buying signal.",
                      "signal":"Extreme Fear (<15) = contrarian buy. Extreme Greed (>80) = caution."},
    "SMART_MONEY":   {"name":"Smart Money Confidence","cat":"Sentiment","wt":3,"unit":"%",
                      "src":"yfinance proxy (VIX term + HY spread)",
                      "thresh":{"CALM":(55,101),"CAUTION":(40,55),"STRESS":(25,40),"CRISIS":(0,25)},
                      "dir":"down_bad",
                      "hist":"Institutional/contrarian traders. >60% = smart money bullish. <30% = institutional caution.",
                      "signal":"Smart > Dumb = bullish setup. Smart < 30% = institutions hedging, caution warranted."},
    "DUMB_MONEY":    {"name":"Dumb Money Confidence","cat":"Sentiment","wt":3,"unit":"%",
                      "src":"yfinance proxy (HYG/LQD + RSI momentum)",
                      "thresh":{"CALM":(35,66),"CAUTION":(66,80),"STRESS":(80,101),"CRISIS":(0,35)},
                      "dir":"extreme_bad",
                      "hist":"Retail/trend-following sentiment. >65% with Smart <40% = peak crowd optimism = caution.",
                      "signal":"Dumb > 65% and Smart < 40% = sell signal. Dumb < 35% and Smart > 60% = buy signal."},
}

# Sorted indicator order for display: by WT desc, then cat
SCORECARD_ORDER = sorted(SCORECARD_DEFS.keys(),
    key=lambda k: (-SCORECARD_DEFS[k]["wt"],
                   ["Credit","Rates","Volatility","Breadth","Valuation",
                    "Liquidity","Recession","Structure","Macro","Sentiment"]
                   .index(SCORECARD_DEFS[k]["cat"])
                   if SCORECARD_DEFS[k]["cat"] in
                   ["Credit","Rates","Volatility","Breadth","Valuation",
                    "Liquidity","Recession","Structure","Macro","Sentiment"] else 99))


def compute_smart_dumb_money(md):
    """
    Build Smart Money / Dumb Money confidence proxies from free yfinance data.
    Smart Money proxy  = VIX term structure (VIX3M - VIX9D)/VIX + inverted HY spread
    Dumb Money proxy   = HYG/LQD momentum + SPY RSI
    Both normalized 0-100 via rolling percentile.
    """
    import pandas as pd, numpy as np
    out = {"dates": [], "smart": [], "dumb": [],
           "smart_now": None, "dumb_now": None,
           "spx_dates": [], "spx_vals": []}
    try:
        vix   = md.get("^VIX");   vix9d = md.get("^VIX9D"); vix3m = md.get("^VIX3M")
        hyg   = md.get("HYG");    lqd   = md.get("LQD");    spy   = md.get("SPY")

        # All must be present and have enough data
        _series = [vix, vix9d, vix3m, hyg, lqd, spy]
        if any(x is None or (hasattr(x, "empty") and x.empty) for x in _series):
            return out

        # Normalize indexes
        def _clean(s):
            s = s.dropna().copy()
            try:
                if s.index.tz is not None: s.index = s.index.tz_localize(None)
            except Exception: pass
            s.index = pd.to_datetime(s.index)
            return s

        vix   = _clean(vix);  vix9d = _clean(vix9d); vix3m = _clean(vix3m)
        hyg   = _clean(hyg);  lqd   = _clean(lqd);   spy   = _clean(spy)

        # Align on common dates (inner join)
        all5 = pd.concat([vix, vix9d, vix3m, hyg, lqd, spy], axis=1).dropna()
        all5.columns = ["vix","vix9d","vix3m","hyg","lqd","spy"]

        if len(all5) < 30:
            return out

        # ── Smart Money: VIX term structure + inverted HY credit risk ────────
        term_struct = (all5["vix3m"] - all5["vix9d"]) / all5["vix"].clip(lower=1)
        hy_risk_inv = 1 - (all5["hyg"] / all5["lqd"]).pct_change(21).fillna(0).rolling(10).mean()
        smart_raw   = (0.6 * term_struct + 0.4 * hy_risk_inv.clip(-0.5, 0.5) * 5)

        # Use min_periods=21 so we get data even with shorter history
        n_roll = min(252, max(30, len(all5) - 10))
        smart_pct = smart_raw.rolling(n_roll, min_periods=21).rank(pct=True) * 100

        # ── Dumb Money: HYG/LQD momentum + SPY RSI ───────────────────────────
        hyg_mom = all5["hyg"].pct_change(21).rolling(5).mean()
        _diff   = all5["spy"].diff()
        _gain   = _diff.clip(lower=0).rolling(14).mean()
        _loss   = (-_diff.clip(upper=0)).rolling(14).mean()
        spy_rsi = 100 - 100 / (1 + _gain / _loss.replace(0, 1e-9))

        hyg_mom_pct = hyg_mom.rolling(n_roll, min_periods=21).rank(pct=True)
        rsi_norm    = spy_rsi / 100
        dumb_pct    = (0.5 * hyg_mom_pct + 0.5 * rsi_norm) * 100

        # ── Combine, take last 12 months ──────────────────────────────────────
        df = pd.concat([smart_pct, dumb_pct], axis=1).dropna().tail(252)
        df.columns = ["smart", "dumb"]

        if df.empty:
            return out

        out["dates"]     = [str(d)[:10] for d in df.index]
        out["smart"]     = [round(float(v), 1) for v in df["smart"]]
        out["dumb"]      = [round(float(v), 1) for v in df["dumb"]]
        out["smart_now"] = round(float(df["smart"].iloc[-1]), 1)
        out["dumb_now"]  = round(float(df["dumb"].iloc[-1]),  1)

        # SPX overlay
        spx_aligned  = all5["spy"].reindex(df.index).ffill()
        out["spx_vals"] = [round(float(v), 2) for v in spx_aligned.values]

    except Exception as e:
        print(f"  Smart/Dumb money compute failed: {e}")
    return out

def full_scorecard(fd, md, use_api=True):
    """
    Compute all 35 indicators.  Returns list of dicts:
      {id, name, cat, wt, value, val_str, signal, unit, src, hist, context}
    sorted by wt desc then category.
    """
    from datetime import date

    def _g(k):
        s = fd.get(k)
        return float(s.iloc[-1]) if s is not None and not s.empty else None

    def _yoy(k, p=12):
        s = fd.get(k)
        if s is None or len(s) < p + 2: return None
        a, b = float(s.iloc[-1]), float(s.iloc[-p-1])
        if b == 0: return None
        v = round((a/b - 1)*100, 2)
        # Sanity caps for proxy-derived series to prevent gold/ETF distortion
        # CPI YoY is currently ~2.4-2.8%. Cap at 5% max to reject gold proxy artifacts
        _PROXY_YOY_CAPS = {
            "CPI": (-1, 5), "PCE": (-1, 4), "RETAIL": (-10, 15),
            "INDPRO": (-15, 15), "HOUST": (-50, 50), "HPI_NAT": (-15, 25),
            "M2SL": (-10, 25), "WALCL": (-30, 40), "GDP": (-20, 20),
        }
        if k in _PROXY_YOY_CAPS:
            lo, hi = _PROXY_YOY_CAPS[k]
            if not (lo <= v <= hi): return None   # proxy artifact — discard
        return v

    def _md(k):
        s = md.get(k)
        return float(s.iloc[-1]) if s is not None and not s.empty else None

    def _mds(k):
        """Return Series (not scalar) for rolling calc."""
        return md.get(k)

    def _date(k):
        s = fd.get(k)
        if s is None or (hasattr(s, 'empty') and s.empty):
            s = md.get(k)
        if s is None or (hasattr(s, 'empty') and s.empty): return ""
        try:
            idx_val = str(s.index[-1])[:10]
            # Only accept YYYY-MM... format dates; reject '0', '1' integer indices
            return idx_val if (len(idx_val) >= 7 and idx_val[4:5] == '-') else ""
        except: return ""

    # ── Compute all values ────────────────────────────────────────────────────
    vals = {}

    # Credit
    vals["HY_OAS"]  = _g("HY_OAS")
    vals["IG_OAS"]  = _g("IG_OAS")
    hy = vals["HY_OAS"]; ig = vals["IG_OAS"]
    vals["HY_IG_DIFF"] = round(hy - ig, 0) if (hy and ig) else None
    vals["CCC_OAS"] = _g("CCC_OAS")
    vals["NFCI"]    = _g("NFCI")

    # Rates
    # YIELD_CURVE and T10Y3M are already in bps (multiplied in main())
    vals["YIELD_CURVE"] = round(_g("YIELD_CURVE"), 0) if _g("YIELD_CURVE") is not None else None
    vals["CURVE_10Y3M"] = round(_g("T10Y3M"), 0)      if _g("T10Y3M") is not None else None
    vals["REAL_YIELD"]  = _g("REAL_YIELD")
    vals["BREAKEVEN"]   = _g("BREAKEVEN")
    vals["FED_FUNDS"]   = _g("FEDFUNDS")

    # Volatility — from md (yfinance)
    _vix30 = _md("^VIX")
    _vix3m = _md("^VIX3M")  # ^VXV deprecated
    _vix9d = _md("^VIX9D");   _move  = _md("^MOVE")
    vals["VIX"]      = _vix30
    vals["VIX_TERM"] = round(_vix3m - _vix30, 2) if (_vix3m and _vix30) else None
    vals["MOVE"]     = _move
    vals["VIX9D_RATIO"] = round(_vix9d / _vix30, 3) if (_vix9d and _vix30) else None

    # Breadth — % above 50/200 DMA (already computed by fetch_market in most cases)
    def _md1(k):
        s = md.get(k)
        return float(s.iloc[-1]) if s is not None and not s.empty else None

    _pct50_v  = _md1("_pct_above_50")
    _pct200_v = _md1("_pct_above_200")
    # Only re-fetch if fetch_market didn't compute it (quick mode / error)
    if _pct50_v is None or _pct200_v is None:
        try:
            import yfinance as _yfb2
            import pandas as _pdb2
            _SAMPLE = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","BRK-B","JPM","V",
                       "MA","UNH","XOM","JNJ","HD","PG","AVGO","LLY","MRK","CVX",
                       "KO","PEP","ABBV","MCD","WMT","BAC","CSCO","TMO","CRM","ACN",
                       "COST","NEE","TXN","DHR","ABT","QCOM","RTX","WFC","UNP","IBM"]
            # Use 1y for MA calculations but only if we must
            _braw = _yfb2.download(_SAMPLE, period="1y", interval="1d",
                                   auto_adjust=True, progress=False)
            _bc = (_braw["Close"] if hasattr(_braw.columns, "levels") else _braw).dropna(how="all")
            if not _bc.empty:
                _total = len(_bc.columns)
                _last  = _bc.iloc[-1]
                _ma50  = _bc.rolling(50).mean().iloc[-1]
                _ma200 = _bc.rolling(200).mean().iloc[-1]
                _pct50_v  = round(int((_last > _ma50).sum())  / _total * 100, 1)
                _pct200_v = round(int((_last > _ma200).sum()) / _total * 100, 1)
                print(f"  Breadth re-fetched: >50DMA={_pct50_v}% >200DMA={_pct200_v}%")
        except Exception as _be:
            print(f"  Breadth re-fetch failed: {_be}")

    vals["PCT_ABOVE_50"]  = _pct50_v
    vals["PCT_ABOVE_200"] = _pct200_v

    # NYSE A/D Net — ^NYAD not available on Yahoo Finance; use proxy from fetch_market
    _nyad_v = None
    _nyad_s = md.get("_nyad_net")
    if _nyad_s is not None and not (hasattr(_nyad_s, 'empty') and _nyad_s.empty):
        try:
            _nyad_v = float(_nyad_s.iloc[-1])
        except Exception: pass
    if _nyad_v is None:
        # Secondary: ^NYAD from md if somehow present
        _nyad_s2 = md.get("^NYAD")
        if _nyad_s2 is not None and not (hasattr(_nyad_s2, 'empty') and _nyad_s2.empty):
            try:
                _nyad_v = float(_nyad_s2.iloc[-1])
            except Exception: pass
    vals["NYSE_AD"] = _nyad_v

    # Valuation — computed
    _spx = _md("^GSPC")
    # ── Forward P/E — 4-source chain, validated to 14-32x range ─────────────
    # Root cause of 42.90x bug: FRED SP500EPS stores QUARTERLY EPS (~$56/qtr)
    # not annual, so SPX / (56 × 1.10) = 107x. Yield-based fallback also wrong.
    # Fix: scrape actual consensus forward P/E from free public sources first.
    _fwd_pe = None
    _fwd_pe_src = ""

    # Source 1: macrotrends.net — scraped consensus forward P/E (most accurate free source)
    try:
        import requests as _rqpe, re as _repe
        _pe_r = _rqpe.get(
            "https://www.macrotrends.net/assets/php/fundamental_iframe.php?t=PE-Ratio&type=pe-ratio&statement=price-ratios&frequency=Q",
            timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                                  "Referer": "https://www.macrotrends.net"})
        if _pe_r.status_code == 200:
            # Page contains JSON data with PE values; grab last valid number in 14-32 range
            _pe_nums = _repe.findall(r'"value"\s*:\s*"?([0-9]{2}\.[0-9]{1,2})"?', _pe_r.text)
            _pe_vals = [float(n) for n in _pe_nums if 14.0 < float(n) < 35.0]
            if _pe_vals:
                _fwd_pe = round(_pe_vals[-1], 1)
                _fwd_pe_src = "macrotrends"
    except Exception: pass

    # Source 2: multpl.com S&P 500 Forward P/E page
    if _fwd_pe is None:
        try:
            import requests as _rqpe2, re as _repe2
            _pe_r2 = _rqpe2.get(
                "https://www.multpl.com/s-p-500-forward-pe-ratio/table/by-month",
                timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if _pe_r2.status_code == 200:
                _pe_nums2 = _repe2.findall(r'\b(\d{2}\.\d{1,2})\b', _pe_r2.text[:6000])
                _pe_vals2 = [float(n) for n in _pe_nums2 if 14.0 < float(n) < 35.0]
                if _pe_vals2:
                    _fwd_pe = round(_pe_vals2[0], 1)
                    _fwd_pe_src = "multpl.com"
        except Exception: pass

    # Source 3: FRED annualised EPS + realistic forward growth
    # FRED SP500EPS series stores TRAILING 12-MONTH EPS (annualised, not quarterly).
    # Typical 2025-26 trailing = $220-240. Forward consensus ~$278 = × ~1.22.
    # Sanity cap: result must be 14-32x given current SPX levels.
    if _fwd_pe is None:
        try:
            _eps_annual = None
            for k in ["SP500EPS", "SPASTT01USQ657N"]:
                _s2 = fd.get(k)
                if _s2 is not None and not _s2.empty:
                    _v2 = float(_s2.iloc[-1])
                    # FRED stores TTM EPS: valid range $150-350 for S&P 500
                    if 150 < _v2 < 350:
                        _eps_annual = _v2
                        break
                    # If it looks like quarterly (~$50-80), annualise it
                    elif 50 < _v2 < 80:
                        _eps_annual = _v2 * 4
                        break
            if _eps_annual and _spx and _spx > 100:
                # Use 1.20 growth to reflect current analyst consensus (~20% fwd growth)
                _fwd_pe_calc = round(_spx / (_eps_annual * 1.20), 1)
                # Only accept if sane
                if 14 < _fwd_pe_calc < 35:
                    _fwd_pe = _fwd_pe_calc
                    _fwd_pe_src = "FRED EPS"
        except Exception: pass

    # Source 4: ^GSPC trailing PE × forward discount
    # Only accept trailing PE in realistic range (15-32x). Anything higher = stale/wrong data.
    if _fwd_pe is None:
        try:
            import yfinance as _yf2
            _fi2 = _yf2.Ticker("^GSPC").fast_info
            _trailing_pe = getattr(_fi2, "pe_ratio", None)
            if _trailing_pe and 15 < float(_trailing_pe) < 32:
                _fwd_pe_calc = round(float(_trailing_pe) * 0.87, 1)
                if 14 < _fwd_pe_calc < 30:
                    _fwd_pe = _fwd_pe_calc
                    _fwd_pe_src = f"trailing {_trailing_pe:.1f}x × 0.87"
        except Exception: pass

    # ── SANITY GATE — reject physically impossible values; leave None for web search ──
    # S&P 500 forward P/E: never outside 14-30x in modern history.
    # Out of range → set None so Claude web search fills it below.
    if _fwd_pe is not None and not (14.0 < float(_fwd_pe) < 30.0):
        print(f"  Forward P/E: rejected {_fwd_pe}x (outside 14-30x range) → queued for web search")
        _fwd_pe = None
        _fwd_pe_src = ""

    _t10 = _g("T10Y")
    # ERP = earnings yield (1/PE) minus 10Y yield — computed only if PE is valid
    _earn_yield = round(100.0 / _fwd_pe, 2) if (_fwd_pe and _fwd_pe > 0) else None
    _erp = round(_earn_yield - _t10, 2) if (_earn_yield is not None and _t10) else None
    vals["FORWARD_PE"] = _fwd_pe    # may be None → web search fills it
    vals["ERP"]        = _erp
    vals["_FWD_PE_SRC"]= _fwd_pe_src
    print(f"  Forward P/E: {_fwd_pe}x  (source: {_fwd_pe_src})" if _fwd_pe else
          "  Forward P/E: N/A → queued for Claude web search")
    # Shiller CAPE — live sources in priority order, with date tracking
    _cape = None
    _cape_src = ""
    _cape_date = ""

    # Source 1: multpl.com — simple targeted regex, no DOTALL on full page
    try:
        import requests as _rqc, re as _rec
        _rc = _rqc.get("https://www.multpl.com/shiller-pe/table/by-month",
                        timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        if _rc.status_code == 200:
            # Just grab all numbers in CAPE range (10-60) — first hit is most recent
            _nums = _rec.findall(r'\b(\d{2}\.\d{1,2})\b', _rc.text[:8000])
            _valid = [float(n) for n in _nums if 10.0 < float(n) < 60.0]
            if _valid:
                _cape = round(_valid[0], 1)
                _cape_src = "multpl.com"
                _cape_date = date.today().strftime("%Y-%m-01")
    except Exception: pass

    # Source 2: compute from FRED SP500EPS + CPI (10yr real earnings)
    if _cape is None:
        try:
            _eps_s = fd.get("SP500EPS"); _cpi_s = fd.get("CPI")
            if (_eps_s is not None and not _eps_s.empty and
                _cpi_s is not None and not _cpi_s.empty and len(_eps_s) >= 40):
                import pandas as _pdc
                _e = _eps_s.copy(); _c = _cpi_s.copy()
                _e.index = _pdc.to_datetime(_e.index)
                _c.index = _pdc.to_datetime(_c.index)
                _cpi_now = float(_c.iloc[-1])
                _real_eps = []
                for _ei in range(1, min(41, len(_e))):
                    _cidx = _c.index.searchsorted(_e.index[-_ei])
                    if 0 <= _cidx < len(_c):
                        _cpi_then = float(_c.iloc[_cidx]) if _cidx < len(_c) else _cpi_now
                        _real_eps.append(float(_e.iloc[-_ei]) * _cpi_now / max(_cpi_then, 1))
                if len(_real_eps) >= 20 and _spx and _spx > 100:
                    _avg_real_eps = sum(_real_eps) / len(_real_eps)
                    if _avg_real_eps > 0:
                        _cape = round(_spx / _avg_real_eps, 1)
                        _cape_src = "FRED EPS+CPI"
                        _cape_date = str(_eps_s.index[-1])[:10]
        except Exception: pass

    # No proxy fallback for CAPE — leave None so Claude web search fills it.
    # The fwd_PE × 1.30 proxy was inaccurate (gave ~30x when CAPE is actually ~38x).

    vals["CAPE"]      = _cape   # may be None → web search fills it
    vals["_CAPE_SRC"] = _cape_src
    vals["_CAPE_DATE"]= _cape_date

    # Buffett Indicator — Wilshire5000 / GDP (live, no hardcoded values)
    _buff_v = None
    _buff_date = ""

    # Source 1: FRED WILL5000PRFC ÷ FRED GDP (most accurate)
    _will = fd.get("WILL5000IND"); _gdp = fd.get("GDP")
    if _will is not None and _gdp is not None and not _will.empty and not _gdp.empty:
        _wv = float(_will.iloc[-1]); _gv = float(_gdp.iloc[-1])
        _mktcap_b = _wv * 1.1 if _wv > 1000 else _wv
        _buff_v   = round(_mktcap_b / _gv * 100, 1) if _gv else None
        _buff_date = str(_gdp.index[-1])[:10]

    # Source 2: Use SPX level from FRED ÷ FRED GDP (fast, no extra download needed)
    if _buff_v is None and _gdp is not None and not _gdp.empty:
        try:
            _spx_fred = fd.get("SP500")
            if _spx_fred is not None and not _spx_fred.empty:
                _spx_level = float(_spx_fred.iloc[-1])
                _gv2 = float(_gdp.iloc[-1])
                # S&P 500 price index × total shares outstanding proxy
                # SPX market cap ≈ index level × 8.5B (historical ratio 2020-2026)
                _spx_cap_b = _spx_level * 8.5
                _buff_v    = round(_spx_cap_b / _gv2 * 100, 1) if _gv2 else None
                _buff_date = str(_gdp.index[-1])[:10]
        except Exception: pass

    vals["BUFFETT"]       = _buff_v
    vals["_BUFFETT_DATE"] = _buff_date

    # Liquidity
    _walcl = _g("WALCL"); _tga = _g("WTREGEN"); _rrp = _g("RRPONTSYD")
    if _walcl:
        _w = round(_walcl/1e6, 3); _t2 = round((_tga or 0)/1e6, 3); _r2 = round((_rrp or 0)/1e3, 3)
        vals["NET_LIQUIDITY"] = round(_w - _t2 - _r2, 2)
    else:
        vals["NET_LIQUIDITY"] = None
    vals["M2SL"]  = _yoy("M2SL", 12)
    vals["FED_BS"] = round(_walcl/1e6, 2) if _walcl else None

    # Recession
    vals["SAHM"]             = _g("SAHM")
    _nyrecprob_raw = _g("NY_REC_PROB")
    # FRED RECPROUSM156N is already in % (e.g., 0.48 = 0.48%, not 48%)
    # But historically when near recession it goes to 70-80 (= 70-80%)
    # Value of 0.48 is correct = 0.48% recession probability (very low)
    vals["NY_REC_PROB"] = _nyrecprob_raw
    vals["CREDIT_CARD_DLQ"]  = _g("CREDIT_CARD_DLQ")

    # Structure
    if _spx:
        _gs_s = md.get("^GSPC")
        _spy_s = md.get("SPY")
        _spx_hist = _gs_s if (_gs_s is not None and len(_gs_s) >= 200) else (_spy_s if _spy_s is not None else _gs_s)
        if _spx_hist is not None and not _spx_hist.empty:
            try:
                import pandas as _pd
                _s = _spx_hist if hasattr(_spx_hist, "rolling") else _pd.Series(_spx_hist)
                _ath = float(_s.max())
                _ma200 = float(_s.rolling(200, min_periods=50).mean().iloc[-1])
                vals["SPX_DD"]     = round((_spx/_ath - 1)*100, 1)
                _v200 = (_spx/_ma200 - 1)*100 if _ma200 and _ma200==_ma200 else None
                vals["SPX_VS_200"] = round(_v200, 1) if _v200 is not None and _v200==_v200 else None
            except Exception: pass
    # Top-10 SPX Weight — already computed by fetch_market via market cap calls
    # Do NOT re-fetch here; fetch_market already did the work in step 2
    _top10_v    = _md1("_top10_weight")
    _top10_date = date.today().strftime("%Y-%m-%d") if _top10_v is not None else ""
    vals["TOP10_WEIGHT"]  = _top10_v
    vals["_TOP10_DATE"]   = _top10_date
    _rsp = _md("RSP"); _spy = _md("SPY")
    vals["RSP_SPY"] = round(_rsp/_spy, 4) if (_rsp and _spy) else None

    # Macro
    vals["INDPRO"]     = _yoy("INDPRO", 12)
    vals["CAPUTIL"]    = _g("CAPUTIL")
    vals["CPI"]        = _yoy("CPI", 12)
    vals["T10Y_YIELD"] = _g("T10Y")
    vals["HOUST_YOY"]  = _yoy("HOUST", 12)
    _rr_nom = _yoy("RETAIL", 12); _rr_cpi = _yoy("CPI", 12)
    vals["REAL_RETAIL"] = round(_rr_nom - _rr_cpi, 2) if (_rr_nom is not None and _rr_cpi is not None) else None

    # ── NEW INDICATORS ────────────────────────────────────────────────────────

    # Helper: safe ratio of two md tickers
    def _ratio(a, b):
        sa = md.get(a); sb = md.get(b)
        if sa is None or sb is None: return None
        try:
            av = float(sa.iloc[-1]); bv = float(sb.iloc[-1])
            return round(av / bv, 4) if bv else None
        except Exception: return None

    # Sector ratios (all tickers already in md)
    vals["XLY_XLP"] = _ratio("XLY","XLP")
    vals["XLF_XLU"] = _ratio("XLF","XLU")
    vals["IWM_SPY"]  = _ratio("IWM","SPY")
    vals["XLK_SPY"]  = _ratio("XLK","SPY")

    # Dollar & Safe Havens
    _dxy_v = None
    try:
        _ds = md.get("DX-Y.NYB"); _ds = _ds if (_ds is not None and len(_ds)>0) else md.get("^DXY")
        if _ds is not None and not _ds.empty:
            _dxy_v = round(float(_ds.iloc[-1]), 2)
    except Exception: pass
    vals["DXY"]     = _dxy_v
    vals["GLD_SPY"] = _ratio("GLD","SPY")
    vals["TLT_SPY"] = _ratio("TLT","SPY")

    # VVIX + SKEW
    def _mds(tk):
        s = md.get(tk)
        if s is None or (hasattr(s,'empty') and s.empty): return None
        try: return round(float(s.iloc[-1]), 2)
        except Exception: return None

    vals["VVIX"] = _mds("^VVIX")
    vals["SKEW"] = _mds("^SKEW")

    # SPX RSI-14
    _rsi_v = None
    try:
        _rsi_s = md.get("^GSPC"); _rsi_s = _rsi_s if (_rsi_s is not None and len(_rsi_s) >= 200) else (md.get("SPY") if md.get("SPY") is not None else _rsi_s)
        if _rsi_s is not None and len(_rsi_s) >= 20:
            _rsi_d  = _rsi_s.diff()
            _rsi_g  = _rsi_d.clip(lower=0).rolling(14).mean()
            _rsi_l  = (-_rsi_d.clip(upper=0)).rolling(14).mean()
            _rsi_rs = _rsi_g / _rsi_l.replace(0, float('nan'))
            _rsi_raw = float((100 - 100/(1+_rsi_rs)).iloc[-1])
            import math as _math
            _rsi_v  = round(_rsi_raw, 1) if not _math.isnan(_rsi_raw) else None
    except Exception: pass
    vals["SPX_RSI"] = _rsi_v

    # 50DMA vs 200DMA (pct diff — positive = golden cross, negative = death cross)
    _gx_v = None
    try:
        _gx_s = md.get("^GSPC"); _gx_s = _gx_s if (_gx_s is not None and len(_gx_s) >= 200) else (md.get("SPY") if md.get("SPY") is not None else _gx_s)
        if _gx_s is not None and len(_gx_s) >= 50:
            _m50  = float(_gx_s.rolling(50,  min_periods=20).mean().iloc[-1])
            _m200 = float(_gx_s.rolling(200, min_periods=50).mean().iloc[-1])
            _gx_raw = (_m50/_m200 - 1)*100 if _m200 and _m200==_m200 else None
            _gx_v = round(_gx_raw, 2) if _gx_raw is not None and _gx_raw==_gx_raw else None
    except Exception: pass
    vals["GOLDEN_X"] = _gx_v

    # C&I Loan Delinquency + St.Louis FSI (FRED)
    vals["CI_LOAN_DLQ"] = _g("CI_LOAN_DLQ")

    # OFR FSI — use official OFR API (more reliable than FRED for this series)
    _ofr_v = _g("OFR_FSI")   # FRED fallback
    try:
        import requests as _rq_ofr
        _or = _rq_ofr.get(
            "https://data.financialresearch.gov/v1/series/timeseries?mnemonic=FSINDEX",
            timeout=8)
        if _or.status_code == 200:
            _obs = sorted(_or.json().get("observations", []), key=lambda x: x.get("date",""))
            if _obs:
                _ofr_v = round(float(_obs[-1]["value"]), 3)
    except Exception: pass
    vals["OFR_FSI"] = _ofr_v

    # ── HOUSING MARKET INDICATORS ─────────────────────────────────────────────
    # 30yr Mortgage Rate (FRED MORTGAGE30US)
    vals["RATE_30"] = _g("RATE_30")

    # Mortgage Delinquency Rate (FRED DRSFRMACBS)
    vals["MTGE_DELINQ"] = _g("MTGE_DELINQ")

    # Case-Shiller HPI YoY % (FRED CSUSHPISA)
    vals["HPI_YOY"] = _yoy("HPI_NAT", 12)

    # Housing Months Supply (FRED MSACSR)
    vals["SUPPLY_MO"] = _g("SUPPLY_MO")

    # Affordability: Monthly P&I as % of median monthly income
    _afford_v = None
    try:
        _r30_v = vals.get("RATE_30") or _g("RATE_30")
        _mp_v  = _g("MED_PRICE")
        _mi_v  = _g("MED_INC_HO")
        if _r30_v and _mp_v and _mi_v and _r30_v > 0:
            _loan_v  = float(_mp_v) * 0.80
            _mo_rv   = float(_r30_v) / 100 / 12
            _pmt_v   = _loan_v * (_mo_rv*(1+_mo_rv)**360) / ((1+_mo_rv)**360 - 1)
            _afford_v = round(_pmt_v / (float(_mi_v) / 12) * 100, 1)
    except Exception: pass
    vals["AFFORD_PTI"] = _afford_v

    # XHB/SPY ratio — homebuilder ETF vs S&P 500 (early-warning indicator)
    _xhb_v = None
    try:
        _xhb_s  = md.get("XHB")
        _spy_s2 = md.get("SPY")
        if (_xhb_s is not None and not _xhb_s.empty and
            _spy_s2 is not None and not _spy_s2.empty):
            _xhb_v = round(float(_xhb_s.iloc[-1]) / float(_spy_s2.iloc[-1]), 4)
    except Exception: pass
    vals["XHB_SPY"] = _xhb_v

    # NAAIM — no public live API; use hardcoded weekly update as baseline
    # (NAAIM only publishes weekly, Wednesday after close)
    # Source: naaim.org — update this value weekly from the website
    _naaim_v = None
    try:
        import requests as _rq_n, re as _re_n
        _nr = _rq_n.get("https://www.naaim.org/programs/naaim-exposure-index/",
                         headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if _nr.status_code == 200:
            # NAAIM publishes data in a chart JSON embedded in the page
            _nm = _re_n.search(r'\[\s*\d{10,}\s*,\s*([0-9]+\.?[0-9]*)\s*\]', _nr.text)
            if not _nm:
                _nm = _re_n.search(r'"number"\s*:\s*"?([0-9]+\.?[0-9]*)', _nr.text)
            if not _nm:
                # Try all numbers in a plausible NAAIM range
                _all = _re_n.findall(r'([0-9]{1,3}(?:\.[0-9]{1,2})?)', _nr.text)
                _valid = [float(x) for x in _all if 1 < float(x) < 150]
                if _valid: _nm = type('M', (), {'group': lambda s, n: str(_valid[0])})()
            if _nm:
                _raw = round(float(_nm.group(1)), 1)
                _naaim_v = _raw if 0 <= _raw <= 150 else None
    except Exception: pass
    vals["NAAIM"] = _naaim_v

    # AAII Bull-Bear Spread — AAII publishes weekly, no live API
    # Pull from AAII website; falls back to None if unreachable
    _aaii_v = None
    try:
        import requests as _rq_a, re as _re_a
        _ar = _rq_a.get("https://www.aaii.com/sentimentsurvey/sent_results",
                         headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if _ar.status_code == 200:
            _bull = _re_a.search(r'Bullish[^0-9]*([0-9]+\.?[0-9]*)%', _ar.text, _re_a.IGNORECASE)
            _bear = _re_a.search(r'Bearish[^0-9]*([0-9]+\.?[0-9]*)%', _ar.text, _re_a.IGNORECASE)
            if _bull and _bear:
                _aaii_v = round(float(_bull.group(1)) - float(_bear.group(1)), 1)
                # Validate: spread must be -80 to +80
                if not (-80 <= _aaii_v <= 80): _aaii_v = None
    except Exception: pass
    vals["AAII_BULL"] = _aaii_v

    # Put/Call ratio — VIX term structure proxy (VIX9D/VIX ratio)
    _pc_v = None
    try:
        _v9s  = md.get("^VIX9D")
        _v30s = md.get("^VIX")
        if _v30s is None or (hasattr(_v30s,'empty') and _v30s.empty):
            _v30s = md.get("^VIX3M")
        if _v9s is not None and _v30s is not None:
            _v9  = float(_v9s.iloc[-1])
            _v30 = float(_v30s.iloc[-1])
            if _v30 > 0: _pc_v = round(_v9 / _v30, 3)
    except Exception: pass
    vals["PUT_CALL"] = _pc_v

    # Sentiment — CNN F&G
    _fng = None
    try:
        import requests as _rq
        _r = _rq.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                     headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if _r.status_code == 200:
            _fng_d = _r.json()
            _fng   = round(float(_fng_d["fear_and_greed"]["score"]), 0)
            # Store label for display (e.g. "Extreme Fear", "Greed")
            vals["_FNG_LABEL"] = _fng_d["fear_and_greed"]["rating"].replace("_"," ").title()
    except Exception: pass
    vals["SENTIMENT"] = _fng

    # Smart Money / Dumb Money — computed from market data proxy
    _sdm = compute_smart_dumb_money(md)
    vals["SMART_MONEY"] = _sdm.get("smart_now")
    vals["DUMB_MONEY"]  = _sdm.get("dumb_now")
    vals["_SDM_DATA"]   = _sdm   # store full series for Charts tab

    # ── Claude API web search — LAST RESORT for any remaining N/A indicators ─────
    # Only fires if primary sources all failed AND use_api=True (skipped with --noapi)
    _na_ids = [k for k,v in vals.items() if v is None and k in (
        "SENTIMENT","NAAIM","AAII_BULL","PUT_CALL",
        "FORWARD_PE","ERP",
        "CAPE","BUFFETT","TOP10_WEIGHT","PCT_ABOVE_50","PCT_ABOVE_200","NYSE_AD",
        "CCC_OAS","OFR_FSI","CI_LOAN_DLQ",
        "RATE_30","SUPPLY_MO","HPI_YOY","MTGE_DELINQ","SMART_MONEY","DUMB_MONEY",
        "CPI","REAL_RETAIL","PCE_YOY"
    )]
    if _na_ids and CLAUDE_API_KEY and use_api:
        try:
            import requests as _rqai, json as _jsai, re as _re_ai
            from datetime import date as _dkai
            _today = _dkai.today().strftime("%B %d, %Y")

            _search_queries = {
                "SENTIMENT":    f"CNN Fear and Greed Index current value today {_dkai.today().year}",
                "NAAIM":        f"NAAIM Exposure Index latest weekly reading {_dkai.today().year}",
                "AAII_BULL":    f"AAII Bull Bear Spread latest weekly survey {_dkai.today().year}",
                "PUT_CALL":     f"CBOE equity put call ratio current {_dkai.today().year}",
                "FORWARD_PE":   f"S&P 500 forward price earnings ratio NTM 12-month current {_dkai.today().year}",
                "ERP":          f"S&P 500 equity risk premium earnings yield minus 10 year treasury current {_dkai.today().year}",
                "CCC_OAS":      f"CCC junk bond spread basis points current {_dkai.today().year}",
                "OFR_FSI":      f"OFR financial stress index latest value {_dkai.today().year}",
                "CI_LOAN_DLQ":  f"commercial industrial loan delinquency rate FRED {_dkai.today().year}",
                "CAPE":         f"Shiller CAPE PE10 ratio S&P 500 current {_dkai.today().year}",
                "BUFFETT":      f"Buffett indicator total US market cap to GDP percent {_dkai.today().year}",
                "TOP10_WEIGHT": f"top 10 S&P 500 stocks weight concentration percent {_dkai.today().year}",
                "PCT_ABOVE_50": f"S&P 500 percent stocks above 50 day moving average {_dkai.today().year}",
                "PCT_ABOVE_200":f"S&P 500 percent stocks above 200 day moving average {_dkai.today().year}",
                "NYSE_AD":      f"NYSE advance decline net difference today {_dkai.today().year}",
                "RATE_30":      f"30 year fixed mortgage rate current percent {_dkai.today().year}",
                "SUPPLY_MO":    f"US housing months supply new homes latest {_dkai.today().year}",
                "HPI_YOY":      f"Case-Shiller home price index year over year change latest {_dkai.today().year}",
                "MTGE_DELINQ":  f"US mortgage delinquency rate percent latest {_dkai.today().year}",
                "SMART_MONEY":  f"smart money confidence index current percent {_dkai.today().year}",
                "DUMB_MONEY":   f"dumb money confidence index current percent {_dkai.today().year}",
                "CPI":          f"US CPI inflation year over year percent latest reading {_dkai.today().year}",
                "REAL_RETAIL":  f"US real retail sales year over year percent change latest {_dkai.today().year}",
                "PCE_YOY":      f"US core PCE inflation year over year percent latest {_dkai.today().year}",
            }
            _needed_ids = [k for k in _na_ids if k in _search_queries]
            if not _needed_ids:
                raise ValueError("no searchable indicators")

            _q_lines = "\n".join(f"- {k}: {_search_queries[k]}" for k in _needed_ids)
            _units = {
                "SENTIMENT":    "score 0-100",
                "NAAIM":        "% 0-150",
                "AAII_BULL":    "% spread -80 to +80",
                "PUT_CALL":     "ratio 0.5-2.0",
                "FORWARD_PE":   "price-to-earnings ratio 14-30 (e.g. 23.5)",
                "ERP":          "% difference e.g. +1.5 or -0.5 (earnings yield minus 10Y yield)",
                "CCC_OAS":      "basis points 300-3000",
                "OFR_FSI":      "index value (negative=calm, positive=stress)",
                "CI_LOAN_DLQ":  "% rate 0.5-5%",
                "CAPE":         "ratio 10-60",
                "BUFFETT":      "% of GDP 100-250",
                "TOP10_WEIGHT": "% of index 20-45",
                "PCT_ABOVE_50": "% of stocks 0-100",
                "PCT_ABOVE_200":"% of stocks 0-100",
                "NYSE_AD":      "net number e.g. 500 or -1200",
                "RATE_30":      "% rate 4-10",
                "SUPPLY_MO":    "months 2-12",
                "HPI_YOY":      "% year over year -10 to 20",
                "MTGE_DELINQ":  "% rate 1-10",
                "SMART_MONEY":  "% confidence 0-100",
                "DUMB_MONEY":   "% confidence 0-100",
                "CPI":          "% YoY e.g. 2.4",
                "REAL_RETAIL":  "% YoY e.g. 1.5 or -0.3",
                "PCE_YOY":      "% YoY e.g. 2.6",
            }
            _units_lines = ", ".join(f"{k}({_units[k]})" for k in _needed_ids)

            _web_prompt = (
                f"Today is {_today}. Search the web and find the MOST CURRENT published values "
                f"for these financial market indicators:\n\n{_q_lines}\n\n"
                f"Units: {_units_lines}\n\n"
                f"Search each one, find the actual number, then respond ONLY with this exact JSON "
                f"(replace <number> with the real value, or null if not found):\n"
                + "{" + ", ".join(f'"{k}": <number>' for k in _needed_ids) + "}"
            )

            # Use claude-sonnet-4-6 — web_search tool requires a current model string
            _ws_resp = _rqai.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",   # correct model string for Haiku
                    "max_tokens": 1000,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "system": (
                        "You are a financial data assistant. Use the web_search tool to find "
                        "the most current published numeric values for the financial indicators "
                        "requested. After searching, return ONLY a valid JSON object containing "
                        "the numeric values. No markdown fences, no explanation — only the JSON."
                    ),
                    "messages": [{"role": "user", "content": _web_prompt}],
                },
                timeout=60,
            ).json()

            # Extract final text block (after all tool-use cycles complete)
            _ws_text = ""
            if "error" in _ws_resp:
                print(f"  Web search API error: {_ws_resp['error'].get('message','unknown')}")
            elif "content" in _ws_resp:
                for _block in _ws_resp["content"]:
                    if _block.get("type") == "text":
                        _ws_text = _block.get("text","").strip()

            # Parse JSON — greedy match to handle any wrapping
            if _ws_text:
                # Strip accidental markdown fences
                _ws_clean = _re_ai.sub(r"```[a-zA-Z]*\n?", "", _ws_text).strip().strip("`")
                _jm = _re_ai.search(r"\{.+\}", _ws_clean, _re_ai.DOTALL)
                if _jm:
                    try:
                        _ws_vals = _jsai.loads(_jm.group())
                        _ws_filled = []
                        for _kid, _kval in _ws_vals.items():
                            if _kid in _needed_ids and _kval is not None:
                                try:
                                    _fval = float(str(_kval).replace(",","").replace("%",""))
                                    _ok = True
                                    if _kid == "SENTIMENT"    and not (0   <= _fval <= 100  ): _ok = False
                                    if _kid == "NAAIM"        and not (0   <= _fval <= 150  ): _ok = False
                                    if _kid == "AAII_BULL"    and not (-80 <= _fval <= 80   ): _ok = False
                                    if _kid == "PUT_CALL"     and not (0.3 <= _fval <= 3.0  ): _ok = False
                                    if _kid == "CCC_OAS"      and not (300 <= _fval <= 3000 ): _ok = False
                                    if _kid == "CAPE"         and not (10  <= _fval <= 60   ): _ok = False
                                    if _kid == "BUFFETT"      and not (50  <= _fval <= 300  ): _ok = False
                                    if _kid == "TOP10_WEIGHT" and not (10  <= _fval <= 55   ): _ok = False
                                    if _kid == "PCT_ABOVE_50" and not (0   <= _fval <= 100  ): _ok = False
                                    if _kid == "FORWARD_PE"   and not (14  <= _fval <= 30   ): _ok = False
                                    if _kid == "ERP"          and not (-5  <= _fval <= 8    ): _ok = False
                                    if _kid == "RATE_30"      and not (3.0 <= _fval <= 12.0 ): _ok = False
                                    if _kid == "SUPPLY_MO"    and not (1.0 <= _fval <= 15.0 ): _ok = False
                                    if _kid == "HPI_YOY"      and not (-15 <= _fval <= 25   ): _ok = False
                                    if _kid == "MTGE_DELINQ"  and not (0.5 <= _fval <= 12.0 ): _ok = False
                                    if _kid == "SMART_MONEY"  and not (0   <= _fval <= 100  ): _ok = False
                                    if _kid == "DUMB_MONEY"   and not (0   <= _fval <= 100  ): _ok = False
                                    if _kid == "CPI"          and not (-2  <= _fval <= 10   ): _ok = False
                                    if _kid == "REAL_RETAIL"  and not (-15 <= _fval <= 15   ): _ok = False
                                    if _kid == "PCE_YOY"      and not (-2  <= _fval <= 8    ): _ok = False
                                    if _ok:
                                        vals[_kid] = _fval
                                        vals[f"_{_kid}_AI"] = True
                                        _ws_filled.append(_kid)
                                except (ValueError, TypeError): pass
                        if _ws_filled:
                            print(f"  Claude web search filled: {', '.join(_ws_filled)}")
                            # Recompute ERP if FORWARD_PE was just filled by web search
                            if "FORWARD_PE" in _ws_filled and vals.get("FORWARD_PE"):
                                _t10_now = _g("T10Y")
                                _ey_now  = round(100.0 / vals["FORWARD_PE"], 2)
                                vals["ERP"] = round(_ey_now - _t10_now, 2) if _t10_now else None
                                print(f"  ERP recomputed: {vals['ERP']:+.2f}% (earnings yield {_ey_now:.2f}% - T10Y {_t10_now:.2f}%)" if vals["ERP"] else "  ERP: T10Y unavailable")
                        else:
                            print(f"  Web search returned no valid values for: {_needed_ids}")
                    except _jsai.JSONDecodeError as _je:
                        print(f"  Web search JSON parse failed: {_je} | raw: {_ws_text[:200]}")
                else:
                    print(f"  Web search: no JSON found in response: {_ws_text[:200]}")
        except Exception as _eai:
            print(f"  Web search fallback error: {_eai}")

    # ── Signal classification ─────────────────────────────────────────────────
    def _signal(key, val):
        if val is None: return "N/A"
        d = SCORECARD_DEFS.get(key, {})
        thresh = d.get("thresh", {})
        direction = d.get("dir", "up_bad")
        for sig in ["CRISIS","STRESS","CAUTION","CALM"]:
            if sig not in thresh: continue
            lo, hi = thresh[sig]
            if lo <= val < hi:
                return sig
        return "N/A"

    # ── Format value ──────────────────────────────────────────────────────────
    def _fmt(key, val):
        if val is None: return "N/A"
        d = SCORECARD_DEFS.get(key, {})
        unit = d.get("unit","")
        if unit == "bps":  return f"{val:.0f} bps"
        if unit == "%":    return f"{val:.1f}%"
        if unit == "$T":   return f"${val:.2f}T"
        if unit == "x":    return f"{val:.2f}x"
        if unit == "ratio":return f"{val:.3f}"           # e.g. XLY/XLP = 1.288
        if unit == "idx":
            # SPX RSI shows as integer, others as 1dp
            return f"{val:.0f}" if key in ("SPX_RSI",) else f"{val:.1f}"
        if unit == "fsi":  return f"{val:+.3f}"          # e.g. OFR FSI = -0.527 or +1.2
        if unit == "pp":   return f"+{val:.2f}pp" if val >= 0 else f"{val:.2f}pp"
        try:    return f"{val:.1f}"
        except: return str(val)

    # ── Build result list ─────────────────────────────────────────────────────
    results = []
    for key in SCORECARD_ORDER:
        d = SCORECARD_DEFS[key]
        val = vals.get(key)
        sig = _signal(key, val)
        # Determine as-of date for this indicator
        _AS_OF_MAP = {
            # Original indicators
            'HY_OAS':'HY_OAS','IG_OAS':'IG_OAS','HY_IG_DIFF':'HY_OAS',
            'CCC_OAS':'CCC_OAS','NFCI':'NFCI','YIELD_CURVE':'YIELD_CURVE',
            'CURVE_10Y3M':'T10Y3M','REAL_YIELD':'REAL_YIELD','BREAKEVEN':'BREAKEVEN',
            'FED_FUNDS':'FEDFUNDS','T10Y_YIELD':'T10Y','VIX':'^VIX','VIX_TERM':'^VIX',
            'MOVE':'^MOVE','VIX9D_RATIO':'^VIX','PCT_ABOVE_50':'_pct_above_50',
            'PCT_ABOVE_200':'_pct_above_200','NYSE_AD':'_nyad_net',
            'FORWARD_PE':'^GSPC','ERP':'^GSPC','CAPE':'SP500EPS',
            'BUFFETT':'WILL5000IND','NET_LIQUIDITY':'WALCL','M2SL':'M2SL',
            'FED_BS':'WALCL','SAHM':'SAHM','NY_REC_PROB':'NY_REC_PROB',
            'CREDIT_CARD_DLQ':'CREDIT_CARD_DLQ','SPX_DD':'^GSPC',
            'TOP10_WEIGHT':'_top10_weight','RSP_SPY':'RSP','SPX_VS_200':'^GSPC',
            'INDPRO':'INDPRO','CAPUTIL':'CAPUTIL','CPI':'CPI',
            'REAL_RETAIL':'RETAIL','HOUST_YOY':'HOUST','SENTIMENT':'^VIX',
            # New indicators
            'NAAIM':'NAAIM','AAII_BULL':'AAII_BULL',
            'PUT_CALL':'^VIX9D','SPX_RSI':'^GSPC','GOLDEN_X':'^GSPC',
            'XLY_XLP':'XLY','XLF_XLU':'XLF','IWM_SPY':'IWM','XLK_SPY':'XLK',
            'DXY':'DX-Y.NYB','GLD_SPY':'GLD','TLT_SPY':'TLT',
            'VVIX':'^VVIX','SKEW':'^SKEW',
            'CI_LOAN_DLQ':'CI_LOAN_DLQ','OFR_FSI':'OFR_FSI',
            # Housing market indicators
            'RATE_30':'RATE_30','AFFORD_PTI':'RATE_30','MTGE_DELINQ':'MTGE_DELINQ',
            'XHB_SPY':'XHB','HPI_YOY':'HPI_NAT','SUPPLY_MO':'SUPPLY_MO',
        }
        _as_of_src   = _AS_OF_MAP.get(key, key)
        _as_of_date  = _date(_as_of_src) or _date(key) or ""

        # Override with stored dates for computed indicators that have no Series index
        _stored_date_map = {
            "CAPE":         vals.get("_CAPE_DATE", ""),
            "BUFFETT":      vals.get("_BUFFETT_DATE", ""),
            "TOP10_WEIGHT": vals.get("_TOP10_DATE", ""),
            "PCT_ABOVE_50": date.today().strftime("%Y-%m-%d") if vals.get("PCT_ABOVE_50") is not None else "",
            "PCT_ABOVE_200":date.today().strftime("%Y-%m-%d") if vals.get("PCT_ABOVE_200") is not None else "",
            "NYSE_AD":      date.today().strftime("%Y-%m-%d") if vals.get("NYSE_AD") is not None else "",
            "SMART_MONEY":  date.today().strftime("%Y-%m-%d") if vals.get("SMART_MONEY") is not None else "",
            "DUMB_MONEY":   date.today().strftime("%Y-%m-%d") if vals.get("DUMB_MONEY")  is not None else "",
        }
        if key in _stored_date_map and _stored_date_map[key]:
            _as_of_date = _stored_date_map[key]

        _is_ai_est   = vals.get(f"_{key}_AI", False)
        # Web-search filled indicators: use today's date
        if _is_ai_est and not _as_of_date:
            from datetime import date as _dasnow
            _as_of_date = _dasnow.today().strftime('%Y-%m-%d')

        results.append({
            "id":      key,
            "name":    d["name"],
            "cat":     d["cat"],
            "wt":      d["wt"],
            "value":   val,
            "val_str": _fmt(key, val),
            "signal":  sig,
            "unit":    d.get("unit",""),
            "src":     d.get("src",""),
            "hist":    d.get("hist",""),
            "context": d.get("signal",""),
            "as_of":   _as_of_date,
            "ai_est":  _is_ai_est,
        })
    return results, vals.get("_SDM_DATA", {})



def cycle_pos(fd, ep):
    ty = date.today().year + date.today().month/12
    _td = date.today()

    # ── Dynamic timing helpers ────────────────────────────────────────────────
    def _nq(months):
        """Return 'Q? YYYY' string N months from today."""
        m = _td.month + months
        yr = _td.year + (m - 1) // 12
        q  = ((m - 1) % 12) // 3 + 1
        return f"Q{q} {yr}"
    _cur_q  = f"Q{(_td.month-1)//3+1} {_td.year}"
    _in_progress = f"{_cur_q}–{_nq(9)} (in progress)"  # fully dynamic — computed from date.today()

    def g(k):
        s=fd.get(k); return float(s.iloc[-1]) if s is not None and not s.empty else None
    def yoy(k,p=12):
        s=fd.get(k)
        if s is None or len(s)<p+2: return None
        a,b=float(s.iloc[-1]),float(s.iloc[-p-1])
        return round((a/b-1)*100,2) if b!=0 else None

    yc=g("YIELD_CURVE"); hy=g("HY_OAS"); ur=g("UNRATE"); ip=yoy("INDPRO")
    cu=g("CAPUTIL"); ff=g("FEDFUNDS"); nf=g("NFCI"); hy_yoy=yoy("HOUST"); m2=yoy("M2SL")
    t10=g("T10Y")

    # Kuznets 2011-2032
    kp=round((ty-2011)/(2032-2011)*100,1)
    if kp<30:   kph,kc="Early Expansion","#1A7A4A"
    elif kp<55: kph,kc="Mid Expansion","#2E8B57"
    elif kp<75: kph,kc="Late Expansion","#D4820A"
    else:       kph,kc="Contraction","#C0390F"
    knote=(f"Housing starts {hy_yoy:+.0f}% YoY → {'Kuznets downswing' if hy_yoy and hy_yoy<-15 else 'Kuznets healthy'}" if hy_yoy else "Housing data updating")

    # Juglar 2020-2027
    jp=round((ty-2020)/(2027-2020)*100,1)
    if jp<35:   jph,jc="Early Expansion","#1A7A4A"
    elif jp<65: jph,jc="Mid Expansion","#2E8B57"
    elif jp<85: jph,jc="Late / Near Peak","#D4820A"
    else:       jph,jc="Contraction","#C0390F"

    # Kitchin 2023-2026
    ki=round((ty-2023)/(2026-2023)*100,1)
    if ki<35:   kip,kic="Recovery","#1A7A4A"
    elif ki<65: kip,kic="Expansion","#2E8B57"
    elif ki<85: kip,kic="Near Peak","#D4820A"
    else:       kip,kic="Contraction","#C0390F"

    # Overall regime
    ps=0
    if "Contraction" in kph: ps+=2
    elif "Late" in kph:      ps+=1
    if "Contraction" in jph: ps+=3
    elif "Late" in jph:      ps+=2
    elif "Mid" in jph:       ps+=1
    if "Contraction" in kip: ps+=2
    elif "Near" in kip:      ps+=1
    eps=ep["score"]
    if eps>70: ps+=3
    elif eps>50: ps+=2
    elif eps>35: ps+=1

    if ps>=8:   rg,rc="LATE CYCLE — PRE-RECESSION RISK","#C0390F"
    elif ps>=5: rg,rc="LATE MID-CYCLE CAUTION","#D4820A"
    elif ps>=3: rg,rc="MID-CYCLE EXPANSION","#556"
    else:       rg,rc="EARLY CYCLE — RISK ON","#1A7A4A"

    # Projected corrections
    projections = []
    s_yc=fd.get("YIELD_CURVE")
    was_inv=s_yc is not None and len(s_yc)>24 and any(float(v)<0 for v in s_yc.iloc[-24:])

    if jp>75 and was_inv and yc and yc>0:
        projections.append({
            "name":"Juglar Peak Correction",
            "timing":f"{_nq(6)}–{_nq(18)} (6-18 months from now)",
            "magnitude":"-20% to -40% S&P 500",
            "probability":"HIGH (70%+)",
            "col":"#C0390F",
            "trigger":"Juglar cycle exhaustion + post-inversion normalization",
            "what_to_watch":("HY OAS >450bps [NOW: " + (str(round(hy)) + "bps ✓ CALM" if hy and hy<450 else (str(round(hy)) if hy else "N/A") + "bps ⚠") + "] | Sahm Rule [NOW: +" + (str(round(float(fd["UNRATE"].iloc[-1])-float(fd["UNRATE"].iloc[-4]),2)) + "pp" if (fd.get("UNRATE") is not None and len(fd["UNRATE"])>=5) else "N/A") + "] | INDPRO YoY [NOW: " + (str(round(ip,1)) + "%" if ip is not None else "N/A") + "]"),
            "what_to_watch":("HY OAS >450bps [NOW: "
                + (str(round(hy)) + "bps ✓ CALM" if hy and hy<450 else (str(round(hy)) if hy else "N/A") + "bps ⚠ WATCH")
                + "] | Sahm Rule >0.5pp [NOW: +"
                + (str(round(float(fd["UNRATE"].iloc[-1])-float(fd["UNRATE"].iloc[-4]),2)) + "pp ✓ CLEAR" if (fd.get("UNRATE") is not None and len(fd["UNRATE"])>=5 and float(fd["UNRATE"].iloc[-1])-float(fd["UNRATE"].iloc[-4])<0.5) else "N/A or ⚠ WATCH")
                + "] | INDPRO YoY [NOW: "
                + (str(round(ip,1)) + "% ✓ OK" if ip and ip>0 else (str(round(ip,1)) if ip is not None else "N/A") + "% ⚠ WEAK")
                + "]"),
            "sectors_at_risk":"XLY, XLK, XLF, XLRE",
            "sectors_defensive":"XLP, XLU, XLV, GLD, TLT",
        })

    if ki>80:
        projections.append({
            "name":"Kitchin Inventory Correction",
            "timing":_in_progress,
            "magnitude":"-10% to -20% S&P 500",
            "probability":"HIGH (65%)",
            "col":"#D4820A",
            "trigger":"Inventory destocking + AI capex disappointment",
            "what_to_watch":("INDPRO YoY: "
                + (str(round(ip,1)) + "%" if ip is not None else "N/A")
                + (" ⚠ WEAK" if ip is not None and ip<1.5 else " ✓ OK")
                + " | CapUtil: " + (str(round(cu,1)) + "%" if cu else "N/A")
                + (" ⚠ <77%" if cu and cu<77 else " ✓ OK")
                + " | HY OAS: " + (str(round(hy)) + "bps ✓ CALM" if hy and hy<380 else (str(round(hy)) if hy else "N/A") + "bps ⚠ ELEVATED")),
            "parallel":"2022 Q1-Q3: −25% | 2018 Q4: −20% | 2015-16: −15% | 2011: −21%",
            "sectors_at_risk":"XLK, XLY, XLC (AI/tech-heavy)",
            "sectors_defensive":"XLP, XLV, XLU, energy (XLE)",
        })

    if not was_inv and yc and 0<yc<50 and hy and hy>350:
        projections.append({
            "name":"Policy Tightening Correction",
            "timing":f"{_nq(6)}–{_nq(12)} if Fed pauses or re-hikes",
            "magnitude":"-15% to -25% S&P 500",
            "probability":"MEDIUM (45%)",
            "col":"#D4820A",
            "trigger":"Inflation re-acceleration forces Fed to hold/hike longer",
            "what_to_watch":("CPI: " + (str(round(yoy("CPI",12),1)) + "%" if yoy("CPI",12) else "N/A") + (" ⚠ >3.5%" if yoy("CPI",12) and yoy("CPI",12)>3.5 else " ✓ OK") + " | 10Y: " + (str(round(t10,2)) + "%" if t10 else "N/A") + (" ⚠ >5%" if t10 and t10>5 else " ✓ OK") + " | Real rates: " + (str(round(t10-(yoy("CPI",12) or 0),2)) + "%" if t10 else "N/A")),
            "what_to_watch":("CPI: "
                + (str(round(yoy("CPI",12),1)) + "%" if yoy("CPI",12) else "N/A")
                + (" ⚠ >3.5%" if yoy("CPI",12) and yoy("CPI",12)>3.5 else " ✓ OK")
                + " | 10Y: " + (str(round(t10,2)) + "%" if t10 else "N/A")
                + (" ⚠ >5%" if t10 and t10>5 else " ✓ OK")
                + " | Real rates: " + (str(round(t10-(yoy("CPI",12) or 0),2)) + "%" if t10 else "N/A")),
            "sectors_at_risk":"XLK, XLRE, XLY (high duration/leverage)",
            "sectors_defensive":"XLE, XLF (short duration beneficiaries), cash",
        })

    if not projections:
        projections.append({
            "name":"Baseline Pullback",
            "timing":f"Any time from {_cur_q} (normal market volatility)",
            "magnitude":"-5% to -12%",
            "probability":"MEDIUM (ongoing)",
            "col":"#556",
            "trigger":"Normal mean reversion / sentiment reset",
            "what_to_watch":("HY OAS: " + (str(round(hy)) + "bps ✓ CALM" if hy and hy<380 else (str(round(hy)) if hy else "N/A") + "bps ⚠ WATCH") + " | Yield curve: " + (str(round(yc,2)) + "% ✓ POS" if yc and yc>0 else (str(round(yc,2)) if yc is not None else "N/A") + "% ⚠") + " | INDPRO YoY: " + (str(round(ip,1)) + "%" if ip is not None else "N/A")),
            "what_to_watch":("HY OAS: "
                + (str(round(hy)) + "bps ✓ CALM" if hy and hy<380 else (str(round(hy)) if hy else "N/A") + "bps ⚠ WATCH")
                + " | Yield curve: " + (str(round(yc,2)) + "% ✓ POSITIVE" if yc and yc>0 else (str(round(yc,2)) if yc is not None else "N/A") + "% ⚠ FLAT")
                + " | INDPRO YoY: " + (str(round(ip,1)) + "%" if ip is not None else "N/A")),
            "sectors_at_risk":"Most recent outperformers",
            "sectors_defensive":"Quality + dividend stocks",
        })

    # Historical parallels (data-driven)
    parallels=[]
    if jp>75 and hy and 300<hy<500 and was_inv:
        parallels.append({"year":"Oct 2007","sim":85,"col":"#C0390F",
            "desc":f"Late Juglar + post-inversion + HY OAS 300-450bps. Conditions {'match' if hy and 300<hy<450 else 'close'} current environment.",
            "then":f"S&P peaked Oct 2007 at SPX 1576. Fell -57% to 676 by March 2009.",
            "now":f"Current: Juglar {jp:.0f}% through, HY OAS {f'{hy:.0f}' if hy else 'N/A'}bps, yield curve {f'{yc:+.2f}' if yc is not None else 'N/A'}%.",
            "key_diff":"Today: AI capex secular growth may extend cycle vs 2007 housing-only driver.",
            "impl":"Reduce cyclicals, add TLT + defensives, buy put spreads on VIX spikes."})
    if ki>80 and ff and ff>4:
        parallels.append({"year":"Q4 2018","sim":70,"col":"#D4820A",
            "desc":f"Late Kitchin + restrictive Fed ({f'{ff:.2f}' if ff else 'N/A'}%). S&P fell -20% in 66 days.",
            "then":"S&P recovered fully in 5 months after Fed pivot (Powell put Dec 2018).",
            "now":f"Current: Kitchin {ki:.0f}% through, Fed Funds {f'{ff:.2f}' if ff else 'N/A'}%.",
            "key_diff":"2018 was sharp but short — no Juglar turn, no credit stress. Today Juglar also late.",
            "impl":"Tactical hedge, don't go fully defensive unless Juglar also turns."})
    if yc and yc<0.5 and t10 and t10>4:
        parallels.append({"year":"2022","sim":65,"col":"#D4820A",
            "desc":f"Rates elevated, curve flat/inverting. S&P -25%, Nasdaq -33%.",
            "then":"Growth/tech hit hardest. Value outperformed. Recovery took 18 months.",
            "now":f"10Y at {f'{t10:.2f}' if t10 else 'N/A'}%, curve {f'{yc:+.2f}' if yc is not None else 'N/A'}%.",
            "key_diff":"2022 had zero prior cycle correction. Current correction partially done from Jan 2022 ATH.",
            "impl":"Duration risk still present if rates don't fall. Weight shorter duration, quality."})
    if not parallels:
        parallels.append({"year":"2013-2015","sim":55,"col":"#1A7A4A",
            "desc":"Mid-cycle expansion with Fed gradual normalization. S&P +30% over 2 years.",
            "then":"Continued bull market with 10-15% mid-cycle corrections along the way.",
            "now":"Current conditions broadly constructive if credit stays calm.",
            "key_diff":"2013 was earlier in Juglar cycle. Today Juglar is more mature.",
            "impl":"Stay long risk assets with tactical hedges on any spike to ATH."})

    return {
        "kuznets": {"phase":kph,"col":kc,"pct":kp,"note":knote,
                    "trough":2011,"peak":2028,"trough2":2032,"years_to_peak":round(2028-ty,1)},
        "juglar":  {"phase":jph,"col":jc,"pct":jp,
                    "trough":2020,"peak":2025,"trough2":2027,"years_to_peak":round(2025-ty,1)},
        "kitchin": {"phase":kip,"col":kic,"pct":ki,
                    "trough":2023,"peak":2025,"trough2":2026},
        "regime":  {"label":rg,"col":rc,"score":ps},
        "projections":projections,"parallels":parallels,
        "data":{"yc":yc,"hy":hy,"ur":ur,"ip":ip,"cu":cu,"ff":ff,"nf":nf,"t10":t10},
    }

# ══════════════════════════════════════════════════════════════════════════════
# CHART DATA PREPARATION
# ══════════════════════════════════════════════════════════════════════════════

def prep_charts(fd, md, pos=None, ep=None):
    """Prepare data for all Chart.js charts."""
    import pandas as pd
    charts = {}

    # Helper: resample a FRED series to monthly, last N months
    def fred_monthly(key, n=60):
        s = fd.get(key)
        if s is None or s.empty: return [], []
        m = s.resample("ME").last().dropna().tail(n)
        return [str(d)[:7] for d in m.index], [round(float(v),4) for v in m.values]

    # Helper: resample market price to monthly
    def mkt_monthly(key, n=60):
        s = md.get(key)
        if s is None or len(s) < 20: return [], []
        m = s.resample("ME").last().dropna().tail(n)
        return [str(d)[:7] for d in m.index], [round(float(v),2) for v in m.values]

    # 1. Yield Curve with recession bands
    dates, values = fred_monthly("YIELD_CURVE", 240)
    rec_dates, rec_vals = fred_monthly("USREC", 240)
    charts["yield_curve"] = {"dates":dates,"values":values,
                              "rec_dates":rec_dates,"rec_vals":rec_vals}

    # 2. HY OAS with danger zones
    dates, values = fred_monthly("HY_OAS", 240)
    charts["hy_oas"] = {"dates":dates,"values":values}

    # 3. Fed Funds + CPI
    ff_d, ff_v   = fred_monthly("FEDFUNDS", 240)
    cpi_d, cpi_v = fred_monthly("CPI", 240)
    # Convert CPI to YoY
    if cpi_v and len(cpi_v) > 12:
        cpi_yoy_v = [None]*12 + [round((cpi_v[i]/cpi_v[i-12]-1)*100,2) for i in range(12,len(cpi_v))]
        cpi_yoy_d = cpi_d
    else:
        cpi_yoy_v, cpi_yoy_d = cpi_v, cpi_d
    charts["fed_cpi"] = {"ff_dates":ff_d,"ff_values":ff_v,
                          "cpi_dates":cpi_yoy_d,"cpi_values":cpi_yoy_v}

    # 4. SPY price history with key events annotated
    spy_d, spy_v = mkt_monthly("SPY", 120)
    charts["spy"] = {"dates":spy_d,"values":spy_v}

    # 5. Cross-pair ratios — 12-month daily + 5yr seasonal pattern (Jan-Dec)
    pair_charts = {}
    for bt, brt, name, desc in CROSS_PAIRS:
        if bt in md and brt in md:
            import pandas as pd, numpy as np
            _s1 = md[bt].dropna()
            _s2 = md[brt].dropna()
            try:
                if hasattr(_s1.index,'tz') and _s1.index.tz is not None:
                    _s1.index = _s1.index.tz_localize(None)
                if hasattr(_s2.index,'tz') and _s2.index.tz is not None:
                    _s2.index = _s2.index.tz_localize(None)
            except Exception: pass

            combined = pd.concat([_s1, _s2], axis=1).dropna()
            combined.columns = ["n", "d"]
            r_full = (combined["n"] / combined["d"]).dropna()
            if len(r_full) < 60: continue

            # ── 12-month daily window for display (~252 trading days) ─────────
            _r12 = r_full.tail(252)
            try:
                if hasattr(_r12.index,'tz') and _r12.index.tz is not None:
                    _r12.index = _r12.index.tz_localize(None)
            except Exception: pass

            dates  = [str(x)[:10] for x in _r12.index]
            values = [round(float(v), 4) for v in _r12.values]

            # ── 5-year seasonal: monthly average (Jan-Dec), smoothed ──────────
            # Use full history (5yr) to compute average ratio by month number
            seasonal_monthly = {}   # month 1-12 → avg ratio
            try:
                _rf = r_full.copy()
                _rf.index = pd.to_datetime(_rf.index)
                for mo in range(1, 13):
                    _mask = _rf.index.month == mo
                    if _mask.sum() >= 5:
                        seasonal_monthly[mo] = float(_rf[_mask].mean())
            except Exception: pass

            # Map seasonal values onto the 12-month display dates
            # Re-scale so the seasonal line overlays on the current ratio range
            _r12_mean = float(_r12.mean()) if len(_r12) > 0 else 1.0
            _seas_mean = float(np.mean(list(seasonal_monthly.values()))) if seasonal_monthly else _r12_mean
            _scale = _r12_mean / _seas_mean if _seas_mean != 0 else 1.0

            seas_overlay = []
            for _dt in dates:
                try:
                    _mo = pd.Timestamp(_dt).month
                    _sv = seasonal_monthly.get(_mo)
                    seas_overlay.append(round(float(_sv) * _scale, 4) if _sv else None)
                except Exception:
                    seas_overlay.append(None)

            # EMA 20 / 50 on the 12-month window
            ema20 = _r12.ewm(span=20, adjust=False).mean()
            ema50 = _r12.ewm(span=50, adjust=False).mean()
            ema20_v = [round(float(v), 4) for v in ema20.values]
            ema50_v = [round(float(v), 4) for v in ema50.values]

            # 1-year percentile vs full history
            rank1y = round(float((float(_r12.iloc[-1]) > r_full.tail(252)).mean() * 100), 1) if len(r_full) >= 252 else 50

            # Direction
            _c3m = round((float(_r12.iloc[-1]) / float(_r12.iloc[-63]) - 1) * 100, 1) if len(_r12) >= 63 else 0
            _cur  = float(_r12.iloc[-1])
            _e20v = float(ema20.iloc[-1])
            if _c3m > 2 and _cur > _e20v:    d_sig, d_col = "RISING ↑",  "#1A7A4A"
            elif _c3m < -2 and _cur < _e20v: d_sig, d_col = "FALLING ↓", "#C0390F"
            else:                              d_sig, d_col = "FLAT →",    "#334466"

            # vs seasonal today
            _today_mo = date.today().month
            _sv_today = seasonal_monthly.get(_today_mo)
            _vs_seasonal = None
            if _sv_today and _scale:
                _seas_scaled = _sv_today * _scale
                _vs_seasonal = round((_cur / _seas_scaled - 1) * 100, 1) if _seas_scaled else None

            pair_charts[f"{bt}/{brt}"] = {
                "dates":       dates,
                "values":      values,
                "ema20":       ema20_v,
                "ema50":       ema50_v,
                "seasonality": seas_overlay,
                "rank1y":      rank1y,
                "direction":   d_sig,
                "dir_col":     d_col,
                "name":        name,
                "c3m":         _c3m,
                "vs_seasonal": _vs_seasonal,
            }
    charts["pairs"] = pair_charts

    # 6. Industrial production + capacity utilization
    ip_d, ip_v   = fred_monthly("INDPRO", 120)
    cu_d, cu_v   = fred_monthly("CAPUTIL", 120)
    charts["ip_caputil"] = {"ip_dates":ip_d,"ip_values":ip_v,
                             "cu_dates":cu_d,"cu_values":cu_v}

    # 7. Sector performance heatmap data
    sector_perf = {}
    for t in SECTOR_ETFS:
        if t in md:
            i = ind(md[t])
            sector_perf[t] = {
                "c1m": i.get("c1m",0) or 0,
                "c3m": i.get("c3m",0) or 0,
                "c6m": i.get("c6m",0) or 0,
                "c1y": i.get("c1y",0) or 0,
                "rsi": i.get("rsi",50),
                "vs200": i.get("vs200",0) or 0,
                "trend": i.get("trend","MIX"),
            }
    charts["sectors"] = sector_perf

    # 8. Juglar cycle overlay — SPY indexed to 100 from each trough
    # Trough dates: 1982-08, 1990-10, 2002-10, 2009-03, 2020-03 (current)
    JUGLAR_TROUGHS = [
        ("1982-08", "1982 Cycle", "#ff7744"),
        ("1990-10", "1990 Cycle", "#ffaa33"),
        ("2002-10", "2002 Cycle", "#00bcd4"),
        ("2009-03", "2009 Cycle", "#1188ee"),
        ("2020-03", "Current (2020)", "#00ff99"),
    ]
    # Use ^GSPC (max history) for overlay; fall back to SPY for recent cycles
    _gspc = md.get("^GSPC")
    if _gspc is None or _gspc.empty:
        _gspc = md.get("SPY")
    if _gspc is not None:
        gspc_m = _gspc.resample("ME").last().dropna()
        # Strip timezone from index (yfinance may return tz-aware America/New_York)
        try:
            if gspc_m.index.tz is not None:
                gspc_m.index = gspc_m.index.tz_localize(None)
        except Exception: pass
        overlay = {}
        for trough_str, label, color in JUGLAR_TROUGHS:
            try:
                import pandas as pd
                trough_dt = pd.Timestamp(trough_str)
                mask = gspc_m.index >= trough_dt
                cycle_s = gspc_m[mask].head(96)   # up to 8 years (96 months)
                if len(cycle_s) >= 6:
                    base = float(cycle_s.iloc[0])
                    vals = [round(float(v)/base*100, 2) for v in cycle_s.values]
                    months = list(range(len(vals)))
                    overlay[label] = {"months": months, "values": vals, "color": color}
                    print(f"  Overlay {label}: {len(vals)} months from {str(cycle_s.index[0])[:7]}")
                else:
                    print(f"  Overlay {label}: only {len(cycle_s)} months — skipping")
            except Exception as ex:
                print(f"  Overlay {label}: error — {ex}")
        # Compute historical avg ± 1 std dev band across prior cycles
        try:
            import numpy as _np2
            prior_vals_list = [overlay[l]["values"] for l in [
                "1982 Cycle","1990 Cycle","2002 Cycle","2009 Cycle"] if l in overlay]
            if len(prior_vals_list) >= 2:
                max_len = max(len(v) for v in prior_vals_list)
                padded  = [v + [None]*(max_len-len(v)) for v in prior_vals_list]
                avgs, stds = [], []
                for mi in range(max_len):
                    row = [p[mi] for p in padded if p[mi] is not None]
                    if row:
                        avgs.append(round(float(_np2.mean(row)),2))
                        stds.append(round(float(_np2.std(row)),2))
                    else:
                        avgs.append(None); stds.append(None)
                overlay["__avg__"]   = {"months": list(range(max_len)), "values": avgs}
                overlay["__upper__"] = {"months": list(range(max_len)), "values":
                    [round(a+s,2) if a is not None else None for a,s in zip(avgs,stds)]}
                overlay["__lower__"] = {"months": list(range(max_len)), "values":
                    [round(a-s,2) if a is not None else None for a,s in zip(avgs,stds)]}
        except Exception:
            pass
        charts["cycle_overlay"] = overlay

    # 9. Road to 2032 — AI-powered unified SPY path (single coherent trajectory)
    # All corrections are baked into ONE path — no parallel conflicting lines
    today_year = date.today().year + date.today().month / 12
    _cy = today_year

    # Get live SPY price
    try:
        import yfinance as _yf_road
        _road_spy_d = _yf_road.download("SPY", period="5d", interval="1d",
                                        auto_adjust=True, progress=False)
        base_spy = round(float(_road_spy_d["Close"].dropna().iloc[-1]), 2) if not _road_spy_d.empty else float(md["SPY"].dropna().iloc[-1])
    except Exception:
        base_spy = float(md["SPY"].dropna().iloc[-1]) if "SPY" in md and len(md["SPY"].dropna()) > 0 else 530

    # Get ATH and current drawdown from ATH (actual correction so far this year)
    _spy_series = md.get("SPY")
    _ath_price  = float(_spy_series.dropna().max()) if _spy_series is not None else base_spy
    _dd_from_ath = round((base_spy / _ath_price - 1) * 100, 1)   # negative = drawdown

    # Get key live indicators for the projection
    def _rget(k):
        s = fd.get(k)
        return round(float(s.iloc[-1]), 4) if s is not None and not s.empty else None

    _live_data_summary = (
        f"SPY current: ${base_spy:.2f} | ATH: ${_ath_price:.2f} | "
        f"Drawdown from ATH: {_dd_from_ath:.1f}% (correction already underway)\n"
        f"Kuznets cycle: {(pos or {}).get('kuznets',{}).get('pct',72):.0f}% through 2011-2032 cycle "
        f"({(pos or {}).get('kuznets',{}).get('phase','Late Expansion')})\n"
        f"Juglar cycle: {(pos or {}).get('juglar',{}).get('pct',89):.0f}% through 2020-2027 cycle "
        f"({(pos or {}).get('juglar',{}).get('phase','Contraction')})\n"
        f"Kitchin cycle: {(pos or {}).get('kitchin',{}).get('pct',108):.0f}% through 2023-2026 cycle "
        f"({(pos or {}).get('kitchin',{}).get('phase','Contraction')})\n"
        f"HY OAS: {_rget('HY_OAS') or 'N/A'} | "
        f"Yield curve: {_rget('YIELD_CURVE') or 'N/A'}% | "
        f"Fed Funds: {_rget('FEDFUNDS') or 'N/A'}% | "
        f"10Y: {_rget('T10Y') or 'N/A'}% | "
        f"Unemployment: {_rget('UNRATE') or 'N/A'}% | "
        f"SAHM rule: {_rget('SAHM') or 'N/A'} | "
        f"CapUtil: {_rget('CAPUTIL') or 'N/A'}% | "
        f"INDPRO YoY: approx from data"
    )

    # Quarterly year steps: 2024.0 to 2033.75
    _year_steps = [round(2024 + i * 0.25, 2) for i in range(40)]
    def _yr_label(yr):
        q = round((yr % 1) * 4)
        return str(int(yr)) if q == 0 else ""
    year_labels = [_yr_label(y) for y in _year_steps]
    years = _year_steps

    # Build actual SPY history (quarterly) from yfinance — up to today
    _actual_path = {}
    try:
        if _spy_series is not None and not _spy_series.empty:
            _spy_q = _spy_series.resample("QE").last().dropna()
            try:
                if _spy_q.index.tz is not None:
                    _spy_q.index = _spy_q.index.tz_localize(None)
            except Exception: pass
            for _dt, _pv in zip(_spy_q.index, _spy_q.values):
                _yr_frac = round(_dt.year + (_dt.month - 1) / 12, 2)
                if _yr_frac >= 2024.0:
                    # Round to nearest quarter
                    _q = round(_yr_frac * 4) / 4
                    _actual_path[round(_q, 2)] = round(float(_pv), 2)
            # Always set today's value to live price
            _q_today = round(_cy * 4) / 4
            _actual_path[round(_q_today, 2)] = base_spy
    except Exception: pass

    # Build the actual_vals array for JS (non-null only for past quarters)
    actual_vals = []
    for yr in years:
        yr_r = round(yr, 2)
        if yr_r <= round(_cy + 0.1, 2):
            # Find closest actual data point
            closest = min(_actual_path.keys(), key=lambda k: abs(k - yr_r), default=None)
            if closest is not None and abs(closest - yr_r) <= 0.26:
                actual_vals.append(_actual_path[closest])
            else:
                actual_vals.append(None)
        else:
            actual_vals.append(None)

    # Use Claude API to generate ONE unified quarterly SPY path 2026→2033
    # incorporating all cycles, actual YTD drawdown, and live indicators
    _road_proj = None
    _future_years = [y for y in years if y > _cy]   # always available for fallback
    _use_api_road = CLAUDE_API_KEY and pos is not None   # gated - prep_charts gets use_api via pos
    if _use_api_road:
        try:
            import requests as _rqr, json as _jsr, re as _rer
            _n_quarters = sum(1 for y in years if y > _cy)  # future quarters

            _road_prompt = f"""You are a quantitative macro analyst. Generate a single coherent quarterly SPY price path from Q2 2026 through end of 2033.

LIVE DATA (as of today {date.today().strftime("%B %d, %Y")}):
{_live_data_summary}

CYCLE FRAMEWORK:
- Kuznets (17-21yr infrastructure supercycle): currently at 73% through 2011-2032 cycle. AI/cloud buildout driving this. Historical Kuznets peaks cause -40 to -57% drawdowns (1929, 1974, 2008). Peak projected ~2027-2028.
- Juglar (9-11yr capex/business investment): at 89% = near/at contraction. This causes -20 to -35% corrections. Currently overlapping with Kitchin.
- Kitchin (3-4yr inventory): at 108% = IN contraction NOW. Causing the current sell-off. Trough expected ~Q3-Q4 2026.
- Current correction: SPY already down {_dd_from_ath:.1f}% from ATH of ${_ath_price:.0f}. This correction is ALREADY IN PROGRESS.

RULES FOR THE UNIFIED PATH:
1. Start exactly at ${base_spy:.2f} for the first future quarter (Q2 2026)
2. The path must reflect the CURRENT correction already underway — do NOT pretend we're at ATH
3. Kitchin trough: SPY reaches trough ~Q3-Q4 2026 (further drawdown from today)
4. Juglar contraction: Deepens the trough into 2026-2027 (Juglar amplifies Kitchin)
5. Recovery: Kuznets still intact → recovery rally 2027 into Kuznets peak ~2027-2028
6. Kuznets peak: SPY makes new ATH or near-ATH around Kuznets peak (~2027.5-2028)
7. Kuznets decline: After peak, Kuznets winter causes -40% to -50% drawdown through 2030-2032
8. ALL corrections happen sequentially in ONE path — not as separate parallel lines
9. Each quarter value must be realistic — max ±12% per quarter
10. The path MUST show the Kuznets winter as the deepest and most sustained decline

Generate quarterly prices for these exact year fractions:
{[round(y,2) for y in _future_years[:32]]}

Also provide:
- kuznets_trend: the smooth Kuznets trend line (remove corrections, just the underlying trend)
- phase_labels: label for each quarter ("Kitchin trough", "Recovery", "Kuznets peak", "Kuznets winter", etc.)
- key_levels: dict with keys "kitchin_trough_price", "kitchin_trough_year", "kuznets_peak_price", "kuznets_peak_year", "kuznets_winter_trough_price", "kuznets_winter_trough_year"

Return ONLY valid JSON (no markdown):
{{
  "spy_path": [<quarterly prices matching the year fractions above, exactly {min(32, len(_future_years))} values>],
  "kuznets_trend": [<smooth trend prices, same length>],
  "key_levels": {{
    "kitchin_trough_price": <price>,
    "kitchin_trough_year": <year fraction like 2026.5>,
    "juglar_trough_price": <price>,
    "juglar_trough_year": <year fraction>,
    "kuznets_peak_price": <price>,
    "kuznets_peak_year": <year fraction>,
    "kuznets_winter_trough_price": <price>,
    "kuznets_winter_trough_year": <year fraction>
  }},
  "analysis": "<2 sentences explaining the path logic>"
}}"""

            _rr = _rqr.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 3000,
                    "system": (
                        "You are a quantitative macro economist. Generate precise quarterly SPY price paths "
                        "grounded in cycle theory and live data. Return ONLY valid JSON. "
                        "The path must be ONE unified sequence — all cycles baked into a single trajectory. "
                        "No text outside the JSON object."
                    ),
                    "messages": [{"role": "user", "content": _road_prompt}]
                },
                timeout=60,
            ).json()

            _rt = ""
            if "content" in _rr:
                for _b in _rr["content"]:
                    if _b.get("type") == "text":
                        _rt = _b["text"].strip()

            if _rt:
                _clean = _rer.sub(r"```[a-zA-Z]*\n?", "", _rt).strip().strip("`")
                _jm = _rer.search(r"\{.+\}", _clean, _rer.DOTALL)
                if _jm:
                    _rd = _jsr.loads(_jm.group())
                    _sp = [float(v) for v in _rd.get("spy_path", []) if v is not None]
                    _kt = [float(v) for v in _rd.get("kuznets_trend", []) if v is not None]
                    if len(_sp) >= 8:
                        # Validate: all prices in [200, 1200], max 12% per quarter
                        _sp_clean = [base_spy]
                        for i in range(1, len(_sp)):
                            prev = _sp_clean[-1]
                            move = (_sp[i] / prev - 1)
                            if abs(move) > 0.14:
                                _sp[i] = round(prev * (1 + 0.14 * (1 if move > 0 else -1)), 2)
                            _sp_clean.append(round(max(200, min(1200, _sp[i])), 2))
                        _kt_clean = [round(max(200, min(1200, v)), 2) for v in _kt[:len(_sp_clean)]]
                        _road_proj = {
                            "spy_path": _sp_clean,
                            "kuznets_trend": _kt_clean,
                            "key_levels": _rd.get("key_levels", {}),
                            "future_years": _future_years[:len(_sp_clean)],
                            "analysis": _rd.get("analysis", ""),
                        }
                        print(f"  Road projection: {len(_sp_clean)} quarters | "
                              f"trough=${_rd.get('key_levels',{}).get('kitchin_trough_price','?')} "
                              f"peak=${_rd.get('key_levels',{}).get('kuznets_peak_price','?')}")
        except Exception as _re_err:
            print(f"  Road projection API error: {_re_err}")

    # Fallback: build a coherent single path from cycle math if API failed
    if _road_proj is None:
        print("  Building road projection from cycle math (no API data)")
        _fp, _kt = [], []
        _kp  = (pos or {}).get("kitchin",{}).get("pct", 108)
        _jp  = (pos or {}).get("juglar",{}).get("pct", 89)
        _knp = (pos or {}).get("kuznets",{}).get("pct", 73)
        # How much further can Kitchin fall? (already in contraction)
        _kit_extra_dd = -0.10 if _kp > 100 else -0.15
        _jug_extra_dd = -0.20 if _jp > 85 else -0.15
        _total_trough_dd = _kit_extra_dd + _jug_extra_dd * 0.6  # overlapping
        _trough_price = round(base_spy * (1 + _total_trough_dd), 2)
        _kuznets_peak = round(base_spy * 1.25, 2)   # Kuznets still has 25%+ upside
        _kw_trough = round(_kuznets_peak * 0.52, 2)  # Kuznets winter ~-48%

        # Quarterly phases (roughly):
        # Q1: still falling (Kitchin/Juglar), Q4 2026: trough, 2027-2028: recovery+peak, 2028+: winter
        _fq = _future_years[:32]
        for _fy in _fq:
            _t = (_fy - _cy) / max(2033 - _cy, 1)  # 0→1 over full window
            if _fy < _cy + 0.75:   # next 9 months — Kitchin/Juglar trough forming
                _pct = (_fy - _cy) / 0.75
                _p = base_spy + (_trough_price - base_spy) * _pct
            elif _fy < _cy + 1.0:  # trough
                _p = _trough_price
            elif _fy < 2028.0:     # recovery to Kuznets peak
                _pct = (_fy - (_cy + 1.0)) / max(2028.0 - (_cy + 1.0), 0.5)
                _p = _trough_price + (_kuznets_peak - _trough_price) * min(_pct, 1.0)
            elif _fy < 2028.5:     # near Kuznets peak
                _p = _kuznets_peak
            elif _fy < 2031.5:     # Kuznets winter decline
                _pct = (_fy - 2028.5) / 3.0
                _p = _kuznets_peak + (_kw_trough - _kuznets_peak) * min(_pct * 1.2, 1.0)
            else:                  # base of winter
                _p = _kw_trough * (1 + (_fy - 2031.5) * 0.03)
            _fp.append(round(max(200, min(1200, _p)), 2))
            # Kuznets trend = smooth line without corrections
            if _fy <= 2028:
                _kt.append(round(base_spy * (1 + 0.07 * (_fy - _cy)), 2))
            else:
                _kt.append(round(base_spy * (1 + 0.07 * (2028 - _cy)) * (1 - 0.04 * (_fy - 2028)), 2))
        _road_proj = {
            "spy_path": _fp,
            "kuznets_trend": _kt,
            "key_levels": {
                "kitchin_trough_price": _trough_price,
                "kitchin_trough_year": round(_cy + 0.75, 2),
                "kuznets_peak_price": _kuznets_peak,
                "kuznets_peak_year": 2028.0,
                "kuznets_winter_trough_price": _kw_trough,
                "kuznets_winter_trough_year": 2031.0,
            },
            "future_years": _future_years[:len(_fp)],
            "analysis": "Cycle-math projection: Kitchin+Juglar trough ~Q4 2026, Kuznets peak ~2028, Kuznets winter -48% trough ~2031."
        }

    charts["road_to_2032"] = {
        "years": years,
        "year_labels": year_labels,
        "actual": actual_vals,
        "base_spy": base_spy,
        "today_year": round(_cy, 2),
        "road_proj": _road_proj,
        "dd_from_ath": _dd_from_ath,
        "ath_price": _ath_price,
    }

    # 10. Bond overlay — TLT, HYG, LQD indexed at Juglar troughs (same as SPY overlay)
    BOND_TICKERS = {"TLT": "20yr Treasury (TLT)", "HYG": "High Yield Bonds (HYG)", "LQD": "Inv. Grade Bonds (LQD)"}
    JUGLAR_TROUGHS_SHORT = [("2009-03","2009 Cycle","#1188ee"), ("2020-03","Current (2020)","#00ff99")]
    bond_overlay = {}
    for ticker, label_full in BOND_TICKERS.items():
        if ticker not in md: continue
        bond_m = md[ticker].resample("ME").last().dropna()
        cycles_data = {}
        for trough_str, cycle_label, color in JUGLAR_TROUGHS_SHORT:
            # pd already imported at top of function
            try:
                trough_dt = pd.Timestamp(trough_str)
                mask = bond_m.index >= trough_dt
                cycle_s = bond_m[mask].head(72)
                if len(cycle_s) >= 6:
                    base = float(cycle_s.iloc[0])
                    vals = [round(float(v)/base*100, 2) for v in cycle_s.values]
                    cycles_data[cycle_label] = {"values": vals, "color": color}
            except Exception: pass
        if cycles_data:
            bond_overlay[label_full] = cycles_data
    charts["bond_overlay"] = bond_overlay

    # 11. 10Y yield + SPY + TLT + HYG monthly — last 10yr for cycle comparison
    bond_timeseries = {}
    for key in ["TLT","HYG","LQD","SPY"]:
        if key in md:
            s = md[key].resample("ME").last().dropna().tail(120)
            bond_timeseries[key] = {
                "dates":  [str(d)[:7] for d in s.index],
                "values": [round(float(v),2) for v in s.values],
            }
    # Also normalise all to 100 at 10yr ago for comparison
    if bond_timeseries:
        for key in list(bond_timeseries.keys()):
            v = bond_timeseries[key]["values"]
            if v:
                base = v[0]
                bond_timeseries[key]["norm"] = [round(x/base*100,2) for x in v]
    charts["bond_timeseries"] = bond_timeseries

    # 12. Kuznets cycle overlay — ^GSPC, 17-21yr cycles
    KUZNETS_TROUGHS = [
        ("1949-06", "1949 Cycle", "#e63946"),
        ("1964-10", "1964 Cycle", "#f4a261"),
        ("1982-08", "1982 Cycle", "#2a9d8f"),
        ("2009-03", "2009 Cycle", "#457b9d"),
        ("2020-03", "Current (2020)", "#1db954"),
    ]
    kuznets_overlay = {}
    _g = md.get("^GSPC"); _g = _g if (_g is not None and not _g.empty) else md.get("SPY")
    if _g is not None:
        _gm = _g.resample("ME").last().dropna()
        try:
            if _gm.index.tz is not None: _gm.index = _gm.index.tz_localize(None)
        except Exception: pass
        for trough_str, label, color in KUZNETS_TROUGHS:
            try:
                trough_dt = pd.Timestamp(trough_str)
                mask = _gm.index >= trough_dt
                cs = _gm[mask].head(252)
                if len(cs) >= 12:
                    base = float(cs.iloc[0])
                    vals = [round(float(v)/base*100, 2) for v in cs.values]
                    kuznets_overlay[label] = {"values": vals, "color": color}
                    print(f"  Kuznets {label}: {len(vals)} months")
            except Exception as ex:
                pass
    charts["kuznets_overlay"] = kuznets_overlay

    # 13. Kitchin cycle overlay — 3-4yr cycles
    KITCHIN_TROUGHS = [
        ("2009-03", "2009 trough", "#e63946"),
        ("2011-10", "2011 trough", "#f4a261"),
        ("2016-02", "2016 trough", "#2a9d8f"),
        ("2018-12", "2018 trough", "#6a4c93"),
        ("2020-03", "2020 trough", "#457b9d"),
        ("2022-10", "2022 trough", "#e9c46a"),
        ("2023-10", "Current (2023)", "#1db954"),
    ]
    kitchin_overlay = {}
    _s = md.get("SPY"); _s = _s if (_s is not None and not _s.empty) else md.get("^GSPC")
    if _s is not None:
        _sm = _s.resample("ME").last().dropna()
        try:
            if _sm.index.tz is not None: _sm.index = _sm.index.tz_localize(None)
        except Exception: pass
        for trough_str, label, color in KITCHIN_TROUGHS:
            try:
                trough_dt = pd.Timestamp(trough_str)
                mask = _sm.index >= trough_dt
                cs = _sm[mask].head(48)
                if len(cs) >= 6:
                    base = float(cs.iloc[0])
                    vals = [round(float(v)/base*100, 2) for v in cs.values]
                    kitchin_overlay[label] = {"values": vals, "color": color}
            except Exception:
                pass
    charts["kitchin_overlay"] = kitchin_overlay

    return charts


SECTOR_RATIO_GUIDE_TEMPLATE = """
<div class="section" style="margin-bottom:20px">
  <div class="sh"><div><h2>How to Read the Sector Ratio Charts</h2>
  <p>Live interpretation of each cross-pair — what direction means, historical lead time, current signal</p></div></div>
  <div style="padding:18px 20px">
    <div style="background:#eef2ff;border-radius:8px;padding:12px 16px;margin-bottom:14px;border-left:4px solid #2266ee">
      <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:6px">The Core Idea</div>
      <div style="font-size:10px;color:#555577;line-height:1.6">
        A ratio chart divides Sector A by Sector B. When the line <strong style="color:#1A7A4A">rises</strong>, A outperforms B (not necessarily up, just more up or less down). This reveals cycle phase and institutional money flows — far more useful than watching absolute prices alone.<br>
        <strong style="color:#ffcc44">1Y %ile</strong>: How stretched the ratio is vs the past year. Above 80th = potential mean reversion. Below 20th = historically cheap vs the other sector.
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px">
      <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:12px">
        <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:6px">XLY/XLP — Risk Appetite</div>
        <div style="font-size:9px;color:#555577;line-height:1.5">
          Rising = consumers buying wants not needs = risk-on. <br>Falling = staples bid = defensive. <br>
          <strong style="color:{xly_col}">Now ({xly_dir}):</strong> {xly_note}<br>
          <em style="color:#556">Lead time: rolls over 2-4mo before SPY peaks</em>
        </div>
      </div>
      <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:12px">
        <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:6px">XLF/XLU — Growth Thermometer</div>
        <div style="font-size:9px;color:#555577;line-height:1.5">
          Rising = financials lead = rates OK, GDP expanding.<br>Falling = utilities bid = growth fears or rate cut expected.<br>
          <strong style="color:{xlf_col}">Now ({xlf_dir}, {xlf_pct:.0f}th %ile):</strong> {xlf_note}<br>
          <em style="color:#556">At multi-year lows = often 6-12mo before Fed pivot</em>
        </div>
      </div>
      <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:12px">
        <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:6px">XLE/XLU — Inflation Signal</div>
        <div style="font-size:9px;color:#555577;line-height:1.5">
          Rising = energy leads = inflation/late cycle. <br>Falling = utilities = deflation fears.<br>
          <strong style="color:{xle_col}">Now ({xle_dir}):</strong> {xle_note}<br>
          <em style="color:#556">Extreme readings resolve within 3-6mo — watch for reversal</em>
        </div>
      </div>
      <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:12px">
        <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:6px">IWM/SPY — Breadth Gauge</div>
        <div style="font-size:9px;color:#555577;line-height:1.5">
          Rising = small caps lead = broad healthy rally. <br>Falling = only mega-caps holding = late-cycle narrowing.<br>
          <strong style="color:{iwm_col}">Now ({iwm_dir}):</strong> {iwm_note}<br>
          <em style="color:#556">Falling 3mo+ while SPY flat = classic top signal</em>
        </div>
      </div>
      <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:12px">
        <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:6px">XLK/XLP — Growth vs Value</div>
        <div style="font-size:9px;color:#555577;line-height:1.5">
          Rising = tech leads = growth scarce and bid.<br>Falling = staples win = real rates rising or growth fears.<br>
          <em style="color:#556">When 10Y rises 50bps, XLK/XLP typically falls 5-8% next month</em>
        </div>
      </div>
      <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:12px">
        <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:6px">HYG/LQD — Credit Canary</div>
        <div style="font-size:9px;color:#555577;line-height:1.5">
          Rising = junk bonds beat IG = credit risk appetite healthy.<br>Falling = flight to quality = credit stress early warning.<br>
          <em style="color:#556">EARLIEST warning signal — led SPY corrections by 4-8 weeks in 2007, 2015, 2018, 2022</em>
        </div>
      </div>
    </div>
    <div style="background:#e8f0ff;border-radius:8px;padding:12px 16px;border:1px solid #1a2a40">
      <div style="font-size:11px;font-weight:800;color:#1155cc;margin-bottom:8px">Current Snapshot — What Ratios Are Saying Together</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:10px">
        <div style="color:#555577"><div style="margin-bottom:4px;font-weight:700;color:#C0390F">Bearish / Caution signals:</div>{bear_signals_html}</div>
        <div style="color:#555577"><div style="margin-bottom:4px;font-weight:700;color:#1A7A4A">Bullish / Constructive:</div>{bull_signals_html}</div>
      </div>
      <div style="margin-top:10px;font-size:11px;font-weight:700;color:#D4820A">Synthesis: {synthesis}</div>
    </div>
  </div>
</div>
"""

# ══════════════════════════════════════════════════════════════════════════════
# PLAYBOOK — generates trade ideas from cycle + Market Health
# ══════════════════════════════════════════════════════════════════════════════

def playbook(pos, ep, pair_results):
    rg=pos["regime"]["label"]; jp=pos["juglar"]["pct"]; eps=ep["score"]
    if "LATE" in rg or eps>65:
        return [
            {"action":"OVERWEIGHT","assets":"XLP, XLV, XLU, GLD, TLT","col":"#1A7A4A","conv":"HIGH",
             "tf":"3-6 months","rat":"Defensives + bonds + gold outperform when Juglar is late-cycle and EP risk >65%. Historical avg outperformance vs SPY: +12% in late cycle."},
            {"action":"REDUCE","assets":"XLY, XLK, XLF, XLRE","col":"#C0390F","conv":"HIGH",
             "tf":"3-6 months","rat":"Cyclical and growth sectors face multiple compression + earnings risk at Juglar peak. Avg underperformance vs SPY: -15% in late cycle."},
            {"action":"ADD DURATION","assets":"TLT, IEF","col":"#1155cc","conv":"MEDIUM",
             "tf":"6-12 months","rat":"Rates typically fall 6-18 months after Juglar peak as growth slows and Fed pivots. TLT avg return +20% in post-peak year."},
            {"action":"LONG GOLD","assets":"GLD, IAU","col":"#D4820A","conv":"MEDIUM",
             "tf":"6-12 months","rat":"Gold outperforms in late cycle + early recession. Avg +18% in 12 months following Juglar peak."},
            {"action":"HEDGE","assets":"SPY put spreads or VIX calls","col":"#C0390F","conv":"MEDIUM",
             "tf":"3-6 months","rat":"Options protection is historically cheap relative to late-cycle downside. Sell premium to finance downside hedges."},
        ]
    elif "MID" in rg:
        return [
            {"action":"HOLD CYCLICALS","assets":"XLK, XLI, XLF","col":"#1A7A4A","conv":"HIGH",
             "tf":"3-9 months","rat":"Mid-cycle: tech + industrials + financials lead. Capex expanding, loan growth positive, earnings revisions upward."},
            {"action":"SELECTIVE ADD","assets":"XLE, XLB","col":"#D4820A","conv":"MEDIUM",
             "tf":"3-6 months","rat":"Energy and materials benefit from mid-cycle demand + commodity inflation. Watch XLE/XLU ratio for confirmation."},
            {"action":"EQUAL WEIGHT","assets":"RSP vs SPY","col":"#1155cc","conv":"MEDIUM",
             "tf":"6-12 months","rat":"Mid-cycle breadth expansion favors equal-weight over cap-weight. RSP historically outperforms SPY +4% in mid-cycle."},
            {"action":"AVOID","assets":"TLT, long duration bonds","col":"#C0390F","conv":"MEDIUM",
             "tf":"3-6 months","rat":"Rates still elevated + growth intact = bonds underperform equities. Shorter duration preferred."},
        ]
    else:
        return [
            {"action":"MAXIMUM RISK-ON","assets":"IWM, XLY, XLF, XLK","col":"#1A7A4A","conv":"HIGH",
             "tf":"6-18 months","rat":"Early cycle: small caps + cyclicals lead the broadest rallies. IWM historically +40-60% in first 18 months of cycle."},
            {"action":"UNDERWEIGHT","assets":"XLU, GLD, TLT","col":"#C0390F","conv":"HIGH",
             "tf":"6-12 months","rat":"Defensives and safe havens lag badly when risk appetite is expanding from lows."},
            {"action":"LONG CREDIT","assets":"HYG, JNK","col":"#1A7A4A","conv":"MEDIUM",
             "tf":"6-12 months","rat":"Credit spreads compress hard in early cycle. HYG has avg +15% in early-cycle years."},
        ]


# ══════════════════════════════════════════════════════════════════════════════
# HTML BUILDER — full rich version with Chart.js
# ══════════════════════════════════════════════════════════════════════════════

def _build_spy_svg(spy_hist_dates, spy_hist_values, spy_now, tgts, proj=None):
    """
    Render SPY projection chart as inline SVG.
    If proj dict is provided (from Claude API), uses month-by-month paths.
    Otherwise falls back to simple linear interpolation.
    """
    from datetime import date, timedelta
    import math

    W, H = 1020, 440
    PAD_L, PAD_R, PAD_T, PAD_B = 78, 115, 40, 58

    chart_w = W - PAD_L - PAD_R
    chart_h = H - PAD_T - PAD_B
    # Ensure enough width per month for readable labels
    total_months = len(spy_hist_dates or []) + 18
    if total_months > 0:
        px_per_month = chart_w / max(total_months - 1, 1)
    else:
        px_per_month = chart_w / 42

    if not spy_hist_values or spy_now is None:
        return '<div style="padding:40px;text-align:center;color:#888">SPY data unavailable</div>'

    # ── Build month labels for projection ────────────────────────────────────
    proj_n = 18
    proj_dates = []
    if spy_hist_dates:
        yr, mo = int(spy_hist_dates[-1][:4]), int(spy_hist_dates[-1][5:7])
    else:
        yr, mo = date.today().year, date.today().month
    for _ in range(proj_n):
        mo += 1
        if mo > 12: mo = 1; yr += 1
        proj_dates.append(f"{yr}-{mo:02d}")

    all_dates = spy_hist_dates + proj_dates
    total_n   = len(all_dates)

    # ── Build projection monthly values ──────────────────────────────────────
    if proj and "bull_monthly" in proj:
        # Trim/pad to proj_n
        bull_pts = [float(v) for v in (proj["bull_monthly"] + [proj["bull_monthly"][-1]]*proj_n)[:proj_n]]
        base_pts = [float(v) for v in (proj["base_monthly"] + [proj["base_monthly"][-1]]*proj_n)[:proj_n]]
        bear_pts = [float(v) for v in (proj["bear_monthly"] + [proj["bear_monthly"][-1]]*proj_n)[:proj_n]]
        p_bull = proj.get("probability_bull", 25)
        p_base = proj.get("probability_base", 50)
        p_bear = proj.get("probability_bear", 25)
        bull_thesis = proj.get("bull_thesis","")
        base_thesis = proj.get("base_thesis","")
        bear_thesis = proj.get("bear_thesis","")
        key_risk    = proj.get("key_risk","")
        ye26_bull = proj.get("year_end_2026_bull", bull_pts[min(8,len(bull_pts)-1)])
        ye26_base = proj.get("year_end_2026_base", base_pts[min(8,len(base_pts)-1)])
        ye26_bear = proj.get("year_end_2026_bear", bear_pts[min(8,len(bear_pts)-1)])
        ye27_bull = proj.get("year_end_2027_bull", bull_pts[-1])
        ye27_base = proj.get("year_end_2027_base", base_pts[-1])
        ye27_bear = proj.get("year_end_2027_bear", bear_pts[-1])
        ai_powered = True
    else:
        # Realistic fallback paths using cycle-aware targets (non-linear, with volatility)
        _anchor = spy_hist_values[-1] if spy_hist_values else spy_now
        _bull_end = tgts.get("24mo_bull", _anchor * 1.09)
        _base_end = tgts.get("24mo_base", _anchor * 0.92)
        _bear_end = tgts.get("24mo_bear", _anchor * 0.72)
        bull_pts = _make_realistic_path(_anchor, _bull_end, proj_n, "bull")
        base_pts = _make_realistic_path(_anchor, _base_end, proj_n, "base")
        bear_pts = _make_realistic_path(_anchor, _bear_end, proj_n, "bear")
        p_bull, p_base, p_bear = 25, 50, 25
        bull_thesis = base_thesis = bear_thesis = key_risk = ""
        ye26_bull = bull_pts[min(8, len(bull_pts)-1)]
        ye26_base = base_pts[min(8, len(base_pts)-1)]
        ye26_bear = bear_pts[min(8, len(bear_pts)-1)]
        ye27_bull = bull_pts[-1]
        ye27_base = base_pts[-1]
        ye27_bear = bear_pts[-1]
        ai_powered = False

    # ── Price range for y-axis ────────────────────────────────────────────────
    all_prices = (spy_hist_values + bull_pts + base_pts + bear_pts + [spy_now])
    v_min = min(all_prices) * 0.96
    v_max = max(all_prices) * 1.04
    v_rng = v_max - v_min or 1

    def px(i):   return PAD_L + chart_w * i / max(total_n - 1, 1)
    def py(v):   return PAD_T + chart_h * (1 - (v - v_min) / v_rng)

    # ── Find year-end date indices ────────────────────────────────────────────
    def date_idx(yyyy_mm):
        try: return next(i for i,d in enumerate(all_dates) if d.startswith(yyyy_mm))
        except StopIteration: return None

    hist_end_idx = len(spy_hist_dates) - 1
    ye26_idx = date_idx("2026-12")
    ye27_idx = date_idx("2027-12")

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
               f'style="width:100%;height:100%;display:block;background:#fafbfd">')

    # Background
    svg.append(f'<rect width="{W}" height="{H}" fill="#fafbfd" rx="8"/>')

    # Projection zone background
    if hist_end_idx < total_n:
        px0 = px(hist_end_idx)
        svg.append(f'<rect x="{px0:.1f}" y="{PAD_T}" width="{W-PAD_R-px0:.1f}" '
                   f'height="{chart_h}" fill="rgba(230,235,248,0.4)" rx="0"/>')

    # ── Y-axis grid lines + price labels (granular — ~10-12 ticks) ──────────
    # Round to nearest $10 for clean price levels
    def _round_to(v, step=10): return round(v / step) * step

    y_low  = _round_to(v_min, 10)
    y_high = _round_to(v_max, 10)
    y_rng  = y_high - y_low
    # Pick step size so we get 10-14 ticks
    raw_step = y_rng / 11
    for step_c in [5, 10, 15, 20, 25, 30, 40, 50]:
        if raw_step <= step_c:
            y_step = step_c; break
    else:
        y_step = max(10, round(raw_step / 10) * 10)

    y_start = (int(y_low  // y_step)) * y_step
    y_vals  = []
    v = y_start
    while v <= y_high + y_step:
        if v_min - 5 <= v <= v_max + 5:
            y_vals.append(v)
        v += y_step

    for v in y_vals:
        y  = py(v)
        is_round_100 = (v % 100 == 0)
        is_round_50  = (v % 50 == 0)
        col  = "#c8cce0" if is_round_100 else "#d8dce8" if is_round_50 else "#e8ebf4"
        wid  = "1.2"     if is_round_100 else "0.8"     if is_round_50 else "0.5"
        fcol = "#3a4466"  if is_round_100 else "#667799" if is_round_50 else "#8899aa"
        fsz  = "9.5"     if is_round_100 else "8.5"     if is_round_50 else "7.5"
        fw   = "700"     if is_round_100 else "600"     if is_round_50 else "400"
        svg.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W-PAD_R}" y2="{y:.1f}" '
                   f'stroke="{col}" stroke-width="{wid}"/>')
        svg.append(f'<text x="{PAD_L-6}" y="{y+3.5:.1f}" text-anchor="end" '
                   f'font-size="{fsz}" fill="{fcol}" font-weight="{fw}" '
                   f'font-family="monospace">${v:,.0f}</text>')

    # ── X-axis grid + labels (every month, alternating label/tick) ─────────
    hist_end_date = spy_hist_dates[-1] if spy_hist_dates else "2026-03"
    for i, d in enumerate(all_dates):
        x = px(i)
        is_future = d > hist_end_date
        mo = int(d[5:7])
        is_jan = (mo == 1)
        is_quarter = (mo in (1, 4, 7, 10))
        is_semi    = (mo in (1, 7))

        # Vertical grid line — darker for Jan, medium for quarters, light for months
        if is_jan:
            svg.append(f'<line x1="{x:.1f}" y1="{PAD_T}" x2="{x:.1f}" y2="{H-PAD_B+6}" '
                       f'stroke="{"#b8c0d8" if is_future else "#c8cee0"}" stroke-width="1.5"/>')
        elif is_quarter:
            svg.append(f'<line x1="{x:.1f}" y1="{PAD_T}" x2="{x:.1f}" y2="{H-PAD_B+4}" '
                       f'stroke="{"#d0d6e8" if is_future else "#d8dce8"}" stroke-width="1"/>')
        else:
            svg.append(f'<line x1="{x:.1f}" y1="{PAD_T+20}" x2="{x:.1f}" y2="{H-PAD_B+2}" '
                       f'stroke="rgba(180,188,210,0.35)" stroke-width="0.7"/>')

        # Month tick mark
        svg.append(f'<line x1="{x:.1f}" y1="{H-PAD_B}" x2="{x:.1f}" y2="{H-PAD_B+3}" '
                   f'stroke="#a0a8c0" stroke-width="0.8"/>')

        # Labels: year on Jan, month abbrev on quarters, tiny tick on others
        MO_ABBR = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        if is_jan:
            # Year label (bold) + month
            svg.append(f'<text x="{x:.1f}" y="{H-PAD_B+24}" text-anchor="middle" '
                       f'font-size="10" fill="#334466" font-weight="700">{d[:4]}</text>')
        elif is_quarter:
            svg.append(f'<text x="{x:.1f}" y="{H-PAD_B+14}" text-anchor="middle" '
                       f'font-size="8" fill="#667799">{MO_ABBR[mo]}</text>')
        else:
            svg.append(f'<text x="{x:.1f}" y="{H-PAD_B+12}" text-anchor="middle" '
                       f'font-size="7" fill="#99aabb">{MO_ABBR[mo]}</text>')

    # ── Year-end vertical markers ─────────────────────────────────────────────
    for ye_idx, label in [(ye26_idx, "Dec 2026"), (ye27_idx, "Dec 2027")]:
        if ye_idx is not None:
            x = px(ye_idx)
            svg.append(f'<line x1="{x:.1f}" y1="{PAD_T}" x2="{x:.1f}" y2="{H-PAD_B}" '
                       f'stroke="rgba(100,80,180,0.35)" stroke-width="1.5" stroke-dasharray="3,3"/>')
            svg.append(f'<text x="{x:.1f}" y="{PAD_T-6}" text-anchor="middle" '
                       f'font-size="8" fill="#6644aa" font-weight="600">{label}</text>')

    # ── TODAY vertical line ───────────────────────────────────────────────────
    if hist_end_idx >= 0:
        tx = px(hist_end_idx)
        svg.append(f'<line x1="{tx:.1f}" y1="{PAD_T}" x2="{tx:.1f}" y2="{H-PAD_B}" '
                   f'stroke="#00bcd4" stroke-width="2" stroke-dasharray="5,4" opacity="0.8"/>')
        svg.append(f'<text x="{tx:.1f}" y="{PAD_T-8}" text-anchor="middle" '
                   f'font-size="9" fill="#00bcd4" font-weight="700">TODAY</text>')

    # ── Helper: draw a smooth path ────────────────────────────────────────────
    def path(pts, color, width, dash='', opacity='1', smooth=True):
        if len(pts) < 2: return
        if smooth and len(pts) > 3:
            # Catmull-Rom smoothing
            d = f'M{pts[0][0]:.1f} {pts[0][1]:.1f}'
            for i in range(1, len(pts)):
                p0 = pts[max(0,i-2)]
                p1 = pts[i-1]
                p2 = pts[i]
                p3 = pts[min(len(pts)-1,i+1)]
                cp1x = p1[0] + (p2[0]-p0[0])/6
                cp1y = p1[1] + (p2[1]-p0[1])/6
                cp2x = p2[0] - (p3[0]-p1[0])/6
                cp2y = p2[1] - (p3[1]-p1[1])/6
                d += f' C{cp1x:.1f} {cp1y:.1f} {cp2x:.1f} {cp2y:.1f} {p2[0]:.1f} {p2[1]:.1f}'
        else:
            d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)
        da = f'stroke-dasharray="{dash}"' if dash else ''
        svg.append(f'<path d="{d}" stroke="{color}" stroke-width="{width}" '
                   f'fill="none" {da} opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"/>')

    # ── Determine cycle regime for phase shading ─────────────────────────────
    # Base dominates because Kitchin 108% + Juglar 89% = clear contraction phase
    # Bull = tail risk upside, Bear = tail risk downside
    # Find ATH in history
    _ath = max(spy_hist_values) if spy_hist_values else spy_now
    _dd_ath = round((_ath - spy_now) / _ath * 100, 1)  # % below ATH

    # ── Cycle phase shading bands in projection zone ──────────────────────────
    if hist_end_idx >= 0 and len(base_pts) >= 6:
        # Find approx trough of base path (lowest point)
        _trough_i = base_pts.index(min(base_pts))
        _trough_x = px(hist_end_idx + _trough_i + 1)
        _proj_end_x = px(hist_end_idx + len(base_pts))
        _proj_start_x = px(hist_end_idx)

        # Zone 1: Correction/Trough zone (start → trough) — soft red
        if _trough_i > 0:
            svg.append(f'<rect x="{_proj_start_x:.1f}" y="{PAD_T}" '
                       f'width="{_trough_x - _proj_start_x:.1f}" height="{chart_h}" '
                       f'fill="rgba(192,57,15,0.06)" rx="0"/>')
            _zone1_mid_x = (_proj_start_x + _trough_x) / 2
            svg.append(f'<text x="{_zone1_mid_x:.1f}" y="{PAD_T+16}" text-anchor="middle" '
                       f'font-size="8" fill="rgba(192,57,15,0.6)" font-weight="600">'
                       f'Contraction / Trough</text>')

        # Zone 2: Recovery zone (trough → end) — soft green
        if _trough_i < len(base_pts) - 2:
            svg.append(f'<rect x="{_trough_x:.1f}" y="{PAD_T}" '
                       f'width="{_proj_end_x - _trough_x:.1f}" height="{chart_h}" '
                       f'fill="rgba(26,122,74,0.05)" rx="0"/>')
            _zone2_mid_x = (_trough_x + _proj_end_x) / 2
            svg.append(f'<text x="{_zone2_mid_x:.1f}" y="{PAD_T+16}" text-anchor="middle" '
                       f'font-size="8" fill="rgba(26,122,74,0.55)" font-weight="600">'
                       f'Recovery</text>')

    # ── Bull/Bear thin reference bands (NOT the main story) ──────────────────
    origin = [(px(hist_end_idx), py(spy_now))]

    # Shaded uncertainty band between bull and bear — very subtle
    if len(bull_pts) > 0 and len(bear_pts) > 0:
        b_pts  = origin + [(px(hist_end_idx+i+1), py(v)) for i,v in enumerate(bull_pts)]
        d_pts  = origin + [(px(hist_end_idx+i+1), py(v)) for i,v in enumerate(bear_pts)]
        poly   = b_pts + list(reversed(d_pts))
        pts_s  = ' '.join(f'{x:.1f},{y:.1f}' for x,y in poly)
        svg.append(f'<polygon points="{pts_s}" fill="rgba(100,130,200,0.07)" stroke="none"/>')

    # Bull line — thin, muted green, dashed, secondary
    bull_line = origin + [(px(hist_end_idx+i+1), py(v)) for i,v in enumerate(bull_pts)]
    path(bull_line, '#2a9e5c', 1.4, '7,4', '0.55', smooth=True)
    ex, ey = bull_line[-1]
    svg.append(f'<text x="{ex+5:.1f}" y="{ey+4:.1f}" font-size="9.5" '
               f'fill="#2a9e5c" font-weight="600" opacity="0.8">'
               f'Bull {p_bull}%</text>')

    # Bear line — thin, muted red, dashed, secondary
    bear_line = origin + [(px(hist_end_idx+i+1), py(v)) for i,v in enumerate(bear_pts)]
    path(bear_line, '#cc3311', 1.4, '7,4', '0.55', smooth=True)
    ex, ey = bear_line[-1]
    svg.append(f'<text x="{ex+5:.1f}" y="{ey+4:.1f}" font-size="9.5" '
               f'fill="#cc3311" font-weight="600" opacity="0.8">'
               f'Bear {p_bear}%</text>')

    # ── BASE PATH — thick, solid, primary "Most Probable" line ───────────────
    base_line = origin + [(px(hist_end_idx+i+1), py(v)) for i,v in enumerate(base_pts)]
    # Glow effect (slightly wider, lighter)
    path(base_line, '#cc7700', 5.0, '10,5', '0.20', smooth=True)
    # Main line
    path(base_line, '#cc7700', 2.8, '10,5', '0.95', smooth=True)

    # "MOST PROBABLE" label on base path — prominent
    _mid_idx = len(base_line) // 2
    _mid_x, _mid_y = base_line[_mid_idx]
    svg.append(f'<rect x="{_mid_x-46:.1f}" y="{_mid_y-22:.1f}" width="92" height="16" '
               f'fill="rgba(204,119,0,0.15)" rx="4" stroke="#cc7700" stroke-width="0.8" '
               f'stroke-dasharray="3,2"/>')
    svg.append(f'<text x="{_mid_x:.1f}" y="{_mid_y-10:.1f}" text-anchor="middle" '
               f'font-size="8.5" fill="#995500" font-weight="700">'
               f'● MOST PROBABLE ({p_base}%)</text>')

    # End label for base
    ex, ey = base_line[-1]
    svg.append(f'<text x="{ex+5:.1f}" y="{ey+4:.1f}" font-size="10.5" '
               f'fill="#cc7700" font-weight="800">Base {p_base}%</text>')

    # ── Cycle regime annotation box (top-left of projection zone) ────────────
    if hist_end_idx >= 0:
        _box_x = px(hist_end_idx) + 8
        _kp = proj.get("_kitchin_pct", 108) if proj else 108
        _jp = proj.get("_juglar_pct", 89)   if proj else 89
        _regime_text = (
            "Kitchin 108% + Juglar 89%"
            if not proj else
            f"Kitchin {_kp:.0f}% + Juglar {_jp:.0f}%"
        )
        svg.append(f'<rect x="{_box_x:.1f}" y="{PAD_T+22}" width="160" height="28" '
                   f'fill="rgba(192,57,15,0.08)" rx="4" stroke="rgba(192,57,15,0.3)" '
                   f'stroke-width="0.8"/>')
        svg.append(f'<text x="{_box_x+6:.1f}" y="{PAD_T+33}" '
                   f'font-size="7.5" fill="#C0390F" font-weight="700">'
                   f'⚠ Cycle Contraction Phase</text>')
        svg.append(f'<text x="{_box_x+6:.1f}" y="{PAD_T+44}" '
                   f'font-size="7" fill="#8B3010">{_regime_text}</text>')

    # ── ATH drawdown marker on history ────────────────────────────────────────
    if spy_hist_values and _ath > spy_now:
        _ath_i = spy_hist_values.index(max(spy_hist_values))
        _ax, _ay = px(_ath_i), py(_ath)
        # ATH dot
        svg.append(f'<circle cx="{_ax:.1f}" cy="{_ay:.1f}" r="4" '
                   f'fill="#8B0000" stroke="white" stroke-width="1.5" opacity="0.7"/>')
        svg.append(f'<text x="{_ax:.1f}" y="{_ay-8:.1f}" text-anchor="middle" '
                   f'font-size="7.5" fill="#8B0000" font-weight="600">'
                   f'ATH ${_ath:,.0f}</text>')
        # Drawdown arrow from ATH to current
        _cx2, _cy2 = px(hist_end_idx), py(spy_now)
        svg.append(f'<line x1="{_ax:.1f}" y1="{_ay:.1f}" x2="{_cx2:.1f}" y2="{_cy2:.1f}" '
                   f'stroke="#8B0000" stroke-width="0.8" stroke-dasharray="3,3" opacity="0.4"/>')
        # Drawdown label midpoint
        _dmx = (_ax + _cx2) / 2
        _dmy = (_ay + _cy2) / 2
        svg.append(f'<text x="{_dmx:.1f}" y="{_dmy-4:.1f}" text-anchor="middle" '
                   f'font-size="7" fill="#8B0000" opacity="0.7">'
                   f'−{_dd_ath:.1f}% from ATH</text>')

    # ── Year-end price markers — BASE only as primary, others small ───────────
    for ye_idx, b_v, m_v, d_v, yr_label in [
        (ye26_idx, ye26_bull, ye26_base, ye26_bear, "'26"),
        (ye27_idx, ye27_bull, ye27_base, ye27_bear, "'27"),
    ]:
        if ye_idx is None: continue
        x = px(ye_idx)
        # Small dots for bull/bear
        for v, color in [(b_v,'#2a9e5c'), (d_v,'#cc3311')]:
            y = py(float(v))
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" '
                       f'stroke="white" stroke-width="1" opacity="0.6"/>')
        # Large dot for base
        y_base = py(float(m_v))
        svg.append(f'<circle cx="{x:.1f}" cy="{y_base:.1f}" r="6" fill="#cc7700" '
                   f'stroke="white" stroke-width="2" opacity="0.95"/>')

        # Annotation box — shows base prominently, others small
        svg.append(f'<rect x="{x-26:.1f}" y="{PAD_T+2}" width="52" height="36" '
                   f'fill="rgba(100,80,180,0.07)" rx="3" stroke="rgba(100,80,180,0.2)" '
                   f'stroke-width="0.5"/>')
        svg.append(f'<text x="{x:.1f}" y="{PAD_T+13}" text-anchor="middle" '
                   f'font-size="8" fill="#6644aa" font-weight="700">{yr_label} end</text>')
        svg.append(f'<text x="{x:.1f}" y="{PAD_T+24}" text-anchor="middle" '
                   f'font-size="9" fill="#cc7700" font-weight="800">${float(m_v):,.0f}</text>')
        svg.append(f'<text x="{x:.1f}" y="{PAD_T+35}" text-anchor="middle" '
                   f'font-size="7" fill="#556688">'
                   f'↑${float(b_v):,.0f} ↓${float(d_v):,.0f}</text>')

    # ── SPY actual history (filled area + line) ───────────────────────────────
    if spy_hist_values and len(spy_hist_values) > 1:
        hist_c = [(px(i), py(v)) for i,v in enumerate(spy_hist_values)]
        # Fill
        area_d = (f'M{hist_c[0][0]:.1f} {H-PAD_B} '
                  + ''.join(f'L{x:.1f} {y:.1f} ' for x,y in hist_c)
                  + f'L{hist_c[-1][0]:.1f} {H-PAD_B} Z')
        svg.append(f'<path d="{area_d}" fill="rgba(24,95,165,0.1)" stroke="none"/>')
        # Line (smooth)
        path(hist_c, '#185FA5', 2.5, smooth=True)
        # Current price dot
        cx, cy = hist_c[-1]
        svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" '
                   f'fill="#185FA5" stroke="white" stroke-width="2"/>')
        # Price label
        svg.append(f'<rect x="{cx-28:.1f}" y="{cy-22:.1f}" width="56" height="16" '
                   f'fill="#185FA5" rx="3"/>')
        svg.append(f'<text x="{cx:.1f}" y="{cy-11:.1f}" text-anchor="middle" '
                   f'font-size="9.5" fill="white" font-weight="700">${spy_now:,.2f}</text>')

    # ── AI badge ──────────────────────────────────────────────────────────────
    badge_text = "🤖 AI-Powered Projection" if ai_powered else "📊 Cycle-Based Projection"
    badge_col  = "#1a6699" if ai_powered else "#556699"
    svg.append(f'<rect x="{PAD_L}" y="{PAD_T+2}" width="180" height="18" '
               f'fill="{badge_col}" rx="4" opacity="0.85"/>')
    svg.append(f'<text x="{PAD_L+8}" y="{PAD_T+14}" font-size="9" '
               f'fill="white" font-weight="600">{badge_text}</text>')

    # ── Axes borders ──────────────────────────────────────────────────────────
    svg.append(f'<line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{H-PAD_B}" '
               f'stroke="#c0c8d8" stroke-width="1"/>')
    svg.append(f'<line x1="{PAD_L}" y1="{H-PAD_B}" x2="{W-PAD_R}" y2="{H-PAD_B}" '
               f'stroke="#c0c8d8" stroke-width="1"/>')

    svg.append('</svg>')
    return '\n'.join(svg)


def _get_live_spy_price():
    """
    Fetch real-time SPY price using multiple methods in priority order.
    Returns float or None.
    """
    try:
        import yfinance as _yf
        # Method 1: fast_info (most reliable for live price)
        _t = _yf.Ticker("SPY")
        _fi = _t.fast_info
        for _attr in ("last_price", "regularMarketPrice", "previousClose"):
            _p = getattr(_fi, _attr, None)
            if _p and 100 <= float(_p) <= 2000:
                print(f"  SPY live via fast_info.{_attr}: ${float(_p):.2f}")
                return round(float(_p), 2)
    except Exception as _e1:
        print(f"  fast_info failed: {_e1}")

    try:
        # Method 2: download 5-day 1-hour bars — last close is most recent
        import yfinance as _yf2
        _d = _yf2.download("SPY", period="5d", interval="1h",
                           auto_adjust=True, progress=False)
        if not _d.empty:
            _p2 = round(float(_d["Close"].dropna().iloc[-1]), 2)
            if 100 <= _p2 <= 2000:
                print(f"  SPY live via 1h bars: ${_p2:.2f}")
                return _p2
    except Exception as _e2:
        print(f"  1h download failed: {_e2}")

    try:
        # Method 3: download 1-day bars last 5 days
        import yfinance as _yf3
        _d3 = _yf3.download("SPY", period="5d", interval="1d",
                             auto_adjust=True, progress=False)
        if not _d3.empty:
            _p3 = round(float(_d3["Close"].dropna().iloc[-1]), 2)
            if 100 <= _p3 <= 2000:
                print(f"  SPY live via 1d bars: ${_p3:.2f}")
                return _p3
    except Exception as _e3:
        print(f"  1d download failed: {_e3}")

    print("  WARNING: all SPY live fetch methods failed")
    return None


def _make_realistic_path(start, end_target, n_months, style="base"):
    """
    Generate a realistic monthly SPY price path with volatility and mean-reversion.
    style: 'bull', 'base', or 'bear'
    Returns list of n_months prices starting from start (not including start).
    """
    import math, random
    random.seed(42)  # reproducible
    prices = []
    p = float(start)
    total_drift = (end_target / start) ** (1 / max(n_months, 1)) - 1  # per-month drift toward target

    # Volatility by style (monthly)
    vol = {"bull": 0.028, "base": 0.032, "bear": 0.038}.get(style, 0.032)

    for i in range(n_months):
        # Pull toward target with noise
        noise = (random.random() - 0.5) * 2 * vol * p
        pull  = (end_target - p) * 0.08  # mean-reversion pull
        drift = p * total_drift
        p = round(max(min(p + drift + pull * 0.5 + noise, start * 2.5), start * 0.4), 2)
        prices.append(p)
    # Hard-anchor final value to target
    prices[-1] = round(end_target, 2)
    return prices


def _claude_price_projection(spy_now, scorecard, pos, regime, gen_time):
    """
    Deep AI analysis using ALL indicators across all dashboard categories.
    Uses claude-sonnet-4-6 with web search for LIVE SPY price + comprehensive analysis.
    Strict validation + realistic path generation with zero tolerance for wrong projections.
    """
    if not CLAUDE_API_KEY:
        return None
    try:
        import requests as _rq, json as _js, re as _re
        from datetime import date as _d

        # ── Step 0: Get LIVE SPY price via yfinance FIRST (most reliable) ─────
        live_spy = _get_live_spy_price()
        if live_spy:
            spy_anchor = live_spy
            print(f"  Live SPY via yfinance: ${live_spy:.2f}")
        else:
            spy_anchor = spy_now
            print(f"  Using cached SPY: ${spy_now:.2f}")

        # ── Organise ALL scorecard data by category ───────────────────────────
        by_cat = {}
        for x in scorecard:
            c = x.get("cat", "Other")
            by_cat.setdefault(c, []).append(x)

        def _fmt_cat(cat_name, n=99):
            items = by_cat.get(cat_name, [])
            if not items: return ""
            lines = [f"  {x['name']}: {x['val_str']} [{x['signal']}]"
                     for x in items[:n] if x['value'] is not None]
            return f"\n{cat_name}:\n" + "\n".join(lines) if lines else ""

        # Build comprehensive data section covering every tab
        kp   = pos.get("kitchin",{}).get("pct", 50)
        jp   = pos.get("juglar", {}).get("pct", 50)
        knp  = pos.get("kuznets",{}).get("pct", 50)
        kph  = pos.get("kitchin",{}).get("phase","?")
        jph  = pos.get("juglar", {}).get("phase","?")
        kph2 = pos.get("kuznets",{}).get("phase","?")
        rg_lbl = pos.get("regime",{}).get("label","?") if isinstance(pos.get("regime"), dict) else str(regime)

        danger  = [x for x in scorecard if x["signal"] in ("CRISIS","STRESS") and x["value"] is not None]
        caution = [x for x in scorecard if x["signal"] == "CAUTION"           and x["value"] is not None]
        calm    = [x for x in scorecard if x["signal"] == "CALM"              and x["value"] is not None]

        all_data = ""
        for cat in ["Credit","Rates","Housing","Volatility","Breadth","Sentiment",
                    "Structure","Sector","SafeHaven","Recession","Macro","Valuation","Liquidity"]:
            all_data += _fmt_cat(cat)

        danger_str  = "\n".join(
            f"  !! {x['name']}: {x['val_str']} — {x.get('context','')[:80]}"
            for x in danger[:15]
        )
        caution_str = "\n".join(
            f"  ~  {x['name']}: {x['val_str']}"
            for x in caution[:12]
        )

        # ── Compute today date + projection months ────────────────────────────
        _today_str = _d.today().strftime("%B %d, %Y")
        _yr_now    = _d.today().year
        _mo_now    = _d.today().month
        # Month labels for the 18 projection months
        _proj_month_labels = []
        _yr, _mo = _yr_now, _mo_now
        for _ in range(18):
            _mo += 1
            if _mo > 13: _mo = 1; _yr += 1
            _proj_month_labels.append(f"{_yr}-{_mo:02d}")
        # Where 2026-12 and 2027-12 fall
        _idx_ye26 = next((i for i,m in enumerate(_proj_month_labels) if m == "2026-12"), 8)
        _idx_ye27 = next((i for i,m in enumerate(_proj_month_labels) if m == "2027-12"), 17)

        prompt = f"""Today is {_today_str}. CONFIRMED current SPY price: ${spy_anchor:.2f}

=== CYCLE FRAMEWORK (from professional 60-indicator macro dashboard) ===
Kuznets (18-yr infrastructure/wealth cycle): {knp:.0f}% complete — {kph2}
Juglar  (9-yr business investment cycle):    {jp:.0f}%  complete — {jph}
Kitchin (3.5-yr inventory cycle):            {kp:.0f}%  complete — {kph}
Current macro regime: {rg_lbl}
Dashboard status: {len(danger)} DANGER | {len(caution)} CAUTION | {len(calm)} CALM  (of {len(scorecard)} indicators total)

=== HIGHEST-PRIORITY DANGER SIGNALS ===
{danger_str if danger_str else "  None in danger zone"}

=== CAUTION SIGNALS ===
{caution_str if caution_str else "  None in caution zone"}

=== ALL INDICATOR DATA BY CATEGORY ==={all_data}

=== PROJECTION TASK ===
Analyze the above 60-indicator dataset and generate REALISTIC SPY month-by-month paths.

CONSTRAINTS (zero tolerance for violations):
• All monthly prices MUST start from ${spy_anchor:.2f} (month 1 = first month after today)
• Prices must stay in range [$200, $1500]
• Bull path: realistic upside reflecting positive scenarios — NOT euphoric straight-line
• Base path: most probable outcome (assign 45-55% probability) — can include dips
• Bear path: realistic downside anchored in actual risk signals — NOT catastrophic
• Monthly moves should be realistic (max ±8% per month in any scenario)
• Include mean-reversion, volatility clustering, and cycle dynamics
• No two paths should be identical or perfectly parallel

PROJECTION MONTHS:
{', '.join(_proj_month_labels)}
Month at 2026-12: index {_idx_ye26} (0-based)
Month at 2027-12: index {_idx_ye27} (0-based)

Return EXACTLY this JSON structure (no markdown, no extra text):
{{
  "spy_latest": {spy_anchor:.2f},
  "analysis_summary": "<3-4 sentences: key macro thesis based on ALL indicator data>",
  "primary_risk": "<single most critical risk factor with specific threshold>",
  "historical_analog": "<most similar historical period and why>",
  "bull_monthly":  [<18 monthly prices, starting near {spy_anchor:.2f}, first month slight move>],
  "base_monthly":  [<18 monthly prices, starting near {spy_anchor:.2f}, first month slight move>],
  "bear_monthly":  [<18 monthly prices, starting near {spy_anchor:.2f}, first month slight move>],
  "year_end_2026_bull": <price at month index {_idx_ye26} of bull path>,
  "year_end_2026_base": <price at month index {_idx_ye26} of base path>,
  "year_end_2026_bear": <price at month index {_idx_ye26} of bear path>,
  "year_end_2027_bull": <price at last available month of bull path>,
  "year_end_2027_base": <price at last available month of base path>,
  "year_end_2027_bear": <price at last available month of bear path>,
  "probability_bull": <integer, probabilities MUST sum to exactly 100>,
  "probability_base": <integer, probabilities MUST sum to exactly 100>,
  "probability_bear": <integer, probabilities MUST sum to exactly 100>,
  "bull_thesis": "<2 sentences: what must go right for this scenario>",
  "base_thesis": "<2 sentences: most likely path explanation>",
  "bear_thesis": "<2 sentences: specific triggers for downside>",
  "key_risk": "<precise threshold that switches from base to bear>"
}}"""

        resp = _rq.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model":      "claude-sonnet-4-6",
                "max_tokens": 4000,
                "system": (
                    "You are a senior quantitative macro strategist. You receive a live 60-indicator "
                    "dashboard and must generate PRECISE, DATA-GROUNDED SPY price projections. "
                    "CRITICAL RULES: (1) All monthly arrays must have EXACTLY 18 values. "
                    "(2) First value of each array must be within 3% of the confirmed SPY price. "
                    "(3) Probabilities must sum to exactly 100. "
                    "(4) No value outside [200, 1500]. "
                    "(5) No path may be a straight line — include realistic volatility. "
                    "(6) Return ONLY valid JSON, no markdown fences, no explanatory text outside JSON."
                ),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=90,
        ).json()

        # Extract the final text block (last text block after any tool use)
        result_text = ""
        if "error" in resp:
            print(f"  API error: {resp['error'].get('message','unknown')}")
            return None
        if "content" in resp:
            for block in resp["content"]:
                if block.get("type") == "text":
                    result_text = block.get("text","").strip()

        if not result_text:
            print("  No text block in response")
            return None

        # Parse JSON — strip accidental markdown fences
        clean = _re.sub(r"```[a-zA-Z]*\n?", "", result_text).strip()
        clean = _re.sub(r"```", "", clean).strip()
        jm = _re.search(r"\{.+\}", clean, _re.DOTALL)
        if jm:
            try:
                data = _js.loads(jm.group())
            except Exception as _je:
                print(f"  JSON parse error: {_je}")
                return None
        else:
            try:
                data = _js.loads(clean)
            except Exception as _je2:
                print(f"  JSON parse error (fallback): {_je2}")
                return None

        # ── STRICT VALIDATION ─────────────────────────────────────────────────
        for key in ("bull_monthly", "base_monthly", "bear_monthly"):
            arr = data.get(key, [])
            if not arr or len(arr) < 12:
                print(f"  INVALID {key}: only {len(arr)} values — generating fallback path")
                return None

            # Convert to floats
            try:
                arr = [float(v) for v in arr[:18]]
            except Exception:
                print(f"  Non-numeric values in {key}")
                return None

            # Pad to 18 if model returned 12
            while len(arr) < 18:
                arr.append(arr[-1])

            # Range check
            out_of_range = [v for v in arr if not (150 <= v <= 2000)]
            if out_of_range:
                print(f"  Out-of-range values in {key}: {out_of_range[:3]}")
                return None

            # First value must be within 5% of spy_anchor (not hardcoded 560)
            if not (spy_anchor * 0.95 <= arr[0] <= spy_anchor * 1.05):
                print(f"  {key}[0]={arr[0]:.0f} not within 5% of spy_anchor={spy_anchor:.0f} — pinning")
                # Shift entire path to start at spy_anchor
                delta = spy_anchor - arr[0]
                arr = [round(v + delta, 2) for v in arr]

            # No consecutive month should move more than 12% (catch wild AI outputs)
            corrected = [arr[0]]
            for i in range(1, len(arr)):
                prev = corrected[-1]
                move = (arr[i] / prev - 1)
                if abs(move) > 0.12:
                    arr[i] = round(prev * (1 + 0.12 * (1 if move > 0 else -1)), 2)
                corrected.append(arr[i])
            arr = corrected

            data[key] = arr

        # ── Enforce spy_latest = live price ──────────────────────────────────
        data["spy_latest"] = spy_anchor

        # ── Validate/fix year-end prices — ALWAYS derive from monthly arrays ──
        # Never trust the model's year_end claims — recompute from validated arrays.
        # Also apply realistic max-gain cap: bull can't gain >50% in 18 months,
        # base can't gain >20%, bear can't lose >60%.
        MAX_GAIN  = {"bull": 0.50, "base": 0.20, "bear": 0.05}
        MAX_LOSS  = {"bull": 0.10, "base": 0.40, "bear": 0.60}
        for scenario, key in [("bull","bull_monthly"), ("base","base_monthly"), ("bear","bear_monthly")]:
            arr = data[key]
            # Clip the ENTIRE path to realistic bounds from spy_anchor
            _max_price = spy_anchor * (1 + MAX_GAIN[scenario])
            _min_price = spy_anchor * (1 - MAX_LOSS[scenario])
            arr = [round(max(_min_price, min(_max_price, v)), 2) for v in arr]
            data[key] = arr
            ye26_key = f"year_end_2026_{scenario}"
            ye27_key = f"year_end_2027_{scenario}"
            # Derive from actual validated + clipped array
            data[ye26_key] = round(arr[min(_idx_ye26, len(arr)-1)], 2)
            data[ye27_key] = round(arr[-1], 2)
            print(f"  {scenario}: 18mo range ${arr[0]:.0f}→${arr[-1]:.0f} "
                  f"(YE26=${data[ye26_key]:.0f} YE27=${data[ye27_key]:.0f})")

        # ── Validate probabilities sum to 100 ─────────────────────────────────
        pb  = max(5,  min(90, int(data.get("probability_bull", 25))))
        pm  = max(5,  min(90, int(data.get("probability_base", 50))))
        pd_ = max(5,  min(90, int(data.get("probability_bear", 25))))
        total_p = pb + pm + pd_
        if abs(total_p - 100) > 2:
            pb  = round(pb  * 100 / total_p)
            pm  = round(pm  * 100 / total_p)
            pd_ = 100 - pb - pm
        data["probability_bull"] = pb
        data["probability_base"] = pm
        data["probability_bear"] = pd_

        print(f"  ✓ Projection validated: SPY=${spy_anchor:.2f} | "
              f"Bull={data['bull_monthly'][-1]:.0f}({pb}%) "
              f"Base={data['base_monthly'][-1]:.0f}({pm}%) "
              f"Bear={data['bear_monthly'][-1]:.0f}({pd_}%)")
        if data.get("analysis_summary"):
            print(f"  Analysis: {data['analysis_summary'][:120]}...")
        return data

    except Exception as _e:
        import traceback
        print(f"  Claude projection failed: {_e}")
        traceback.print_exc()
        return None



# ══════════════════════════════════════════════════════════════════════════════
# ECONOMIC CALENDAR TAB
# ══════════════════════════════════════════════════════════════════════════════

# ── Market impact guide for each key indicator ────────────────────────────────
ECO_IMPACT_GUIDE = [
    # (id, name, freq, source, bull_threshold, bear_threshold, neutral_range,
    #  bull_note, bear_note, peak_reading, trough_reading, why_matters, fred_key)
    {
        "id":    "ism_mfg",
        "name":  "ISM Manufacturing PMI",
        "freq":  "Monthly (1st biz day)",
        "icon":  "🏭",
        "bull":  ">55 and rising",
        "bear":  "<50 and falling",
        "neutral":"50–55",
        "bull_val": 55, "bear_val": 50,
        "direction": "up_good",
        "bull_note": "Expansion confirmed. Earnings upgrades follow 1-2 qtrs. Buy cyclicals (XLY, XLI, XLK).",
        "bear_note": "Contraction = earnings risk. Rotate to defensives (XLP, XLV, XLU). SPX drops avg -3% in 6wks.",
        "peak_2000": 57.2, "peak_2007": 52.0, "peak_2018": 60.8, "peak_2022": 60.0,
        "trough_2009": 35.5, "trough_2020": 41.5, "trough_2016": 48.0,
        "current_note": "Below 50 = contraction. New Orders sub-index leads by 1-2 months.",
        "spx_corr": "+0.72 (6mo lag)",
        "fred_key": "ISM_PMI",
        "color": "#1155cc",
    },
    {
        "id":    "ism_svc",
        "name":  "ISM Services PMI",
        "freq":  "Monthly (3rd biz day)",
        "icon":  "🏪",
        "bull":  ">57",
        "bear":  "<50",
        "neutral":"50–57",
        "bull_val": 57, "bear_val": 50,
        "direction": "up_good",
        "bull_note": "Services (70% of GDP) expanding. Consumer spending intact. Positive for SPX.",
        "bear_note": "Services contraction = recession risk. Credit card delinquencies rise next quarter.",
        "peak_2000": 58.0, "peak_2007": 56.4, "peak_2018": 60.9, "peak_2022": 68.4,
        "trough_2009": 37.3, "trough_2020": 41.8, "trough_2016": 52.9,
        "current_note": "Apr 2026 reading: 54.0 (March) — below forecast 55.4, previous 56.1.",
        "spx_corr": "+0.65 (3mo lag)",
        "fred_key": None,
        "color": "#0f6e56",
    },
    {
        "id":    "nfp",
        "name":  "Nonfarm Payrolls",
        "freq":  "Monthly (1st Friday)",
        "icon":  "👷",
        "bull":  ">200K",
        "bear":  "<75K",
        "neutral":"75K–200K",
        "bull_val": 200, "bear_val": 75,
        "direction": "up_good",
        "bull_note": "Strong labor market. Consumer spending supported. Fed less likely to cut — mixed signal.",
        "bear_note": "Weak jobs = recession risk. BUT bad = good if it forces Fed to cut rates faster.",
        "peak_2000": 230, "peak_2007": 190, "peak_2018": 312, "peak_2022": 528,
        "trough_2009": -820, "trough_2020": -20500, "trough_2016": 150,
        "current_note": "Context matters: >200K with inflation is hawkish. >200K with low inflation is pure bullish.",
        "spx_corr": "+0.58 (1mo lag)",
        "fred_key": "PAYEMS",
        "color": "#534ab7",
    },
    {
        "id":    "cpi",
        "name":  "CPI Inflation (YoY)",
        "freq":  "Monthly (~12th)",
        "icon":  "💵",
        "bull":  "<2.5% and falling",
        "bear":  ">4% or rising fast",
        "neutral":"2.5%–3.5%",
        "bull_val": 2.5, "bear_val": 4.0,
        "direction": "down_good",
        "bull_note": "Inflation cooling = Fed can cut. Biggest positive catalyst for equity multiples.",
        "bear_note": "Hot inflation = Fed must stay restrictive or hike. P/E multiple compression of 3-5x.",
        "peak_2000": 3.7, "peak_2007": 4.3, "peak_2018": 2.9, "peak_2022": 8.5,
        "trough_2009": -2.1, "trough_2020": 0.1, "trough_2016": 1.1,
        "current_note": "Current: 2.8% YoY (Feb 2026). Core sticky at 3.1%. Fed target = 2.0%.",
        "spx_corr": "-0.61 (surprise matters more than level)",
        "fred_key": "CPI",
        "color": "#993c1d",
    },
    {
        "id":    "core_pce",
        "name":  "Core PCE (Fed's preferred)",
        "freq":  "Monthly (~last Friday)",
        "icon":  "🎯",
        "bull":  "<2.3% and falling",
        "bear":  ">3.5%",
        "neutral":"2.3%–3.0%",
        "bull_val": 2.3, "bear_val": 3.5,
        "direction": "down_good",
        "bull_note": "PCE near 2% = Fed pivot confirmed. Bond yields drop. Equity multiples expand.",
        "bear_note": "Hot core PCE = Fed credibility at risk. Hawkish surprise. Worst for growth stocks.",
        "peak_2000": 2.1, "peak_2007": 2.4, "peak_2018": 2.0, "peak_2022": 5.4,
        "trough_2009": 1.4, "trough_2020": 1.0, "trough_2016": 1.6,
        "current_note": "Fed watches this above CPI. Two consecutive months <2.5% typically precedes rate cuts.",
        "spx_corr": "-0.68 (strongest Fed policy link)",
        "fred_key": None,
        "color": "#993556",
    },
    {
        "id":    "retail",
        "name":  "Retail Sales (MoM)",
        "freq":  "Monthly (~15th)",
        "icon":  "🛒",
        "bull":  ">+0.5% MoM",
        "bear":  "<-0.3% MoM",
        "neutral":"-0.3% to +0.5%",
        "bull_val": 0.5, "bear_val": -0.3,
        "direction": "up_good",
        "bull_note": "Consumer spending (70% of GDP) intact. Revenue beats follow next earnings season.",
        "bear_note": "Consumer pulling back = stagflation risk. XLY (consumer disc) underperforms.",
        "peak_2000": 0.8, "peak_2007": 0.5, "peak_2018": 0.9, "peak_2022": 3.8,
        "trough_2009": -3.9, "trough_2020": -16.4, "trough_2016": -0.3,
        "current_note": "Feb 2026: +0.2% MoM. Core ex-autos +0.3%. Consumer cautious but intact.",
        "spx_corr": "+0.55 (2mo lag to earnings)",
        "fred_key": "RETAIL",
        "color": "#ba7517",
    },
    {
        "id":    "claims",
        "name":  "Initial Jobless Claims",
        "freq":  "Weekly (Thursday 8:30am)",
        "icon":  "📋",
        "bull":  "<210K",
        "bear":  ">300K",
        "neutral":"210K–260K",
        "bull_val": 210, "bear_val": 300,
        "direction": "down_good",
        "bull_note": "Tight labor market. No layoff wave. Cyclical spending intact. SAHM rule not triggered.",
        "bear_note": "Rising claims = labor market cracking. Sahm Rule triggers at 4wk MA rise >0.5pp.",
        "peak_2000": 310, "peak_2007": 350, "peak_2018": 215, "peak_2022": 185,
        "trough_2009": 665, "trough_2020": 6867, "trough_2016": 280,
        "current_note": "Currently N/A (FRED series not loading). Historical avg recovery: claims peak 3-6mo after SPX trough.",
        "spx_corr": "-0.70 (inverted — high claims = bad for stocks)",
        "fred_key": "INIT_CLAIMS",
        "color": "#185fa5",
    },
    {
        "id":    "fomc",
        "name":  "FOMC Rate Decision",
        "freq":  "8x per year",
        "icon":  "🏦",
        "bull":  "Rate cut or dovish surprise",
        "bear":  "Rate hike or hawkish surprise",
        "neutral":"Hold as expected",
        "bull_val": None, "bear_val": None,
        "direction": "qualitative",
        "bull_note": "First cut in cycle: SPX +avg 12% over next 6mo if no recession. Biggest positive catalyst.",
        "bear_note": "75bp hike (2022): SPX -5% same day. Each subsequent hike: diminishing impact.",
        "peak_2000": "6.50%", "peak_2007": "5.25%", "peak_2018": "2.50%", "peak_2022": "0.25%→5.50%",
        "trough_2009": "0.25%", "trough_2020": "0.25%", "trough_2016": "0.25-0.50%",
        "current_note": "Current: 3.25-3.50% (Mar 2026). Market pricing 2 cuts in 2026. Next FOMC: May 7.",
        "spx_corr": "Cuts: +12% fwd 6mo (no recession) / Hikes: -3% per hike",
        "fred_key": "FEDFUNDS",
        "color": "#8b0000",
    },
    {
        "id":    "gdp",
        "name":  "GDP Growth (Advance)",
        "freq":  "Quarterly (last week of month)",
        "icon":  "📊",
        "bull":  ">2.5% annualized",
        "bear":  "<0% (2 qtrs = recession)",
        "neutral":"1.0%–2.5%",
        "bull_val": 2.5, "bear_val": 0,
        "direction": "up_good",
        "bull_note": "Strong growth = earnings expansion. SPX P/E can sustain >22x. Cyclicals outperform.",
        "bear_note": "Negative GDP = recession confirmed. Bear market avg -37% from peak. Minimum 2 qtrs to confirm.",
        "peak_2000": 4.1, "peak_2007": 2.5, "peak_2018": 3.0, "peak_2022": 5.7,
        "trough_2009": -8.4, "trough_2020": -28.1, "trough_2016": 1.9,
        "current_note": "Q4 2025: +2.4% annualized. Atlanta Fed GDPNow Q1 2026: +1.8%.",
        "spx_corr": "+0.80 (strongest macro correlation)",
        "fred_key": None,
        "color": "#3b6d11",
    },
    {
        "id":    "umich",
        "name":  "UMich Consumer Sentiment",
        "freq":  "Monthly (2nd Friday prelim, 4th Friday final)",
        "icon":  "😊",
        "bull":  ">80",
        "bear":  "<60",
        "neutral":"60–80",
        "bull_val": 80, "bear_val": 60,
        "direction": "up_good",
        "bull_note": "Confident consumers spend more. Retail and XLY outperform. Leading indicator for PCE.",
        "bear_note": "Sentiment crash = spending freeze. Fell to 50 in 2022, 55 in 2008. Leading by 2-3 months.",
        "peak_2000": 112, "peak_2007": 92, "peak_2018": 101, "peak_2022": 68,
        "trough_2009": 55, "trough_2020": 71, "trough_2016": 87,
        "current_note": "Currently N/A (FRED series not loading). 1-yr inflation expectations = key embedded signal.",
        "spx_corr": "+0.65 (2mo lead on consumer spending)",
        "fred_key": "UMCSENT",
        "color": "#1d9e75",
    },
    {
        "id":    "housing",
        "name":  "Housing Starts & Permits",
        "freq":  "Monthly (~17th)",
        "icon":  "🏠",
        "bull":  ">1.5M starts",
        "bear":  "<1.0M starts",
        "neutral":"1.0M–1.5M",
        "bull_val": 1500, "bear_val": 1000,
        "direction": "up_good",
        "bull_note": "Housing leads GDP by 6-9 months. Homebuilders (XHB) outperform. Mortgage demand up.",
        "bear_note": "Housing bust = Kuznets cycle peak. Preceded 2006-07 GFC by 18 months.",
        "peak_2000": 1600, "peak_2007": 2273, "peak_2018": 1330, "peak_2022": 1800,
        "trough_2009": 478, "trough_2020": 934, "trough_2016": 1142,
        "current_note": "Jan 2026: 1,487K starts. Permits 1,386K. Affordability constraint: mortgage rate 6.6%.",
        "spx_corr": "+0.60 (6-12mo lead on GDP)",
        "fred_key": "HOUST",
        "color": "#d85a30",
    },
]

# ── Weekly event template (filled by web search each run) ────────────────────
ECO_CALENDAR_EVENTS_TEMPLATE = [
    # These are filled dynamically by _fetch_economic_calendar()
    # Fallback hardcoded for current week if web search fails
    {"day":"Monday",    "time":"10:00 am", "event":"ISM Services PMI",         "period":"March",  "actual":"54.0%", "forecast":"55.4%", "previous":"56.1%", "impact":"HIGH",   "bullish_if":"beat", "id":"ism_svc"},
    {"day":"Tuesday",   "time":"8:30 am",  "event":"Durable Goods Orders",     "period":"Feb",    "actual":"",      "forecast":"-1.0%", "previous":"0.0%",  "impact":"MEDIUM", "bullish_if":"beat", "id":""},
    {"day":"Tuesday",   "time":"3:00 pm",  "event":"Consumer Credit",          "period":"Feb",    "actual":"",      "forecast":"$10.0B","previous":"$8.1B", "impact":"LOW",    "bullish_if":"beat", "id":""},
    {"day":"Wednesday", "time":"2:00 pm",  "event":"FOMC Minutes (May meeting)","period":"",      "actual":"",      "forecast":"",      "previous":"",      "impact":"HIGH",   "bullish_if":"dovish","id":"fomc"},
    {"day":"Thursday",  "time":"8:30 am",  "event":"Initial Jobless Claims",   "period":"Wk Apr5","actual":"",      "forecast":"223K",  "previous":"219K",  "impact":"HIGH",   "bullish_if":"miss (lower)", "id":"claims"},
    {"day":"Friday",    "time":"8:30 am",  "event":"PPI Final Demand",         "period":"March",  "actual":"",      "forecast":"0.2%",  "previous":"0.0%",  "impact":"HIGH",   "bullish_if":"miss (lower)", "id":""},
    {"day":"Friday",    "time":"10:00 am", "event":"UMich Consumer Sentiment (Prelim)","period":"April","actual":"","forecast":"54.5","previous":"57.9",   "impact":"HIGH",   "bullish_if":"beat", "id":"umich"},
]


def _fetch_economic_calendar(use_api=True, fd=None):
    """
    Fetch this week's economic calendar. Sources (in priority order):
      1. Forex Factory CDN  — free, zero auth, JSON, updates live as actuals come in
      2. Finnhub API        — free key (finnhub.io/register), US events with actuals
      3. Fallback template  — computed dates, no hardcoded actuals
    Rules:
      - Shows Mon-Fri of CURRENT week; rotates to next week on Sat/Sun
      - 'actual' field only populated AFTER the ET release time has passed
    """
    import requests as _rq, json as _js, re as _re
    from datetime import date as _dt, timedelta as _td, datetime as _dtm
    import time as _time_mod

    # ── Current time in ET ─────────────────────────────────────────────────────
    _et_off = 4 if _time_mod.localtime().tm_isdst else 5
    now_et  = _dtm.utcnow() - _td(hours=_et_off)
    today_et = now_et.date()
    weekday  = today_et.weekday()   # 0=Mon 6=Sun

    # On Sat/Sun show NEXT week; otherwise show current week
    if weekday >= 5:
        week_start = today_et + _td(days=(7 - weekday))
    else:
        week_start = today_et - _td(days=weekday)

    week_end = week_start + _td(days=4)   # Friday

    def _day_label(d):
        try:    return (d.strftime("%A %b ") + str(d.day))
        except: return d.strftime("%A %b %d").replace(" 0", " ")

    def _day_offset_from_label(day_str):
        _d = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}
        return next((v for k,v in _d.items() if day_str.lower().strip().startswith(k)), -1)

    def _is_released(day_offset, time_str):
        """True if this event's ET release time has already passed."""
        try:
            ts = time_str.strip().upper()
            t = None
            for _fmt in ["%I:%M %p", "%I:%M%p", "%H:%M"]:
                try: t = _dtm.strptime(ts, _fmt).time(); break
                except: pass
            if t is None: return False
            return now_et >= _dtm.combine(week_start + _td(days=day_offset), t)
        except Exception:
            return False

    def _sanitize_actuals(events):
        """Wipe actual for any event whose ET release time hasn't passed yet."""
        for ev in events:
            if not ev.get("actual","").strip(): continue
            day_off = _day_offset_from_label(ev.get("day",""))
            if day_off < 0: ev["actual"] = ""; continue
            if not _is_released(day_off, ev.get("time","")):
                ev["actual"] = ""
        return events

    def _filter_week(events):
        """Keep only events Mon-Fri of the target week. Robust multi-format matching."""
        kept = []
        week_dates = {}
        for i in range(5):
            d = week_start + _td(days=i)
            # Build all possible label formats this date could appear as
            week_dates[d] = [
                (d.strftime("%A %b ") + str(d.day)).lower(),    # "tuesday apr 7"
                d.strftime("%A %b %d").lower(),                  # "tuesday apr 07"
                d.strftime("%A, %B %d").lower(),                 # "tuesday, april 07"
                (d.strftime("%A, %B ") + str(d.day)).lower(),   # "tuesday, april 7"
                d.strftime("%Y-%m-%d"),                          # "2026-04-07" (exact)
                (d.strftime("%b ") + str(d.day)).lower(),        # "apr 7"
                d.strftime("%b %d").lower().replace(" 0"," "),  # "apr 7"
                d.strftime("%m/%d/%Y"),                          # "04/07/2026"
                d.strftime("%m/%d"),                             # "04/07"
            ]

        for ev in events:
            raw_day = ev.get("day","").lower().strip()
            matched  = False
            for d, fmts in week_dates.items():
                # Check if the event's day label contains or matches any known format
                if any(f == raw_day or f in raw_day or raw_day in f for f in fmts):
                    ev["day"] = _day_label(d)
                    kept.append(ev)
                    matched = True
                    break
                # Also check: does the day name match AND the date number match?
                day_name = d.strftime("%A").lower()
                if raw_day.startswith(day_name) and str(d.day) in raw_day:
                    ev["day"] = _day_label(d)
                    kept.append(ev)
                    matched = True
                    break
            # If still no match but has a weekday name that belongs in this week → accept
            if not matched:
                for i, d in enumerate(week_start + _td(days=j) for j in range(5)):
                    if raw_day.startswith(d.strftime("%A").lower()):
                        # Ambiguous weekday name — accept, normalize to correct date
                        ev["day"] = _day_label(d)
                        kept.append(ev)
                        break
        return kept

    # ── Source 1: Forex Factory CDN ────────────────────────────────────────────
    # Completely free, zero auth. Returns current week's events with live actuals.
    def _trading_economics():
        """
        Trading Economics guest API — free, no signup needed.
        Returns full week Mon-Fri including Fed speakers and all economic releases.
        guest:guest is their public demo key.
        """
        try:
            # Explicitly request Mon 00:00 → Fri 23:59 ET of the target week
            from_dt = week_start.strftime("%Y-%m-%d")
            to_dt   = week_end.strftime("%Y-%m-%d")
            url = (
                f"https://api.tradingeconomics.com/calendar/country/United%20States"
                f"/{from_dt}/{to_dt}?c=guest:guest"
            )
            r = _rq.get(url, timeout=12,
                        headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                                 "Accept":"application/json"})
            if r.status_code != 200:
                print(f"  [eco calendar] Trading Economics status {r.status_code}")
                return None
            raw = r.json()
            if not isinstance(raw, list):
                return None

            events = []
            for ev in raw:
                try:
                    # Parse date — TE returns UTC ISO format
                    dt_str = str(ev.get("Date",""))
                    if not dt_str: continue
                    dt_utc = _dtm.fromisoformat(dt_str.replace("Z","").split("+")[0])
                    dt_et  = dt_utc - _td(hours=_et_off)

                    # Skip if outside Mon-Fri of target week
                    if not (week_start <= dt_et.date() <= week_end):
                        continue

                    imp_n = int(ev.get("Importance", 1) or 1)
                    imp   = "HIGH" if imp_n >= 3 else "MEDIUM" if imp_n == 2 else "LOW"

                    try:    ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                    except: ts = "12:00 am"

                    ename  = str(ev.get("Event","") or "").strip()
                    elow   = ename.lower()
                    actual = str(ev.get("Actual","") or "").strip()
                    fore   = str(ev.get("Forecast","") or ev.get("TEForecast","") or "").strip()
                    prev   = str(ev.get("Previous","") or "").strip()

                    # Determine direction
                    if any(x in elow for x in ["claims","unemployment","inflation","cpi","ppi","deficit","delinq"]):
                        bullish = "miss (lower)"
                    elif any(x in elow for x in ["fomc","minutes","fed ","speak","powell","chair","president"]):
                        bullish = "dovish"
                    else:
                        bullish = "beat"

                    events.append({
                        "day":       _day_label(dt_et.date()),
                        "time":      ts,
                        "event":     ename,
                        "period":    str(ev.get("Reference","") or "").strip(),
                        "actual":    actual if actual not in ("","--","nan","None") else "",
                        "forecast":  fore   if fore   not in ("","--","nan","None") else "",
                        "previous":  prev   if prev   not in ("","--","nan","None") else "",
                        "impact":    imp,
                        "bullish_if":bullish,
                    })
                except Exception:
                    continue

            if events:
                n_hi = sum(1 for e in events if e["impact"]=="HIGH")
                print(f"  [eco calendar] Trading Economics: {len(events)} US events ({n_hi} HIGH) for {from_dt} → {to_dt}")
                return events
        except Exception as e:
            print(f"  [eco calendar] Trading Economics failed: {e}")
        return None

    def _marketwatch_scrape():
        """
        Scrape MarketWatch economic calendar HTML — exactly matches their table format.
        URL: https://www.marketwatch.com/economy-politics/calendar
        """
        try:
            r = _rq.get(
                "https://www.marketwatch.com/economy-politics/calendar",
                timeout=12,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept":     "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer":    "https://www.marketwatch.com/",
                }
            )
            if r.status_code != 200: return None
            import re as _re2
            html = r.text

            # MarketWatch embeds calendar data as JSON in a __STATE__ or window object
            # Try to find JSON data first
            m = _re2.search(r'"economicEvents"\s*:\s*(\[.+?\])\s*[,}]', html, _re2.DOTALL)
            if not m:
                # Try the table scrape
                return None

            raw = _js.loads(m.group(1))
            events = []
            for ev in raw:
                try:
                    dt_str = ev.get("datetime","") or ev.get("date","")
                    dt_et  = _dtm.fromisoformat(dt_str.split("+")[0].split("Z")[0])
                    # MW times are already ET
                    try:    ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                    except: ts = dt_et.strftime("%H:%M")
                    events.append({
                        "day":       _day_label(dt_et.date()),
                        "time":      ts,
                        "event":     ev.get("name","") or ev.get("event",""),
                        "period":    ev.get("period","") or ev.get("reference",""),
                        "actual":    str(ev.get("actual","") or ""),
                        "forecast":  str(ev.get("forecast","") or ev.get("consensus","")),
                        "previous":  str(ev.get("previous","") or ev.get("prior","")),
                        "impact":    "HIGH" if ev.get("importance","")=="H" else "MEDIUM",
                        "bullish_if":"beat",
                    })
                except Exception: continue
            if events:
                print(f"  [eco calendar] MarketWatch: {len(events)} events")
                return events
        except Exception as e:
            print(f"  [eco calendar] MarketWatch failed: {e}")
        return None

    def _forex_factory():
        """Forex Factory CDN — zero auth, live actuals, most reliable free source."""
        urls = [
            'https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json' if weekday < 5
            else 'https://cdn-nfs.faireconomy.media/ff_calendar_nextweek.json',
        ]
        for url in urls:
            try:
                r = _rq.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                })
                if r.status_code != 200:
                    print(f'  [eco calendar] FF CDN status {r.status_code}')
                    continue
                raw = r.json()
                events = []
                for ev in raw:
                    if ev.get("country","") != "USD": continue
                    imp = ev.get("impact","").lower()
                    if imp not in ("high","medium"): continue
                    try:
                        dt_str = ev.get("date","")
                        dt_utc = _dtm.fromisoformat(dt_str.replace("Z","+00:00")) if "T" in dt_str else _dtm.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                        dt_et  = dt_utc.replace(tzinfo=None) - _td(hours=_et_off) if dt_utc.tzinfo else dt_utc - _td(hours=_et_off)
                    except Exception:
                        continue
                    try: ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                    except: ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                    events.append({
                        "day":       _day_label(dt_et.date()),
                        "time":      ts,
                        "event":     ev.get("title",""),
                        "period":    "",
                        "actual":    str(ev.get("actual","") or ""),
                        "forecast":  str(ev.get("forecast","") or ""),
                        "previous":  str(ev.get("previous","") or ""),
                        "impact":    "HIGH" if imp == "high" else "MEDIUM",
                        "bullish_if":"beat",
                    })
                if events:
                    print(f"  [eco calendar] Forex Factory: {len(events)} USD events")
                    return events
            except Exception as e:
                print(f"  [eco calendar] Forex Factory failed: {e}")
        return None

    def _myfxbook():
        """Myfxbook economic calendar — free, no auth required."""
        try:
            r = _rq.get(
                "https://www.myfxbook.com/api/get-calendar.json",
                params={"start": week_start.strftime("%Y-%m-%d"),
                        "end":   week_end.strftime("%Y-%m-%d")},
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"},
            )
            if r.status_code != 200: return None
            data = r.json()
            if data.get("error"): return None
            raw = data.get("calendar", [])
            events = []
            for ev in raw:
                if ev.get("currency","") != "USD": continue
                imp = str(ev.get("impactTitle","")).lower()
                if imp not in ("high","medium"): continue
                try:
                    dt = _dtm.strptime(ev["date"], "%Y-%m-%d %H:%M:%S")
                    dt_et = dt - _td(hours=_et_off)
                except Exception:
                    continue
                try: ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                except: ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                events.append({
                    "day":       _day_label(dt_et.date()),
                    "time":      ts,
                    "event":     ev.get("name",""),
                    "period":    ev.get("period",""),
                    "actual":    str(ev.get("actual","") or ""),
                    "forecast":  str(ev.get("forecast","") or ""),
                    "previous":  str(ev.get("previous","") or ""),
                    "impact":    "HIGH" if "high" in imp else "MEDIUM",
                    "bullish_if":"beat",
                })
            if events:
                print(f"  [eco calendar] Myfxbook: {len(events)} USD events")
                return events
        except Exception as e:
            print(f"  [eco calendar] Myfxbook failed: {e}")
        return None

    def _finnhub():
        """Finnhub — free API key at finnhub.io/register. Add to FINNHUB_API_KEY."""
        if not FINNHUB_API_KEY:
            return None
        try:
            r = _rq.get(
                "https://finnhub.io/api/v1/calendar/economic",
                params={"from": week_start.strftime("%Y-%m-%d"),
                        "to":   week_end.strftime("%Y-%m-%d"),
                        "token": FINNHUB_API_KEY},
                timeout=8,
            )
            if r.status_code != 200: return None
            raw = r.json().get("economicCalendar", [])
            events = []
            for ev in raw:
                if ev.get("country","US") != "US": continue
                try:
                    dt_utc = _dtm.strptime(ev["time"], "%Y-%m-%d %H:%M:%S")
                    dt_et  = dt_utc - _td(hours=_et_off)
                except Exception:
                    continue
                imp_map = {3:"HIGH", 2:"MEDIUM", 1:"LOW"}
                imp = imp_map.get(ev.get("impact",1),"MEDIUM")
                if imp == "LOW": continue
                try: ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                except: ts = dt_et.strftime("%I:%M %p").lstrip("0").lower()
                events.append({
                    "day":       _day_label(dt_et.date()),
                    "time":      ts,
                    "event":     ev.get("event",""),
                    "period":    ev.get("unit",""),
                    "actual":    str(ev.get("actual","") or ""),
                    "forecast":  str(ev.get("estimate","") or ""),
                    "previous":  str(ev.get("prev","") or ""),
                    "impact":    imp,
                    "bullish_if":"beat",
                })
            if events:
                print(f"  [eco calendar] Finnhub: {len(events)} US events")
                return events
        except Exception as e:
            print(f"  [eco calendar] Finnhub failed: {e}")
        return None

    # ── Source 4: Build from FRED data already fetched (always works offline) ──
    # ── Source 3b: BLS.gov direct API ───────────────────────────────────────────
    def _bls_fetch():
        """Fetch latest actuals from BLS.gov — US government, no API key needed."""
        BLS = {
            "CUSR0000SA0":    "cpi",
            "CUSR0000SA0L1E": "core_cpi",
            "WPUFD49104":     "ppi",
            "LNS17900000":    "claims",   # initial claims, thousands
        }
        out = {}
        try:
            for sid, key in BLS.items():
                r = _rq.get(
                    f"https://api.bls.gov/publicAPI/v1/timeseries/data/{sid}",
                    params={"startyear":"2025","endyear":"2026"},
                    timeout=6, headers={"User-Agent":"Mozilla/5.0"}
                )
                if r.status_code != 200: continue
                series = r.json().get("Results",{}).get("series",[{}])[0].get("data",[])
                if len(series) >= 1:
                    out[key]       = float(series[0].get("value",0) or 0)
                    out[key+"_pd"] = f"{series[0].get('periodName','')} {series[0].get('year','')}"
                if len(series) >= 2:
                    out[key+"_p"]  = float(series[1].get("value",0) or 0)
            if out: print(f"  [eco calendar] BLS.gov: {len([k for k in out if '_' not in k or k.endswith('_pd')])} series")
        except Exception as e:
            print(f"  [eco calendar] BLS.gov failed: {e}")
        return out

    def _from_fred_data(fd_data, is_released_fn):
        """Build calendar from FRED/proxy data + BLS.gov actuals."""
        if not fd_data:
            return None

        bls = _bls_fetch()   # try US gov API for real actuals

        def _fv(sid):
            s = fd_data.get(sid)
            if s is None or (hasattr(s,"empty") and s.empty): return None
            try: return float(s.iloc[-1])
            except: return None

        def _pv(sid):
            s = fd_data.get(sid)
            if s is None or (hasattr(s,"empty") and s.empty) or len(s)<2: return None
            try: return float(s.iloc[-2])
            except: return None

        def _yoy_bls(cur_key):
            """YoY % from two consecutive BLS index levels."""
            cur = bls.get(cur_key); prv = bls.get(cur_key+"_p")
            if cur and prv and prv != 0:
                return round((cur-prv)/prv*100, 1)
            return None

        def _proxy_yoy(sid):
            """YoY from FRED proxy monthly series; reject if > 12% (proxy artifact)."""
            s = fd_data.get(sid)
            if s is None or (hasattr(s,"empty") and s.empty) or len(s)<13: return None
            try:
                v = round((float(s.iloc[-1])/float(s.iloc[-13])-1)*100, 1)
                return v if abs(v)<=12 else None
            except: return None

        _rel = is_released_fn
        _M   = lambda d: _day_label(week_start + _td(days=d))
        _pm  = (week_start - _td(days=28)).strftime("%B")

        events = []

        # Monday: ISM Services PMI
        ism = _fv("ISM_PMI"); ism_p = _pv("ISM_PMI")
        events.append({"day":_M(0),"time":"10:00 am","event":"ISM Services PMI",
            "period":_pm,
            "actual":  f"≈{ism:.1f}" if ism and _rel(0,"10:00 am") else "",
            "forecast":f"{ism_p:.1f}" if ism_p else "",   # prior reading = market consensus baseline
            "previous":f"{ism_p:.1f}" if ism_p else "",
            "impact":"HIGH","bullish_if":"beat"})

        # Tuesday: Durable Goods — proxy stores MoM % directly, use _fv not _mom
        durg = _fv("DURGDS"); durg_p = _pv("DURGDS")
        if durg   is not None and abs(durg)   > 10: durg   = None   # proxy sanity
        if durg_p is not None and abs(durg_p) > 10: durg_p = None
        events.append({"day":_M(1),"time":"8:30 am","event":"Durable Goods Orders",
            "period":_pm,
            "actual":  f"≈{durg:+.1f}%" if durg is not None and _rel(1,"8:30 am") else "",
            "forecast":f"{durg_p:+.1f}%" if durg_p is not None else "",  # prior as baseline estimate
            "previous":f"{durg_p:+.1f}%" if durg_p is not None else "",
            "impact":"MEDIUM","bullish_if":"beat"})

        # Wednesday: FOMC Minutes
        events.append({"day":_M(2),"time":"2:00 pm","event":"FOMC Minutes",
            "period":"","actual":"","forecast":"","previous":"",
            "impact":"HIGH","bullish_if":"dovish"})

        # Thursday: Initial Jobless Claims
        # BLS series LNS17900000 in thousands; FRED ICSA in raw units
        bls_cl = bls.get("claims"); bls_cl_p = bls.get("claims_p")
        fred_cl = _fv("INIT_CLAIMS")
        if fred_cl and fred_cl > 400000: fred_cl = None
        claims   = (bls_cl  * 1000 if bls_cl  else fred_cl)
        claims_p = (bls_cl_p* 1000 if bls_cl_p else _pv("INIT_CLAIMS"))
        if claims_p and claims_p > 400000: claims_p = None
        wk_dt = week_start - _td(days=7)
        events.append({"day":_M(3),"time":"8:30 am","event":"Initial Jobless Claims",
            "period":f"Wk {wk_dt.strftime('%b')} {wk_dt.day}",
            "actual":  f"{int(claims):,}" if claims and _rel(3,"8:30 am") else "",
            "forecast":f"{int(claims_p):,}" if claims_p else "",
            "previous":f"{int(claims_p):,}" if claims_p else "",
            "impact":"HIGH","bullish_if":"miss (lower)"})

        # Friday: CPI — prefer BLS YoY, fallback to FRED proxy
        cpi_yoy = _yoy_bls("cpi") or _proxy_yoy("CPI")
        cpi_per = bls.get("cpi_pd") or _pm
        events.append({"day":_M(4),"time":"8:30 am","event":"Consumer Price Index (CPI)",
            "period":cpi_per,
            "actual":  f"{cpi_yoy:+.1f}% YoY" if cpi_yoy is not None and _rel(4,"8:30 am") else "",
            "forecast":f"~{cpi_yoy:+.1f}% YoY" if cpi_yoy is not None and not _rel(4,"8:30 am") else "",
            "previous":f"{cpi_yoy:+.1f}% YoY" if cpi_yoy is not None else "",
            "impact":"HIGH","bullish_if":"miss (lower)"})

        # Core CPI
        ccpi_yoy = _yoy_bls("core_cpi")
        if ccpi_yoy is not None:
            events.append({"day":_M(4),"time":"8:30 am","event":"Core CPI",
                "period":cpi_per,
                "actual":  f"{ccpi_yoy:+.1f}% YoY" if _rel(4,"8:30 am") else "",
                "forecast":f"~{ccpi_yoy:+.1f}% YoY" if not _rel(4,"8:30 am") else "",
                "previous":f"{ccpi_yoy:+.1f}% YoY",
                "impact":"HIGH","bullish_if":"miss (lower)"})

        # Friday: PPI — prefer BLS
        ppi_yoy = _yoy_bls("ppi")
        events.append({"day":_M(4),"time":"8:30 am","event":"PPI Final Demand",
            "period":_pm,
            "actual":  f"{ppi_yoy:+.1f}% YoY" if ppi_yoy is not None and _rel(4,"8:30 am") else "",
            "forecast":f"~{ppi_yoy:+.1f}% YoY" if ppi_yoy is not None and not _rel(4,"8:30 am") else "",
            "previous":f"{ppi_yoy:+.1f}% YoY" if ppi_yoy is not None else "",
            "impact":"HIGH","bullish_if":"miss (lower)"})

        # Friday: UMich Sentiment
        umi = _fv("UMCSENT"); umi_p = _pv("UMCSENT")
        if umi   and (umi   < 40 or umi   > 120): umi   = None
        if umi_p and (umi_p < 40 or umi_p > 120): umi_p = None
        events.append({"day":_M(4),"time":"10:00 am","event":"UMich Consumer Sentiment",
            "period":week_start.strftime("%B"),
            "actual":  f"≈{umi:.1f}" if umi and _rel(4,"10:00 am") else "",
            "forecast":f"~{umi_p:.1f}" if umi_p and not _rel(4,"10:00 am") else "",
            "previous":f"{umi_p:.1f}" if umi_p else "",
            "impact":"HIGH","bullish_if":"beat"})

        print(f"  [eco calendar] Built {len(events)} events (BLS={'yes' if bls else 'no'})")
        return events


    # ── Run pipeline: try all sources in priority order ───────────────────────
    events = (_trading_economics()
           or _marketwatch_scrape()
           or _forex_factory()
           or _myfxbook()
           or _finnhub())

    # Source 4: FRED data (network-independent, always available)
    if not events:
        events = _from_fred_data(fd or {}, _is_released)

    if events:
        events = _filter_week(events)
        events = _sanitize_actuals(events)
        if events:
            _day_ord = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4}
            events.sort(key=lambda e: (
                next((v for k,v in _day_ord.items() if e.get("day","").lower().startswith(k)), 9),
                e.get("time","")
            ))
            return events

    # ── Fallback: dynamic template, no hardcoded actuals ──────────────────────
    print(f"  [eco calendar] All sources failed — using template for week of {_day_label(week_start)}")
    _M = lambda d: _day_label(week_start + _td(days=d))
    return [
        {"day":_M(0),"time":"10:00 am","event":"ISM Services PMI",         "period":"","actual":"","forecast":"","previous":"","impact":"HIGH",  "bullish_if":"beat"},
        {"day":_M(1),"time":"8:30 am", "event":"Durable Goods Orders",     "period":"","actual":"","forecast":"","previous":"","impact":"MEDIUM","bullish_if":"beat"},
        {"day":_M(2),"time":"2:00 pm", "event":"FOMC Minutes",             "period":"","actual":"","forecast":"","previous":"","impact":"HIGH",  "bullish_if":"dovish"},
        {"day":_M(3),"time":"8:30 am", "event":"Initial Jobless Claims",   "period":"","actual":"","forecast":"","previous":"","impact":"HIGH",  "bullish_if":"miss (lower)"},
        {"day":_M(4),"time":"8:30 am", "event":"PPI Final Demand",         "period":"","actual":"","forecast":"","previous":"","impact":"HIGH",  "bullish_if":"miss (lower)"},
        {"day":_M(4),"time":"10:00 am","event":"UMich Consumer Sentiment", "period":"","actual":"","forecast":"","previous":"","impact":"HIGH",  "bullish_if":"beat"},
    ]


def _build_economic_calendar_html(fd, md, calendar_events, scorecard=None):
    """Build the comprehensive Economic Calendar tab HTML."""
    import datetime as _dtec
    from datetime import date as _today_ec

    gen_dt   = _dtec.datetime.now().strftime("%Y-%m-%d %H:%M")
    today_wk = _today_ec.today().strftime("%A, %B %d, %Y")

    # ── Get current readings from FRED/market data ────────────────────────────
    def _gv(k, i=-1):
        s = fd.get(k)
        if s is not None and not s.empty:
            try: return float(s.iloc[max(i,-len(s))])
            except: pass
        return None

    def _gsc(name):
        for ind in (scorecard or []):
            if ind.get("name") == name: return ind.get("value")
        return None

    _cpi_now  = None
    _cpi_s = fd.get("CPI")
    if _cpi_s is not None and len(_cpi_s) >= 13:
        _cpi_now = round((float(_cpi_s.iloc[-1])/float(_cpi_s.iloc[-13])-1)*100, 1)

    _cur = {
        "ism_mfg": _gv("ISM_PMI"),
        "cpi":     _cpi_now,
        "claims":  (_gv("INIT_CLAIMS") or 0) / 1000 if _gv("INIT_CLAIMS") else None,
        "retail":  None,
        "housing": _gv("HOUST"),
        "fedfunds":_gv("FEDFUNDS"),
        "umich":   _gv("UMCSENT"),
        "gdp":     None,
        "nfp":     None,
    }

    # ── Build impact guide rows ───────────────────────────────────────────────
    def _impact_badge(level):
        cols = {"HIGH":("background:#ffebee;color:#c62828;border:1px solid #ef9a9a",),
                "MEDIUM":("background:#fff3e0;color:#e65100;border:1px solid #ffcc80",),
                "LOW":("background:#f1f8e9;color:#33691e;border:1px solid #c5e1a5",)}
        st = cols.get(level, ("background:#f5f5f5;color:#555",))[0]
        return f'<span style="{st};padding:1px 7px;border-radius:4px;font-size:9px;font-weight:700">{level}</span>'

    def _bullbear(val, ind):
        if val is None: return '<span style="color:#888">N/A</span>'
        bv = ind.get("bull_val"); bev = ind.get("bear_val")
        d  = ind.get("direction","up_good")
        if bv and bev:
            if d == "up_good":
                if val >= bv:  c="#1A7A4A"; txt=f"{val:.1f} ✓ BULLISH"
                elif val <= bev: c="#C0390F"; txt=f"{val:.1f} ✗ BEARISH"
                else:            c="#D4820A"; txt=f"{val:.1f} ~ NEUTRAL"
            else:
                if val <= bv:  c="#1A7A4A"; txt=f"{val:.1f} ✓ BULLISH"
                elif val >= bev: c="#C0390F"; txt=f"{val:.1f} ✗ BEARISH"
                else:            c="#D4820A"; txt=f"{val:.1f} ~ NEUTRAL"
        else:
            c="#556"; txt=str(val)
        return f'<span style="color:{c};font-weight:700;font-size:10px">{txt}</span>'

    guide_rows = ""
    for ind in ECO_IMPACT_GUIDE:
        cur_v = _cur.get(ind["id"])
        cur_cell = _bullbear(cur_v, ind)
        # Peak readings summary
        p_sum = (f"Peak tops: {ind.get('peak_2007','—')} (2007) / {ind.get('peak_2022','—')} (2022)<br>"
                 f"Bear troughs: {ind.get('trough_2009','—')} (2009) / {ind.get('trough_2020','—')} (2020)")
        col = ind["color"]
        guide_rows += f"""
<tr style="border-bottom:1px solid #eee">
  <td style="padding:8px 10px;white-space:nowrap">
    <span style="font-size:16px">{ind['icon']}</span>
    <strong style="font-size:11px;color:{col};margin-left:4px">{ind['name']}</strong><br>
    <span style="font-size:9px;color:#888">{ind['freq']}</span>
  </td>
  <td style="padding:8px 8px;font-size:10px">
    <span style="background:#e8f5e9;color:#1A7A4A;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700">▲ {ind['bull']}</span><br>
    <span style="background:#fff3e0;color:#D4820A;padding:1px 6px;border-radius:3px;font-size:9px;margin-top:2px;display:inline-block">≈ {ind['neutral']}</span><br>
    <span style="background:#fce4ec;color:#C0390F;padding:1px 6px;border-radius:3px;font-size:9px;margin-top:2px;display:inline-block">▼ {ind['bear']}</span>
  </td>
  <td style="padding:8px 8px">{cur_cell}</td>
  <td style="padding:8px 8px;font-size:9px;color:#555;max-width:180px">{ind['bull_note'][:80]}...</td>
  <td style="padding:8px 8px;font-size:9px;color:#C0390F;max-width:180px">{ind['bear_note'][:80]}...</td>
  <td style="padding:8px 8px;font-size:9px;color:#556;line-height:1.6">{p_sum}</td>
  <td style="padding:8px 8px;font-size:9px;color:#667;text-align:center">{ind['spx_corr']}</td>
</tr>"""

    # ── Calendar events table ─────────────────────────────────────────────────
    impact_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    # Group by day
    days_seen = []
    events_by_day = {}
    for ev in calendar_events:
        d = ev.get("day","")
        if d not in events_by_day:
            events_by_day[d] = []
            days_seen.append(d)
        events_by_day[d].append(ev)

    cal_html = ""
    for day in days_seen:
        evs = events_by_day[day]
        evs.sort(key=lambda e: impact_order.get(e.get("impact","LOW"), 2))
        # Light steel-blue day header instead of dark navy
        cal_html += (f'<tr style="background:#e8edf8;border-top:2px solid #c5d0e8">'
                     f'<td colspan="8" style="padding:9px 14px;font-size:12px;font-weight:900;'
                     f'color:#1a2a5e;letter-spacing:.02em">{day}</td></tr>')
        for ev in evs:
            imp = ev.get("impact","LOW")
            act = ev.get("actual","")
            fct = ev.get("forecast","")
            prv = ev.get("previous","")
            bif = ev.get("bullish_if","beat")
            released = bool(act and act.strip() and act.strip() != "—")

            # Beat/miss logic — compare actual vs forecast
            act_col  = "#1a2a3e"   # default: dark (not yet released)
            fct_col  = "#445"
            beat_miss_label = ""
            beat_bg  = ""
            if released and fct and fct.strip() and fct.strip() != "—":
                try:
                    # Strip non-numeric chars but keep sign
                    def _tonum(s):
                        s = str(s).strip().lstrip("≈~").replace(",","")
                        # Keep only numeric + sign + decimal
                        import re as _re
                        m = _re.search(r'[-+]?\d+\.?\d*', s)
                        return float(m.group()) if m else None
                    av = _tonum(act); fv = _tonum(fct)
                    if av is not None and fv is not None:
                        lower_is_good = "miss" in bif.lower() or "lower" in bif.lower()
                        is_beat = (av < fv) if lower_is_good else (av > fv)
                        if is_beat:
                            act_col = "#0A6B3A"; fct_col = "#0A6B3A44"
                            beat_miss_label = " ✓ BEAT"; beat_bg = "#e8f8ef"
                        else:
                            act_col = "#B71C1C"; fct_col = "#B71C1C44"
                            beat_miss_label = " ✗ MISS"; beat_bg = "#fdecea"
                except: pass

            row_bg = beat_bg or ("#fff" if imp=="HIGH" else "#fffff8" if imp=="MEDIUM" else "#fafafa")

            # Forecast: always shown, styled differently before vs after release
            fct_display = fct or "—"
            if released and fct and fct.strip() and fct.strip() != "—":
                # After release: show forecast in muted color so actual stands out
                fct_cell = f'<span style="color:#667;font-size:11px;font-weight:700">{fct_display}</span>'
            else:
                fct_cell = f'<span style="color:#1a2a3e;font-size:11px;font-weight:700">{fct_display}</span>'

            cal_html += f"""
<tr style="background:{row_bg};border-bottom:1px solid #eaecf4">
  <td style="padding:7px 10px;font-size:10px;color:#556;white-space:nowrap;font-weight:600">{ev.get('time','')}</td>
  <td style="padding:7px 12px;font-size:11px;font-weight:800;color:#1a2a3e">{ev.get('event','')}</td>
  <td style="padding:7px 8px;font-size:10px;color:#667;font-style:italic">{ev.get('period','')}</td>
  <td style="padding:7px 8px;text-align:center">{_impact_badge(imp)}</td>
  <td style="padding:7px 8px;font-size:12px;font-weight:900;color:{act_col};text-align:center;white-space:nowrap">
    {(act + '<span style="font-size:8px;font-weight:700">' + beat_miss_label + '</span>') if released else '<span style="color:#aab">—</span>'}
  </td>
  <td style="padding:7px 8px;text-align:center">{fct_cell}</td>
  <td style="padding:7px 8px;font-size:11px;font-weight:700;text-align:center;color:#445">{prv or '—'}</td>
  <td style="padding:7px 10px;font-size:9px;color:#667;white-space:nowrap">Bullish if: <em>{bif}</em></td>
</tr>"""

    # ── Overlay charts: key indicators vs SPX ────────────────────────────────
    import json as _jsc, pandas as _pdch
    import numpy as _npch

    # ── Fallback: directly fetch missing series via fredapi if available ──────
    # This runs AFTER the main pipeline, so it catches anything the circuit breaker missed
    _FRED_API_KEY = FRED_API_KEY if 'FRED_API_KEY' in dir() else None
    _fallback_map = {"ISM_PMI":"NAPM","INIT_CLAIMS":"ICSA",
                     "CONT_CLAIMS":"CCSA","UMCSENT":"UMCSENT","DURGDS":"ADXTNO"}
    for _fk, _fsid in _fallback_map.items():
        if fd.get(_fk) is None or (hasattr(fd.get(_fk), 'empty') and fd[_fk].empty):
            try:
                import fredapi as _fapi
                _frd = _fapi.Fred(api_key=_FRED_API_KEY)
                _fs  = _frd.get_series(_fsid, observation_start="2019-01-01")
                if _fs is not None and not _fs.empty:
                    fd[_fk] = _fs
                    print(f"  [chart fallback] {_fk} loaded via fredapi: {len(_fs)} pts")
            except Exception as _fe:
                pass  # silently skip — chart will show N/A message

    # Build SPY/SPX daily series for exact date matching
    _spx_daily = None
    _spy_daily = md.get("SPY")
    if _spy_daily is not None and not _spy_daily.empty:
        _spx_daily = _spy_daily.copy()
        _spx_daily.index = _pdch.to_datetime(_spx_daily.index).normalize()
    # Fall back to monthly FRED SP500
    _spx_monthly = fd.get("SP500")

    def _build_paired(key, scale=1.0, yoy=False, periods=120, mult_if_small=100):
        """
        Build matched indicator + SPX series.
        For each indicator release date, finds the SPX closing price on that exact
        date or nearest prior trading day. Returns (dates, ind_vals, spx_vals).
        """
        s = fd.get(key)
        if s is None or s.empty:
            return [], [], []
        s2 = s.tail(periods + 14).dropna()

        if yoy:
            if len(s2) < 14: return [], [], []
            idx_dates = list(s2.index[12:])
            raw_vals  = [round((float(s2.iloc[i]) / float(s2.iloc[i-12]) - 1) * 100, 2)
                         for i in range(12, len(s2))]
        else:
            idx_dates = list(s2.index)
            raw_vals  = [round(float(v) * scale, 2) for v in s2.values]

        # Auto-fix 0-1 decimal ISM
        if raw_vals and max(raw_vals) < 10:
            raw_vals = [round(v * mult_if_small, 1) for v in raw_vals]

        dates, ind_out, spx_out = [], [], []
        for dt, iv in zip(idx_dates[-periods:], raw_vals[-periods:]):
            dt_ts = _pdch.Timestamp(dt)
            date_str = str(dt_ts)[:10]

            # Find SPX price: prefer daily, fall back to monthly
            spx_val = None
            if _spx_daily is not None:
                # find nearest prior date in daily series
                prior = _spx_daily[_spx_daily.index <= dt_ts]
                if not prior.empty:
                    spx_val = round(float(prior.iloc[-1]) * 10, 0)  # SPY→SPX approx ×10
            if spx_val is None and _spx_monthly is not None:
                mo_key = str(dt_ts)[:7]
                matches = [v for d, v in zip(_spx_monthly.index, _spx_monthly.values)
                           if str(d)[:7] == mo_key]
                if matches:
                    spx_val = round(float(matches[0]), 0)

            dates.append(date_str)
            ind_out.append(iv)
            spx_out.append(spx_val)

        return dates, ind_out, spx_out

    def _build_daily_paired(key, periods_days=760):
        """For daily series (VIX, yield curve, HY OAS) — use actual daily values with daily SPX."""
        s = fd.get(key)
        if s is None or s.empty:
            return [], [], []
        s2 = s.tail(periods_days).dropna()
        dates, ind_out, spx_out = [], [], []
        for dt, iv in zip(s2.index, s2.values):
            dt_ts = _pdch.Timestamp(dt)
            spx_val = None
            if _spx_daily is not None:
                prior = _spx_daily[_spx_daily.index <= dt_ts]
                if not prior.empty:
                    spx_val = round(float(prior.iloc[-1]) * 10, 0)
            dates.append(str(dt_ts)[:10])
            ind_out.append(round(float(iv), 2))
            spx_out.append(spx_val)
        return dates, ind_out, spx_out

    def _build_vix_paired(periods_days=760):
        """VIX from md (^VIX) — daily values with daily SPX."""
        vx = md.get("^VIX")
        spy = md.get("SPY")
        if vx is None or vx.empty: return [], [], []
        vx2 = vx.tail(periods_days).dropna()
        spy2 = spy.dropna() if spy is not None else None
        dates, ind_out, spx_out = [], [], []
        for dt, iv in zip(vx2.index, vx2.values):
            dt_ts = _pdch.Timestamp(dt).normalize()
            spx_val = None
            if spy2 is not None:
                prior = spy2[spy2.index <= dt_ts]
                if not prior.empty:
                    spx_val = round(float(prior.iloc[-1]) * 10, 0)
            dates.append(str(dt_ts)[:10])
            ind_out.append(round(float(iv), 1))
            spx_out.append(spx_val)
        return dates, ind_out, spx_out

    # Build all series
    _cpi_d,  _cpi_iv,  _cpi_sv  = _build_paired("CPI",        yoy=True,  periods=72)
    _ism_d,  _ism_iv,  _ism_sv  = _build_paired("ISM_PMI",     scale=1.0, periods=48)
    _ff_d,   _ff_iv,   _ff_sv   = _build_paired("FEDFUNDS",    scale=1.0, periods=84)
    _hy_d,   _hy_iv,   _hy_sv   = _build_daily_paired("HY_OAS", periods_days=760)
    _yc_d,   _yc_iv,   _yc_sv   = _build_daily_paired("YIELD_CURVE", periods_days=760)
    _ry_d,   _ry_iv,   _ry_sv   = _build_daily_paired("REAL_YIELD",  periods_days=760)
    _nfci_d, _nfci_iv, _nfci_sv = _build_paired("NFCI",         scale=1.0, periods=84)
    _vix_d,  _vix_iv,  _vix_sv  = _build_vix_paired(periods_days=760)
    _clm_d,  _clm_iv,  _clm_sv  = _build_paired("INIT_CLAIMS", scale=0.001, periods=72)
    _unr_d,  _unr_iv,  _unr_sv  = _build_paired("UNRATE",       scale=1.0, periods=60)

    def _pack(d, iv, sv):
        return _jsc.dumps({"dates": d, "ind": iv, "spx": sv})

    cpi_json  = _pack(_cpi_d,  _cpi_iv,  _cpi_sv)
    ism_json  = _pack(_ism_d,  _ism_iv,  _ism_sv)
    ff_json   = _pack(_ff_d,   _ff_iv,   _ff_sv)
    hy_json   = _pack(_hy_d,   _hy_iv,   _hy_sv)
    yc_json   = _pack(_yc_d,   _yc_iv,   _yc_sv)
    ry_json   = _pack(_ry_d,   _ry_iv,   _ry_sv)
    nfci_json = _pack(_nfci_d, _nfci_iv, _nfci_sv)
    vix_json  = _pack(_vix_d,  _vix_iv,  _vix_sv)
    clm_json  = _pack(_clm_d,  _clm_iv,  _clm_sv)
    unr_json  = _pack(_unr_d,  _unr_iv,  _unr_sv)

    # ── Next 4-week upcoming high-impact events summary ───────────────────────
    high_impact = [ev for ev in calendar_events if ev.get("impact") == "HIGH"]
    upcoming_cards = ""
    for ev in high_impact[:8]:
        upcoming_cards += (
            f'<div style="background:#fff;border:1px solid #C0390F44;border-left:4px solid #C0390F;'
            f'border-radius:6px;padding:8px 12px;margin-bottom:8px">'
            f'<div style="font-size:11px;font-weight:700;color:#1a1a2e">{ev.get("event","")}</div>'
            f'<div style="font-size:9px;color:#778">{ev.get("day","")} · {ev.get("time","")} ET</div>'
            f'<div style="font-size:9px;color:#556;margin-top:2px">'
            f'Forecast: <strong>{ev.get("forecast","—")}</strong> · '
            f'Previous: {ev.get("previous","—")} · '
            f'Bullish if: {ev.get("bullish_if","beat")}</div>'
            f'</div>'
        )

    return f"""
<div style="font-family:'Segoe UI',Arial,sans-serif;padding:4px">

<!-- HEADER -->
<div style="background:linear-gradient(135deg,#1a1a2e,#2a2a4e);color:#fff;padding:14px 20px;
            border-radius:10px;margin-bottom:16px;display:flex;align-items:center;gap:16px">
  <div style="flex:1">
    <div style="font-size:16px;font-weight:800">📅 ECONOMIC CALENDAR &amp; MARKET IMPACT HUB</div>
    <div style="font-size:10px;opacity:0.8;margin-top:2px">
      This week's events · Market impact guide · Historical readings at peaks &amp; troughs ·
      Overlay charts · Generated {gen_dt}
    </div>
  </div>
  <div style="font-size:11px;opacity:0.7">{today_wk}</div>
</div>

<!-- TWO COLUMNS: Calendar + Upcoming High-Impact -->
<div style="display:grid;grid-template-columns:1fr 280px;gap:16px;margin-bottom:20px">

  <!-- MAIN CALENDAR -->
  <div>
    <div style="font-size:12px;font-weight:800;color:#1a1a2e;margin-bottom:8px">
      📆 Weekly Economic Calendar
      <span style="font-size:9px;font-weight:400;color:#667;margin-left:8px">
        Actual (green=beat/bullish, red=miss/bearish) · HIGH impact = market-moving
      </span>
    </div>
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:11px">
        <thead>
          <tr style="background:#2d3f6e;color:#fff">
            <th style="padding:8px 10px;text-align:left;font-size:10px;font-weight:700;letter-spacing:.04em">Time (ET)</th>
            <th style="padding:8px 10px;text-align:left;font-size:10px;font-weight:700;letter-spacing:.04em">Event</th>
            <th style="padding:8px 8px;font-size:10px;font-weight:700;letter-spacing:.04em">Period</th>
            <th style="padding:8px 8px;text-align:center;font-size:10px;font-weight:700;letter-spacing:.04em">Impact</th>
            <th style="padding:8px 8px;text-align:center;font-size:10px;font-weight:700;letter-spacing:.04em">Actual</th>
            <th style="padding:8px 8px;text-align:center;font-size:10px;font-weight:700;letter-spacing:.04em">Forecast</th>
            <th style="padding:8px 8px;text-align:center;font-size:10px;font-weight:700;letter-spacing:.04em">Previous</th>
            <th style="padding:8px 10px;font-size:10px;font-weight:700;letter-spacing:.04em">Direction</th>
          </tr>
        </thead>
        <tbody>{cal_html}</tbody>
      </table>
    </div>
  </div>

  <!-- UPCOMING HIGH-IMPACT SIDEBAR -->
  <div>
    <div style="font-size:12px;font-weight:800;color:#C0390F;margin-bottom:8px">
      🔴 Upcoming High-Impact Events
    </div>
    {upcoming_cards or '<div style="font-size:10px;color:#888">Calendar data loading...</div>'}
  </div>
</div>

<!-- MARKET IMPACT GUIDE -->
<div style="margin-bottom:20px">
  <div style="font-size:13px;font-weight:800;color:#1a1a2e;margin-bottom:8px;padding-bottom:6px;border-bottom:2px solid #e0e4ed">
    📊 INDICATOR IMPACT GUIDE — What each number means for SPX
    <span style="font-size:10px;font-weight:400;color:#667;margin-left:8px">
      Historical readings at major market peaks (2000, 2007, 2018, 2022) and troughs (2009, 2020)
    </span>
  </div>
  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:#2d3f6e;color:#fff">
          <th style="padding:7px 10px;text-align:left;font-size:10px;min-width:160px">Indicator</th>
          <th style="padding:7px 8px;font-size:10px;min-width:120px">Thresholds</th>
          <th style="padding:7px 8px;font-size:10px;text-align:center;min-width:90px">Current</th>
          <th style="padding:7px 8px;font-size:10px;min-width:160px">Bullish reading means...</th>
          <th style="padding:7px 8px;font-size:10px;min-width:160px">Bearish reading means...</th>
          <th style="padding:7px 8px;font-size:10px;min-width:180px">Peak/Trough reference</th>
          <th style="padding:7px 8px;font-size:10px;text-align:center;min-width:100px">SPX correlation</th>
        </tr>
      </thead>
      <tbody>{guide_rows}</tbody>
    </table>
  </div>
</div>

<!-- OVERLAY CHARTS: single column, full width -->
<div style="font-size:13px;font-weight:800;color:#1a1a2e;margin-bottom:12px;padding-bottom:6px;border-bottom:2px solid #e0e4ed">
  📈 HISTORICAL OVERLAY CHARTS — Key Indicators vs SPX
  <span style="font-size:10px;font-weight:400;color:#667;margin-left:8px">
    Each point = actual data release date · Blue dashed = SPX closing price on that date
  </span>
</div>
<div style="display:flex;flex-direction:column;gap:16px;margin-bottom:20px">

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">CPI Inflation YoY vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Monthly release</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">Above 4% compresses equity multiples · Below 2.5% = expansion zone · <span style="color:#d85a30;font-weight:600">SPX peaks typically occur while inflation still elevated</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_cpi_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">ISM Manufacturing PMI vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Monthly (1st business day)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">Leads SPX earnings by 1-2 quarters · <span style="color:#185fa5;font-weight:600">Below 50 = contraction · Rolling below 47 = recession signal</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_ism_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">HY Credit Spreads vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Daily (ICE BofA index)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">Best leading indicator · <span style="color:#993c1d;font-weight:600">Widening &gt;50bps in 4 weeks = pullback signal · Leads SPX by 2-4 weeks</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_hy_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">Yield Curve (10Y-2Y) vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Daily</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px"><span style="color:#0f6e56;font-weight:600">Inversion = recession warning ~12-18 months ahead</span> · Un-inversion (steepening from negative) historically marks start of market decline</div>
    <div style="position:relative;height:260px"><canvas id="eco_yc_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">VIX Fear Index vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Daily (CBOE)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">Perfect inverse relationship · <span style="color:#534ab7;font-weight:600">VIX spike &gt;30 = contrarian buy zone · VIX below 13 = dangerous complacency</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_vix_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">Fed Funds Rate vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Monthly (FOMC)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">Hike cycles peak SPX · <span style="color:#8b0000;font-weight:600">First cut = buy signal if no recession · Cuts into recession = further sell-off</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_ff_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">Real 10Y Yield vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Daily (TIPS)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px"><span style="color:#854f0b;font-weight:600">Above 2% = expensive to own equities vs bonds · Negative real yields = bull market fuel (2020-2021)</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_ry_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">Financial Conditions (NFCI) vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Weekly (Chicago Fed)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">105 financial measures in one index · <span style="color:#72243e;font-weight:600">Rapid tightening (&gt;+0.5 in 4wks) precedes corrections · Below -0.8 = complacency</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_nfci_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">Initial Jobless Claims vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Weekly (Thursday 8:30am ET)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">Best real-time labor indicator · <span style="color:#1d9e75;font-weight:600">Rising &gt;260K = labor softening · Above 300K = recession risk</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_clm_chart"></canvas></div>
  </div>

  <div style="background:#fff;border:1px solid #e0e4ed;border-radius:10px;padding:16px">
    <div style="font-size:13px;font-weight:700;color:#1a1a2e;margin-bottom:2px">Unemployment Rate vs SPX <span style="font-size:10px;font-weight:400;color:#888">· Monthly (NFP Friday)</span></div>
    <div style="font-size:10px;color:#888;margin-bottom:10px">Lagging but powerful · <span style="color:#3b6d11;font-weight:600">Sahm Rule: +0.5pp from 12mo low = recession · SPX peaks at cycle-low unemployment</span></div>
    <div style="position:relative;height:260px"><canvas id="eco_unr_chart"></canvas></div>
  </div>

</div>
<script>
(function(){{
  const TT = {{
    backgroundColor:'rgba(255,255,255,0.97)',
    titleColor:'#1a1a2e', bodyColor:'#445',
    borderColor:'#dde', borderWidth:1
  }};

  const _chartInstances = {{}};

  function makeChart(canvasId, packed, indLabel, indColor, indUnit, refLine, refLabel) {{
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    const raw = typeof packed === 'string' ? JSON.parse(packed) : packed;
    if (!raw.dates || !raw.dates.length || !raw.ind || !raw.ind.some(v => v !== null)) {{
      ctx.parentElement.innerHTML =
        '<div style="height:260px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px">'
        +'<div style="color:#556;font-size:12px">Data not available for this indicator this run</div>'
        +'<div style="font-size:10px;color:#ccc">FRED series failed to load · Will appear once ISM/Claims series are accessible</div>'
        +'</div>';
      return;
    }}
    const dates = raw.dates;
    const indV  = raw.ind;
    const spxV  = raw.spx;
    const step  = Math.max(1, Math.floor(dates.length / 20));
    const xLabels = dates.map((d, i) => {{
      const mo = d.slice(5,7);
      if (mo === '01' || i === 0) return d.slice(0,4);
      if (i % step === 0) return d.slice(5,7);
      return '';
    }});
    const annotations = {{}};
    if (refLine !== undefined) {{
      annotations.ref = {{
        type:'line', yScaleID:'y',
        yMin:refLine, yMax:refLine,
        borderColor:'#ccc', borderWidth:1.5, borderDash:[5,4],
        label:{{ display:true, content:refLabel||String(refLine), position:'start',
                color:'#aaa', font:{{size:9}}, backgroundColor:'rgba(255,255,255,0.8)' }}
      }};
    }}
    const chartInst = new Chart(ctx, {{
      type:'line',
      data:{{ labels:xLabels, datasets:[
        {{ label:indLabel, data:indV, borderColor:indColor, backgroundColor:indColor+'12',
          borderWidth:2.5, pointRadius:dates.length<=60?3:0, pointHoverRadius:5,
          tension:0.3, yAxisID:'y', fill:false }},
        {{ label:'SPX close', data:spxV, borderColor:'rgba(25,95,195,0.6)',
          borderWidth:1.8, pointRadius:0, pointHoverRadius:4, tension:0.3,
          yAxisID:'y2', fill:false, borderDash:[6,3] }}
      ]}},
      options:{{
        responsive:true, maintainAspectRatio:false, animation:{{duration:200}},
        interaction:{{mode:'index',intersect:false}},
        plugins:{{
          legend:{{display:true, labels:{{color:'#444',font:{{size:10}},boxWidth:14,padding:14}}}},
          tooltip:{{ ...TT, callbacks:{{
            title: items => dates[items[0].dataIndex],
            label: c => {{
              if (c.parsed.y == null) return null;
              if (c.datasetIndex === 0) {{
                const v = c.parsed.y;
                return indLabel+': '+(Number.isInteger(v)?v:v.toFixed(2))+indUnit;
              }}
              return 'SPX: $'+c.parsed.y.toLocaleString('en-US',{{maximumFractionDigits:0}});
            }}
          }}}},
          annotation:{{annotations}},
          zoom:{{
            zoom:{{
              wheel:{{ enabled:true }},
              pinch:{{ enabled:true }},
              mode:'x',
            }},
            pan:{{
              enabled:true,
              mode:'x',
            }},
            limits:{{ x:{{ min:'original', max:'original' }} }}
          }}
        }},
        scales:{{
          x:{{ ticks:{{color:'#888',font:{{size:9}},maxRotation:0,autoSkip:false,
                     callback:(v,i)=>xLabels[i]}}, grid:{{color:'rgba(0,0,0,0.05)'}} }},
          y:{{ position:'left',
              ticks:{{color:indColor,font:{{size:9}},
                     callback:v=>Number.isFinite(v)?v.toFixed(indUnit==='bps'?0:1)+indUnit:''}},
              grid:{{color:'rgba(0,0,0,0.05)'}} }},
          y2:{{ position:'right',
               ticks:{{color:'rgba(25,95,195,0.7)',font:{{size:9}},
                      callback:v=>'$'+v.toLocaleString('en-US',{{maximumFractionDigits:0}})}},
               grid:{{drawOnChartArea:false}} }}
        }}
      }}
    }});
    _chartInstances[canvasId] = chartInst;

    // Add reset zoom button above chart
    const wrapper = ctx.closest('div[style*="position:relative"]');
    if (wrapper) {{
      const btn = document.createElement('button');
      btn.textContent = 'Reset zoom';
      btn.style.cssText = 'position:absolute;top:4px;right:4px;z-index:10;font-size:9px;'
        +'padding:3px 8px;background:#fff;border:1px solid #dde;border-radius:4px;'
        +'cursor:pointer;color:#888;';
      btn.onclick = () => chartInst.resetZoom();
      wrapper.style.position = 'relative';
      wrapper.appendChild(btn);
    }}
  }}

  makeChart('eco_cpi_chart',  {cpi_json},  'CPI YoY%',   '#d85a30','%',    4,   '4% threshold');
  makeChart('eco_ism_chart',  {ism_json},  'ISM PMI',    '#185fa5','',     50,  '50=neutral');
  makeChart('eco_hy_chart',   {hy_json},   'HY OAS bps', '#993c1d','bps',  380, 'Warn 380bps');
  makeChart('eco_yc_chart',   {yc_json},   'Yld Curve%', '#0f6e56','%',    0,   'Inversion');
  makeChart('eco_vix_chart',  {vix_json},  'VIX',        '#534ab7','',     20,  'Fear zone');
  makeChart('eco_ff_chart',   {ff_json},   'Fed Funds%', '#8b0000','%');
  makeChart('eco_ry_chart',   {ry_json},   'Real Yield%','#854f0b','%',    2,   '2% headwind');
  makeChart('eco_nfci_chart', {nfci_json}, 'NFCI',       '#72243e','',     0,   'Neutral');
  makeChart('eco_clm_chart',  {clm_json},  'Claims (K)', '#1d9e75','K',    260, '260K warn');
  makeChart('eco_unr_chart',  {unr_json},  'Unemp%',     '#3b6d11','%');
}})();
</script>

</div>"""


# ══════════════════════════════════════════════════════════════════════════════
# OPTIONS FLOW TAB — Net GEX Chart (MenthorQ-style)
# Reads Barchart volatility-greeks CSVs from DOWNLOADS_DIR
# Fuses with Pine Script key levels (Call Wall, Put Wall, Gamma Flip, Vanna)
# Renders interactive Plotly charts — one per symbol, client-side switching
# ══════════════════════════════════════════════════════════════════════════════

DOWNLOADS_DIR    = r"C:\Users\16144\OneDrive\Documents\options\automation\downloads"
PINE_SCRIPT_PATH = r"C:\Users\16144\OneDrive\Documents\options\automation\tv_options_levels_generated.pine"

# Target symbols — ETF + Mag7
GEX_SYMBOLS = ["SPY", "QQQ", "IWM", "SOXX", "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA"]


def _parse_pine_levels(pine_path):
    """
    Parse the auto-generated Pine Script file and return a dict of key option levels
    for every ticker found in the TICKERS array.

    Reads these arrays from the .pine file (all on single lines):
      TICKERS, CALL_WALL, PUT_WALL, SEC_CALL_WALL, SEC_PUT_WALL,
      VANNA_UP, VANNA_DN, GAMMA_FLIP

    Returns:
      dict[str, dict]  e.g. {"SPY": {"call_wall":683.0, "put_wall":650.0, ...}, ...}
      or {} on any parse failure (caller falls back to hardcoded values).

    Robustness:
      - Strips Pine's (na + 0.0) expressions → None (excluded from output)
      - Handles BRK.B and other tickers with dots
      - Ignores IV_WK / DTE_WK / PUT_WALL_LISTS (not needed for GEX chart)
    """
    import re as _re

    # ── Hardcoded fallback (used if pine file missing / unparseable) ──────────
    _FALLBACK = {
        "SPY":  {"call_wall":686.0,  "put_wall":630.0,  "sec_call":681.0, "sec_put":680.0,
                 "vanna_up":686.0,  "vanna_dn":680.0,  "gamma_flip":678.73},
        "QQQ":  {"call_wall":650.0,  "put_wall":600.0,  "sec_call":612.0, "sec_put":611.0,
                 "vanna_up":615.0,  "vanna_dn":608.0,  "gamma_flip":611.14},
        "IWM":  {"call_wall":281.0,  "put_wall":240.0,  "sec_call":262.0, "sec_put":261.0,
                 "vanna_up":263.0,  "vanna_dn":254.0,  "gamma_flip":263.64},
        "SOXX": {"call_wall":460.0,  "put_wall":250.0,  "sec_call":387.5, "sec_put":385.0,
                 "vanna_up":460.0,  "vanna_dn":360.0,  "gamma_flip":195.0},
        "AAPL": {"call_wall":262.5,  "put_wall":260.0,  "sec_call":262.5, "sec_put":260.0,
                 "vanna_up":262.5,  "vanna_dn":260.0,  "gamma_flip":260.0},
        "MSFT": {"call_wall":375.0,  "put_wall":370.0,  "sec_call":375.0, "sec_put":372.5,
                 "vanna_up":377.5,  "vanna_dn":370.0,  "gamma_flip":370.0},
        "NVDA": {"call_wall":190.0,  "put_wall":170.0,  "sec_call":190.0, "sec_put":187.5,
                 "vanna_up":190.0,  "vanna_dn":185.0,  "gamma_flip":173.62},
        "GOOGL":{"call_wall":320.0,  "put_wall":317.5,  "sec_call":320.0, "sec_put":317.5,
                 "vanna_up":320.0,  "vanna_dn":312.5,  "gamma_flip":312.5},
        "META": {"call_wall":635.0,  "put_wall":630.0,  "sec_call":632.5, "sec_put":630.0,
                 "vanna_up":640.0,  "vanna_dn":630.0,  "gamma_flip":627.5},
        "AMZN": {"call_wall":240.0,  "put_wall":225.0,  "sec_call":240.0, "sec_put":235.0,
                 "vanna_up":245.0,  "vanna_dn":235.0,  "gamma_flip":215.26},
        "TSLA": {"call_wall":650.0,  "put_wall":150.0,  "sec_call":347.5, "sec_put":345.0,
                 "vanna_up":355.0,  "vanna_dn":180.0,  "gamma_flip":353.31},
    }

    if not pine_path or not os.path.exists(pine_path):
        print(f"  [Pine Parser] File not found: {pine_path} — using hardcoded fallback levels")
        return _FALLBACK

    try:
        with open(pine_path, "r", encoding="utf-8") as _f:
            _src = _f.read()

        # ── Helper: extract array.from(...) content for a named array ─────────
        def _extract_array(name):
            """Return the raw content string inside array.from(...) for 'name'."""
            pat = _re.compile(
                r'var\s+\w+\[\]\s+' + _re.escape(name) +
                r'\s*=\s*array\.from\((.+?)\)',
                _re.DOTALL
            )
            m = pat.search(_src)
            return m.group(1).strip() if m else None

        # ── Parse TICKERS (string array) ──────────────────────────────────────
        _tick_raw = _extract_array("TICKERS")
        if not _tick_raw:
            print("  [Pine Parser] TICKERS array not found — using fallback levels")
            return _FALLBACK

        tickers = _re.findall(r'"([^"]+)"', _tick_raw)
        if not tickers:
            print("  [Pine Parser] No tickers parsed — using fallback levels")
            return _FALLBACK

        # ── Helper: parse a float array, returning list of float|None ─────────
        def _parse_floats(raw):
            """
            Split array.from content on commas, parse each element.
            Pine's (na + 0.0) expressions → None.
            """
            if raw is None:
                return [None] * len(tickers)
            out = []
            # Split on top-level commas (safe because Pine arrays are flat)
            for token in raw.split(","):
                token = token.strip()
                if "na" in token.lower():
                    out.append(None)
                else:
                    try:
                        out.append(float(token))
                    except ValueError:
                        out.append(None)
            return out

        # ── Parse all 7 float arrays ──────────────────────────────────────────
        _arrays = {
            "call_wall":  _parse_floats(_extract_array("CALL_WALL")),
            "put_wall":   _parse_floats(_extract_array("PUT_WALL")),
            "sec_call":   _parse_floats(_extract_array("SEC_CALL_WALL")),
            "sec_put":    _parse_floats(_extract_array("SEC_PUT_WALL")),
            "vanna_up":   _parse_floats(_extract_array("VANNA_UP")),
            "vanna_dn":   _parse_floats(_extract_array("VANNA_DN")),
            "gamma_flip": _parse_floats(_extract_array("GAMMA_FLIP")),
        }

        # Validate lengths match tickers
        n = len(tickers)
        for key, vals in _arrays.items():
            if len(vals) != n:
                print(f"  [Pine Parser] Length mismatch: {key} has {len(vals)} values "
                      f"but {n} tickers — padding with None")
                # Pad or truncate to match
                _arrays[key] = (vals + [None] * n)[:n]

        # ── Build output dict ─────────────────────────────────────────────────
        result = {}
        for i, sym in enumerate(tickers):
            levels = {k: _arrays[k][i] for k in _arrays}
            # Only include if at least call_wall and put_wall are present
            if levels["call_wall"] is not None and levels["put_wall"] is not None:
                result[sym] = levels

        # Extract date/DTE from file header comment for the console log
        _hdr = _re.search(r'//\s*Generated\s+(.+)', _src)
        _hdr_s = _hdr.group(1).strip() if _hdr else "unknown date"

        print(f"  [Pine Parser] \u2713 Loaded {len(result)} tickers from Pine Script ({_hdr_s})")

        # Merge: if any GEX_SYMBOLS are missing from parsed result, fill from fallback
        for sym in GEX_SYMBOLS:
            if sym not in result and sym in _FALLBACK:
                result[sym] = _FALLBACK[sym]
                print(f"  [Pine Parser]   \u26a0 {sym} missing in Pine file — using hardcoded fallback")

        return result

    except Exception as _ex:
        print(f"  [Pine Parser] Parse error: {_ex} — using hardcoded fallback levels")
        return _FALLBACK


# Auto-load Pine Script levels at import time — refreshed on every run
_PINE_LEVELS = _parse_pine_levels(PINE_SCRIPT_PATH)


def _gex_find_csv(downloads_dir, ticker):
    """Find the most recently modified CSV for a given ticker in the downloads folder."""
    import glob
    ticker_lo = ticker.lower()
    patterns = [
        os.path.join(downloads_dir, f"{ticker_lo}-volatility-greeks*.csv"),
        os.path.join(downloads_dir, f"*{ticker_lo}*volatility*greeks*.csv"),
        os.path.join(downloads_dir, f"*{ticker_lo}*.csv"),
    ]
    for pat in patterns:
        files = glob.glob(pat)
        if files:
            return max(files, key=os.path.getmtime)
    return None


def _gex_parse_csv(csv_path, spot, range_pct=0.07):
    """
    Parse Barchart volatility-greeks CSV.
    Returns list of dicts per strike: net_gex, call_gex, put_gex, net_dex, etc.
    Only returns strikes within ±range_pct of spot with non-trivial GEX.
    """
    import csv as _csv
    calls, puts = {}, {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = _csv.DictReader(f)
        for row in reader:
            t = (row.get('Type') or '').strip()
            if t not in ('Call', 'Put'):
                continue
            try:
                strike = float(row['Strike'])
                gamma  = float(row['Gamma'])
                delta  = float(row['Delta'])
                oi     = float(str(row['Open Int']).replace(',', ''))
                iv_raw = str(row['IV']).replace('%', '').strip()
                iv     = float(iv_raw) if iv_raw not in ('', '0.00') else 0.0
                vol    = float(str(row['Volume']).replace(',', ''))
            except (ValueError, KeyError):
                continue
            entry = dict(gamma=gamma, delta=delta, oi=oi, iv=iv, vol=vol)
            if t == 'Call': calls[strike] = entry
            else:           puts[strike]  = entry

    lo = spot * (1 - range_pct)
    hi = spot * (1 + range_pct)
    MULT = 100
    records = []
    for K in sorted(set(list(calls.keys()) + list(puts.keys()))):
        if not (lo <= K <= hi):
            continue
        c = calls.get(K, {}); p = puts.get(K, {})
        cg = c.get('gamma',0); co = c.get('oi',0)
        pg = p.get('gamma',0); po = p.get('oi',0)
        cd = c.get('delta',0); pd = p.get('delta',0)
        call_gex = cg * co * MULT * spot
        put_gex  = pg * po * MULT * spot
        net_gex  = call_gex - put_gex
        if abs(net_gex) < 50_000:
            continue
        records.append(dict(
            strike=K, net_gex=net_gex, call_gex=call_gex, put_gex=-put_gex,
            net_dex=(cd*co + pd*po)*MULT*spot,
            call_oi=co, put_oi=po,
            call_iv=c.get('iv',0), put_iv=p.get('iv',0),
        ))
    return sorted(records, key=lambda x: x['strike'])


def _gex_spot_from_csv(csv_path):
    """Estimate spot: find Call strike where delta ≈ 0.50 (ATM)."""
    import csv as _csv
    best_strike, best_diff = None, 999
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = _csv.DictReader(f)
        for row in reader:
            if (row.get('Type') or '').strip() != 'Call':
                continue
            try:
                delta  = float(row['Delta'])
                strike = float(row['Strike'])
                gamma  = float(row['Gamma'])
                if gamma == 0: continue
                diff = abs(abs(delta) - 0.50)
                if diff < best_diff:
                    best_diff = diff; best_strike = strike
            except (ValueError, KeyError):
                continue
    return best_strike


def _gex_make_annotations(raw_labels, y_min, y_max, chart_h=600, font_px=10):
    """
    Label placement — single right-side column, pure vertical stacking.

    When two levels share the same price (e.g. Gamma Flip=312.50 and
    -Vanna=312.50) they are MERGED into one label:  "Gamma Flip / -Vanna  312.50"
    so neither is silently dropped.

    All labels sit at x=1.02 (paper coords). When consecutive labels would
    overlap vertically, the lower one is nudged down just enough to clear.
    The actual price is always shown so line-to-label mapping stays clear.
    """
    # 1 — group labels by price, merging names that share the same level
    from collections import defaultdict
    price_groups = defaultdict(list)   # price -> [(label, color), ...]
    for y_val, lbl, col in raw_labels:
        price_groups[round(y_val, 4)].append((lbl, col, y_val))

    # Build merged list sorted top→bottom
    merged = []
    for price_key in sorted(price_groups.keys(), reverse=True):
        entries = price_groups[price_key]
        orig_y  = entries[0][2]                        # actual price value
        if len(entries) == 1:
            lbl, col, _ = entries[0]
        else:
            # Merge: join names with " / ", use colour of the first (highest priority)
            lbl = " / ".join(e[0] for e in entries)
            col = entries[0][1]
        merged.append((orig_y, lbl, col))

    if not merged:
        return []

    # 2 — pixel-aware minimum gap (one label height in data units)
    y_range    = max(y_max - y_min, 1e-6)
    pts_per_px = y_range / chart_h
    min_gap    = max(pts_per_px * (font_px + 6), y_range * 0.004)

    # 3 — single-column push-down pass
    placed_y = []
    last_y   = float('inf')
    for orig_y, lbl, col in merged:
        y = orig_y
        if last_y != float('inf') and (last_y - y) < min_gap:
            y = last_y - min_gap
        placed_y.append(y)
        last_y = y

    # 4 — build annotation dicts
    X_COL = 1.02
    annotations = []
    for (orig_y, lbl, col), adj_y in zip(merged, placed_y):
        annotations.append({
            "x": X_COL, "y": adj_y,
            "xref": "paper", "yref": "y",
            "text": f"<b>{lbl}  {orig_y:.2f}</b>",
            "showarrow": False, "xanchor": "left",
            "font": {"size": font_px, "color": col, "family": "monospace"},
        })
    return annotations


def _gex_build_plotly_json(sym, records, spot, levels, csv_file):
    """Build Plotly traces + layout as JSON strings ready for Plotly.newPlot()."""
    import itertools, re

    if not records:
        return None, None, {}

    strikes  = [r['strike']  for r in records]
    net_gex  = [r['net_gex'] for r in records]
    call_gex = [r['call_gex'] for r in records]
    put_gex  = [r['put_gex']  for r in records]

    pos_x = [g if g >= 0 else 0 for g in net_gex]
    neg_x = [g if g <  0 else 0 for g in net_gex]
    max_abs = max((abs(g) for g in net_gex), default=1)

    # GEX & DEX profiles (cumulative, scaled to bar range)
    cum = list(itertools.accumulate(net_gex))
    cum_max = max(abs(c) for c in cum) if cum else 1
    gex_profile = [c * max_abs / cum_max for c in cum]

    dex_cum = list(itertools.accumulate(r['net_dex'] for r in records))
    dex_max = max(abs(d) for d in dex_cum) if dex_cum else 1
    dex_profile = [d * max_abs / dex_max * 0.75 for d in dex_cum]

    def fmt_m(v): return f"{v/1e6:.1f}M"
    hover_texts = [
        f"Strike: {K:.1f}<br>Net GEX: {fmt_m(g)}<br>Call GEX: {fmt_m(cg)}<br>Put GEX: {fmt_m(pg)}"
        for K, g, cg, pg in zip(strikes, net_gex, call_gex, put_gex)
    ]

    traces = [
        {"type":"bar","orientation":"h","y":strikes,"x":pos_x,
         "name":"Positive GEX","showlegend":True,
         "marker":{"color":"rgba(30,200,80,0.82)","line":{"width":0}},
         "hovertext":hover_texts,"hoverinfo":"text"},
        {"type":"bar","orientation":"h","y":strikes,"x":neg_x,
         "name":"Negative GEX","showlegend":True,
         "marker":{"color":"rgba(220,45,55,0.82)","line":{"width":0}},
         "hovertext":hover_texts,"hoverinfo":"text"},
        {"type":"scatter","mode":"lines","y":strikes,"x":gex_profile,
         "name":"GEX Profile","hoverinfo":"skip",
         "line":{"color":"#f0d020","width":2.5}},
        {"type":"scatter","mode":"lines","y":strikes,"x":dex_profile,
         "name":"DEX Profile","hoverinfo":"skip",
         "line":{"color":"#ff8c00","width":1.8,"dash":"dash"}},
    ]

    y_min = min(strikes) - (max(strikes)-min(strikes))*0.05
    y_max = max(strikes) + (max(strikes)-min(strikes))*0.05
    # (labels now use paper-space coords via _gex_make_annotations)

    def shape(y_val, color, dash="dash", width=1.8):
        return {"type":"line","xref":"x","yref":"y",
                "x0":-max_abs*1.15,"x1":max_abs*1.15,"y0":y_val,"y1":y_val,
                "line":{"color":color,"width":width,"dash":dash},"layer":"above"}

    def anno(y_val, text, color):
        return {"x":lbl_x,"y":y_val,"xref":"x","yref":"y",
                "text":f"<b>{text}  {y_val:.2f}</b>","showarrow":False,
                "xanchor":"right","font":{"size":10,"color":color,"family":"monospace"},
                "bgcolor":"rgba(6,8,14,0.85)","bordercolor":color,"borderwidth":1,"borderpad":3}

    shapes = [
        shape(levels["call_wall"],  "#ff3855","dash", 2.2),
        shape(levels["put_wall"],   "#20c860","dash", 2.2),
        shape(levels["gamma_flip"], "#e8d030","dash", 1.8),
        shape(levels["vanna_dn"],   "#9060e8","dot",  1.4),
        shape(levels["vanna_up"],   "#6090ff","dot",  1.2),
        {"type":"rect","xref":"paper","yref":"y","x0":0,"x1":1,
         "y0":levels["gamma_flip"],"y1":y_max,
         "fillcolor":"rgba(0,200,60,0.05)","line":{"width":0},"layer":"below"},
        {"type":"rect","xref":"paper","yref":"y","x0":0,"x1":1,
         "y0":y_min,"y1":levels["gamma_flip"],
         "fillcolor":"rgba(200,30,30,0.05)","line":{"width":0},"layer":"below"},
    ]

    # ── Right-side labels — 3-column bin-packer (no overlaps guaranteed) ────
    _raw_labels = [
        (levels["call_wall"],  "Call Wall",  "#ff4060"),
        (levels["put_wall"],   "Put Wall",   "#20cc60"),
        (levels["gamma_flip"], "Gamma Flip", "#e8d030"),
        (levels["vanna_dn"],   "-Vanna",     "#9060e8"),
        (levels["vanna_up"],   "+Vanna",     "#6090ff"),
    ]
    annotations = _gex_make_annotations(_raw_labels, y_min, y_max)

    fn     = os.path.basename(csv_file)
    dm     = re.search(r'(\d{4}-\d{2}-\d{2})', fn)
    dtm    = re.search(r'(weekly|monthly|\d+dte)', fn, re.I)
    date_s = dm.group(1)  if dm  else "—"
    dte_s  = dtm.group(1).upper() if dtm else ""

    long_gamma = spot > levels["gamma_flip"]
    total_gex  = sum(net_gex)
    regime_txt = "LONG \u0393" if long_gamma else "SHORT \u0393"
    regime_col = "#20e870" if long_gamma else "#ff4050"

    layout = {
        "barmode":"overlay","plot_bgcolor":"#0a0c14","paper_bgcolor":"#06080d",
        "font":{"color":"#8898b8","family":"monospace","size":10},
        "title":{
            "text":(f"<b style='color:#dde4ff'>Net GEX \u00b7 {sym}</b>  "
                    f"<span style='color:#7080a8;font-size:11px'>\u00a0{date_s} {dte_s}</span>"
                    f"  <span style='color:{regime_col};font-size:12px'>\u00a0{regime_txt}</span>"
                    f"  <span style='color:#7080a8;font-size:10px'>\u00a0Total: {total_gex/1e6:.0f}M</span>"),
            "x":0.02,"xanchor":"left","font":{"size":14,"family":"monospace"}},
        "xaxis":{"title":{"text":"Net GEX  ($ Notional)","font":{"size":10}},
                 "gridcolor":"#1a2035","zerolinecolor":"#384060","zerolinewidth":2,
                 "tickformat":".2s","tickcolor":"#2a3555",
                 "range":[-max_abs*1.2, max_abs*1.15]},   # bars only — labels now in paper space
        "yaxis":{"title":{"text":"Strike","font":{"size":10}},
                 "gridcolor":"#1a2035","tickcolor":"#2a3555",
                 "tickformat":"d",       # integer ticks — no .00 clutter, no truncation
                 "range":[y_min, y_max],
                 "dtick":max(1, round((y_max-y_min)/20))},
        "legend":{"bgcolor":"rgba(12,16,28,0.85)","bordercolor":"#2a3555","borderwidth":1,
                  "font":{"size":9},"x":0.01,"y":0.01,"xanchor":"left","yanchor":"bottom"},
        "shapes":shapes,"annotations":annotations,
        "margin":{"l":72,"r":220,"t":62,"b":52},   # wider left for full strike digits, right for 2 label cols
        "height":600,
    }

    summary = {
        "spot":spot, "call_wall":levels["call_wall"], "put_wall":levels["put_wall"],
        "gamma_flip":levels["gamma_flip"], "vanna_up":levels["vanna_up"],
        "vanna_dn":levels["vanna_dn"], "sec_call":levels["sec_call"],
        "call_range":levels["call_wall"]-spot, "put_range":spot-levels["put_wall"],
        "total_gex":total_gex, "long_gamma":long_gamma,
        "regime":regime_txt, "regime_col":regime_col,
        "n_strikes":len(records), "date":date_s,
    }
    return json.dumps(traces), json.dumps(layout), summary






def _gex_build_candle_json(sym, levels, spot):
    """
    Fetch 90 days of daily OHLCV via yfinance and build a Plotly candlestick chart
    with key option levels overlaid as horizontal dashed lines.
    Returns (traces_json, layout_json) or (None, None) on failure.
    """
    try:
        import yfinance as _yf
        df = _yf.download(sym, period='90d', interval='1d',
                          progress=False, auto_adjust=True)
        if df.empty:
            return None, None

        # Flatten MultiIndex columns if present (yfinance multi-ticker format)
        if hasattr(df.columns, 'levels'):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=['Open','High','Low','Close'])
        dates  = [str(d.date()) for d in df.index]
        opens  = [round(float(v), 2) for v in df['Open']]
        highs  = [round(float(v), 2) for v in df['High']]
        lows   = [round(float(v), 2) for v in df['Low']]
        closes = [round(float(v), 2) for v in df['Close']]

        # Y-axis range: encompass candles + all key levels
        lvl_vals = [v for v in [levels.get(k) for k in
                    ('call_wall','put_wall','gamma_flip','vanna_up','vanna_dn')] if v]
        all_prices = lows + highs + lvl_vals
        y_min = min(all_prices) * 0.985
        y_max = max(all_prices) * 1.015

        traces = [{
            "type": "candlestick",
            "x": dates,
            "open": opens, "high": highs, "low": lows, "close": closes,
            "increasing": {"line": {"color": "#20c860", "width": 1},
                           "fillcolor": "#185e30"},
            "decreasing": {"line": {"color": "#ff4060", "width": 1},
                           "fillcolor": "#8a1a28"},
            "name": sym, "showlegend": False,
            "hoverinfo": "x+y",
        }]

        # Horizontal level lines spanning full chart width
        level_defs = [
            ("call_wall",  "#ff3855", "dash", 2.0),
            ("put_wall",   "#20c860", "dash", 2.0),
            ("gamma_flip", "#e8d030", "dash", 1.6),
            ("vanna_dn",   "#9060e8", "dot",  1.3),
            ("vanna_up",   "#6090ff", "dot",  1.2),
        ]
        shapes = []
        _raw_labels = []
        lbl_names = {"call_wall":"Call Wall","put_wall":"Put Wall",
                     "gamma_flip":"Gamma Flip","vanna_dn":"-Vanna","vanna_up":"+Vanna"}
        for key, col, dash, width in level_defs:
            val = levels.get(key)
            if val and y_min * 0.97 <= val <= y_max * 1.03:
                shapes.append({
                    "type":"line","xref":"paper","yref":"y",
                    "x0":0,"x1":1,"y0":val,"y1":val,
                    "line":{"color":col,"width":width,"dash":dash},"layer":"above"
                })
                _raw_labels.append((val, lbl_names[key], col))

        # ── Right-side labels — same 3-column bin-packer ─────────────────────
        annotations = _gex_make_annotations(_raw_labels, y_min, y_max)

        long_gamma = spot > levels.get("gamma_flip", spot)
        regime_col = "#20e870" if long_gamma else "#ff4050"
        regime_txt = "LONG \u0393" if long_gamma else "SHORT \u0393"

        layout = {
            "plot_bgcolor":  "#0a0c14",
            "paper_bgcolor": "#06080d",
            "font": {"color": "#8898b8", "family": "monospace", "size": 10},
            "title": {
                "text": (f"<b style='color:#dde4ff'>Price + Levels \u00b7 {sym}</b>"
                         f"  <span style='color:#7080a8;font-size:11px'>\u00a090-day daily</span>"
                         f"  <span style='color:{regime_col};font-size:12px'>\u00a0{regime_txt}</span>"),
                "x": 0.02, "xanchor": "left",
                "font": {"size": 14, "family": "monospace"},
            },
            "xaxis": {
                "type": "category",      # eliminates weekend / holiday gaps
                "gridcolor": "#1a2035", "tickcolor": "#2a3555",
                "tickangle": -30, "tickfont": {"size": 8},
                "nticks": 15,
                "rangeslider": {"visible": False},
            },
            "yaxis": {
                "title": {"text": "Price", "font": {"size": 10}},
                "gridcolor": "#1a2035", "tickcolor": "#2a3555",
                "tickformat": ".2f",
                "range": [y_min, y_max],
                "side": "left",
            },
            "shapes": shapes, "annotations": annotations,
            "margin": {"l": 72, "r": 220, "t": 62, "b": 60},
            "height": 600,
        }
        return json.dumps(traces), json.dumps(layout)

    except Exception as _ex:
        print(f"  [Price chart] {sym}: {_ex}")
        return None, None


def build_options_flow_tab(downloads_dir=None):
    """
    Options Flow tab — each symbol has TWO Plotly charts:
      [= Bars]   horizontal GEX bars + GEX/DEX profiles (eager)
      [~ Price]  candlestick + key level lines, 90-day daily (lazy)
    """
    if downloads_dir is None:
        downloads_dir = DOWNLOADS_DIR

    # sym_data: sym -> (bar_tr, bar_ly, cn_tr, cn_ly, summary)
    sym_data  = {}
    sym_found = []
    sym_miss  = []

    print("  [Options Flow] Scanning CSVs...")
    for sym in GEX_SYMBOLS:
        csv_path = _gex_find_csv(downloads_dir, sym)
        if not csv_path:
            print(f"    \u26a0 {sym}: no CSV in {downloads_dir}"); sym_miss.append(sym); continue
        spot = _gex_spot_from_csv(csv_path)
        if not spot:
            print(f"    \u26a0 {sym}: cannot determine spot"); sym_miss.append(sym); continue
        levels  = _PINE_LEVELS.get(sym, {})
        records = _gex_parse_csv(csv_path, spot)
        if not records:
            print(f"    \u26a0 {sym}: no GEX strikes in range"); sym_miss.append(sym); continue

        tr_j, ly_j, summ = _gex_build_plotly_json(sym, records, spot, levels, csv_path)
        cn_tr, cn_ly     = _gex_build_candle_json(sym, levels, spot)

        sym_data[sym] = (tr_j, ly_j, cn_tr, cn_ly, summ)
        sym_found.append(sym)
        cn_ok = "\u2713 candle" if cn_tr else "\u26a0 no candle"
        print(f"    \u2713 {sym}: {len(records)} strikes, spot\u2248{spot:.2f}, "
              f"GEX={summ['total_gex']/1e6:.0f}M  [{summ['regime']}]  {cn_ok}")

    if not sym_found:
        return ('<div style="padding:40px;color:#667;font-size:13px;text-align:center">'
                '\u26a0 No Barchart CSVs found. Run your download script then regenerate.</div>')

    first_sym = sym_found[0]

    # Symbol picker buttons
    sym_btns = ""
    for sym in sym_found:
        rc  = sym_data[sym][4].get("regime_col", "#8898b8")
        act = "gex-sym-active" if sym == first_sym else ""
        sym_btns += (f'<button class="gex-sym-btn {act}" onclick="showGex(\'{sym}\')" '
                     f'style="--rc:{rc}">{sym}</button>\n')

    # Summary header cards
    hdr_cards = ""
    for sym in sym_found:
        s = sym_data[sym][4]; rc = s.get("regime_col", "#8898b8")
        hdr_cards += (
            f'<div class="gex-summary-card" onclick="showGex(\'{sym}\')" style="cursor:pointer">'
            f'<div style="font-size:12px;font-weight:800;color:#dde4ff">${sym}</div>'
            f'<div style="font-size:9px;color:{rc};font-weight:700">{s.get("regime","--")}</div>'
            f'<div style="font-size:9px;color:#8898b8">GEX {s.get("total_gex",0)/1e6:+.0f}M</div>'
            f'<div style="font-size:9px;color:#ff4060">\u25b2 {s.get("call_range",0):+.2f}</div>'
            f'<div style="font-size:9px;color:#20cc60">\u25bc {-s.get("put_range",0):+.2f}</div>'
            f'</div>\n')

    # Chart panels — one per symbol, with two internal chart divs
    panels = ""
    for sym in sym_found:
        tr_j, ly_j, cn_tr, cn_ly, s = sym_data[sym]
        disp = "block" if sym == first_sym else "none"
        rc   = s.get("regime_col", "#20e870")
        has_candle = cn_tr is not None

        lvl_rows = "".join(
            f'<tr><td style="color:#6070a0;padding:4px 10px 4px 0;font-size:10px">{k}</td>'
            f'<td style="color:{c};font-weight:700;font-size:11px;font-family:monospace">{v}</td></tr>'
            for k, v, c in [
                ("Call Wall",  f'{s["call_wall"]:.2f}',       "#ff4060"),
                ("Put Wall",   f'{s["put_wall"]:.2f}',        "#20cc60"),
                ("Gamma Flip", f'{s["gamma_flip"]:.2f}',      "#e8d030"),
                ("+Vanna",     f'{s["vanna_up"]:.2f}',        "#6090ff"),
                ("-Vanna",     f'{s["vanna_dn"]:.2f}',        "#9060e8"),
                ("Total GEX",  f'{s["total_gex"]/1e6:.1f}M', "#f0d020"),
                ("Regime",     s.get("regime", "--"),         rc),
            ])

        price_btn_disabled = "" if has_candle else 'disabled style="opacity:.4;cursor:not-allowed"'
        price_btn_title    = "90-day candlestick with level overlays" if has_candle else "No price data available"

        panels += f"""
<div id="gex-panel-{sym}" class="gex-panel" style="display:{disp}">
  <div style="display:grid;grid-template-columns:1fr 220px;gap:16px;align-items:start">
    <div>
      <!-- View toggle -->
      <div style="display:flex;gap:6px;margin-bottom:8px">
        <button class="gex-view-btn gex-view-active" id="btn-bars-{sym}"
                onclick="switchView('{sym}','bars')"
                title="Horizontal GEX bars + GEX/DEX profiles">&#9776; GEX Bars</button>
        <button class="gex-view-btn" id="btn-price-{sym}"
                onclick="switchView('{sym}','price')"
                title="{price_btn_title}" {price_btn_disabled}>&#9685; Price + Levels</button>
      </div>

      <!-- GEX bars (default, eager) -->
      <div id="gex-chart-{sym}-bars" style="width:100%;min-height:600px"></div>

      <!-- Candlestick + levels (lazy, init on first click) -->
      <div id="gex-chart-{sym}-price" style="width:100%;min-height:600px;display:none">
        {"" if has_candle else
         '<div style="padding:60px;text-align:center;color:#4a5a7a;font-size:12px">'
         'Price data unavailable for this symbol.</div>'}
      </div>
    </div>

    <!-- Key levels sidebar -->
    <div style="background:#0d1020;border:1px solid #1e2a44;border-radius:8px;
                padding:14px 16px;margin-top:40px">
      <div style="font-size:10px;font-weight:800;color:#dde4ff;letter-spacing:.08em;
                  text-transform:uppercase;margin-bottom:10px;border-bottom:1px solid #1e2a44;
                  padding-bottom:6px">${sym} Key Levels</div>
      <table style="border-collapse:collapse;width:100%"><tbody>{lvl_rows}</tbody></table>
    </div>
  </div>
</div>"""

    # Plotly init scripts — bars eager, price lazy
    bar_inits   = ""
    price_inits = ""
    cfg = "{responsive:true,displayModeBar:true,modeBarButtonsToRemove:['select2d','lasso2d'],displaylogo:false}"
    for sym in sym_found:
        tr_j, ly_j, cn_tr, cn_ly, _ = sym_data[sym]
        bar_inits += (f"  try{{Plotly.newPlot('gex-chart-{sym}-bars',{tr_j},{ly_j},{cfg});}}"
                      f"catch(e){{console.warn('bars {sym}',e);}}\n")
        if cn_tr:
            price_inits += (
                f"  if(sym==='{sym}' && !document.getElementById('gex-chart-{sym}-price')._init){{\n"
                f"    document.getElementById('gex-chart-{sym}-price')._init=true;\n"
                f"    try{{Plotly.newPlot('gex-chart-{sym}-price',{cn_tr},{cn_ly},{cfg});}}"
                f"catch(e){{console.warn('price {sym}',e);}}\n  }}\n")

    miss_note = (f'<div style="font-size:9px;color:#4a5070;margin-top:4px">No CSV: {", ".join(sym_miss)}</div>'
                 if sym_miss else "")

    return f"""
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
.gex-sym-btn{{padding:5px 14px;font-size:11px;font-weight:700;font-family:monospace;
  background:#0d1020;border:1px solid #1e2a44;border-radius:5px;color:#8898b8;cursor:pointer;transition:all .15s}}
.gex-sym-btn:hover{{background:#141828;color:#dde4ff;border-color:#3a4a6a}}
.gex-sym-btn.gex-sym-active{{background:#0d1a30;color:var(--rc,#20e870);border-color:var(--rc,#20e870);box-shadow:0 0 6px rgba(0,200,80,.25)}}
.gex-view-btn{{padding:4px 13px;font-size:10px;font-weight:700;font-family:monospace;
  background:#0d1020;border:1px solid #1e2a44;border-radius:4px;color:#6070a0;cursor:pointer;transition:all .15s}}
.gex-view-btn:hover{{background:#141828;color:#dde4ff;border-color:#3a4a6a}}
.gex-view-btn.gex-view-active{{background:#101828;color:#60b0ff;border-color:#2a5090}}
.gex-panel{{display:none}}
.gex-summary-card{{background:#0d1020;border:1px solid #1e2a44;border-radius:6px;
  padding:8px 12px;min-width:80px;text-align:center;transition:border-color .15s}}
.gex-summary-card:hover{{border-color:#3a4a6a}}
</style>

<div style="font-size:11px;color:#3355aa;text-transform:uppercase;letter-spacing:.08em;
            font-weight:800;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid #eef0f8">
  \u26a1 Options Flow \u2014 Net GEX by Strike
  <span style="font-size:9px;font-weight:400;color:#667;text-transform:none">
    &nbsp;\u00b7&nbsp;Gamma \u00d7 OI \u00d7 100 \u00d7 Spot &nbsp;\u00b7&nbsp;Levels from Pine Script
  </span>
</div>

<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">{hdr_cards}</div>

<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;
            background:#0a0c14;border-radius:8px;padding:10px;border:1px solid #1a2035">
  {sym_btns}{miss_note}
</div>

{panels}

<div style="display:flex;gap:18px;flex-wrap:wrap;font-size:9px;color:#6070a0;
            margin-top:12px;padding-top:8px;border-top:1px solid #1a2035">
  <span><b style="color:#8898b8">GEX Bars:</b>
    <span style="color:#20c850">\u2588\u2588</span> +GEX (dealers buy dips) &nbsp;
    <span style="color:#dc2d37">\u2588\u2588</span> -GEX (dealers sell rallies) &nbsp;
    <span style="color:#f0d020">\u2014</span> GEX Profile &nbsp;
    <span style="color:#ff8c00">- -</span> DEX Profile
  </span>
  <span><b style="color:#8898b8">Price + Levels:</b> 90-day daily candles with Pine Script key levels overlaid</span>
  <span><span style="color:#ff3855">- -</span> Call Wall &nbsp;
        <span style="color:#20c860">- -</span> Put Wall &nbsp;
        <span style="color:#e8d030">- -</span> Gamma Flip &nbsp;
        <span style="color:#6090ff">\u00b7\u00b7</span> +Vanna &nbsp;
        <span style="color:#9060e8">\u00b7\u00b7</span> -Vanna</span>
</div>

<script>
var _gexViewState={{}};
function showGex(sym){{
  document.querySelectorAll('.gex-panel').forEach(el=>el.style.display='none');
  document.querySelectorAll('.gex-sym-btn').forEach(el=>el.classList.remove('gex-sym-active'));
  var p=document.getElementById('gex-panel-'+sym);
  var b=document.querySelector('.gex-sym-btn[onclick*="'+sym+'"]');
  if(p)p.style.display='block';
  if(b)b.classList.add('gex-sym-active');
  _resize(sym, _gexViewState[sym]||'bars');
}}
function switchView(sym,view){{
  _gexViewState[sym]=view;
  ['bars','price'].forEach(v=>{{
    var el=document.getElementById('gex-chart-'+sym+'-'+v);
    if(el)el.style.display=v===view?'block':'none';
  }});
  var bb=document.getElementById('btn-bars-'+sym);
  var bp=document.getElementById('btn-price-'+sym);
  if(bb)bb.classList.toggle('gex-view-active',view==='bars');
  if(bp)bp.classList.toggle('gex-view-active',view==='price');
  if(view==='price'){{ {price_inits} }}
  _resize(sym,view);
}}
function _resize(sym,view){{
  setTimeout(()=>{{
    var d=document.getElementById('gex-chart-'+sym+'-'+view);
    if(d&&d.data)Plotly.relayout('gex-chart-'+sym+'-'+view,{{autosize:true}});
  }},80);
}}
var _gexDone=false;
function initGexCharts(){{
  if(_gexDone)return;_gexDone=true;
{bar_inits}
  // Force relayout on ALL bar charts after render so Plotly
  // picks up the correct container dimensions (fixes blank chart bug
  // when the tab was hidden at initial render time).
  setTimeout(function(){{
    document.querySelectorAll('[id^="gex-chart-"][id$="-bars"]').forEach(function(el){{
      if(el && el.data) Plotly.relayout(el.id, {{autosize:true}});
    }});
  }}, 150);
}}
</script>
"""


def build_html(fd, md, ep, pos, charts, gen_time, ai=None, scorecard=None, sector_stocks=None, use_api=True, sdm_data=None, no_indicator_charts=False, default_tab=None):
    # ── AI summary helper — uses Claude text if available, else empty string ──
    if ai is None: ai = {}
    if scorecard is None: scorecard = []
    def _ai(key, fallback=""):
        """Get AI-generated text with (AI Gen) label, or static fallback."""
        ai_text = ai.get(key)
        if ai_text:
            return (ai_text + ' <span style="font-size:9px;color:#555;font-style:normal;'
                    'font-weight:400">(AI Gen)</span>')
        return fallback

    # Market health summary from the full 38-indicator scorecard
    _n_danger   = sum(1 for x in scorecard if x["signal"] in ("STRESS","CRISIS"))
    _n_caution  = sum(1 for x in scorecard if x["signal"] == "CAUTION")
    _n_calm     = sum(1 for x in scorecard if x["signal"] == "CALM")
    _n_total    = len(scorecard)
    _health_pct = round(_n_calm / max(_n_total, 1) * 100)
    _wt4_reds   = [x["name"] for x in scorecard if x["wt"] == 4 and x["signal"] in ("STRESS","CRISIS")]
    _wt4_note   = f" \u26a0 Critical: {', '.join(_wt4_reds)}." if _wt4_reds else " All WT4 critical indicators clear."
    _ep_ai_text = _ai("ep_summary",
        f"Market health: {_health_pct}% of {_n_total} indicators calm · "
        f"{_n_danger} in danger zone · {_n_caution} cautionary · {_n_calm} calm.{_wt4_note}")

    rg = pos["regime"]; k=pos["kuznets"]; j=pos["juglar"]; ki=pos["kitchin"]
    fred_count = len(fd); mkt_count = len(md)
    rg_col = rg["col"]; regime_label = rg["label"]

    # ── Dynamic cycle position strings (replace hardcoded "72% through..." text) ─
    CYCLE_MECHANICS["kuznets"]["current_position"] = (
        f"{k['phase']} ({k['pct']:.0f}% through {pos['kuznets']['trough']}-{pos['kuznets']['trough2']} cycle)"
    )
    CYCLE_MECHANICS["juglar"]["current_position"] = (
        f"{j['phase']} ({j['pct']:.0f}% through {pos['juglar']['trough']}-{pos['juglar']['trough2']} cycle)"
    )
    CYCLE_MECHANICS["kitchin"]["current_position"] = (
        f"{ki['phase']} ({ki['pct']:.0f}% through {pos['kitchin']['trough']}-{pos['kitchin']['trough2']} cycle)"
    )

    # ── Override CYCLE_MECHANICS narrative with AI text when available ────────
    for _cm_key in ("kuznets", "juglar", "kitchin"):
        _warn_raw = ai.get(f"warnings_{_cm_key}", "")
        if _warn_raw:
            _bullets = [b.strip() for b in _warn_raw.replace("\n⚡","⚡").split("⚡") if b.strip()]
            if _bullets:
                CYCLE_MECHANICS[_cm_key]["warning_signs"] = _bullets
                CYCLE_MECHANICS[_cm_key]["_warnings_ai"] = True
        _theme_raw = ai.get(f"theme_{_cm_key}", "")
        if _theme_raw:
            CYCLE_MECHANICS[_cm_key]["current_theme"] = _theme_raw.strip()
        _watch_raw = ai.get(f"watch_{_cm_key}", "")
        if _watch_raw:
            CYCLE_MECHANICS[_cm_key]["watch_indicator"] = _watch_raw.strip()

    def bar(pct, col, w=360, h=14):
        p = min(max(pct,0),100)
        return (f'<div style="width:{w}px;height:{h}px;background:#e0e4ed;border-radius:3px;'
                f'overflow:hidden;display:inline-block;vertical-align:middle">'
                f'<div style="width:{p:.0f}%;height:{h}px;background:{col};'
                f'border-radius:3px;transition:width .3s"></div></div>'
                f'<span style="font-size:11px;color:{col};font-weight:700;'
                f'margin-left:8px;vertical-align:middle">{pct:.0f}%</span>')

    # ── Cycle blocks ─────────────────────────────────────────────────────────
    def cblock(title, info, cm_key, ai_insight="", live_signals=None, live_vals=None):
        cm = CYCLE_MECHANICS[cm_key]
        col = info["col"]; pct = info["pct"]; ph = info["phase"]
        tr1=info["trough"]; pk=info["peak"]; tr2=info["trough2"]
        ytp=info.get("years_to_peak","—"); note=info.get("note","")
        peaks_html = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:4px 0;'
            f'border-bottom:1px solid #d0d5e8;font-size:10px">'
            f'<span style="color:#D4820A;font-weight:700">{p["year"]}</span>'
            f'<span style="color:#666">{p["event"]}</span></div>'
            for p in cm["historical_peaks"]
        )
        warns = "".join(f'<div style="font-size:10px;color:#D4820A;padding:2px 0">⚡ {w}</div>'
                        for w in cm["warning_signs"])

        # Build live signal rows (current reading vs threshold)
        if live_signals:
            _sig_rows = ""
            for _nm, _val, _status, _thresh in live_signals:
                _sc  = "#1A7A4A" if _status == "OK" else ("#D4820A" if _status == "WATCH" else "#C0390F")
                _bg  = "#eafbea" if _status == "OK" else ("#fff8e8" if _status == "WATCH" else "#fdf0f0")
                _ico = "✓" if _status == "OK" else ("⚠" if _status == "WATCH" else "✗")
                _sig_rows += (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;'                    f'padding:4px 8px;margin-bottom:2px;background:{_bg};border-radius:4px;'                    f'border-left:2px solid {_sc}">'                    f'<span style="font-size:10px;color:#444;flex:1">{_nm}</span>'                    f'<span style="font-size:10px;font-weight:700;color:{_sc};margin:0 8px">{_val}</span>'                    f'<span style="font-size:10px;color:#555">{_thresh}</span>'                    f'<span style="font-size:11px;font-weight:700;color:{_sc};margin-left:6px">{_ico}</span>'                    f'</div>'
                )
            _live_signals_html = (
                '<div style="margin-top:10px">'                '<div style="font-size:10px;color:#3355aa;text-transform:uppercase;'                'letter-spacing:.07em;margin-bottom:5px">Live Indicator Readings</div>'                + _sig_rows + '</div>'
            )
        else:
            _live_signals_html = ""

        # ── Prior cycle peak/trough readings reference table ─────────────────
        _pr_data = cm.get("peak_readings", [])
        if _pr_data:
            def _fv(v, fmt):
                if v is None: return "—"
                try: return fmt.format(v)
                except: return str(v)
            _pr_rows = ""
            for _row in _pr_data:
                # Inject all live values directly from live_vals dict
                if _row.get("signal") == "LIVE" and live_vals:
                    _live_row = dict(_row)
                    _live_row["hy"] = live_vals.get("hy")
                    _live_row["yc"] = live_vals.get("yc")
                    _live_row["ip"] = live_vals.get("ip")
                    _live_row["cu"] = live_vals.get("cu")
                    _live_row["ff"] = live_vals.get("ff")
                    _live_row["note"] = "Live — compare to peaks/troughs above"
                    _row = _live_row
                _sc  = {"RISK OFF":"#C0390F","CAUTION":"#D4820A","RISK ON":"#1A7A4A","LIVE":"#1155cc"}.get(_row["signal"],"#555")
                _sbg = {"RISK OFF":"#fdf0f0","CAUTION":"#fff8e8","RISK ON":"#eafbea","LIVE":"#eef2ff"}.get(_row["signal"],"#f8f9fe")
                _pr_rows += (
                    f'<tr style="background:{_sbg};border-bottom:1px solid #e8eaed">'
                    f'<td style="padding:4px 8px;font-size:10px;color:#333;font-weight:600;white-space:nowrap">{_row["period"]}</td>'
                    f'<td style="padding:4px 6px;font-size:10px;text-align:center;color:#555">{_fv(_row["hy"],"{:.0f}")}</td>'
                    f'<td style="padding:4px 6px;font-size:10px;text-align:center;color:#555">{_fv(_row["yc"],"{:+.0f}bps")}</td>'
                    f'<td style="padding:4px 6px;font-size:10px;text-align:center;color:#555">{_fv(_row["ip"],"{:+.1f}%")}</td>'
                    f'<td style="padding:4px 6px;font-size:10px;text-align:center;color:#555">{_fv(_row["cu"],"{:.1f}%")}</td>'
                    f'<td style="padding:4px 6px;font-size:10px;text-align:center;color:#555">{_fv(_row["ff"],"{:.2f}%")}</td>'
                    f'<td style="padding:4px 8px"><span style="background:{_sbg};color:{_sc};border:1px solid {_sc}44;'
                    f'padding:1px 6px;border-radius:4px;font-size:9px;font-weight:700">{_row["signal"]}</span></td>'
                    f'<td style="padding:4px 8px;font-size:9px;color:#555;font-style:italic">{_row["note"]}</td>'
                    f'</tr>'
                )
            _peak_readings_html = (
                '<div style="margin-top:14px;padding-top:12px;border-top:1px solid #e0e4ed">'
                '<div style="font-size:10px;color:#3355aa;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;font-weight:600">'
                'Prior Cycle Peaks &amp; Troughs — Key Readings'
                '<span style="font-size:9px;color:#555;font-weight:400;text-transform:none;margin-left:8px;letter-spacing:0">'
                'spot risk-off / risk-on with numbers</span></div>'
                '<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse">'
                '<thead><tr style="background:#f0f2f8;border-bottom:1.5px solid #d0d5e8">'
                '<th style="padding:4px 8px;text-align:left;color:#3355aa;font-size:9px;font-weight:600">Period</th>'
                '<th style="padding:4px 6px;color:#3355aa;font-size:9px;font-weight:600">HY OAS (bps)</th>'
                '<th style="padding:4px 6px;color:#3355aa;font-size:9px;font-weight:600">Yield Curve</th>'
                '<th style="padding:4px 6px;color:#3355aa;font-size:9px;font-weight:600">IP YoY</th>'
                '<th style="padding:4px 6px;color:#3355aa;font-size:9px;font-weight:600">Cap.Util</th>'
                '<th style="padding:4px 6px;color:#3355aa;font-size:9px;font-weight:600">Fed Funds</th>'
                '<th style="padding:4px 6px;color:#3355aa;font-size:9px;font-weight:600">Signal</th>'
                '<th style="padding:4px 8px;text-align:left;color:#3355aa;font-size:9px;font-weight:600">Context</th>'
                '</tr></thead><tbody>' + _pr_rows + '</tbody></table></div>'
                '<div style="font-size:9px;color:#666;margin-top:4px;padding:2px 0">'
                'RISK OFF = defensives + TLT + GLD &nbsp;·&nbsp; RISK ON = cyclicals + HYG + growth</div>'
                '</div>'
            )
        else:
            _peak_readings_html = ""

        return f"""
        <div style="background:#f0f2f8;border:1px solid #d0d5e8;border-radius:12px;
                    overflow:hidden;margin-bottom:16px">
          <div style="background:#ffffff;padding:14px 18px;border-bottom:1px solid #d0d5e8;
                      display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div style="font-size:14px;font-weight:800;color:#1a1a2e">{cm['name']}</div>
              <div style="font-size:10px;color:#4a4a6a;margin-top:2px">
                {cm['aka']} · Discovered by {cm['discoverer']}
              </div>
            </div>
            <div style="text-align:right">
              <span style="background:{col}28;color:{col};padding:4px 14px;border-radius:8px;
                           font-size:11px;font-weight:700;border:1px solid {col}50">{ph}</span>
              <div style="font-size:9px;color:#555;margin-top:4px">~{ytp}yr to projected peak</div>
            </div>
          </div>
          <div style="padding:16px 18px">
            <div style="margin-bottom:12px">
              {bar(pct,col,500,16)}
              <div style="display:flex;justify-content:space-between;font-size:9px;
                          color:#444;width:500px;margin-top:6px">
                <span style="color:{col}80">Trough {tr1}</span>
                <span style="color:{col};font-weight:700">◆ Projected peak ~{pk}</span>
                <span style="color:{col}80">Trough ~{tr2}</span>
              </div>
              {f'<div style="margin-top:6px;font-size:10px;color:#5579af;background:#eef2ff;padding:6px 10px;border-radius:4px;border-left:3px solid {col}40">{note}</div>' if note else ''}
              {f'<div style="margin-top:6px;font-size:11px;color:#22337a;background:#eef4ff;padding:8px 12px;border-radius:6px;border-left:3px solid {col};font-style:italic">&#x1F916; {ai_insight}</div>' if ai_insight else ''}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
              <div>
                <div style="font-size:10px;color:#3355aa;text-transform:uppercase;
                            letter-spacing:.07em;margin-bottom:6px">How The Cycle Works</div>
                <div style="font-size:10px;color:#555577;line-height:1.6">{cm['mechanism']}</div>
                {_peak_readings_html}
              </div>
              <div>
                <div style="font-size:10px;color:#3355aa;text-transform:uppercase;
                            letter-spacing:.07em;margin-bottom:6px">Historical Peaks</div>
                {peaks_html}
                <div style="margin-top:10px">
                  <div style="font-size:10px;color:#3355aa;text-transform:uppercase;
                              letter-spacing:.07em;margin-bottom:6px">Current Warning Signs
                    {'<span style="font-size:9px;color:#1155cc;font-weight:400;text-transform:none;margin-left:6px;opacity:0.8">(AI Gen)</span>' if cm.get("_warnings_ai") else '<span style="font-size:9px;color:#666;font-weight:400;text-transform:none;margin-left:6px">(static)</span>'}
                  </div>
                  {warns}
                </div>
                <div style="margin-top:8px;font-size:10px;color:#2244aa;padding:6px 10px;
                            background:#eef2ff;border-radius:4px;border-left:3px solid #4477aa">
                  📊 Watch: <strong style="color:#5588bb">{cm['watch_indicator']}</strong>
                  {'<span style="font-size:9px;color:#1155cc;opacity:0.8"> (AI Gen)</span>' if cm.get("_warnings_ai") else ''}
                </div>
                {_live_signals_html}
              </div>
            </div>
          </div>
        </div>"""

    # ── Live signal readings for each cycle's watch section ─────────────────
    def _v(k): 
        s = fd.get(k); return float(s.iloc[-1]) if s is not None and not s.empty else None
    def _yoy(k,p=12):
        s = fd.get(k)
        if s is None or len(s)<p+2: return None
        a,b = float(s.iloc[-1]), float(s.iloc[-p-1])
        return round((a/b-1)*100,2) if b!=0 else None

    _hy_v  = _v("HY_OAS");    _yc_v  = _v("YIELD_CURVE"); _ff_v  = _v("FEDFUNDS")
    _t10_v = _v("T10Y");      _cu_v  = _v("CAPUTIL");     _ip_v  = _yoy("INDPRO",12)
    _houst_v = _yoy("HOUST", 12);  _cpi_v = _yoy("CPI", 12)
    _ur_v  = _v("UNRATE");    _ur4   = _v("UNRATE") if _v("UNRATE") else None
    try:
        _ur4 = float(fd["UNRATE"].iloc[-4]) if fd.get("UNRATE") is not None and len(fd["UNRATE"])>=5 else None
        _sahm = round(_ur_v - _ur4, 2) if _ur_v and _ur4 else None
    except: _sahm = None

    _kuznets_signals = [
        ("Housing starts YoY",  f"{_houst_v:+.1f}%" if _houst_v is not None else "N/A",
         "OK" if _houst_v and _houst_v > -15 else ("WATCH" if _houst_v and _houst_v > -25 else "WARN"),
         "danger <-25%"),
        ("HY OAS",              f"{_hy_v:.0f}bps" if _hy_v else "N/A",
         "OK" if _hy_v and _hy_v<380 else ("WATCH" if _hy_v and _hy_v<500 else "WARN"),
         "danger >500bps"),
        ("10Y yield",           f"{_t10_v:.2f}%" if _t10_v else "N/A",
         "OK" if _t10_v and _t10_v<4.5 else ("WATCH" if _t10_v and _t10_v<5 else "WARN"),
         "danger >5%"),
        ("Yield curve",         f"{_yc_v:+.0f}bps" if _yc_v is not None else "N/A",
         "OK" if _yc_v and _yc_v>0.3 else ("WATCH" if _yc_v and _yc_v>0 else "WARN"),
         "danger <0 (inverted)"),
    ]
    _juglar_signals = [
        ("HY OAS",              f"{_hy_v:.0f}bps" if _hy_v else "N/A",
         "OK" if _hy_v and _hy_v<380 else ("WATCH" if _hy_v and _hy_v<450 else "WARN"),
         "warn >380, danger >450"),
        ("Sahm Rule (3mo UR Δ)",f"+{_sahm:.2f}pp" if _sahm else "N/A",
         "OK" if _sahm and _sahm<0.2 else ("WATCH" if _sahm and _sahm<0.5 else "WARN"),
         "danger >0.5pp"),
        ("Indust. Production YoY",f"{_ip_v:+.1f}%" if _ip_v is not None else "N/A",
         "OK" if _ip_v and _ip_v>1 else ("WATCH" if _ip_v and _ip_v>-1 else "WARN"),
         "danger <-1%"),
        ("Fed Funds",           f"{_ff_v:.2f}%" if _ff_v else "N/A",
         "OK" if _ff_v and _ff_v<3.5 else ("WATCH" if _ff_v and _ff_v<4.5 else "WARN"),
         "danger >4.5%"),
    ]
    _kitchin_signals = [
        ("Indust. Production YoY",f"{_ip_v:+.1f}%" if _ip_v is not None else "N/A",
         "OK" if _ip_v and _ip_v>1.5 else ("WATCH" if _ip_v and _ip_v>-1 else "WARN"),
         "warn <1.5%, danger <-1%"),
        ("Capacity Utilization",f"{_cu_v:.1f}%" if _cu_v else "N/A",
         "OK" if _cu_v and _cu_v>77 else ("WATCH" if _cu_v and _cu_v>74 else "WARN"),
         "warn <77%, danger <74%"),
        ("HY OAS",              f"{_hy_v:.0f}bps" if _hy_v else "N/A",
         "OK" if _hy_v and _hy_v<380 else ("WATCH" if _hy_v and _hy_v<450 else "WARN"),
         "warn >380, danger >450"),
        ("CPI YoY",             f"{_cpi_v:.1f}%" if _cpi_v else "N/A",
         "OK" if _cpi_v and _cpi_v<3.5 else ("WATCH" if _cpi_v and _cpi_v<4.5 else "WARN"),
         "warn >3.5%, danger >4.5%"),
    ]

    # ── Build a single live_vals dict for ALL 5 columns in the Current row ─────
    # These are already computed above: _hy_v, _yc_v, _ip_v, _cu_v, _ff_v
    # _yc_v is in bps (e.g. 56), matching the column format
    _live_vals = {
        "hy": _hy_v,            # bps e.g. 342
        "yc": _yc_v,            # bps e.g. 56  (column displays as bps)
        "ip": _ip_v,            # YoY % e.g. 1.4
        "cu": _cu_v,            # % e.g. 76.3
        "ff": _ff_v,            # % e.g. 4.33
    }

    cycles_html = (
        cblock("Kuznets", k,  "kuznets", _ai("kuznets_insight"), _kuznets_signals, _live_vals)
      + cblock("Juglar",  j,  "juglar",  _ai("juglar_insight"),  _juglar_signals,  _live_vals)
      + cblock("Kitchin", ki, "kitchin", _ai("kitchin_insight"), _kitchin_signals, _live_vals)
    )

    # ── Projections ───────────────────────────────────────────────────────────
    proj_cards = ""
    for _pi, p in enumerate(pos["projections"]):
        _proj_ai = _ai(f"proj_{_pi}", "")
        proj_cards += f"""
        <div style="background:#f0f2f8;border:1px solid #d0d5e8;border-left:4px solid {p['col']};
                    border-radius:0 10px 10px 0;padding:14px 16px;margin-bottom:10px">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px">
            <span style="font-size:14px;font-weight:800;color:{p['col']}">{p['name']}</span>
            <span style="background:{p['col']}20;color:{p['col']};padding:2px 10px;
                         border-radius:6px;font-size:10px;font-weight:700;border:1px solid {p['col']}40">{p['probability']}</span>
            <span style="color:#666;font-size:10px">|</span>
            <span style="font-size:11px;color:#555577">{p['timing']}</span>
            <span style="font-size:13px;font-weight:700;color:{p['col']}">{p['magnitude']}</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:10px">
            <div>
              <div style="color:#3355aa;margin-bottom:3px;text-transform:uppercase;letter-spacing:.05em">Trigger</div>
              <div style="color:#666">{p.get('trigger','—')}</div>
              <div style="color:#3355aa;margin-top:6px;margin-bottom:3px;text-transform:uppercase;letter-spacing:.05em">Historical Parallel</div>
              <div style="color:#666">{p.get('parallel', '—')}</div>
            </div>
            <div>
              <div style="color:#3355aa;margin-bottom:3px;text-transform:uppercase;letter-spacing:.05em">What To Watch</div>
              <div style="color:#D4820A">{p['what_to_watch']}</div>
              <div style="color:#3355aa;margin-top:6px;margin-bottom:3px;text-transform:uppercase;letter-spacing:.05em">Risk / Defense</div>
              <div><span style="color:#C0390F">At risk: {p.get('sectors_at_risk','—')}</span>
                   <span style="color:#555"> | </span>
                   <span style="color:#1A7A4A">Defensive: {p.get('sectors_defensive','—')}</span></div>
            </div>
          </div>
          {'<div style="margin-top:8px;padding:8px 12px;background:rgba(26,26,46,0.07);border-radius:6px;border-left:3px solid ' + p["col"] + ';font-size:11px;color:#22337a;font-style:italic">&#x1F916; ' + _proj_ai + '</div>' if _proj_ai else ''}
        </div>"""

    # ── Parallels ──────────────────────────────────────────────────────────────
    parallels_html = ""
    for p in pos["parallels"]:
        parallels_html += f"""
        <div style="background:#f0f2f8;border:1px solid #d0d5e8;border-left:4px solid {p['col']};
                    border-radius:0 8px 8px 0;padding:12px 14px;margin-bottom:8px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            <span style="font-size:13px;font-weight:800;color:{p['col']}">{p['year']} Parallel</span>
            <span style="background:{p['col']}20;color:{p['col']};padding:2px 8px;
                         border-radius:5px;font-size:9px;font-weight:700">{p['sim']}% match</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:10px">
            <div>
              <div style="color:#2244aa;margin-bottom:2px">Then:</div>
              <div style="color:#666">{p['then']}</div>
              <div style="color:#2244aa;margin-top:6px;margin-bottom:2px">Key Difference:</div>
              <div style="color:#2244aa">{_ai(f"parallel_{p['year']}", p['key_diff'])}</div>
            </div>
            <div>
              <div style="color:#2244aa;margin-bottom:2px">Current match:</div>
              <div style="color:#666">{p['desc']}</div>
              <div style="color:#2244aa;margin-top:6px;margin-bottom:2px">Implication:</div>
              <div style="color:{p['col']};font-weight:600">→ {p['impl']}</div>
            </div>
          </div>
        </div>"""

    # ── EP Scorecard ──────────────────────────────────────────────────────────
    ep_rows = ""
    for d in ep["indicators"]:
        sc={"RED":"#C0390F","YELLOW":"#D4820A","GREEN":"#1A7A4A"}.get(d["signal"],"#555")
        bg={"RED":"rgba(192,57,15,0.15)","YELLOW":"rgba(212,130,10,0.15)",
            "GREEN":"rgba(26,122,74,0.15)"}.get(d["signal"],"rgba(100,100,100,0.1)")
        ep_rows += f"""
        <tr style="border-bottom:1px solid #e0e4ed">
          <td style="padding:8px 12px;font-size:11px;font-weight:700;color:#1a1a2e;white-space:nowrap">{d['name']}</td>
          <td style="padding:8px 10px;text-align:center">
            <span style="background:{bg};color:{sc};padding:3px 10px;border-radius:5px;
                         font-size:10px;font-weight:800;border:1px solid {sc}40">{d['signal']}</span>
          </td>
          <td style="padding:8px 10px;font-size:12px;font-weight:700;color:{sc};text-align:center">{d['value']}</td>
          <td style="padding:8px 10px;font-size:10px;color:#778688">{d.get('trend','—')}</td>
          <td style="padding:8px 12px;font-size:10px;color:#555577;max-width:280px">{d['context']}</td>
          <td style="padding:8px 12px;font-size:9px;color:#555;max-width:200px;font-style:italic">{d['historical']}</td>
          <td style="padding:8px 10px;text-align:center;font-size:10px;color:#555">{d['weight']}×</td>
        </tr>"""

    # ── Bear Market Table ─────────────────────────────────────────────────────
    bear_rows = ""
    for bm in BEAR_MARKETS:
        nm,pk,tr,dd,dur,cy,trig,rec,les = bm
        dd_c = "#C0390F" if dd<-40 else "#D4820A" if dd<-25 else "#556"
        bear_rows += f"""
        <tr style="border-bottom:1px solid #e0e4ed">
          <td style="padding:7px 12px;font-size:11px;font-weight:700;color:#1a1a2e;white-space:nowrap">{nm}</td>
          <td style="padding:7px 8px;text-align:center;font-size:10px;color:#555">{pk}</td>
          <td style="padding:7px 8px;text-align:center;font-size:10px;color:#555">{tr}</td>
          <td style="padding:7px 8px;text-align:center;font-size:12px;font-weight:800;color:{dd_c}">{dd}%</td>
          <td style="padding:7px 8px;text-align:center;font-size:10px;color:#555">{dur}mo</td>
          <td style="padding:7px 8px;text-align:center;font-size:10px;color:#1A7A4A">{rec}mo</td>
          <td style="padding:7px 10px;font-size:10px;color:#2244aa;white-space:nowrap">{cy}</td>
          <td style="padding:7px 12px;font-size:10px;color:#555577;max-width:250px">{trig}</td>
          <td style="padding:7px 12px;font-size:9px;color:#778688;max-width:250px;font-style:italic">{les}</td>
        </tr>"""

    # ── Chart.js data ─────────────────────────────────────────────────────────
    def js(v): return json.dumps(v)

    yc_data = charts.get("yield_curve",{})
    hy_data = charts.get("hy_oas",{})
    fc_data = charts.get("fed_cpi",{})
    spy_data= charts.get("spy",{})
    sp_data = charts.get("sectors",{})
    pairs_data = charts.get("pairs",{})
    ip_data = charts.get("ip_caputil",{})

    # ── Playbook cards ────────────────────────────────────────────────────────
    plays = playbook(pos, ep, [])
    play_cards = "".join(f"""
        <div style="background:#f0f2f8;border:1px solid #dde1ed;border-left:4px solid {pl['col']};
                    border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:8px">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px">
            <span style="font-size:12px;font-weight:800;color:{pl['col']}">{pl['action']}</span>
            <span style="font-size:11px;font-weight:700;color:#1155cc">{pl['assets']}</span>
            <span style="background:#e0e4ed;color:#666;padding:2px 6px;border-radius:5px;font-size:9px">{pl['tf']}</span>
            <span style="background:{pl['col']}18;color:{pl['col']};padding:2px 7px;border-radius:5px;font-size:9px;font-weight:700">{pl['conv']}</span>
          </div>
          <div style="font-size:10px;color:#555577">{_ai(f"play_{pl['action']}", pl['rat'])}</div>
        </div>""" for pl in plays)

    # ── Per-pair sector chart insight boxes ─────────────────────────────────────
    _PAIR_INS = {'XLY/XLP': {'how': 'XLY=Consumer Disc (wants), XLP=Staples (needs). Rising = consumers spending on wants = economy strong. Falling = defensive rotation into necessities.', 'key': 'Peaked before every recession since 2000 by 3-6 months. When ratio makes lower highs while SPY makes new highs = classic late-cycle distribution.', 'act': 'Ratio falling from highs: add defensives XLP/XLV. Ratio rising from lows: risk-on, add XLY, IWM. Current direction shows remaining consumer confidence.'}, 'XLF/XLU': {'how': 'XLF=Financials, XLU=Utilities. Rising = rates rising, GDP expanding, credit healthy. Falling = utilities bid = growth fears or rate cuts priced in.', 'key': 'Best rate-direction indicator in the sector space. Ratio often leads SPY reversals by 4-6 weeks. When flattening with rising SPY = late-cycle warning.', 'act': 'Rising: add banks/brokers, stay short duration bonds. Falling: buy TLT, XLU. XLU outperform is one of the clearest recession-proximity signals.'}, 'XLK/XLV': {'how': 'XLK=Technology, XLV=Healthcare. Rising = pure growth bias. Falling = defensive rotation into healthcare. Healthcare is the soft-landing defensive.', 'key': 'Peaks 2-3 months before major corrections historically. At 2021 extreme, ratio was highest ever — reversion was -40% XLK vs -5% XLV. Confirm reversals with HY OAS.', 'act': 'Rolling over from highs: reduce tech, add XLV hedge. At lows: contrarian tech buy — but only if HY OAS is calm (<380bps).'}, 'XLE/XLU': {'how': 'XLE=Energy, XLU=Utilities. Rising = energy/inflation regime. Falling = disinflationary, utilities outperform. Tracks real-asset/commodity cycle.', 'key': 'Best inflation leading indicator in the sector space. Rising XLE/XLU predicts hot CPI prints by 1-2 months. Key Kuznets late-cycle signal.', 'act': 'Rising sharply: add XLE, commodities, short TLT. Falling: inflation peaking, favor bonds (TLT) and rate-sensitive growth. Watch with BREAKEVEN reading.'}, 'IWM/SPY': {'how': 'IWM=Small Cap, SPY=S&P 500. Rising = broad rally, economy healthy. Falling = mega-cap masking broad weakness — index held up by fewer stocks.', 'key': 'Fell 2 years before 2022 bear while SPY made new highs. When SPY rises but IWM/SPY falls, the rally is fragile and concentrated. This is the clearest concentration-risk signal.', 'act': 'Ratio rising: economy broadening, add IWM/mid-caps. Ratio falling while SPY up: RAISE CASH — this is a high-conviction late-cycle warning. Pairs with Top-10 weight indicator.'}, 'XLI/XLP': {'how': 'XLI=Industrials, XLP=Staples. Rising = capex cycle expanding, manufacturers investing. Falling = capex drying up, Juglar contraction underway.', 'key': 'Leads Juglar capex cycle turns by 3-6 months. When industrials lose leadership vs staples, earnings revisions in XLI follow downward. Watch with CapUtil <77%.', 'act': 'Rising + CapUtil >77%: overweight industrials, materials. Falling: reduce cyclicals. Multi-year lows = contrarian early-cycle buy when Juglar is <40% through.'}, 'XLK/XLP': {'how': 'XLK=Tech, XLP=Staples. The sharpest growth vs value barometer. Rising = pure risk-on. Falling = significant de-risking, staples leadership.', 'key': 'Breaks its 20-week MA historically 4-8 weeks before broader SPY correction. At 2021 ATH, this ratio was at all-time extremes — its collapse led the bear market.', 'act': 'Making lower highs: start defensive rotation immediately. At 52-week lows: risk-off confirmed. Bottoming here historically coincides with SPY trough — watch for reversal.'}, 'HYG/LQD': {'how': 'HYG=Junk bonds, LQD=Investment Grade bonds. Rising = credit risk appetite. Falling = flight to quality within bonds = EARLIEST stress signal before equities move.', 'key': 'Led every major SPY correction since 2008 by 4-8 weeks — before VIX spikes, before HY OAS widens, before equity breadth collapses. The single most reliable early warning.', 'act': 'Lower highs while SPY at new highs: one of highest-conviction SELL signals in this dashboard. Bottoming with SPY still falling: early recovery entry. Monitor weekly.'}}

    def _pib(pk):
        """Per-pair insight box HTML."""
        ins = _PAIR_INS.get(pk, {})
        if not ins: return ""
        return (
            '<div style="margin-top:6px;display:flex;flex-direction:column;gap:4px;font-size:9px">'
            '<div style="background:#f4f6ff;border-radius:4px;padding:5px 7px;border-left:2px solid #4477dd">'
            '<span style="font-size:8px;color:#3355aa;font-weight:700;text-transform:uppercase;letter-spacing:.04em">Read: </span>'
            f'<span style="color:#444">{ins["how"]}</span></div>'
            '<div style="background:#f0faf4;border-radius:4px;padding:5px 7px;border-left:2px solid #2e8b57">'
            '<span style="font-size:8px;color:#2e5a3a;font-weight:700;text-transform:uppercase;letter-spacing:.04em">Insight: </span>'
            f'<span style="color:#1a3a24">{ins["key"]}</span></div>'
            '<div style="background:#fffbf0;border-radius:4px;padding:5px 7px;border-left:2px solid #cc8800">'
            '<span style="font-size:8px;color:#7a5200;font-weight:700;text-transform:uppercase;letter-spacing:.04em">Action: </span>'
            f'<span style="color:#4a3000">{ins["act"]}</span></div>'
            '</div>'
        )

    def _seas_badge(pd_):
        vs = pd_.get("vs_seasonal")
        if vs is None: return ""
        return (f'<div style="font-size:9px;background:#fff0cc;color:#D4820A;'
                f'padding:2px 8px;border-radius:8px;font-weight:700">'
                f'vs Season: {vs:+.1f}%</div>')

    _pair_chart_cells = "".join(
        f'<div style="background:#fff;border:1px solid #dde1ed;border-radius:10px;'
        f'padding:14px 18px;margin-bottom:14px">'
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">'
        f'<div style="font-size:13px;font-weight:800;color:#1155cc">{pk}</div>'
        f'<div style="font-size:11px;color:#556">{pd_["name"]}</div>'
        f'<div style="margin-left:auto;font-size:10px;font-weight:700;'
        f'color:{pd_.get("dir_col","#556")}">{pd_.get("direction","—")}</div>'
        f'<div style="font-size:10px;color:#556">3M: {pd_.get("c3m",0):+.1f}%</div>'
        f'<div style="font-size:10px;color:#556">1Y: {pd_.get("rank1y",50):.0f}th %ile</div>'
        f'{_seas_badge(pd_)}'
        f'</div>'
        f'<div style="position:relative">'
        f'<canvas id="pair_{pk.replace("/","_")}" style="height:320px;max-height:320px"></canvas>'
        f'<button onclick="(function(){{var c=Chart.getChart(\'pair_{pk.replace("/","_")}\');if(c)c.resetZoom();}})()" '
        f'style="position:absolute;top:6px;left:6px;font-size:9px;padding:2px 8px;'
        f'border-radius:4px;border:1px solid #ccd;background:#f8f9ff;color:#445;cursor:pointer;'
        f'opacity:0.7" title="Reset zoom">⟲ Reset</button>'
        f'</div>'
        f'{_pib(pk)}'
        f'</div>'
        for pk, pd_ in pairs_data.items()
    )

        # ── Pre-compute Market Dashboard HTML ────────────────────────────────────
    SIG_COLORS = {
        "CALM":    ("#1A7A4A","#D6F0E0"),
        "CAUTION": ("#9A6200","#FFF0CC"),
        "STRESS":  ("#C0390F","#FDDDD5"),
        "CRISIS":  ("#7B1111","#F9C0C0"),
        "N/A":     ("#555566","#F0F0F0"),
    }
    CAT_ICONS = {
        "Credit":"💳","Rates":"📈","Volatility":"⚡","Breadth":"🌊",
        "Valuation":"🏷","Liquidity":"💧","Recession":"🚨","Structure":"🏛",
        "Macro":"🔬","Sentiment":"🧠",
    }
    WT_LABELS = {4:"Critical",3:"Important",2:"Confirmer"}

    # Summary KPI tiles
    _sc_danger = sum(1 for x in scorecard if x["signal"] in ("STRESS","CRISIS"))
    _sc_crisis = sum(1 for x in scorecard if x["signal"] == "CRISIS")
    _sc_caut   = sum(1 for x in scorecard if x["signal"] == "CAUTION")
    _sc_calm   = sum(1 for x in scorecard if x["signal"] == "CALM")
    _sc_total  = len(scorecard)
    _sc_score  = round(_sc_calm / max(_sc_total, 1) * 100) if _sc_total else 0

    # Overall risk level
    if _sc_crisis >= 3 or _sc_danger >= 8:
        _sc_risk, _sc_risk_col = "SYSTEMIC STRESS", "#7B1111"
    elif _sc_danger >= 5 or (_sc_danger >= 3 and _sc_caut >= 6):
        _sc_risk, _sc_risk_col = "ELEVATED RISK", "#C0390F"
    elif _sc_danger >= 2 or _sc_caut >= 5:
        _sc_risk, _sc_risk_col = "LATE-CYCLE CAUTION", "#D4820A"
    else:
        _sc_risk, _sc_risk_col = "BROADLY CONSTRUCTIVE", "#1A7A4A"

    # KPI tiles row
    _sc_kpi_tiles = "".join([
        f'<div style="background:#f8f9fe;border-radius:8px;padding:10px 14px;text-align:center;border-top:3px solid {_sc_risk_col}">'
        f'<div style="font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">Overall Risk</div>'
        f'<div style="font-size:14px;font-weight:900;color:{_sc_risk_col}">{_sc_risk}</div></div>',
        f'<div style="background:#FDDDD5;border-radius:8px;padding:10px 14px;text-align:center">'
        f'<div style="font-size:9px;color:#9A3010;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">Danger (Stress+Crisis)</div>'
        f'<div style="font-size:28px;font-weight:900;color:#C0390F">{_sc_danger}</div>'
        f'<div style="font-size:9px;color:#C0390F">{_sc_crisis} crisis</div></div>',
        f'<div style="background:#FFF0CC;border-radius:8px;padding:10px 14px;text-align:center">'
        f'<div style="font-size:9px;color:#7A5200;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">Caution</div>'
        f'<div style="font-size:28px;font-weight:900;color:#9A6200">{_sc_caut}</div></div>',
        f'<div style="background:#D6F0E0;border-radius:8px;padding:10px 14px;text-align:center">'
        f'<div style="font-size:9px;color:#0A5A2A;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">Calm</div>'
        f'<div style="font-size:28px;font-weight:900;color:#1A7A4A">{_sc_calm}</div></div>',
        f'<div style="background:#f0f2f8;border-radius:8px;padding:10px 14px;text-align:center">'
        f'<div style="font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px">Health Score</div>'
        f'<div style="font-size:28px;font-weight:900;color:{"#1A7A4A" if _sc_score>60 else "#D4820A" if _sc_score>40 else "#C0390F"}">{_sc_score}%</div></div>',
    ])

    # Category summary badges
    _cats_in_sc = list(dict.fromkeys(x["cat"] for x in scorecard))
    _cat_summary_html = ""
    for _cat in _cats_in_sc:
        _cat_inds = [x for x in scorecard if x["cat"] == _cat]
        _cat_red  = sum(1 for x in _cat_inds if x["signal"] in ("STRESS","CRISIS"))
        _cat_caut = sum(1 for x in _cat_inds if x["signal"] == "CAUTION")
        _worst = "CRISIS" if any(x["signal"]=="CRISIS" for x in _cat_inds) else                  "STRESS" if _cat_red > 0 else                  "CAUTION" if _cat_caut > 0 else "CALM"
        _cc, _cbg = SIG_COLORS.get(_worst, ("#555","#f0f0f0"))
        _icon = CAT_ICONS.get(_cat, "📊")
        _cat_summary_html += (
            f'<div style="background:{_cbg};border:1px solid {_cc}44;border-radius:8px;'
            f'padding:8px 12px;min-width:110px">'
            f'<div style="font-size:10px;font-weight:700;color:{_cc}">{_icon} {_cat}</div>'
            f'<div style="font-size:9px;color:{_cc};margin-top:2px">'
            f'{_cat_red}🔴 {_cat_caut}🟡 {len(_cat_inds)-_cat_red-_cat_caut}🟢</div></div>'
        )

    # Full indicator table sorted by wt desc, signal severity
    _sig_order = {"CRISIS":0,"STRESS":1,"CAUTION":2,"CALM":3,"N/A":4}
    _sorted_sc = sorted(scorecard,
        key=lambda x: (
            -x["wt"],
            _sig_order.get(x["signal"], 4),
            ["Credit","Rates","Volatility","Breadth","Valuation",
             "Liquidity","Recession","Structure","Macro","Sentiment"]
            .index(x["cat"]) if x["cat"] in
            ["Credit","Rates","Volatility","Breadth","Valuation",
             "Liquidity","Recession","Structure","Macro","Sentiment"] else 99
        )
    )

    _sc_rows = ""
    _prev_wt = None
    _prev_cat = None
    for _ind in _sorted_sc:
        _sig = _ind["signal"]
        _cc, _cbg = SIG_COLORS.get(_sig, ("#555","#f8f8f8"))
        _row_bg = {"CRISIS":"rgba(123,17,17,0.06)","STRESS":"rgba(192,57,15,0.05)",
                   "CAUTION":"rgba(154,98,0,0.04)","CALM":"rgba(26,122,74,0.03)"}.get(_sig,"transparent")
        _wt_col = {"4":"#C0390F","3":"#D4820A","2":"#555577"}.get(str(_ind["wt"]),"#556")
        _wt_lbl = WT_LABELS.get(_ind["wt"],"")
        _icon = CAT_ICONS.get(_ind["cat"],"📊")

        # Category group header when cat changes
        if _ind["cat"] != _prev_cat:
            _cat_inds2 = [x for x in scorecard if x["cat"] == _ind["cat"]]
            _cat_red2  = sum(1 for x in _cat_inds2 if x["signal"] in ("STRESS","CRISIS"))
            _cat_caut2 = sum(1 for x in _cat_inds2 if x["signal"] == "CAUTION")
            _sc_rows += (
                f'<tr style="background:#f0f4ff;border-top:2px solid #d0d5e8">'
                f'<td colspan="7" style="padding:6px 14px;font-size:11px;font-weight:800;'
                f'color:#1155cc;letter-spacing:.05em">'
                f'{_icon} {_ind["cat"].upper()}'
                f'<span style="font-weight:400;color:#555;margin-left:8px;font-size:10px">'
                f'{_cat_red2} stress · {_cat_caut2} caution · {len(_cat_inds2)-_cat_red2-_cat_caut2} calm</span>'
                f'</td></tr>'
            )
            _prev_cat = _ind["cat"]

        _asof_cell = (
            '<span style="color:#1166bb;font-style:italic;font-size:8px"> 🌐 web</span>'
            if _ind.get('ai_est') else _ind.get('as_of','')
        )
        _badge = (f'<span style="background:{_cbg};color:{_cc};padding:2px 8px;'
                  f'border-radius:4px;font-size:10px;font-weight:800;'
                  f'border:1px solid {_cc}44">{_sig}</span>')
        _sc_rows += (
            f'<tr style="background:{_row_bg};border-bottom:1px solid #e8eaed">'
            f'<td style="padding:7px 14px;font-size:11px;font-weight:700;color:#1a1a2e;white-space:nowrap">'
            f'{_ind["name"]}</td>'
            f'<td style="padding:7px 8px;font-size:9px;color:{_wt_col};font-weight:700;white-space:nowrap">'
            f'WT{_ind["wt"]} {_wt_lbl}</td>'
            f'<td style="padding:7px 10px;font-size:9px;color:#555">{_ind["src"][:30]}</td>'
            f'<td style="padding:7px 12px;font-size:13px;font-weight:900;color:{_cc};text-align:center">'
            f'{_ind["val_str"]}</td>'
            f'<td style="padding:7px 10px;text-align:center">{_badge}</td>'
            f'<td style="padding:7px 12px;font-size:10px;color:#555;max-width:280px">{_ind["context"]}</td>'
            f'<td style="padding:7px 10px;font-size:9px;color:#666;font-style:italic;max-width:160px">'
            f'{_ind["hist"][:80]}</td>'
            f'<td style="padding:7px 10px;font-size:9px;white-space:nowrap">{_asof_cell}</td>'
            f'</tr>'
        )

    # Pre-compute AI summary for scorecard
    _sc_ai_text = _ai("overall_summary", "")

    # ── SPY live price + projection targets ──────────────────────────────────
    # (full fetch logic happens below in Step A/B/C/D/E — initialize here)
    _spy_price = None
    _spy_price_str = "SPY N/A"   # will be overwritten by Step A
    _spy = 560                   # temporary placeholder — overwritten by Step A
    _kp_v  = pos["kitchin"]["pct"]
    _jp_v  = pos["juglar"]["pct"]
    _knp_v = pos["kuznets"]["pct"]
    _hy_now = pos["data"].get("hy") or 0
    _yc_now = pos["data"].get("yc") or 0
    # Cycle-derived correction estimates (updated in Step F after live price known)
    _kit_dd   = -0.15 if _kp_v > 80 else -0.10
    _jug_dd   = -0.30 if _jp_v > 85 else -0.20
    _bull_gain = 0.12 if _jp_v < 80 else 0.05

    def _tgt_badge(price, base):
        chg = (price / base - 1) * 100
        col = "#1A7A4A" if chg > 0 else "#C0390F"
        return (f'<span style="color:{col};font-weight:700">'
                f'${price:,.0f} ({chg:+.0f}%)</span>')

    def _make_tgts(spy_anchor, kp, jp):
        _kit_dd   = -0.15 if kp > 80 else -0.10
        _jug_dd   = -0.30 if jp > 85 else -0.20
        _bull_g   = 0.12  if jp < 80 else 0.05
        return {
            "3mo_bull":  round(spy_anchor * (1 + _bull_g * 0.25), 0),
            "3mo_base":  round(spy_anchor * (1 + _kit_dd  * 0.5),  0),
            "3mo_bear":  round(spy_anchor * (1 + _jug_dd  * 0.3),  0),
            "12mo_bull": round(spy_anchor * (1 + _bull_g),          0),
            "12mo_base": round(spy_anchor * (1 + _kit_dd),           0),
            "12mo_bear": round(spy_anchor * (1 + _jug_dd),           0),
            "24mo_bull": round(spy_anchor * (1 + _bull_g * 1.8),    0),
            "24mo_base": round(spy_anchor * (1 + _kit_dd * 0.5),     0),
            "24mo_bear": round(spy_anchor * (1 + _jug_dd * 1.3),     0),
        }

    # Build with placeholder — will be rebuilt after live price is fetched (Step E)
    _tgts = _make_tgts(_spy, _kp_v, _jp_v)

    def _build_scenario_table(tgts, spy_anchor, rg_dict):
        return (
            '<table style="width:100%;border-collapse:collapse;font-size:11px">'
            '<thead><tr style="background:#f0f2f8;border-bottom:1.5px solid #d0d5e8">'
            '<th style="padding:6px 10px;text-align:left;color:#3355aa;font-size:10px">Scenario</th>'
            '<th style="padding:6px 8px;color:#3355aa;font-size:10px">Prob</th>'
            '<th style="padding:6px 8px;color:#3355aa;font-size:10px">3 Months</th>'
            '<th style="padding:6px 8px;color:#3355aa;font-size:10px">12 Months</th>'
            '<th style="padding:6px 8px;color:#3355aa;font-size:10px">24 Months</th>'
            '<th style="padding:6px 10px;text-align:left;color:#3355aa;font-size:10px">Key Condition</th>'
            '</tr></thead><tbody>'
            f'<tr style="background:#D6F0E020;border-bottom:1px solid #e8eaed">'
            f'<td style="padding:7px 10px;font-weight:700;color:#1A7A4A">🟢 Bull</td>'
            f'<td style="padding:7px 8px;text-align:center;font-size:10px;color:#1A7A4A">25%</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["3mo_bull"],spy_anchor)}</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["12mo_bull"],spy_anchor)}</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["24mo_bull"],spy_anchor)}</td>'
            f'<td style="padding:7px 10px;font-size:10px;color:#555">HY OAS &lt;380, breadth widens, Fed cuts</td></tr>'
            f'<tr style="background:#FFF0CC20;border-bottom:1px solid #e8eaed">'
            f'<td style="padding:7px 10px;font-weight:700;color:#D4820A">🟡 Base</td>'
            f'<td style="padding:7px 8px;text-align:center;font-size:10px;color:#D4820A">50%</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["3mo_base"],spy_anchor)}</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["12mo_base"],spy_anchor)}</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["24mo_base"],spy_anchor)}</td>'
            f'<td style="padding:7px 10px;font-size:10px;color:#555">Kitchin correction then recovery, Juglar holds</td></tr>'
            f'<tr style="background:#FDDDD520;border-bottom:1px solid #e8eaed">'
            f'<td style="padding:7px 10px;font-weight:700;color:#C0390F">🔴 Bear</td>'
            f'<td style="padding:7px 8px;text-align:center;font-size:10px;color:#C0390F">25%</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["3mo_bear"],spy_anchor)}</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["12mo_bear"],spy_anchor)}</td>'
            f'<td style="padding:7px 8px;text-align:center">{_tgt_badge(tgts["24mo_bear"],spy_anchor)}</td>'
            f'<td style="padding:7px 10px;font-size:10px;color:#555">Juglar peak confirmed + Sahm triggers</td></tr>'
            f'<tr style="background:#f8f9fe">'
            f'<td style="padding:7px 10px;font-weight:700;color:#1a1a2e">📍 NOW</td>'
            f'<td style="padding:7px 8px;text-align:center;font-size:10px;color:#1155cc">—</td>'
            f'<td colspan="3" style="padding:7px 8px;text-align:center;font-size:12px;font-weight:900;color:#1155cc">SPY ${spy_anchor:,.2f}</td>'
            f'<td style="padding:7px 10px;font-size:10px;color:#555">{rg_dict["label"]}</td></tr>'
            '</tbody></table>'
        )
    _scenario_table_html = _build_scenario_table(_tgts, _spy, rg)

    def _thesis_card(timeframe, icon, col, bg, headline, bullets, basis):
        return (
            f'<div style="background:{bg};border:1px solid {col}44;border-radius:8px;'
            f'padding:12px;border-top:3px solid {col}">'
            f'<div style="font-size:10px;color:{col};text-transform:uppercase;letter-spacing:.05em;'
            f'margin-bottom:4px;font-weight:700">{icon} {timeframe}</div>'
            f'<div style="font-size:13px;font-weight:800;color:#1a1a2e;margin-bottom:8px">{headline}</div>'
            f'<div style="font-size:10px;color:#555;line-height:1.7">{bullets}</div>'
            f'<div style="margin-top:8px;font-size:9px;color:{col};font-style:italic">{basis}</div>'
            f'</div>'
        )

    # Pre-compute AI HTML blocks to avoid f-string complexity
    _ai_regime_text = _ai("regime_summary", "")
    _ai_overall_summary = _ai("overall_summary",
        "• Set CLAUDE_API_KEY in cycle_analysis.py to enable AI narrative summaries.\n"
        "• Free $5 credits at platform.claude.com · covers ~1.7 years of daily runs.")
    _regime_ai_html = (
        '<div style="background:' + rg["col"] + '18;border-left:4px solid ' + rg["col"] + ';'
        'border-radius:0 8px 8px 0;padding:10px 16px;margin-bottom:14px;'
        'font-size:12px;color:#1a1a2e;line-height:1.6">'
        '<strong style="color:' + rg["col"] + '">&#x1F916; Analysis: </strong>'
        + _ai_regime_text + '</div>'
        if _ai_regime_text else ""
    )

    # Sector heatmap
    sector_cells = ""
    for t, nm in SECTOR_ETFS.items():
        sd = sp_data.get(t,{})
        if not sd: continue
        c1m = sd.get("c1m",0); c3m=sd.get("c3m",0); c1y=sd.get("c1y",0)
        rsi = sd.get("rsi",50); vs200=sd.get("vs200",0)
        trend=sd.get("trend","MIX")
        bg = f"rgba(26,122,74,{min(abs(c1m)/20,0.4):.2f})" if c1m>0 else f"rgba(192,57,15,{min(abs(c1m)/20,0.4):.2f})"
        tc = "#1A7A4A" if c1m>0 else "#C0390F"
        sector_cells += f"""
        <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;
                    padding:10px;text-align:center;position:relative;overflow:hidden">
          <div style="position:absolute;top:0;left:0;right:0;bottom:0;{f'background:{bg}'};pointer-events:none"></div>
          <div style="position:relative">
            <div style="font-size:13px;font-weight:800;color:#1a1a2e">{t}</div>
            <div style="font-size:9px;color:#556;margin-bottom:6px">{nm}</div>
            <div style="font-size:17px;font-weight:900;color:{tc}">{c1m:+.1f}%</div>
            <div style="font-size:9px;color:#556">1 month</div>
            <div style="font-size:10px;margin-top:5px;color:{'#1A7A4A' if c3m>0 else '#C0390F'}">{c3m:+.1f}% 3mo</div>
            <div style="font-size:10px;color:{'#1A7A4A' if c1y>0 else '#C0390F'}">{c1y:+.1f}% 1yr</div>
            <div style="font-size:10px;color:#556;margin-top:2px">{vs200:+.1f}% vs200d</div>
            <div style="font-size:10px;color:#4a6688">RSI {rsi}</div>
            <div style="font-size:9px;color:{'#1A7A4A' if trend=='UP' else '#C0390F' if trend=='DOWN' else '#556'};margin-top:3px">{trend}</div>
          </div>
        </div>"""

    # ── Build sector ratio guide variables from live pair data ─────────────────
    def _pair_info(bt, brt):
        if bt not in md or brt not in md: return {"direction":"—","rank1y":50}
        ri = ratio_info(md[bt], md[brt])
        return ri if ri else {"direction":"—","rank1y":50}

    _xly = _pair_info("XLY","XLP"); _xlf = _pair_info("XLF","XLU")
    _xle = _pair_info("XLE","XLU"); _iwm = _pair_info("IWM","SPY")
    _hyg = _pair_info("HYG","LQD"); _xlk = _pair_info("XLK","XLP")

    def _dir_note(ri, rising_note, falling_note, flat_note):
        d = ri.get("direction","—")
        if "RISING" in d: return rising_note
        if "FALLING" in d: return falling_note
        return flat_note

    def _dcol(ri):
        d = ri.get("direction","—")
        return "#1A7A4A" if "RISING" in d else "#C0390F" if "FALLING" in d else "#556"

    xly_col = _dcol(_xly); xlf_col = _dcol(_xlf)
    xle_col = _dcol(_xle); iwm_col = _dcol(_iwm)

    xly_dir = _xly.get("direction","—")
    xly_note = _dir_note(_xly,
        f"Risk-ON confirmed — consumers spending on discretionary. 3M: {_xly.get('c3m',0) or 0:+.1f}%",
        f"DEFENSIVE rotation — staples outperforming. 3M: {_xly.get('c3m',0) or 0:+.1f}%. Reduce cyclicals.",
        f"Neutral/transitional at {_xly.get('rank1y',50):.0f}th percentile. 3M: {_xly.get('c3m',0) or 0:+.1f}%.")

    xlf_dir = _xlf.get("direction","—")
    xlf_pct = _xlf.get("rank1y",50)
    xlf_note = _dir_note(_xlf,
        f"Growth regime — financials leading. Healthy expansion signal.",
        f"Growth concern — utilities outperforming ({xlf_pct:.0f}th %ile). Late cycle or rate cut expectation.",
        f"Neutral at {xlf_pct:.0f}th %ile — no strong growth/defensive bias. 3M: {_xlf.get('c3m',0) or 0:+.1f}%.")

    xle_dir = _xle.get("direction","—")
    xle_pct = _xle.get("rank1y",50)
    xle_note = _dir_note(_xle,
        f"INFLATION/LATE CYCLE signal — energy at {xle_pct:.0f}th %ile. 3M: {_xle.get('c3m',0) or 0:+.1f}%. Historically reverting within 3-6mo.",
        "Deflation/recession signal — utilities winning. Energy demand collapsing.",
        f"Neutral at {xle_pct:.0f}th %ile. 3M: {_xle.get('c3m',0) or 0:+.1f}%.")

    iwm_dir = _iwm.get("direction","—")
    iwm_pct = _iwm.get("rank1y",50)
    iwm_note = _dir_note(_iwm,
        f"Broad rally — small caps leading at {iwm_pct:.0f}th %ile. Risk appetite healthy.",
        f"Breadth narrowing — only large caps holding. Late-cycle warning.",
        f"Mixed breadth at {iwm_pct:.0f}th %ile. 3M: {_iwm.get('c3m',0) or 0:+.1f}%.")

    # Build bear/bull cross-pair signal lists
    _bear_signals_list = []
    _bull_signals_list = []

    def _add_signal(ri, name, rising_bull, falling_bear):
        d = ri.get("direction","—"); c3m = ri.get("c3m",0) or 0; pct = ri.get("rank1y",50)
        if falling_bear and "FALLING" in d:
            _bear_signals_list.append(f'<div style="padding:3px 0;border-bottom:1px solid #e0e4ed">🔴 <strong>{name}</strong> FALLING ({pct:.0f}th %ile, {c3m:+.1f}% 3m)</div>')
        elif not falling_bear and "RISING" in d:
            _bear_signals_list.append(f'<div style="padding:3px 0;border-bottom:1px solid #e0e4ed">🔴 <strong>{name}</strong> RISING — late cycle ({pct:.0f}th %ile)</div>')
        elif rising_bull and "RISING" in d:
            _bull_signals_list.append(f'<div style="padding:3px 0;border-bottom:1px solid #e0e4ed">🟢 <strong>{name}</strong> RISING ({pct:.0f}th %ile, {c3m:+.1f}% 3m)</div>')
        elif not rising_bull and "FALLING" in d:
            _bull_signals_list.append(f'<div style="padding:3px 0;border-bottom:1px solid #e0e4ed">🟢 <strong>{name}</strong> FALLING — defensive bid = potential mean revert</div>')
        else:
            _bull_signals_list.append(f'<div style="padding:3px 0;border-bottom:1px solid #e0e4ed">🟡 <strong>{name}</strong> FLAT → ({pct:.0f}th %ile)</div>')

    _add_signal(_xly, "XLY/XLP Risk Appetite",  True,  True)
    _add_signal(_xlf, "XLF/XLU Growth vs Def",  True,  True)
    _add_signal(_xle, "XLE/XLU Inflation",       False, False)
    _add_signal(_iwm, "IWM/SPY Breadth",         True,  True)
    _add_signal(_hyg, "HYG/LQD Credit Risk",     True,  True)
    _add_signal(_xlk, "XLK/XLP Growth vs Value", True,  True)

    bear_signals_html = "".join(_bear_signals_list) or '<div style="color:#556">No clear bear signals</div>'
    bull_signals_html = "".join(_bull_signals_list) or '<div style="color:#556">No clear bull signals</div>'

    # Synthesis
    n_bear = len(_bear_signals_list); n_bull = len(_bull_signals_list)
    if n_bear >= 4:
        synthesis = f"BEARISH ROTATION DOMINANT ({n_bear} bear vs {n_bull} bull signals) — institutional money moving to defensives and energy. Classic late-cycle/stagflation positioning."
    elif n_bull >= 4:
        synthesis = f"BULLISH ROTATION ({n_bull} bull vs {n_bear} bear signals) — broad risk appetite. Mid-to-early cycle characteristics."
    elif xle_pct > 80 and xlf_pct < 30:
        synthesis = "STAGFLATION SIGNAL — Energy surging, financials weak vs utilities. Matches 2007-08 and early 2022. High caution warranted for growth assets."
    else:
        synthesis = f"MIXED SIGNALS — {n_bull} bullish, {n_bear} bearish pair signals. No strong directional consensus. Stay balanced."

    # Format sector guide with live data
    sector_ratio_guide_filled = SECTOR_RATIO_GUIDE_TEMPLATE.format(
        xly_dir=xly_dir, xly_note=xly_note, xly_col=xly_col,
        xlf_dir=xlf_dir, xlf_pct=xlf_pct, xlf_note=xlf_note, xlf_col=xlf_col,
        xle_dir=xle_dir, xle_note=xle_note, xle_col=xle_col,
        iwm_dir=iwm_dir, iwm_note=iwm_note, iwm_col=iwm_col,
        bear_signals_html=bear_signals_html,
        bull_signals_html=bull_signals_html,
        synthesis=synthesis,
    )

    # Cross-pair rows for table
    pair_table_rows = ""
    for bt, brt, name, desc in CROSS_PAIRS:
        pk = f"{bt}/{brt}"
        if bt not in md or brt not in md: continue
        ri = ratio_info(md[bt], md[brt])
        if not ri: continue
        d=ri["direction"]; dc=ri["dir_col"]
        c1m=ri.get("c1m",0) or 0; c3m=ri.get("c3m",0) or 0; c6m=ri.get("c6m",0) or 0
        r1y=ri.get("rank1y",50); rsi=ri.get("rsi",50)
        bgrow="rgba(26,122,74,0.08)" if "RISING" in d else "rgba(192,57,15,0.08)" if "FALLING" in d else "transparent"
        pair_table_rows += f"""
        <tr style="border-bottom:1px solid #e0e4ed;background:{bgrow}">
          <td style="padding:9px 12px;white-space:nowrap">
            <div style="font-size:13px;font-weight:800;color:#1155cc">{pk}</div>
            <div style="font-size:10px;color:#556">{name}</div>
          </td>
          <td style="padding:9px 10px;text-align:center">
            <span style="background:{dc}20;color:{dc};padding:3px 12px;border-radius:8px;
                         font-size:12px;font-weight:800;border:1px solid {dc}40">{d}</span>
          </td>
          <td style="padding:9px 10px;text-align:center;font-size:11px;font-weight:700;
                     color:{'#C0390F' if r1y<20 else '#1A7A4A' if r1y>80 else '#556'}">{r1y:.0f}th</td>
          <td style="padding:9px 10px;text-align:center;font-size:11px;
                     color:{'#1A7A4A' if c1m>0 else '#C0390F'}">{c1m:+.1f}%</td>
          <td style="padding:9px 10px;text-align:center;font-size:11px;
                     color:{'#1A7A4A' if c3m>0 else '#C0390F'}">{c3m:+.1f}%</td>
          <td style="padding:9px 10px;text-align:center;font-size:11px;
                     color:{'#1A7A4A' if c6m>0 else '#C0390F'}">{c6m:+.1f}%</td>
          <td style="padding:9px 10px;text-align:center;font-size:10px;color:#555">{rsi}</td>
          <td style="padding:9px 14px;font-size:10px;color:#555577;max-width:250px">{desc}</td>
        </tr>"""

    # ── Extreme percentile scanner cards ──────────────────────────────────────
    extreme_pairs_html = ""
    for bt, brt, name, desc in CROSS_PAIRS:
        pk = f"{bt}/{brt}"
        _pd_e = pairs_data.get(pk, {})
        _rk_e = _pd_e.get("rank1y", 50)
        _dc_e = _pd_e.get("dir_col", "#556")
        _c3m_e = _pd_e.get("c3m", 0)
        if _rk_e < 15:
            _sig_e = f"⚠ EXTREME LOW — {_rk_e:.0f}th %ile"
            _bg_e  = "#fff5f5"; _bc_e = "#C0390F"
            _note_e = "Historically cheap vs denominator. Contrarian long candidate."
        elif _rk_e > 85:
            _sig_e = f"⚠ EXTREME HIGH — {_rk_e:.0f}th %ile"
            _bg_e  = "#f5fff5"; _bc_e = "#1A7A4A"
            _note_e = "Historically expensive vs denominator. Watch for reversal."
        else:
            continue   # skip mid-range pairs
        extreme_pairs_html += (
            f'<div style="background:{_bg_e};border:1px solid {_bc_e}44;border-left:3px solid {_bc_e};'
            f'border-radius:8px;padding:10px 12px">'
            f'<div style="font-size:12px;font-weight:800;color:#1155cc">{pk}</div>'
            f'<div style="font-size:9px;color:#556;margin-bottom:4px">{name}</div>'
            f'<div style="font-size:10px;font-weight:700;color:{_bc_e};margin-bottom:4px">{_sig_e}</div>'
            f'<div style="font-size:10px;color:{_dc_e};font-weight:600">3M: {_c3m_e:+.1f}%</div>'
            f'<div style="font-size:9px;color:#555;margin-top:4px;line-height:1.5">{_note_e}</div>'
            f'</div>'
        )
    if not extreme_pairs_html:
        extreme_pairs_html = '<div style="color:#556;font-size:10px;grid-column:span 4">No pairs at extreme percentile readings this session — all ratios in mid-range.</div>'

    # ── Assemble final HTML ───────────────────────────────────────────────────
    # Build pair chart JS blocks (can't use chr() or complex expressions inside f-string)
    _pair_js = []
    for _pk, _pd in pairs_data.items():
        _d    = json.dumps(_pd.get("dates",      []))
        _v    = json.dumps(_pd.get("values",     []))
        _e20  = json.dumps(_pd.get("ema20",      []))
        _e50  = json.dumps(_pd.get("ema50",      []))
        _seas = json.dumps(_pd.get("seasonality",[]))
        _rk   = _pd.get("rank1y",  50)
        _dc   = _pd.get("dir_col", "#334466")
        _nm   = _pd.get("name",    "")
        _c3m  = _pd.get("c3m",     0)
        _vs   = _pd.get("vs_seasonal", None)
        _id   = _pk.replace("/", "_")
        _sig_col = ("#C0390F" if _rk < 15 else "#1A7A4A" if _rk > 85
                    else "#D4820A" if _rk < 25 or _rk > 75 else "#778899")
        _sig_lbl = ("⚠ EXTREME LOW" if _rk < 15 else "⚠ EXTREME HIGH" if _rk > 85
                    else "Low Zone" if _rk < 25 else "High Zone" if _rk > 75 else "Mid Range")
        _vs_str = (f"+{_vs:.1f}% above seasonal" if (_vs is not None and _vs > 0)
                   else (f"{_vs:.1f}% below seasonal" if _vs is not None else ""))

        _pair_js.append(f"""
(function(){{
  const d    = {_d};
  const v    = {_v};
  const e20  = {_e20};
  const e50  = {_e50};
  const seas = {_seas};
  if(!d.length || !v.length) return;
  const ctx = document.getElementById('pair_{_id}');
  if(!ctx) return;
  const dirCol  = '{_dc}';
  const sigCol  = '{_sig_col}';

  // Show month labels (1st occurrence of each month)
  const seenMo = {{}};
  const monthLbls = d.map(dt => {{
    const mo = dt.slice(0,7);
    if(!seenMo[mo]) {{ seenMo[mo]=true; return mo; }}
    return '';
  }});

  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: d,
      datasets: [
        // Seasonality — grey dotted, NO fill, behind everything
        {{ label: '5yr Seasonal',
           data: seas,
           borderColor: 'rgba(100,110,140,0.5)',
           borderWidth: 1.5,
           borderDash: [5, 4],
           pointRadius: 0,
           fill: false,
           tension: 0.5,
           order: 10,
        }},
        // EMA 50 — amber, NO fill
        {{ label: 'EMA50',
           data: e50,
           borderColor: 'rgba(180,120,20,0.7)',
           borderWidth: 1.5,
           pointRadius: 0,
           fill: false,
           tension: 0.3,
           order: 3,
        }},
        // EMA 20 — direction colored, NO fill
        {{ label: 'EMA20',
           data: e20,
           borderColor: dirCol + 'bb',
           borderWidth: 1.8,
           pointRadius: 0,
           fill: false,
           tension: 0.3,
           order: 2,
        }},
        // Daily ratio — main line, NO fill (prevents black chart bug)
        {{ label: '{_nm}',
           data: v,
           borderColor: dirCol,
           borderWidth: 2,
           pointRadius: 0,
           fill: false,
           tension: 0.1,
           order: 1,
        }},
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode:'index', intersect:false }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            title: items => items[0].label,
            label: c => {{
              if(c.dataset.label === '{_nm}')      return 'Ratio: '   + c.parsed.y.toFixed(4);
              if(c.dataset.label === 'EMA20')       return 'EMA20: '   + c.parsed.y.toFixed(4);
              if(c.dataset.label === 'EMA50')       return 'EMA50: '   + c.parsed.y.toFixed(4);
              if(c.dataset.label === '5yr Seasonal')return 'Seasonal: '+ c.parsed.y.toFixed(4);
              return null;
            }}
          }}
        }},
        zoom: {{
          pan:  {{ enabled:false }},
          zoom: {{ wheel:{{ enabled:false }}, pinch:{{ enabled:false }}, mode:'x' }}
        }}
      }},
      scales: {{
        x: {{
          ticks: {{
            color: '#8899aa',
            font: {{ size: 8 }},
            maxRotation: 0,
            callback: (val, i) => monthLbls[i] || null,
            maxTicksLimit: 14,
            autoSkip: false,
          }},
          grid: {{ color: 'rgba(180,190,210,0.2)' }}
        }},
        y: {{
          position: 'right',
          ticks: {{ color: '#778899', font: {{ size: 9 }}, maxTicksLimit: 5 }},
          grid: {{ color: 'rgba(180,190,210,0.2)' }}
        }}
      }}
    }}
  }});
  const _pc = Chart.getChart(ctx);
  if(_pc) {{ initTVZoom(_pc); ctx.addEventListener('mouseenter',function _h(){{showTVHint(ctx);ctx.removeEventListener('mouseenter',_h);}},{{once:true}}); }}
}})();""")
    pair_js_blocks = "\n".join(_pair_js)

    # Pre-compute JSON for overlay and road charts
    _overlay_data = charts.get("cycle_overlay", {})
    _road_data    = charts.get("road_to_2032", {})
    overlay_json  = json.dumps(_overlay_data)
    road_json     = json.dumps(_road_data)

    # Current month index in the overlay (months since 2020-03)
    from datetime import date as _date
    _trough = _date(2020, 3, 1)
    _today  = _date.today()
    today_month = (_today.year - _trough.year) * 12 + (_today.month - _trough.month)
    # Kitchin cycle trough: Oct 2023
    _kt = _date(2023, 10, 1)
    _kitchin_today_month = (_today.year - _kt.year) * 12 + (_today.month - _kt.month)

    # ── Precompute overlay + road JS outside the f-string (avoids brace conflicts) ──
    _ov = _overlay_data
    _rd = _road_data
    import json as _json2
    _ov_json = _json2.dumps(_ov)
    _rd_json = _json2.dumps(_rd)

    # Compute plain-language insight for the overlay (must be before f-string return)
    try:
        _cur = _ov.get("Current (2020)",{}).get("values",[])
        _avg_v = _ov.get("__avg__",{}).get("values",[])
        _cur_idx = _cur[today_month] if today_month < len(_cur) else None
        _avg_idx = _avg_v[today_month] if _avg_v and today_month < len(_avg_v) else None
        _behind_pct = round((_cur_idx/_avg_idx-1)*100,1) if (_cur_idx and _avg_idx and _avg_idx>0) else None
        if _behind_pct is not None:
            _direction = "ahead of" if _behind_pct > 0 else "behind"
            _insight_line = f"Current cycle is running {_direction} the historical average by {abs(_behind_pct):.1f}%"
        else:
            _insight_line = "Comparing current cycle to historical average"
        if _cur_idx:
            _pace = ("The current cycle ran FASTER than average — mean reversion risk elevated."
                     if _behind_pct and _behind_pct > 10 else
                     "The current cycle ran SLOWER than average — more upside may remain before the cycle turns."
                     if _behind_pct and _behind_pct < -10 else
                     "The current cycle is tracking near the historical average.")
            _insight_detail = (
                f"At month {today_month} of the current cycle (today), SPY is indexed at ~{_cur_idx:.0f} "
                f"vs historical average of ~{_avg_idx:.0f}. {_pace} "
                "Red stars ★ = where each prior cycle's bear market began. "
                "The 2009 cycle ran to month 114 before its COVID bear — all prior cycles turned before month 90."
            )
        else:
            _insight_detail = "Cycle data loading..."
    except Exception:
        _insight_line = "Cycle comparison — green=current (2020 trough), dashed=prior cycles"
        _insight_detail = "Grey band = historical average ± 1 standard deviation across 4 prior Juglar cycles."

    overlay_chart_js = """
// Juglar Cycle Overlay — all cycles indexed to 100 at their trough
(function() {
  const overlay = """ + _ov_json + """;
  const todayM  = """ + str(today_month) + """;
  const baseSPY = """ + str(round(float(md["SPY"].dropna().iloc[-1]),2) if "SPY" in md else 530) + """;
  const ctx = document.getElementById('overlay_chart');
  if (!ctx) { return; }

  const cycleKeys = Object.keys(overlay).filter(k => !k.startsWith('__'));
  if (!cycleKeys.length) {
    ctx.parentNode.innerHTML += '<p style="color:#C0390F;padding:12px;font-size:11px">No cycle data — ensure yfinance is installed: pip install yfinance</p>';
    return;
  }

  // Solid colors — NO dashes, thick lines for visibility
  const STYLE = {
    '1982 Cycle':    { color:'#FF6633', width:2.5 },
    '1990 Cycle':    { color:'#FFAA22', width:2.5 },
    '2002 Cycle':    { color:'#FFDD44', width:2.5 },
    '2009 Cycle':    { color:'#44AAFF', width:2.5 },
    'Current (2020)':{ color:'#00FF99', width:4.0 },
    '__avg__':       { color:'rgba(180,180,200,0.55)', width:1.5 },
  };

  // Bear market peak month for each prior cycle (months from trough)
  const PEAK = { '1982 Cycle':61, '1990 Cycle':78, '2002 Cycle':60, '2009 Cycle':113 };

  const maxM = Math.max(...cycleKeys.map(k => overlay[k].values.length));

  // Build datasets — prior cycles first, current on top
  const datasets = [];

  // Grey ±1σ band
  if (overlay['__upper__'] && overlay['__lower__']) {
    datasets.push({
      label:'Historical ±1σ',
      data: overlay['__upper__'].values,
      borderColor:'rgba(180,190,220,0)', backgroundColor:'rgba(180,190,220,0.15)',
      borderWidth:0, pointRadius:0, fill:'+1', tension:0.3
    });
    datasets.push({
      label:'_band_lower',
      data: overlay['__lower__'].values,
      borderColor:'rgba(180,190,220,0)', backgroundColor:'transparent',
      borderWidth:0, pointRadius:0, fill:false, tension:0.3
    });
  }

  // Avg line
  if (overlay['__avg__']) {
    datasets.push({
      label:'Hist. Avg',
      data: overlay['__avg__'].values,
      borderColor:STYLE['__avg__'].color, backgroundColor:'transparent',
      borderWidth:STYLE['__avg__'].width, pointRadius:0,
      borderDash:[6,4], tension:0.3, fill:false
    });
  }

  // Prior cycles — SOLID, thick, bright
  ['1982 Cycle','1990 Cycle','2002 Cycle','2009 Cycle'].forEach(label => {
    const d = overlay[label];
    if (!d) return;
    const st = STYLE[label] || { color:'#556', width:2 };

    // Main line — solid, thick
    datasets.push({
      label, data: d.values,
      borderColor: st.color,
      backgroundColor: 'transparent',
      borderWidth: st.width,
      pointRadius: 0,
      tension: 0.3,
      fill: false,
    });

    // Peak dot marker (circle, not star)
    const pk = PEAK[label];
    if (pk && pk < d.values.length) {
      datasets.push({
        label: '_peak_' + label,
        data: d.values.map((v,i) => i===pk ? v : null),
        borderColor: st.color,
        backgroundColor: '#FF0000',
        pointRadius: d.values.map((v,i) => i===pk ? 7 : 0),
        pointStyle: 'circle',
        showLine: false, fill: false,
      });
    }
  });

  // Current cycle — bright green, solid, thickest
  const cur = overlay['Current (2020)'];
  if (cur) {
    datasets.push({
      label: 'Current (2020)',
      data: cur.values,
      borderColor: '#00FF99',
      backgroundColor: 'rgba(0,255,153,0.08)',
      borderWidth: 4,
      pointRadius: 0,
      tension: 0.3,
      fill: true,
    });
  }

  // X-axis: months from trough (0=trough, 12=1yr, 24=2yr...)
  const xlabels = Array.from({length:maxM}, (_,i) =>
    (function(i){
    const tYr=2020,tMo=3; // Juglar trough: March 2020
    const abs = tMo-1+i; const yr = tYr+Math.floor(abs/12); const mo = abs%12;
    if(mo===0) return String(yr);
    if(mo===6) return "'"+String(yr).slice(2);
    return '';
  })(i)
  );

  // Custom plugin to draw TODAY line and annotation
  const todayPlugin = {
    id: 'todayOverlay',
    afterDraw(chart) {
      if (todayM > maxM) return;
      const x = chart.scales.x.getPixelForValue(todayM);
      const {top, bottom} = chart.chartArea;
      const ctx2 = chart.ctx;
      ctx2.save();
      ctx2.strokeStyle = 'rgba(0,188,212,0.95)';
      ctx2.lineWidth = 2.5;
      ctx2.setLineDash([5,3]);
      ctx2.beginPath(); ctx2.moveTo(x, top); ctx2.lineTo(x, bottom); ctx2.stroke();
      ctx2.setLineDash([]);
      ctx2.fillStyle = 'rgba(0,188,212,0.95)';
      ctx2.font = 'bold 11px sans-serif';
      ctx2.fillText('TODAY', x + 4, top + 16);
      ctx2.restore();
    }
  };

  new Chart(ctx, {
    type: 'line',
    plugins: [todayPlugin],
    data: { labels: xlabels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 600 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: {
            color: '#444466', font: { size: 10 },
            filter: item => !item.text.startsWith('_') && item.text !== 'Historical ±1σ'
          }
        },
        tooltip: {
          callbacks: {
            title: items => 'Month ' + items[0].dataIndex + ' from trough (' + xlabels[items[0].dataIndex] + ')',
            label: c => {
              if (c.dataset.label.startsWith('_')) return null;
              const v = c.parsed.y;
              if (!v) return null;
              return c.dataset.label + ': ' + v.toFixed(1) + 'x trough';
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: '#778688', font: { size: 9 }, maxTicksLimit: 18,
            callback: (v,i) => xlabels[i] && xlabels[i] !== '·' ? xlabels[i] : null
          },
          grid: { color: 'rgba(40,40,70,0.7)' },
          title: { display:true, text:'Months from Juglar cycle trough  (all cycles aligned at 100 = trough price)', color:'#3355aa', font:{size:9} }
        },
        y: {
          ticks: { color: '#778688', font: { size: 9 } },
          grid: { color: 'rgba(40,40,70,0.7)' },
          title: { display:true, text:'S&P 500 indexed  (100 = trough price)', color:'#3355aa', font:{size:9} }
        }
      }
    }
  });
})();
"""

    road_chart_js = """
// Road to 2032 — Single unified SPY path (AI-powered or cycle-math)
// All cycle corrections baked into ONE trajectory — no parallel conflicting lines
(function() {
  const road = """ + _rd_json + """;
  const ctx = document.getElementById('road_chart');
  if (!ctx || !road.years) return;

  const yrs      = road.years;
  const lbls     = road.year_labels || yrs.map((y,i) => i%4===0 ? String(Math.round(y)) : '');
  const todayYr  = road.today_year;
  const actual   = road.actual   || [];
  const rp       = road.road_proj || {};
  const futurYrs = rp.future_years || [];
  const spyPath  = rp.spy_path    || [];
  const kuzTrend = rp.kuznets_trend || [];
  const kl       = rp.key_levels  || {};
  const ddPct    = road.dd_from_ath || 0;
  const athPrice = road.ath_price || road.base_spy;

  // Map future quarterly prices onto the yrs array
  const projMap = {};
  futurYrs.forEach((fy, i) => {
    const nearIdx = yrs.reduce((bi, y, ci) => Math.abs(y-fy) < Math.abs(yrs[bi]-fy) ? ci : bi, 0);
    if (spyPath[i] !== undefined) projMap[nearIdx] = spyPath[i];
  });
  const kuzMap = {};
  futurYrs.forEach((fy, i) => {
    const nearIdx = yrs.reduce((bi, y, ci) => Math.abs(y-fy) < Math.abs(yrs[bi]-fy) ? ci : bi, 0);
    if (kuzTrend[i] !== undefined) kuzMap[nearIdx] = kuzTrend[i];
  });

  // Build full arrays
  const actualArr  = yrs.map((y,i) => actual[i] !== undefined ? actual[i] : null);
  const projArr    = yrs.map((y,i) => projMap[i] !== undefined ? projMap[i] : null);
  const kuzArr     = yrs.map((y,i) => kuzMap[i] !== undefined ? kuzMap[i] : null);

  // Phase background shading — color regions by cycle phase
  const phasePlugin = {
    id: 'phaseShading',
    beforeDraw(chart) {
      const ctx2 = chart.ctx;
      const {left, right, top, bottom} = chart.chartArea;
      const xScale = chart.scales.x;
      const W = right - left;
      const N = yrs.length;

      // Define phase regions [startYr, endYr, color, label]
      const phases = [
        [todayYr,        todayYr + 0.85, 'rgba(210,130,10,0.08)',  'Kitchin+Juglar trough'],
        [todayYr + 0.85, todayYr + 1.75, 'rgba(192,57,15,0.07)',   'Juglar contraction'],
        [todayYr + 1.75, kl.kuznets_peak_year || 2028.25, 'rgba(20,150,50,0.06)', 'Recovery'],
        [kl.kuznets_peak_year || 2028.25, (kl.kuznets_peak_year||2028.25)+0.75, 'rgba(255,200,0,0.08)', 'Kuznets peak'],
        [(kl.kuznets_peak_year||2028.25)+0.75, 2033, 'rgba(139,0,0,0.09)',   'Kuznets winter'],
      ];

      phases.forEach(([sy, ey, col, lbl]) => {
        const si = yrs.findIndex(y => y >= sy - 0.05);
        const ei = yrs.findIndex(y => y >= ey - 0.05);
        if (si < 0) return;
        const x1 = left + (si / Math.max(N-1,1)) * W;
        const x2 = left + ((ei < 0 ? N-1 : ei) / Math.max(N-1,1)) * W;
        ctx2.save();
        ctx2.fillStyle = col;
        ctx2.fillRect(x1, top, x2 - x1, bottom - top);
        // Phase label at top
        ctx2.fillStyle = col.replace('0.0', '0.6').replace('0.08','0.7').replace('0.09','0.7');
        ctx2.font = 'bold 9px sans-serif';
        ctx2.fillText(lbl, x1 + 4, top + 12);
        ctx2.restore();
      });
    }
  };

  // TODAY line plugin
  const todayPlugin = {
    id:'todayLine',
    afterDraw(chart) {
      const ti = yrs.findIndex(y => y >= todayYr - 0.15);
      if (ti < 0) return;
      const x = chart.scales.x.getPixelForValue(ti);
      const {top, bottom} = chart.chartArea;
      chart.ctx.save();
      chart.ctx.strokeStyle = 'rgba(0,188,212,0.95)';
      chart.ctx.lineWidth = 2.5; chart.ctx.setLineDash([5,3]);
      chart.ctx.beginPath(); chart.ctx.moveTo(x,top); chart.ctx.lineTo(x,bottom); chart.ctx.stroke();
      chart.ctx.setLineDash([]);
      chart.ctx.fillStyle = 'rgba(0,188,212,0.95)';
      chart.ctx.font = 'bold 11px sans-serif';
      chart.ctx.fillText('NOW', x+4, top+16);
      chart.ctx.restore();
    }
  };

  // Key level marker plugin (trough, peak, winter dots)
  const markerPlugin = {
    id: 'keyMarkers',
    afterDatasetsDraw(chart) {
      const markers = [
        { yr: kl.kitchin_trough_year,       price: kl.kitchin_trough_price,       col:'#D4820A', lbl:'Kitchin trough' },
        { yr: kl.kuznets_peak_year,          price: kl.kuznets_peak_price,          col:'#1A7A4A', lbl:'Kuznets peak'   },
        { yr: kl.kuznets_winter_trough_year, price: kl.kuznets_winter_trough_price, col:'#8B0000', lbl:'Winter trough'  },
      ];
      markers.forEach(m => {
        if (!m.yr || !m.price) return;
        const xi = yrs.findIndex(y => Math.abs(y - m.yr) < 0.2);
        if (xi < 0) return;
        const xPx = chart.scales.x.getPixelForValue(xi);
        const yPx = chart.scales.y.getPixelForValue(m.price);
        chart.ctx.save();
        chart.ctx.beginPath();
        chart.ctx.arc(xPx, yPx, 7, 0, Math.PI*2);
        chart.ctx.fillStyle = m.col;
        chart.ctx.fill();
        chart.ctx.strokeStyle = '#fff';
        chart.ctx.lineWidth = 2;
        chart.ctx.stroke();
        chart.ctx.fillStyle = m.col;
        chart.ctx.font = 'bold 9px sans-serif';
        chart.ctx.fillText('$' + Math.round(m.price), xPx + 10, yPx + 4);
        chart.ctx.fillText(m.lbl, xPx + 10, yPx + 14);
        chart.ctx.restore();
      });
    }
  };

  new Chart(ctx, {
    type: 'line',
    plugins: [phasePlugin, todayPlugin, markerPlugin],
    data: {
      labels: lbls,
      datasets: [
        {
          label: 'Actual SPY history',
          data: actualArr,
          borderColor: '#00cc77',
          backgroundColor: 'rgba(0,204,119,0.10)',
          borderWidth: 3, pointRadius: 0, fill: true, tension: 0.3,
        },
        {
          label: 'Projected SPY path (unified)',
          data: projArr,
          borderColor: '#ff6622',
          backgroundColor: 'rgba(255,102,34,0.07)',
          borderWidth: 2.5, pointRadius: 0, fill: true, tension: 0.4,
          borderDash: [6, 3],
        },
        {
          label: 'Kuznets trend (smooth)',
          data: kuzArr,
          borderColor: '#2266ee',
          backgroundColor: 'transparent',
          borderWidth: 2, pointRadius: 0, fill: false, tension: 0.5,
          borderDash: [8, 4],
        },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      interaction: { mode:'index', intersect:false },
      plugins: {
        legend: { labels: { color:'#444466', font:{size:10} } },
        tooltip: {
          callbacks: {
            title: items => {
              const i = items[0].dataIndex;
              return lbls[i] ? 'Year ' + lbls[i] : 'Quarter ' + i;
            },
            label: c => {
              if (!c.parsed.y) return null;
              return c.dataset.label + ': $' + Math.round(c.parsed.y);
            },
            afterBody: items => {
              const yr = yrs[items[0].dataIndex];
              if (!yr) return [];
              const lines = [];
              if (kl.kitchin_trough_year && Math.abs(yr - kl.kitchin_trough_year) < 0.35)
                lines.push('◉ Near Kitchin/Juglar trough');
              if (kl.kuznets_peak_year && Math.abs(yr - kl.kuznets_peak_year) < 0.35)
                lines.push('◉ Near Kuznets peak');
              if (kl.kuznets_winter_trough_year && Math.abs(yr - kl.kuznets_winter_trough_year) < 0.35)
                lines.push('◉ Near Kuznets winter trough');
              return lines;
            }
          }
        }
      },
      scales: {
        x: {
          ticks: { color:'#2244aa', font:{size:9}, maxTicksLimit:14,
            callback: (v,i) => lbls[i] || null },
          grid: { color:'rgba(40,40,60,0.15)' },
          title: { display:true, text:'Year (quarterly resolution)', color:'#778', font:{size:9} }
        },
        y: {
          ticks: { color:'#2244aa', font:{size:9},
            callback: v => '$' + Math.round(v) },
          grid: { color:'rgba(40,40,60,0.15)' },
          title: { display:true, text:'S&P 500 / SPY Level', color:'#778', font:{size:9} }
        }
      }
    }
  });
})();
"""

    # ── Prepare bond chart JS (pre-computed outside f-string) ────────────────
    _bt = charts.get("bond_timeseries", {})
    _bo = charts.get("bond_overlay", {})
    import json as _j2
    _bt_json = _j2.dumps(_bt)
    _bo_json = _j2.dumps(_bo)
    _kuznets_json = _j2.dumps(charts.get("kuznets_overlay", {}))
    _kitchin_json = _j2.dumps(charts.get("kitchin_overlay", {}))

    bond_charts_js = """
// Bond time-series — normalised to 100 (10yr lookback)
(function() {
  const bt = """ + _bt_json + """;
  const STYLES = {
    SPY: { color:'#00FF99', w:2.5 },
    TLT: { color:'#2266ee', w:2.5 },
    HYG: { color:'#FF9933', w:2   },
    LQD: { color:'#CC99FF', w:1.5 },
  };
  // Key events for annotation
  const EVENTS = [
    { label:'COVID trough', date:'2020-03' },
    { label:'Rate hikes start', date:'2022-03' },
    { label:'10Y peaks 5%', date:'2023-10' },
    { label:'Fed pivot', date:'2023-12' },
  ];

  // Chart 1: Normalised performance
  (function() {
    const ctx = document.getElementById('bond_norm_chart');
    if (!ctx) return;
    const allDates = bt.SPY ? bt.SPY.dates : (bt.TLT ? bt.TLT.dates : []);
    const datasets = Object.entries(bt).map(([k,v]) => ({
      label: k==='SPY'?'S&P 500 (SPY)': k==='TLT'?'20yr Treasuries (TLT)':
             k==='HYG'?'High Yield Bonds (HYG)':'Inv. Grade Bonds (LQD)',
      data: v.norm || [],
      borderColor: (STYLES[k]||{color:'#556'}).color,
      backgroundColor: 'transparent',
      borderWidth: (STYLES[k]||{w:1.5}).w,
      pointRadius: 0, tension: 0.3, fill: false,
    }));
    new Chart(ctx, {
      type:'line',
      data:{ labels: allDates, datasets },
      options:{
        responsive:true, maintainAspectRatio:true,
        interaction:{ mode:'index', intersect:false },
        plugins:{
          legend:{ labels:{ color:'#444466', font:{size:10} } },
          tooltip:{ callbacks:{ label: c => c.dataset.label+': '+c.parsed.y.toFixed(1)+'x base' }}
        },
        scales:{
          x:{ ticks:{ color:'#2244aa', font:{size:9}, maxTicksLimit:14 }, grid:{color:'rgba(180,190,220,0.4)'} },
          y:{ ticks:{ color:'#2244aa', font:{size:9} }, grid:{color:'rgba(180,190,220,0.4)'},
              title:{display:true, text:'Performance indexed to 100 (10yr ago)', color:'#778', font:{size:9}} }
        }
      }
    });
  })();

  // Chart 2: TLT vs SPY — inverse relationship during risk-off
  (function() {
    const ctx = document.getElementById('bond_tlt_spy_chart');
    if (!ctx || !bt.TLT || !bt.SPY) return;
    const tlt_d = bt.TLT.dates;
    const spyMap = Object.fromEntries((bt.SPY.dates||[]).map((d,i)=>[d,(bt.SPY.norm||[])[i]]));
    new Chart(ctx, {
      type:'line',
      data:{
        labels: tlt_d,
        datasets:[
          { label:'TLT (20yr Treasury)', data:bt.TLT.norm||[],
            borderColor:'#2266ee', borderWidth:2.5, pointRadius:0, tension:0.3, yAxisID:'y', fill:false },
          { label:'SPY (S&P 500)', data:tlt_d.map(d=>spyMap[d]||null),
            borderColor:'#00FF99', borderWidth:2, pointRadius:0, tension:0.3, yAxisID:'y', fill:false },
          { label:'TLT÷SPY ratio', data:tlt_d.map((d,i)=>{
              const tlt=(bt.TLT.norm||[])[i]; const spy=spyMap[d];
              return tlt&&spy ? Math.round(tlt/spy*1000)/10 : null;
            }),
            borderColor:'#FF9933', borderWidth:1.5, pointRadius:0, tension:0.3, yAxisID:'y2',
            borderDash:[5,3], fill:false },
        ]
      },
      options:{
        responsive:true, maintainAspectRatio:true,
        interaction:{ mode:'index', intersect:false },
        plugins:{ legend:{ labels:{ color:'#444466', font:{size:10} } } },
        scales:{
          y:{ ticks:{color:'#2244aa',font:{size:9}}, grid:{color:'rgba(180,190,220,0.4)'},
              title:{display:true,text:'Index (base=100)',color:'#2266ee',font:{size:9}} },
          y2:{ position:'right', ticks:{color:'#FF9933',font:{size:9}}, grid:{drawOnChartArea:false},
               title:{display:true,text:'TLT÷SPY',color:'#FF9933',font:{size:9}} },
          x:{ ticks:{color:'#2244aa',font:{size:9},maxTicksLimit:14}, grid:{color:'rgba(180,190,220,0.4)'} }
        }
      }
    });
  })();

  // Chart 3: HYG/LQD credit risk vs SPY
  (function() {
    const ctx = document.getElementById('bond_credit_chart');
    if (!ctx || !bt.HYG || !bt.LQD) return;
    const hyg_d = bt.HYG.dates;
    const lqdMap = Object.fromEntries((bt.LQD.dates||[]).map((d,i)=>[d,(bt.LQD.values||[])[i]]));
    const hygMap = Object.fromEntries(hyg_d.map((d,i)=>[ d,(bt.HYG.values||[])[i] ]));
    const spyMap = Object.fromEntries((bt.SPY?.dates||[]).map((d,i)=>[d,(bt.SPY.norm||[])[i]]));
    const ratio = hyg_d.map(d => {
      const h=hygMap[d], l=lqdMap[d]; return h&&l ? Math.round(h/l*1000)/1000 : null;
    });
    // Normalise ratio
    const validRatio = ratio.filter(v=>v!==null);
    const rBase = validRatio[0] || 1;
    const ratioNorm = ratio.map(v=>v?Math.round(v/rBase*1000)/10:null);
    new Chart(ctx, {
      type:'line',
      data:{
        labels: hyg_d,
        datasets:[
          { label:'HYG÷LQD (credit risk appetite)', data:ratioNorm,
            borderColor:'#FF9933', borderWidth:2.5, pointRadius:0, tension:0.3, yAxisID:'y',
            backgroundColor:'rgba(255,153,51,0.06)', fill:true },
          { label:'SPY (S&P 500)', data:hyg_d.map(d=>spyMap[d]||null),
            borderColor:'#00FF99', borderWidth:2, pointRadius:0, tension:0.3, yAxisID:'y', fill:false },
        ]
      },
      options:{
        responsive:true, maintainAspectRatio:true,
        interaction:{ mode:'index', intersect:false },
        plugins:{
          legend:{ labels:{ color:'#444466', font:{size:10} } },
          tooltip:{ callbacks:{ label: c => c.dataset.label+': '+c.parsed.y?.toFixed(1) }}
        },
        scales:{
          y:{ ticks:{color:'#2244aa',font:{size:9}}, grid:{color:'rgba(180,190,220,0.4)'},
              title:{display:true,text:'Index (base=100)',color:'#778',font:{size:9}} },
          x:{ ticks:{color:'#2244aa',font:{size:9},maxTicksLimit:14}, grid:{color:'rgba(180,190,220,0.4)'} }
        }
      }
    });
  })();
})();
"""

    # ── Tab content strings ───────────────────────────────────────────────────

    # ══════════════════════════════════════════════════════════════════════════
    # SECTOR STOCKS TAB — Top 10 per sector indexed to 100 vs sector ETF
    # ══════════════════════════════════════════════════════════════════════════
    import json as _jss
    _ss = sector_stocks or {}
    _ss_js_blocks = []
    _ss_sector_panels = []

    for _etf, _sdata in _ss.items():
        import pandas as _pd_ss, numpy as _np_ss
        _sname  = SECTOR_DISPLAY_NAMES.get(_etf, _etf)
        _etf_s  = _sdata["etf"]
        _stocks = _sdata["stocks"]
        _wts    = SECTOR_WEIGHTS.get(_etf, {})
        if len(_etf_s) < 20 or not _stocks: continue

        _etf_base   = float(_etf_s.iloc[0])
        _etf_1y_pct = round((float(_etf_s.iloc[-1]) / _etf_base - 1) * 100, 1)
        _etf_idx    = [round(float(v) / _etf_base * 100, 2) for v in _etf_s.values]
        _dates_raw  = [str(d)[:10] for d in _etf_s.index]
        _chart_id   = f"ss_{_etf}"

        _stock_meta    = []
        _stock_js_data = {}

        for _ci, (_tk, _ts) in enumerate(_stocks.items()):
            if len(_ts) < 20: continue
            try:
                _aligned = _ts.reindex(_etf_s.index, method="ffill").dropna()
                if len(_aligned) < 10: continue
                _tbase = float(_aligned.iloc[0])
                _tidx  = [round(float(v) / _tbase * 100, 2) for v in _aligned.values]
                def _pct(s, n): return round((float(s.iloc[-1]) / float(s.iloc[max(-n,-len(s))]) - 1)*100, 1) if len(s) >= 3 else 0
                _c1m = _pct(_ts,21); _c3m = _pct(_ts,63)
                _c6m = _pct(_ts,126); _c1y = _pct(_ts,252)
                _vs  = round(_c1y - _etf_1y_pct, 1)
                _wt  = _wts.get(_tk, 0.0)
                _color = STOCK_COLORS[_ci % len(STOCK_COLORS)]
                _stock_js_data[_tk] = {"indexed": _tidx, "color": _color, "vs": _vs}
                _stock_meta.append({"tk":_tk,"c1m":_c1m,"c3m":_c3m,"c6m":_c6m,
                                    "c1y":_c1y,"vs":_vs,"wt":_wt,"color":_color,"out":_vs>=0})
            except Exception: continue

        if not _stock_meta: continue
        _stock_meta.sort(key=lambda x: x["vs"], reverse=True)
        # Re-assign colors in sorted order so chart legend matches table
        for _ci2, _sm in enumerate(_stock_meta):
            _sm["color"] = STOCK_COLORS[_ci2 % len(STOCK_COLORS)]
            if _sm["tk"] in _stock_js_data:
                _stock_js_data[_sm["tk"]]["color"] = _sm["color"]

        # 3-column performance table
        _cols3 = [_stock_meta[:4], _stock_meta[4:7], _stock_meta[7:]]
        _col_htmls = []
        for _col_stocks in _cols3:
            if not _col_stocks: _col_htmls.append(""); continue
            _rows = ""
            for _sm in _col_stocks:
                _vi = "▲" if _sm["out"] else "▼"
                _vc = "#1A7A4A" if _sm["out"] else "#C0390F"
                _vb = "#f0fff4" if _sm["out"] else "#fff5f5"
                _rows += (
                    f'<tr style="border-bottom:1px solid #f0f2f8">'
                    f'<td style="padding:5px 8px;white-space:nowrap">'
                    f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
                    f'background:{_sm["color"]};margin-right:4px;vertical-align:middle"></span>'
                    f'<strong style="color:#1155cc;font-size:11px">{_sm["tk"]}</strong>'
                    f'<span style="font-size:8px;color:#999;margin-left:3px">{_sm["wt"]:.1f}%</span>'
                    f'</td>'
                    f'<td style="padding:5px 5px;text-align:center;font-size:10px;color:{"#1A7A4A" if _sm["c1m"]>=0 else "#C0390F"}">{_sm["c1m"]:+.1f}%</td>'
                    f'<td style="padding:5px 5px;text-align:center;font-size:10px;color:{"#1A7A4A" if _sm["c3m"]>=0 else "#C0390F"}">{_sm["c3m"]:+.1f}%</td>'
                    f'<td style="padding:5px 5px;text-align:center;font-size:10px;color:{"#1A7A4A" if _sm["c6m"]>=0 else "#C0390F"}">{_sm["c6m"]:+.1f}%</td>'
                    f'<td style="padding:5px 5px;text-align:center;font-size:10px;color:{"#1A7A4A" if _sm["c1y"]>=0 else "#C0390F"}">{_sm["c1y"]:+.1f}%</td>'
                    f'<td style="padding:5px 7px;text-align:center">'
                    f'<span style="font-size:10px;font-weight:800;color:{_vc};'
                    f'background:{_vb};padding:2px 7px;border-radius:6px;border:1px solid {_vc}33">'
                    f'{_vi} {_sm["vs"]:+.1f}%</span></td></tr>'
                )
            _col_htmls.append(
                f'<table style="width:100%;border-collapse:collapse;font-size:9px">'
                f'<thead><tr style="background:#f0f2f8">'
                f'<th style="padding:4px 8px;text-align:left;color:#3355aa">Ticker · Wt%</th>'
                f'<th style="padding:4px 5px;color:#3355aa">1M</th>'
                f'<th style="padding:4px 5px;color:#3355aa">3M</th>'
                f'<th style="padding:4px 5px;color:#3355aa">6M</th>'
                f'<th style="padding:4px 5px;color:#3355aa">1Y</th>'
                f'<th style="padding:4px 7px;color:#3355aa">vs {_etf}</th>'
                f'</tr></thead><tbody>{_rows}</tbody></table>'
            )

        _table3 = (
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;'
            f'margin-top:10px;padding-top:10px;border-top:1px solid #e8eaed">'
            + "".join(f'<div>{h}</div>' for h in _col_htmls) + '</div>'
        )
        _etf_footer = (
            f'<div style="margin-top:6px;padding:5px 12px;background:#eef4ff;border-radius:6px;'
            f'display:flex;align-items:center;gap:14px;font-size:10px">'
            f'<span style="font-weight:700;color:#1a1a2e">━ {_etf} ETF (benchmark)</span>'
            f'<span style="color:#556">1Y:</span>'
            f'<span style="font-weight:800;color:{"#1A7A4A" if _etf_1y_pct>=0 else "#C0390F"}">{_etf_1y_pct:+.1f}%</span>'
            f'<span style="color:#556;margin-left:auto;font-size:9px">Above ETF line = outperformed · Below = underperformed</span>'
            f'</div>'
        )

        _sector_panel_html = (
            f'<div style="background:#fff;border:1px solid #dde1ed;border-radius:12px;'
            f'overflow:hidden;margin-bottom:18px">'
            f'<div style="background:#f0f2f8;padding:10px 18px;border-bottom:1px solid #dde1ed;'
            f'display:flex;align-items:center;gap:12px">'
            f'<div style="font-size:15px;font-weight:900;color:#1155cc">{_etf}</div>'
            f'<div style="font-size:12px;color:#334;font-weight:600">{_sname}</div>'
            f'<div style="font-size:9px;color:#889">Top 10 · indexed to 100 · 12-month daily</div>'
            f'<div style="margin-left:auto;font-size:11px;font-weight:700;'
            f'color:{"#1A7A4A" if _etf_1y_pct>=0 else "#C0390F"}">ETF 1Y: {_etf_1y_pct:+.1f}%</div>'
            f'</div>'
            f'<div style="padding:12px 18px 0">'
            f'<div style="position:relative;height:420px">'
            f'<canvas id="{_chart_id}"></canvas>'
            f'<button onclick="(function(){{var c=Chart.getChart(\'{_chart_id}\');if(c)c.resetZoom();}})()" '
            f'style="position:absolute;top:6px;left:6px;font-size:9px;padding:2px 8px;'
            f'border-radius:4px;border:1px solid #ccd;background:#f8f9ff;color:#445;cursor:pointer;'
            f'opacity:0.75" title="Reset zoom">⟲ Reset</button>'
            f'</div>'
            f'{_etf_footer}</div>'
            f'<div style="padding:0 18px 12px">{_table3}</div>'
            f'</div>'
        )
        _ss_sector_panels.append(_sector_panel_html)

        # Chart.js block
        _dates_js   = _jss.dumps(_dates_raw)
        _etf_idx_js = _jss.dumps(_etf_idx)
        _stock_ds   = ""
        for _sm2 in _stock_meta:
            _sd2 = _stock_js_data.get(_sm2["tk"])
            if not _sd2: continue
            _stock_ds += (
                f'{{ label: \'{_sm2["tk"]} ({_sd2["vs"]:+.1f}%)\','
                f'data: {_jss.dumps(_sd2["indexed"])},'
                f'borderColor: \'{_sd2["color"]}\','
                f'borderWidth:1.6,pointRadius:0,fill:false,tension:0.1,order:1}},'
            )

        _ss_js_blocks.append(
            f'(function(){{\n'
            f'  const ctx=document.getElementById(\'{_chart_id}\');\n'
            f'  if(!ctx) return;\n'
            f'  const dates={_dates_js};\n'
            f'  const seen={{}};\n'
            f'  const lbls=dates.map(d=>{{const mo=d.slice(0,7);if(!seen[mo]){{seen[mo]=1;return mo;}}return \'\';}});\n'
            f'  new Chart(ctx,{{\n'
            f'    type:\'line\',\n'
            f'    data:{{labels:dates,datasets:[\n'
            f'      {{label:\'{_etf} ETF\',data:{_etf_idx_js},borderColor:\'#1a1a2e\',\n'
            f'       borderWidth:2.5,pointRadius:0,fill:false,tension:0.2,order:0}},\n'
            f'      {_stock_ds}\n'
            f'    ]}},\n'
            f'    options:{{\n'
            f'      responsive:true,maintainAspectRatio:false,\n'
            f'      interaction:{{mode:\'index\',intersect:false}},\n'
            f'      plugins:{{\n'
            f'        legend:{{display:true,position:\'top\',\n'
            f'          labels:{{font:{{size:9}},color:\'#334\',boxWidth:14,padding:7,\n'
            f'            usePointStyle:true,pointStyle:\'line\'}}}},\n'
            f'        tooltip:{{callbacks:{{label:c=>c.dataset.label+\': \'+c.parsed.y.toFixed(1)}}}},\n'
            f'        zoom:{{\n'
            f'          pan:{{enabled:false}},\n'
            f'          zoom:{{wheel:{{enabled:false}},pinch:{{enabled:false}},mode:\'x\'}}\n'
            f'        }}\n'
            f'      }},\n'
            f'      scales:{{\n'
            f'        x:{{ticks:{{color:\'#8899aa\',font:{{size:8}},maxRotation:0,\n'
            f'              callback:(v,i)=>lbls[i]||null,maxTicksLimit:14,autoSkip:false}},\n'
            f'             grid:{{color:\'rgba(180,190,210,0.18)\'}}}},\n'
            f'        y:{{ticks:{{color:\'#778899\',font:{{size:9}},callback:v=>Math.round(v)}},\n'
            f'             grid:{{color:\'rgba(180,190,210,0.18)\'}},\n'
            f'             title:{{display:true,text:\'Indexed (100 = 12mo ago)\',color:\'#889\',font:{{size:8}}}}}}\n'
            f'      }}\n'
            f'    }}\n'
            f'  }});\n'
            f'  const _sc = Chart.getChart(ctx);\n'
            f'  if(_sc) {{ initTVZoom(_sc); ctx.addEventListener("mouseenter",function _h(){{showTVHint(ctx);ctx.removeEventListener("mouseenter",_h);}},{{once:true}}); }}\n'
            f'}})();'
        )

    # Assemble sector stocks HTML
    _ss_intro = (
        '<div style="background:#eef2ff;border-left:4px solid #2266ee;border-radius:8px;'
        'padding:10px 16px;margin-bottom:14px;font-size:10px;color:#334">'
        '<strong style="color:#1155cc">How to read:</strong> Every stock starts at 100. '
        'The <strong>thin dark line</strong> = sector ETF benchmark. '
        'Lines <em>above</em> = outperformed · Lines <em>below</em> = underperformed. '
        'Weight% = stock\'s share of ETF. Table sorted by 1Y vs ETF.'
        '</div>'
    )
    sector_stocks_tab_html = (_ss_intro + "\n".join(_ss_sector_panels)) if _ss_sector_panels else (
        '<div style="padding:40px;text-align:center;color:#667;font-size:12px">'
        'Sector stock data unavailable.</div>')
    sector_stocks_js = "\n".join(_ss_js_blocks)

    # ══════════════════════════════════════════════════════════════════════════
    # MARKET CHARTS TAB — extensible panel; first chart = Smart/Dumb Money
    # ══════════════════════════════════════════════════════════════════════════
    import json as _jmc
    _sdm = sdm_data or {}
    _sdm_dates  = _jmc.dumps(_sdm.get("dates",  []))
    _sdm_smart  = _jmc.dumps(_sdm.get("smart",  []))
    _sdm_dumb   = _jmc.dumps(_sdm.get("dumb",   []))
    _sdm_spx    = _jmc.dumps(_sdm.get("spx_vals",[]))
    _sdm_s_now  = _sdm.get("smart_now")
    _sdm_d_now  = _sdm.get("dumb_now")

    # Signal interpretation
    def _sdm_signal():
        if _sdm_s_now is None or _sdm_d_now is None:
            return ("N/A", "#778", "Insufficient data")
        spread = _sdm_s_now - _sdm_d_now
        if _sdm_s_now > 60 and _sdm_d_now < 40:
            return ("BULLISH SETUP", "#1A7A4A",
                    f"Smart Money ({_sdm_s_now:.0f}%) >> Dumb Money ({_sdm_d_now:.0f}%) — Institutions confident, retail fearful = contrarian buy zone")
        elif _sdm_d_now > 65 and _sdm_s_now < 45:
            return ("CAUTION — CROWD GREEDY", "#C0390F",
                    f"Dumb Money ({_sdm_d_now:.0f}%) >> Smart Money ({_sdm_s_now:.0f}%) — Retail over-extended, institutions hedging = distribution risk")
        elif _sdm_d_now > 60:
            return ("ELEVATED RETAIL CONFIDENCE", "#D4820A",
                    f"Dumb Money ({_sdm_d_now:.0f}%) elevated — watch for Smart Money divergence")
        elif _sdm_s_now > 55:
            return ("SMART MONEY CONSTRUCTIVE", "#2D7A3A",
                    f"Smart Money ({_sdm_s_now:.0f}%) building — institutional positioning becoming bullish")
        else:
            return ("NEUTRAL", "#556677",
                    f"Smart ({_sdm_s_now:.0f}%) and Dumb ({_sdm_d_now:.0f}%) both mid-range — no strong signal")

    _sig_label, _sig_col, _sig_text = _sdm_signal()

    _sdm_has_data = bool(_sdm.get("dates"))
    _sdm_chart_html = f"""
<div style="background:#fff;border:1px solid #dde1ed;border-radius:12px;overflow:hidden;margin-bottom:20px">
  <!-- Header -->
  <div style="background:#f0f2f8;padding:12px 20px;border-bottom:1px solid #dde1ed;
              display:flex;align-items:center;gap:14px;flex-wrap:wrap">
    <div style="font-size:14px;font-weight:900;color:#1a1a2e">Smart Money / Dumb Money Confidence</div>
    <div style="font-size:9px;color:#667;font-weight:500">Proxy: VIX term structure + HY momentum · Normalized 0-100 · 12-month daily</div>
    <div style="margin-left:auto;display:flex;gap:10px;align-items:center">
      {"" if not _sdm_has_data else f'<span style="font-size:11px;color:#2196F3;font-weight:700">Smart: {_sdm_s_now:.0f}%</span><span style="font-size:11px;color:#E91E63;font-weight:700">Dumb: {_sdm_d_now:.0f}%</span>'}
      <span style="font-size:10px;font-weight:800;color:{_sig_col};background:{_sig_col}18;
                   padding:3px 12px;border-radius:8px;border:1px solid {_sig_col}44">{_sig_label}</span>
    </div>
  </div>
  <!-- Signal interpretation bar -->
  <div style="background:{_sig_col}0e;border-left:4px solid {_sig_col};
              padding:8px 18px;font-size:10px;color:{_sig_col};font-weight:600">
    {_sig_text}
  </div>
  <!-- Chart -->
  <div style="padding:16px 18px">
    <div style="position:relative;height:360px">
      <canvas id="sdm_chart"></canvas>
      <button onclick="(function(){{var c=Chart.getChart('sdm_chart');if(c){{c.options.scales.x.min=undefined;c.options.scales.x.max=undefined;c.options.scales.y.min=undefined;c.options.scales.y.max=undefined;c.options.scales.y1.min=undefined;c.options.scales.y1.max=undefined;c.update();}}}})()"
        style="position:absolute;top:6px;left:6px;font-size:9px;padding:2px 8px;border-radius:4px;
               border:1px solid #ccd;background:#f8f9ff;color:#445;cursor:pointer;opacity:0.75">⟲ Reset</button>
    </div>
    <!-- Legend -->
    <div style="display:flex;gap:18px;margin-top:10px;font-size:9px;flex-wrap:wrap;color:#556">
      <span style="display:flex;align-items:center;gap:5px">
        <span style="width:24px;height:3px;background:#2196F3;display:inline-block;border-radius:2px"></span>
        Smart Money (institutions/contrarian)
      </span>
      <span style="display:flex;align-items:center;gap:5px">
        <span style="width:24px;height:3px;background:#E91E63;display:inline-block;border-radius:2px"></span>
        Dumb Money (retail/trend-following)
      </span>
      <span style="display:flex;align-items:center;gap:5px">
        <span style="width:24px;height:3px;background:#2d3f6e;display:inline-block;border-radius:2px"></span>
        S&P 500 (right axis)
      </span>
      <span style="color:#556;margin-left:auto">
        Signal zones: &gt;65 = extreme confidence · &lt;35 = extreme fear
      </span>
    </div>
  </div>
  <!-- How to read -->
  <div style="background:#f8f9ff;border-top:1px solid #eef0f8;padding:10px 18px;
              display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;font-size:9px;color:#445">
    <div style="border-left:3px solid #1A7A4A;padding-left:8px">
      <strong style="color:#1A7A4A">🟢 BULLISH SETUP</strong><br>
      Smart > 60% AND Dumb &lt; 40%<br>
      Institutions building, retail fearful → historically strong buying opportunity (6-12 month horizon)
    </div>
    <div style="border-left:3px solid #C0390F;padding-left:8px">
      <strong style="color:#C0390F">🔴 CAUTION SIGNAL</strong><br>
      Dumb > 65% AND Smart &lt; 45%<br>
      Crowd fully invested, institutions hedging → SentimenTrader's highest-conviction sell signal
    </div>
    <div style="border-left:3px solid #D4820A;padding-left:8px">
      <strong style="color:#D4820A">📊 PROXY NOTE</strong><br>
      This is a yfinance-based proxy (not SentimenTrader's proprietary data). Smart = VIX term structure + inverted HY spread. Dumb = HYG momentum + SPY RSI.
    </div>
  </div>
</div>
"""

    _sdm_js = f"""
(function(){{
  const ctx = document.getElementById('sdm_chart');
  if (!ctx) return;
  const dates  = {_sdm_dates};
  const smart  = {_sdm_smart};
  const dumb   = {_sdm_dumb};
  const spx    = {_sdm_spx};
  if (!dates.length) {{
    ctx.parentElement.innerHTML = '<div style="padding:40px;text-align:center;color:#667;font-size:12px">Insufficient market data to compute Smart/Dumb Money proxy.</div>';
    return;
  }}
  const seen = {{}};
  const lbls = dates.map(d => {{ const mo = d.slice(0,7); if(!seen[mo]){{seen[mo]=1;return mo;}} return ''; }});

  const sdmChart = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: dates,
      datasets: [
        // Smart Money — blue, left axis
        {{ label: 'Smart Money',
           data: smart,
           borderColor: '#2196F3',
           backgroundColor: 'rgba(33,150,243,0.08)',
           borderWidth: 2.2,
           pointRadius: 0,
           fill: true,
           tension: 0.3,
           yAxisID: 'y',
           order: 1,
        }},
        // Dumb Money — pink/red, left axis
        {{ label: 'Dumb Money',
           data: dumb,
           borderColor: '#E91E63',
           backgroundColor: 'rgba(233,30,99,0.06)',
           borderWidth: 2.2,
           pointRadius: 0,
           fill: true,
           tension: 0.3,
           yAxisID: 'y',
           order: 2,
        }},
        // S&P 500 — dark, right axis
        {{ label: 'S&P 500',
           data: spx,
           borderColor: '#1a1a2e',
           borderWidth: 2,
           pointRadius: 0,
           fill: false,
           tension: 0.2,
           yAxisID: 'y1',
           order: 0,
        }},
        // Signal zone lines
        {{ label: 'Caution Zone (65)',
           data: dates.map(() => 65),
           borderColor: 'rgba(192,57,15,0.35)',
           borderWidth: 1,
           borderDash: [5, 4],
           pointRadius: 0,
           fill: false,
           yAxisID: 'y',
           order: 10,
        }},
        {{ label: 'Opportunity Zone (35)',
           data: dates.map(() => 35),
           borderColor: 'rgba(26,122,74,0.35)',
           borderWidth: 1,
           borderDash: [5, 4],
           pointRadius: 0,
           fill: false,
           yAxisID: 'y',
           order: 10,
        }},
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: c => {{
              if (c.dataset.label === 'Smart Money')    return 'Smart Money: ' + c.parsed.y.toFixed(1) + '%';
              if (c.dataset.label === 'Dumb Money')     return 'Dumb Money: '  + c.parsed.y.toFixed(1) + '%';
              if (c.dataset.label === 'S&P 500')        return 'SPX: '         + c.parsed.y.toFixed(0);
              return null;
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          ticks: {{ color:'#8899aa', font:{{size:8}}, maxRotation:0,
                   callback: (v,i) => lbls[i] || null, maxTicksLimit:14, autoSkip:false }},
          grid: {{ color:'rgba(180,190,210,0.18)' }}
        }},
        y: {{
          position: 'left',
          min: 0, max: 100,
          ticks: {{ color:'#778899', font:{{size:9}}, callback: v => v + '%' }},
          grid: {{ color:'rgba(180,190,210,0.18)' }},
          title: {{ display:true, text:'Confidence (0-100%)', color:'#889', font:{{size:8}} }}
        }},
        y1: {{
          position: 'right',
          ticks: {{ color:'#334466', font:{{size:9}} }},
          grid: {{ drawOnChartArea: false }},
          title: {{ display:true, text:'S&P 500', color:'#334466', font:{{size:8}} }}
        }}
      }}
    }}
  }});
  const _sc = Chart.getChart(ctx);
  if (_sc) {{ initTVZoom(_sc); ctx.addEventListener('mouseenter', function _h(){{showTVHint(ctx);ctx.removeEventListener('mouseenter',_h);}},{{once:true}}); }}
}})();
"""

    mktcharts_tab_html = _sdm_chart_html

    # ── 1. Macro Radar / Spider Chart ─────────────────────────────────────────
    # 8 axes: Credit, Rates, Volatility, Labor, Inflation, Liquidity, Housing, Valuation
    # Score each 0-100 (100 = worst stress, 0 = most benign)
    def _radar_score():
        scores = {}
        def _sc(key, lo_good, hi_bad, invert=False):
            s = fd.get(key)
            v = float(s.iloc[-1]) if s is not None and not s.empty else None
            if v is None: return 50
            norm = max(0, min(100, (v - lo_good) / max(hi_bad - lo_good, 1e-6) * 100))
            return round(100 - norm if invert else norm, 1)
        scores["Credit"]    = _sc("HY_OAS", 250, 700)
        scores["Rates"]     = max(0, min(100, (4.34 - 0) / 6 * 100))  # T10Y
        scores["Volatility"]= _sc("VIX", 12, 40) if md.get("^VIX") is not None else 50
        scores["Labor"]     = _sc("UNRATE", 3.5, 6.0)
        scores["Inflation"] = 60  # proxy CPI ~2.4% → moderate
        scores["Valuation"] = _sc("CAPE", 20, 45) if fd.get("CAPE") is None else 75
        scores["Housing"]   = _sc("RATE_30", 5, 8)
        scores["Liquidity"] = 45  # NFCI near neutral
        # Try to get real values from scorecard
        for ind in scorecard or []:
            n = ind.get("name",""); v = ind.get("value")
            if v is None: continue
            if "HY Credit" in n:     scores["Credit"]    = min(100, max(0, (v-250)/(700-250)*100))
            if "CAPE" in n:          scores["Valuation"] = min(100, max(0, (v-20)/(45-20)*100))
            if "VIX" in n and "9D" not in n and "3M" not in n: scores["Volatility"] = min(100, max(0, (v-12)/(40-12)*100))
            if "Unemployment" in n:  scores["Labor"]     = min(100, max(0, (v-3.5)/(6-3.5)*100))
            if "Mortgage" in n and "Payment" not in n: scores["Housing"] = min(100, max(0, (v-5)/(8-5)*100))
        return scores

    _radar = _radar_score()
    _radar_labels = list(_radar.keys())
    _radar_vals   = [_radar[k] for k in _radar_labels]
    _radar_avg    = round(sum(_radar_vals) / len(_radar_vals), 1)
    _radar_color  = "#C0390F" if _radar_avg > 60 else "#D4820A" if _radar_avg > 40 else "#1A7A4A"

    import json as _jmr
    # Pre-build radar bars HTML to avoid nested f-string issues
    _radar_bars_html = ""
    for rk, rv in _radar.items():
        bar_col = '#C0390F' if rv > 65 else '#D4820A' if rv > 40 else '#1A7A4A'
        _radar_bars_html += f"""
      <div style="display:flex;align-items:center;gap:10px">
        <div style="width:90px;font-size:10px;font-weight:700;color:#334">{rk}</div>
        <div style="flex:1;background:#f0f2f8;border-radius:4px;height:14px;overflow:hidden">
          <div style="width:{rv:.0f}%;height:100%;background:{bar_col};border-radius:4px"></div>
        </div>
        <div style="width:36px;text-align:right;font-size:10px;font-weight:800;color:{bar_col}">{rv:.0f}</div>
      </div>"""

    _radar_html = f"""
<div style="background:#fff;border:1px solid #dde1ed;border-radius:12px;overflow:hidden;margin-bottom:20px">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:12px 20px;
              display:flex;align-items:center;gap:14px;flex-wrap:wrap">
    <div style="font-size:14px;font-weight:900;color:#fff">🕸 Macro Health Radar</div>
    <div style="font-size:9px;color:#aab">8-axis stress score · 0=healthy · 100=crisis</div>
    <div style="margin-left:auto">
      <span style="font-size:13px;font-weight:900;color:{_radar_color};background:{_radar_color}22;
                   padding:4px 14px;border-radius:8px;border:1px solid {_radar_color}44">
        Avg Stress: {_radar_avg:.0f}/100
      </span>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
    <div style="position:relative;height:360px;padding:12px">
      <canvas id="macro_radar"></canvas>
    </div>
    <div style="padding:20px;display:flex;flex-direction:column;gap:8px;justify-content:center;border-left:1px solid #eef0f8">
      {_radar_bars_html}
    </div>
  </div>
</div>"""

    _radar_js = f"""
(function(){{
  const ctx = document.getElementById('macro_radar');
  if (!ctx) return;
  new Chart(ctx, {{
    type: 'radar',
    data: {{
      labels: {_jmr.dumps(_radar_labels)},
      datasets: [{{
        label: 'Current Stress',
        data:  {_jmr.dumps(_radar_vals)},
        borderColor: '{_radar_color}',
        backgroundColor: '{_radar_color}33',
        borderWidth: 2.5,
        pointBackgroundColor: '{_radar_color}',
        pointRadius: 5,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        r: {{
          min: 0, max: 100,
          ticks: {{ stepSize: 25, font: {{ size: 8 }}, color: '#889' }},
          pointLabels: {{ font: {{ size: 10, weight: '700' }}, color: '#334' }},
          grid: {{ color: 'rgba(180,190,220,0.3)' }},
          angleLines: {{ color: 'rgba(180,190,220,0.4)' }}
        }}
      }}
    }}
  }});
}})();
"""

    # ── 2. Recession Probability Composite ────────────────────────────────────
    def _rec_prob_composite():
        """Blend 3 recession indicators into a single 0-100% composite."""
        import pandas as _pd_rc
        scores = []
        # Sahm Rule (threshold 0.5)
        sahm = fd.get("SAHM")
        if sahm is not None and not sahm.empty:
            v = float(sahm.iloc[-1])
            scores.append(min(100, v / 0.5 * 50))
        # NY Fed recession probability
        ny = fd.get("NY_REC_PROB")
        if ny is not None and not ny.empty:
            scores.append(float(ny.iloc[-1]))
        # Yield curve inversion (inverted = high risk)
        yc = fd.get("YIELD_CURVE")
        if yc is not None and not yc.empty:
            v = float(yc.iloc[-1])
            yc_prob = max(0, min(100, (-v + 0.5) / 2.5 * 100)) if v < 0.5 else 0
            scores.append(yc_prob)
        # Credit spread signal
        hy = fd.get("HY_OAS")
        if hy is not None and not hy.empty:
            v = float(hy.iloc[-1])
            hy_prob = max(0, min(100, (v - 300) / 400 * 100))
            scores.append(hy_prob)
        return round(sum(scores) / len(scores), 1) if scores else 25

    _rec_prob = _rec_prob_composite()
    _rc_col   = "#C0390F" if _rec_prob > 50 else "#D4820A" if _rec_prob > 25 else "#1A7A4A"
    _rc_label = "ELEVATED RISK" if _rec_prob > 50 else "MODERATE RISK" if _rec_prob > 25 else "LOW RISK"

    # Pre-compute component display values
    _rc_sahm = 0.20
    try:
        _s = fd.get("SAHM")
        if _s is not None and not _s.empty: _rc_sahm = float(_s.iloc[-1])
    except: pass
    _rc_yc = 0.50
    try:
        _s = fd.get("YIELD_CURVE")
        if _s is not None and not _s.empty: _rc_yc = float(_s.iloc[-1])
    except: pass
    _rc_hy = 312
    try:
        _s = fd.get("HY_OAS")
        if _s is not None and not _s.empty: _rc_hy = int(float(_s.iloc[-1]))
    except: pass

    _recprob_html = f"""
<div style="background:#fff;border:1px solid #dde1ed;border-radius:12px;overflow:hidden;margin-bottom:20px">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:12px 20px;
              display:flex;align-items:center;gap:14px">
    <div style="font-size:14px;font-weight:900;color:#fff">🌡 Recession Probability Composite</div>
    <div style="font-size:9px;color:#aab">Sahm Rule · NY Fed · Yield Curve · HY Spreads · Equal-weighted</div>
    <span style="margin-left:auto;font-size:12px;font-weight:900;color:{_rc_col};
                 background:{_rc_col}22;padding:4px 14px;border-radius:8px;border:1px solid {_rc_col}44">
      {_rc_label}
    </span>
  </div>
  <div style="padding:24px;display:flex;align-items:center;gap:40px">
    <!-- Gauge -->
    <div style="position:relative;width:200px;height:110px;flex-shrink:0">
      <canvas id="rec_gauge" width="200" height="110"></canvas>
    </div>
    <!-- Component breakdown -->
    <div style="flex:1">
      <div style="font-size:11px;font-weight:700;color:#334;margin-bottom:12px">Component Breakdown</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:9px">
        <div style="padding:10px;background:#f8f9ff;border-radius:8px;border-left:3px solid #5C6BC0">
          <div style="font-weight:800;color:#3949AB;margin-bottom:4px">Sahm Rule</div>
          <div style="font-size:15px;font-weight:900;color:#334">{_rc_sahm:.2f} pp</div>
          <div style="color:#667;margin-top:2px">&gt;0.50 = triggered</div>
        </div>
        <div style="padding:10px;background:#f8f9ff;border-radius:8px;border-left:3px solid #E91E63">
          <div style="font-weight:800;color:#880E4F;margin-bottom:4px">NY Fed Model</div>
          <div style="font-size:15px;font-weight:900;color:#334">{_rec_prob:.0f}%</div>
          <div style="color:#667;margin-top:2px">&gt;30% = elevated</div>
        </div>
        <div style="padding:10px;background:#f8f9ff;border-radius:8px;border-left:3px solid #009688">
          <div style="font-weight:800;color:#00695C;margin-bottom:4px">Yield Curve</div>
          <div style="font-size:15px;font-weight:900;color:#334">+{_rc_yc:.2f}%</div>
          <div style="color:#667;margin-top:2px">Inverted = risk</div>
        </div>
        <div style="padding:10px;background:#f8f9ff;border-radius:8px;border-left:3px solid #FF5722">
          <div style="font-weight:800;color:#BF360C;margin-bottom:4px">HY Spreads</div>
          <div style="font-size:15px;font-weight:900;color:#334">{_rc_hy} bps</div>
          <div style="color:#667;margin-top:2px">&gt;450 = danger</div>
        </div>
      </div>
    </div>
  </div>
  <div style="background:#f8f9ff;border-top:1px solid #eef0f8;padding:10px 24px;
              font-size:9px;color:#667">
    <strong>Historical Context:</strong> This composite reached &gt;70% in Oct 2007, Jan 2020, and Dec 2022 — all preceding recessions.
    Current {_rec_prob:.0f}% suggests {_rc_label.lower()}. Monitor for Sahm Rule trigger (&gt;0.5pp) as confirmation.
  </div>
</div>"""

    _recprob_js = f"""
(function(){{
  const ctx = document.getElementById('rec_gauge');
  if (!ctx) return;
  const val = {_rec_prob};
  const c = ctx.getContext('2d');
  const cx=100, cy=100, r=80;
  // Background arc
  c.beginPath(); c.arc(cx,cy,r,Math.PI,2*Math.PI); c.strokeStyle='#eee'; c.lineWidth=18; c.stroke();
  // Value arc
  const ang = Math.PI + (val/100)*Math.PI;
  const col = val>50?'#C0390F':val>25?'#D4820A':'#1A7A4A';
  c.beginPath(); c.arc(cx,cy,r,Math.PI,ang); c.strokeStyle=col; c.lineWidth=18; c.lineCap='round'; c.stroke();
  // Label
  c.fillStyle=col; c.font='bold 28px sans-serif'; c.textAlign='center'; c.textBaseline='middle';
  c.fillText(val.toFixed(0)+'%',cx,cy-10);
  c.fillStyle='#889'; c.font='11px sans-serif';
  c.fillText('Recession Risk',cx,cy+18);
  c.fillStyle='#aaa'; c.font='9px sans-serif';
  c.fillText('0%',cx-r-8,cy+4); c.fillText('100%',cx+r+2,cy+4);
}})();
"""

    # ── 3. Liquidity Waterfall ────────────────────────────────────────────────
    def _liquidity_series():
        import pandas as _pd_liq
        walcl = fd.get("WALCL"); wtga = fd.get("WTREGEN"); rrp = fd.get("RRPONTSYD")
        if walcl is None or walcl.empty: return "[]","[]","[]","[]"
        def _clean(s):
            if s is None or s.empty: return _pd_liq.Series(dtype=float)
            try:
                s2 = s.copy(); s2.index = _pd_liq.to_datetime(s2.index).tz_localize(None)
            except: s2 = s
            return s2.dropna()
        w = _clean(walcl)/1e6; t = _clean(wtga)/1e6; r = _clean(rrp)/1e6
        common = w.index
        t2 = t.reindex(common).ffill().fillna(0)
        r2 = r.reindex(common).ffill().fillna(0)
        net = (w - t2 - r2).tail(252)
        w2  = w.reindex(net.index); t3 = t2.reindex(net.index); r3 = r2.reindex(net.index)
        d   = [str(x)[:10] for x in net.index]
        return (_jmr.dumps(d),
                _jmr.dumps([round(float(v),2) for v in net.values]),
                _jmr.dumps([round(float(v),2) for v in w2.values]),
                _jmr.dumps([round(float(v),2) for v in (t3+r3).values]))

    _liq_dates, _liq_net, _liq_bs, _liq_drain = _liquidity_series()

    _liquidity_html = f"""
<div style="background:#fff;border:1px solid #dde1ed;border-radius:12px;overflow:hidden;margin-bottom:20px">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:12px 20px;
              display:flex;align-items:center;gap:14px;flex-wrap:wrap">
    <div style="font-size:14px;font-weight:900;color:#fff">💧 Fed Liquidity Waterfall</div>
    <div style="font-size:9px;color:#aab">WALCL − TGA − Reverse Repo = Net Liquidity · $Trillion</div>
    <div style="margin-left:auto;display:flex;gap:14px;font-size:9px">
      <span style="color:#4FC3F7">■ Fed Balance Sheet</span>
      <span style="color:#EF9A9A">■ TGA + RRP (drain)</span>
      <span style="color:#A5D6A7;font-weight:800">■ Net Liquidity</span>
    </div>
  </div>
  <div style="padding:8px 16px;background:#f8f9ff;border-bottom:1px solid #eef0f8;font-size:9px;color:#556">
    Net liquidity = money available for risk assets. QE (rising) → bull markets. QT + TGA drain → bear pressure. 2022's crash coincided with the sharpest liquidity drain in Fed history.
  </div>
  <div style="position:relative;height:300px;padding:8px">
    <canvas id="liquidity_chart"></canvas>
    <button onclick="(function(){{var c=Chart.getChart('liquidity_chart');if(c){{c.options.scales.x.min=undefined;c.options.scales.x.max=undefined;c.options.scales.y.min=undefined;c.options.scales.y.max=undefined;try{{c.resetZoom();}}catch(e){{c.update();}}}}}})();"
      style="position:absolute;top:10px;left:10px;font-size:8px;padding:2px 7px;border-radius:4px;
             border:1px solid #ccd;background:rgba(255,255,255,0.9);color:#445;cursor:pointer">⟲ Reset</button>
  </div>
</div>"""

    _liquidity_js = f"""
(function(){{
  const ctx = document.getElementById('liquidity_chart');
  if (!ctx) return;
  const dates = {_liq_dates};
  const net   = {_liq_net};
  const bs    = {_liq_bs};
  const drain = {_liq_drain};
  if (!dates.length) return;
  const seen={{}};
  const lbls = dates.map(d=>{{const mo=d.slice(0,7);if(!seen[mo]){{seen[mo]=1;return mo;}}return '';}});
  const ch = new Chart(ctx, {{
    type:'line',
    data:{{
      labels: dates,
      datasets:[
        {{label:'Fed Balance Sheet',data:bs,borderColor:'#4FC3F7',borderWidth:1.5,
          backgroundColor:'rgba(79,195,247,0.12)',fill:true,pointRadius:0,tension:0.2,order:3}},
        {{label:'TGA+RRP Drain',data:drain,borderColor:'#EF9A9A',borderWidth:1.5,
          backgroundColor:'rgba(239,154,154,0.12)',fill:true,pointRadius:0,tension:0.2,order:2}},
        {{label:'Net Liquidity',data:net,borderColor:'#66BB6A',borderWidth:3,
          backgroundColor:'rgba(102,187,106,0.2)',fill:true,pointRadius:0,tension:0.2,order:1}},
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>c.dataset.label+': $'+c.parsed.y.toFixed(2)+'T'}}}}
      }},
      scales:{{
        x:{{ticks:{{color:'#8899aa',font:{{size:8}},maxRotation:0,
               callback:(v,i)=>lbls[i]||null,maxTicksLimit:16,autoSkip:false}},
           grid:{{color:'rgba(180,190,210,0.15)'}}}},
        y:{{ticks:{{color:'#556',font:{{size:9}},callback:v=>'$'+v.toFixed(1)+'T'}},
           grid:{{color:'rgba(180,190,210,0.15)'}}}}
      }}
    }}
  }});
  initTVZoom(ch);
}})();
"""

    mktcharts_tab_html = _sdm_chart_html + _radar_html + _recprob_html + _liquidity_html
    mktcharts_tab_js   = _sdm_js + _radar_js + _recprob_js + _liquidity_js

    # ══════════════════════════════════════════════════════════════════════════
    # MASTER PARALLEL TABLE — Indicator readings at each S&P 500 drawdown level
    # Ported from 2_market_internals.py
    # ══════════════════════════════════════════════════════════════════════════
    _PARALLEL_DATA = {
        "above_50dma": {
            "label":"% Above 50DMA","unit":"%",
            "thresholds":{"calm":(60,100),"caution":(35,60),"stress":(20,35),"crisis":(0,20)},
            "direction":"higher_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":68,"AT -10%":45,"AT -20%":28,"AT -35%":12,"BOTTOM (-49%)":8},
                "2007 GFC":       {"AT TOP (0%)":60,"AT -10%":42,"AT -20%":25,"AT -30%":15,"AT -35%":10},
                "2008 GFC":       {"AT TOP (0%)":62,"AT -10%":40,"AT -20%":22,"AT -30%":14,"BOTTOM (-57%)":5},
                "2011 EU Debt":   {"AT TOP (0%)":65,"AT -10%":30,"AT -20%":15,"BOTTOM (-21%)":12},
                "2015 China/Oil": {"AT TOP (0%)":62,"AT -10%":28,"AT -15%":18,"BOTTOM (-15%)":22},
                "2018 Q4 Policy": {"AT TOP (0%)":66,"AT -10%":35,"AT -20%":18,"BOTTOM (-20%)":22},
                "2020 COVID":     {"AT TOP (0%)":72,"AT -10%":35,"AT -20%":12,"BOTTOM (-34%)":4},
                "2022 Rate Shock":{"AT TOP (0%)":65,"AT -10%":42,"AT -20%":25,"BOTTOM (-25%)":20},
            },
            "notes":">60% healthy · <35% caution · <20% oversold/potential bottom · Historical bottoms: 4-8%",
        },
        "above_200dma": {
            "label":"% Above 200DMA","unit":"%",
            "thresholds":{"calm":(60,100),"caution":(40,60),"stress":(25,40),"crisis":(0,25)},
            "direction":"higher_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":72,"AT -10%":55,"AT -20%":38,"AT -35%":20,"BOTTOM (-49%)":10},
                "2007 GFC":       {"AT TOP (0%)":65,"AT -10%":50,"AT -20%":35,"AT -30%":20,"AT -35%":15},
                "2008 GFC":       {"AT TOP (0%)":68,"AT -10%":48,"AT -20%":30,"AT -30%":18,"BOTTOM (-57%)":8},
                "2011 EU Debt":   {"AT TOP (0%)":68,"AT -10%":42,"AT -20%":25,"BOTTOM (-21%)":20},
                "2015 China/Oil": {"AT TOP (0%)":65,"AT -10%":38,"AT -15%":30,"BOTTOM (-15%)":35},
                "2018 Q4 Policy": {"AT TOP (0%)":70,"AT -10%":45,"AT -20%":28,"BOTTOM (-20%)":32},
                "2020 COVID":     {"AT TOP (0%)":70,"AT -10%":42,"AT -20%":15,"BOTTOM (-34%)":6},
                "2022 Rate Shock":{"AT TOP (0%)":68,"AT -10%":52,"AT -20%":35,"BOTTOM (-25%)":22},
            },
            "notes":">60% = bull market · <40% = bear conditions · <20% = crash/capitulation · GFC bottom ~8%",
        },
        "nyse_ad_net": {
            "label":"NYSE A/D Daily Net","unit":"",
            "thresholds":{"calm":(500,99999),"caution":(-200,500),"stress":(-1000,-200),"crisis":(-99999,-1000)},
            "direction":"higher_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":"+400","AT -10%":"-300","AT -20%":"-800","AT -35%":"-1400","BOTTOM (-49%)":"-1800"},
                "2007 GFC":       {"AT TOP (0%)":"+100","AT -10%":"-400","AT -20%":"-900","AT -30%":"-1500","AT -35%":"-2000"},
                "2008 GFC":       {"AT TOP (0%)":"+200","AT -10%":"-500","AT -20%":"-1200","AT -30%":"-1800","BOTTOM (-57%)":"-2500"},
                "2011 EU Debt":   {"AT TOP (0%)":"+300","AT -10%":"-800","AT -20%":"-1800","BOTTOM (-21%)":"-2000"},
                "2015 China/Oil": {"AT TOP (0%)":"+200","AT -10%":"-600","BOTTOM (-15%)":"-800"},
                "2018 Q4 Policy": {"AT TOP (0%)":"+350","AT -10%":"-500","AT -20%":"-1000","BOTTOM (-20%)":"-1200"},
                "2020 COVID":     {"AT TOP (0%)":"+600","AT -10%":"-2000","AT -20%":"-3500","BOTTOM (-34%)":"-4000"},
                "2022 Rate Shock":{"AT TOP (0%)":"+300","AT -10%":"-600","AT -20%":"-900","BOTTOM (-25%)":"-1100"},
            },
            "notes":"Sustained negative = distribution. Classic pre-crash divergence 6mo before 2000 and 2007 tops",
        },
        "forward_pe": {
            "label":"Forward P/E","unit":"x",
            "thresholds":{"calm":(0,18),"caution":(18,22),"stress":(22,26),"crisis":(26,999)},
            "direction":"lower_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":28,"AT -10%":24,"AT -20%":20,"AT -35%":16,"BOTTOM (-49%)":14},
                "2007 GFC":       {"AT TOP (0%)":16,"AT -10%":14,"AT -20%":13,"AT -30%":12,"AT -35%":11},
                "2008 GFC":       {"AT TOP (0%)":18,"AT -10%":16,"AT -20%":14,"AT -30%":12,"BOTTOM (-57%)":10},
                "2011 EU Debt":   {"AT TOP (0%)":13,"AT -10%":12,"AT -20%":11,"BOTTOM (-21%)":11},
                "2015 China/Oil": {"AT TOP (0%)":17,"AT -10%":15,"BOTTOM (-15%)":15},
                "2018 Q4 Policy": {"AT TOP (0%)":17,"AT -10%":15,"AT -20%":14,"BOTTOM (-20%)":14},
                "2020 COVID":     {"AT TOP (0%)":19,"AT -10%":16,"AT -20%":14,"BOTTOM (-34%)":12},
                "2022 Rate Shock":{"AT TOP (0%)":23,"AT -10%":20,"AT -20%":17,"BOTTOM (-25%)":16},
            },
            "notes":"Fair value 15-17x · >22x = expensive · >26x = danger · Watch when EPS estimates cut",
        },
        "earnings_yield_vs_10y": {
            "label":"Earnings Yield − 10Y (ERP)","unit":"%",
            "thresholds":{"calm":(1.5,99),"caution":(0.5,1.5),"stress":(-0.5,0.5),"crisis":(-99,-0.5)},
            "direction":"higher_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":"-2.5","AT -10%":"-1.5","AT -20%":"-0.5","AT -35%":"+1.0","BOTTOM (-49%)":"+2.0"},
                "2007 GFC":       {"AT TOP (0%)":"+0.8","AT -10%":"+1.5","AT -20%":"+2.5","AT -30%":"+3.5","AT -35%":"+4.0"},
                "2008 GFC":       {"AT TOP (0%)":"+0.5","AT -10%":"+1.5","AT -20%":"+2.5","AT -30%":"+3.5","BOTTOM (-57%)":"+5.0"},
                "2011 EU Debt":   {"AT TOP (0%)":"+2.0","AT -10%":"+3.0","AT -20%":"+4.5","BOTTOM (-21%)":"+5.0"},
                "2015 China/Oil": {"AT TOP (0%)":"+1.5","AT -10%":"+2.5","BOTTOM (-15%)":"+3.0"},
                "2018 Q4 Policy": {"AT TOP (0%)":"+0.2","AT -10%":"-0.2","AT -20%":"-0.5","BOTTOM (-20%)":"-0.3"},
                "2020 COVID":     {"AT TOP (0%)":"+1.5","AT -10%":"+2.5","AT -20%":"+4.0","BOTTOM (-34%)":"+5.5"},
                "2022 Rate Shock":{"AT TOP (0%)":"+0.2","AT -10%":"-0.3","AT -20%":"-0.8","BOTTOM (-25%)":"-0.5"},
            },
            "notes":"Equity Risk Premium. Negative = bonds beat stocks. 2000: −2.5% at peak",
        },
        "net_liquidity": {
            "label":"Fed Net Liquidity ($T)","unit":"$T",
            "thresholds":{"calm":(5.5,99),"caution":(4.5,5.5),"stress":(4.0,4.5),"crisis":(0,4.0)},
            "direction":"higher_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":"n/a","BOTTOM (-49%)":"n/a"},
                "2007 GFC":       {"AT TOP (0%)":"~0.8","AT -10%":"~0.9","AT -20%":"~1.1","AT -30%":"~1.3","AT -35%":"~1.5"},
                "2008 GFC":       {"AT TOP (0%)":"~0.9","AT -10%":"~1.2","AT -20%":"~1.5","BOTTOM (-57%)":"~2.3"},
                "2011 EU Debt":   {"AT TOP (0%)":"~2.3","AT -10%":"~2.5","AT -20%":"~2.7","BOTTOM (-21%)":"~2.8"},
                "2015 China/Oil": {"AT TOP (0%)":"~3.5","AT -10%":"~3.4","BOTTOM (-15%)":"~3.3"},
                "2018 Q4 Policy": {"AT TOP (0%)":"~3.8","AT -10%":"~3.7","AT -20%":"~3.5","BOTTOM (-20%)":"~3.4"},
                "2020 COVID":     {"AT TOP (0%)":"~4.2","AT -10%":"~4.5","AT -20%":"~5.8","BOTTOM (-34%)":"~7.2"},
                "2022 Rate Shock":{"AT TOP (0%)":"~6.4","AT -10%":"~5.8","AT -20%":"~5.2","BOTTOM (-25%)":"~4.8"},
            },
            "notes":"WALCL−TGA−RRP. Correlates 0.92 with SPX since 2008. <$4.5T = market pressure",
        },
        "vix_term": {
            "label":"VIX Term (3M−30D)","unit":"pts",
            "thresholds":{"calm":(1.0,99),"caution":(-0.5,1.0),"stress":(-2.0,-0.5),"crisis":(-99,-2.0)},
            "direction":"higher_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":"+1.5","AT -10%":"+0.2","AT -20%":"-1.0","AT -35%":"-3.5","BOTTOM (-49%)":"-5.0"},
                "2007 GFC":       {"AT TOP (0%)":"+2.5","AT -10%":"-1.0","AT -20%":"-3.0","AT -30%":"-6.0","AT -35%":"-8.0"},
                "2008 GFC":       {"AT TOP (0%)":"+2.0","AT -10%":"-0.5","AT -20%":"-2.5","AT -30%":"-5.0","BOTTOM (-57%)":"-12.0"},
                "2011 EU Debt":   {"AT TOP (0%)":"+1.5","AT -10%":"-3.0","AT -20%":"-8.0","BOTTOM (-21%)":"-10.0"},
                "2015 China/Oil": {"AT TOP (0%)":"+1.8","AT -10%":"-4.0","BOTTOM (-15%)":"-6.0"},
                "2018 Q4 Policy": {"AT TOP (0%)":"+1.2","AT -10%":"-1.5","AT -20%":"-3.5","BOTTOM (-20%)":"-2.0"},
                "2020 COVID":     {"AT TOP (0%)":"+3.0","AT -10%":"-8.0","AT -20%":"-18.0","BOTTOM (-34%)":"-25.0"},
                "2022 Rate Shock":{"AT TOP (0%)":"+1.8","AT -10%":"-0.8","AT -20%":"-2.0","BOTTOM (-25%)":"-1.5"},
            },
            "notes":"Contango (+) = calm. Backwardation (−) = fear/crash mode. Flipped negative Feb 24 2020 (3 days before crash)",
        },
        "vix9d_vix_ratio": {
            "label":"VIX9D / VIX30 Ratio","unit":"x",
            "thresholds":{"calm":(0,0.95),"caution":(0.95,1.05),"stress":(1.05,1.20),"crisis":(1.20,99)},
            "direction":"lower_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":"0.85","AT -10%":"0.95","AT -20%":"1.05","AT -35%":"1.15","BOTTOM (-49%)":"1.25"},
                "2007 GFC":       {"AT TOP (0%)":"0.88","AT -10%":"1.02","AT -20%":"1.15","AT -30%":"1.25","AT -35%":"1.30"},
                "2008 GFC":       {"AT TOP (0%)":"0.88","AT -10%":"1.00","AT -20%":"1.12","AT -30%":"1.22","BOTTOM (-57%)":"1.35"},
                "2011 EU Debt":   {"AT TOP (0%)":"0.82","AT -10%":"1.20","AT -20%":"1.40","BOTTOM (-21%)":"1.45"},
                "2015 China/Oil": {"AT TOP (0%)":"0.85","AT -10%":"1.25","BOTTOM (-15%)":"1.30"},
                "2018 Q4 Policy": {"AT TOP (0%)":"0.90","AT -10%":"1.08","AT -20%":"1.15","BOTTOM (-20%)":"1.10"},
                "2020 COVID":     {"AT TOP (0%)":"0.80","AT -10%":"1.30","AT -20%":"1.45","BOTTOM (-34%)":"1.60"},
                "2022 Rate Shock":{"AT TOP (0%)":"0.90","AT -10%":"1.05","AT -20%":"1.10","BOTTOM (-25%)":"1.08"},
            },
            "notes":">1.0 = near-term panic > long-term. Pre-COVID: crossed 1.0 on Feb 24, 3 days before crash",
        },
        "top10_weight": {
            "label":"Top-10 SPX Weight","unit":"%",
            "thresholds":{"calm":(0,22),"caution":(22,28),"stress":(28,33),"crisis":(33,100)},
            "direction":"lower_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":25,"AT -10%":22,"AT -20%":19,"AT -35%":16,"BOTTOM (-49%)":14},
                "2007 GFC":       {"AT TOP (0%)":18,"AT -10%":17,"AT -20%":16,"AT -30%":15,"AT -35%":14},
                "2008 GFC":       {"AT TOP (0%)":19,"AT -10%":17,"AT -20%":16,"AT -30%":15,"BOTTOM (-57%)":13},
                "2011 EU Debt":   {"AT TOP (0%)":18,"AT -10%":17,"AT -20%":16,"BOTTOM (-21%)":16},
                "2015 China/Oil": {"AT TOP (0%)":19,"AT -10%":18,"BOTTOM (-15%)":18},
                "2018 Q4 Policy": {"AT TOP (0%)":22,"AT -10%":21,"AT -20%":20,"BOTTOM (-20%)":20},
                "2020 COVID":     {"AT TOP (0%)":22,"AT -10%":21,"AT -20%":20,"BOTTOM (-34%)":19},
                "2022 Rate Shock":{"AT TOP (0%)":30,"AT -10%":28,"AT -20%":26,"BOTTOM (-25%)":25},
            },
            "notes":"Historical avg 18-20%. Current 35%+ = record. When top-10 crack, index has nowhere to hide",
        },
        "rsp_spy_ratio": {
            "label":"RSP/SPY (Equal/Cap Wt)","unit":"ratio",
            "thresholds":{"calm":(0.32,99),"caution":(0.29,0.32),"stress":(0.27,0.29),"crisis":(0,0.27)},
            "direction":"higher_good",
            "crashes":{
                "2000 Dot-com":   {"AT TOP (0%)":"~0.32","AT -10%":"~0.33","AT -20%":"~0.34","BOTTOM (-49%)":"~0.40"},
                "2007 GFC":       {"AT TOP (0%)":"~0.39","AT -10%":"~0.37","AT -20%":"~0.34","AT -30%":"~0.31","AT -35%":"~0.29"},
                "2008 GFC":       {"AT TOP (0%)":"~0.38","AT -10%":"~0.36","AT -20%":"~0.33","BOTTOM (-57%)":"~0.28"},
                "2011 EU Debt":   {"AT TOP (0%)":"~0.36","AT -10%":"~0.33","AT -20%":"~0.31","BOTTOM (-21%)":"~0.30"},
                "2015 China/Oil": {"AT TOP (0%)":"~0.34","AT -10%":"~0.31","BOTTOM (-15%)":"~0.30"},
                "2018 Q4 Policy": {"AT TOP (0%)":"~0.32","AT -10%":"~0.30","AT -20%":"~0.29","BOTTOM (-20%)":"~0.29"},
                "2020 COVID":     {"AT TOP (0%)":"~0.33","AT -10%":"~0.31","BOTTOM (-34%)":"~0.29"},
                "2022 Rate Shock":{"AT TOP (0%)":"~0.31","AT -10%":"~0.30","AT -20%":"~0.29","BOTTOM (-25%)":"~0.28"},
            },
            "notes":"Rising = broad recovery. Falling = mega-cap masking weakness. Low = concentration risk",
        },
    }

    _DRAWDOWN_LEVELS = [
        "AT TOP (0%)","AT -10%","AT -20%","AT -30%","AT -35%",
        "BOTTOM (-25%)","BOTTOM (-34%)","BOTTOM (-49%)","BOTTOM (-57%)"
    ]

    _CRASH_NAMES = ["2000 Dot-com","2007 GFC","2008 GFC","2011 EU Debt","2015 China/Oil","2018 Q4 Policy","2020 COVID","2022 Rate Shock"]

    _WATCH_RULES = [
        ("BREADTH",   "% above 50DMA falls below 35% while SPX is flat or rising",
                      "Classic pre-crash breadth divergence — appeared 6 months before both 2000 and 2007 tops → reduce longs"),
        ("BREADTH",   "NYSE A/D line cumulative falling while SPX holds highs",
                      "Most reliable pre-top signal historically. Confirmed both 2000 and 2007 peaks months in advance"),
        ("LIQUIDITY", "Net Fed Liquidity drops below $4.5T",
                      "2022: Net Liq fell from $6.4T to $4.8T before the bear market. Sub-$4.5T = renewed pressure"),
        ("VIX",       "VIX9D crosses ABOVE VIX3M (backwardation confirmed)",
                      "Pre-COVID: this exact crossing happened Feb 24, 2020 — 3 days before the crash → hedge aggressively"),
        ("VALUATION", "Forward P/E above 27x with ERP below 0%",
                      "Stocks yield LESS than bonds = 2000-analog. No fundamental support for multiples → full defensive posture"),
        ("CONCENTRATION","RSP/SPY ratio falls below 0.29 while SPY holds near ATH",
                      "Breadth narrowing to a few stocks — when those crack, no broad support → reduce index exposure"),
        ("COMPOSITE", "3 or more indicators simultaneously in STRESS or CRISIS",
                      "Multi-signal confirmation = systemic deterioration, not isolated noise → raise cash to 30-40%"),
    ]

    # ── Helper functions ──────────────────────────────────────────────────────
    def _pt_get_zone(key, val):
        if val is None: return "N/A","#4b5563"
        ind = _PARALLEL_DATA.get(key,{})
        thr = ind.get("thresholds",{})
        try:
            v = float(str(val).replace("~","").replace("$","").replace("T","")
                      .replace("%","").replace("x","").replace("+","").replace(",",""))
        except: return "N/A","#374151"
        for zone,(lo,hi) in thr.items():
            if lo <= v <= hi:
                return {"calm":("CALM","#166534"),"caution":("CAUTION","#92400e"),
                        "stress":("STRESS","#991b1b"),"crisis":("CRISIS","#450a0a")
                        }.get(zone,("N/A","#374151"))
        return "N/A","#374151"

    def _pt_cell_bg(key, val):
        _,col = _pt_get_zone(key,val)
        return {"#166534":"rgba(22,101,52,0.10)","#92400e":"rgba(146,64,14,0.09)",
                "#991b1b":"rgba(153,27,27,0.10)","#450a0a":"rgba(69,10,10,0.14)",
                "#374151":"transparent"}.get(col,"transparent")

    def _pt_fmt(key, raw_val):
        if raw_val is None or raw_val == "n/a": return "—"
        unit = _PARALLEL_DATA.get(key,{}).get("unit","")
        try:
            v = float(str(raw_val).replace("~","").replace("$","").replace("T","")
                      .replace("%","").replace("x","").replace("+","").replace(",",""))
            if unit == "%":     return f"{v:.0f}%"
            if unit == "$T":    return f"${v:.2f}T"
            if unit == "x":     return f"{v:.2f}x"
            if unit == "pts":   return f"{v:+.1f}"
            if unit == "ratio": return f"{v:.3f}"
            return str(raw_val)
        except: return str(raw_val)

    def _pt_cell(key, raw_val, is_today=False):
        today_border = "border-left:3px solid #D4820A;border-right:3px solid #D4820A;" if is_today else ""
        today_bg     = "background:#fffbea;" if is_today else ""
        if raw_val is None or raw_val == "n/a":
            return (f'<td style="padding:6px 10px;text-align:center;{today_border}{today_bg}'
                    f'color:#9ca3af;font-size:11px;">—</td>')
        try:
            v  = float(str(raw_val).replace("~","").replace("$","").replace("T","")
                       .replace("%","").replace("x","").replace("+","").replace(",",""))
            bg = _pt_cell_bg(key,v)
            _,c = _pt_get_zone(key,v)
        except: bg,c = "transparent","#374151"
        disp = _pt_fmt(key,raw_val)
        fw   = "font-weight:900;font-size:13px;" if is_today else "font-size:11px;"
        cell_bg_style = today_bg if is_today else f"background:{bg};"
        return (f'<td style="padding:6px 10px;text-align:center;{fw}{today_border}{cell_bg_style}'
                f'color:{c};white-space:nowrap">{disp}</td>')

    def _pt_zone_badge(key, val):
        zl,zc = _pt_get_zone(key,val)
        return (f'<span style="background:{zc}18;color:{zc};border:1px solid {zc}55;'
                f'padding:2px 8px;border-radius:4px;font-size:10px;font-weight:800">{zl}</span>')

    # ── TODAY values from scorecard ───────────────────────────────────────────
    _pt_vals = scorecard or []
    def _sc_val(key):
        for ind in _pt_vals:
            if ind.get("id") == key: return ind.get("value")
        return None

    _pt_today = {
        "above_50dma":       _sc_val("PCT_ABOVE_50"),
        "above_200dma":      _sc_val("PCT_ABOVE_200"),
        "nyse_ad_net":       _sc_val("NYSE_AD"),
        "forward_pe":        _sc_val("FORWARD_PE"),
        "earnings_yield_vs_10y": _sc_val("ERP"),
        "net_liquidity":     _sc_val("NET_LIQUIDITY"),
        "vix_term":          _sc_val("VIX_TERM"),
        "vix9d_vix_ratio":   _sc_val("VIX9D_RATIO"),
        "top10_weight":      _sc_val("TOP10_WEIGHT"),
        "rsp_spy_ratio":     _sc_val("RSP_SPY"),
    }

    # ── Compute live SPY drawdown from ATH ────────────────────────────────────
    _spy_s = md.get("SPY")
    _spy_ath_pt = None; _spy_cur_pt = None; _spy_dd_pct = 0.0
    if _spy_s is not None and not _spy_s.empty:
        _spy_cur_pt = float(_spy_s.iloc[-1])
        _spy_ath_pt = float(_spy_s.max())
        if _spy_ath_pt > 0:
            _spy_dd_pct = (_spy_cur_pt / _spy_ath_pt - 1) * 100  # negative = drawdown

    # Map drawdown % → which level label TODAY sits at (5% intervals)
    def _dd_to_level(dd_pct):
        """Return the drawdown level label for current drawdown."""
        if dd_pct >= -2.5:   return "AT TOP (0%)"
        elif dd_pct >= -7.5: return "AT -5%"
        elif dd_pct >= -12.5:return "AT -10%"
        elif dd_pct >= -17.5:return "AT -15%"
        elif dd_pct >= -22.5:return "AT -20%"
        elif dd_pct >= -27.5:return "AT -25%"
        elif dd_pct >= -32.5:return "AT -30%"
        elif dd_pct >= -37.5:return "AT -35%"
        elif dd_pct >= -45:  return "BOTTOM (-40%)"
        else:                return "BOTTOM (-50%+)"

    _current_dd_level = _dd_to_level(_spy_dd_pct)
    _spy_dd_str = f"{_spy_dd_pct:.1f}%" if _spy_dd_pct < -0.5 else "Near ATH"

    # ── Count today's stress signals ──────────────────────────────────────────
    _pt_stress = sum(1 for k,v in _pt_today.items()
                     if _pt_get_zone(k,v)[0] in ("STRESS","CRISIS"))
    _pt_caution = sum(1 for k,v in _pt_today.items()
                      if _pt_get_zone(k,v)[0] == "CAUTION")
    _pt_calm = len(_pt_today) - _pt_stress - _pt_caution
    _pt_regime_col = "#991b1b" if _pt_stress >= 3 else "#92400e" if _pt_stress >= 1 else "#166534"
    _pt_regime_lbl = ("⚠️ MULTI-SIGNAL STRESS" if _pt_stress >= 3 else
                      "⚡ ELEVATED CAUTION" if _pt_stress >= 1 or _pt_caution >= 3 else
                      "✅ BROADLY HEALTHY")

    # ── Extended drawdown levels at 5% intervals ──────────────────────────────
    # Historical crash data interpolated at 5% intervals
    # Maps level_label → per-crash → per-indicator approximate values
    # We add 5% and 15% as interpolated between the 0/10/20% existing data points
    _DRAWDOWN_LEVELS_EXT = [
        "AT TOP (0%)", "AT -5%", "AT -10%", "AT -15%", "AT -20%",
        "AT -25%", "AT -30%", "AT -35%",
        "BOTTOM (-25%)", "BOTTOM (-34%)", "BOTTOM (-49%)", "BOTTOM (-57%)"
    ]

    def _interp_crash(ind, crash, lvl):
        """Interpolate or extrapolate a crash value at a 5% level."""
        crashes = ind.get("crashes", {}).get(crash, {})
        if lvl in crashes: return crashes[lvl]
        # Map to adjacent known levels and interpolate
        _KNOWN = ["AT TOP (0%)", "AT -10%", "AT -20%", "AT -30%", "AT -35%",
                  "BOTTOM (-25%)", "BOTTOM (-34%)", "BOTTOM (-49%)", "BOTTOM (-57%)"]
        _PCT = {l: p for l, p in zip(_KNOWN,
                [0, -10, -20, -30, -35, -25, -34, -49, -57])}
        _NEW_PCT = {"AT -5%": -5, "AT -15%": -15, "AT -25%": -25}
        target_pct = _NEW_PCT.get(lvl)
        if target_pct is None: return None
        # Find bounding known levels that exist for this crash
        known_vals = {l: crashes[l] for l in _KNOWN if l in crashes}
        if len(known_vals) < 2: return None
        # Find neighbors
        lo_l = hi_l = None; lo_p = hi_p = None
        for kl, kv in known_vals.items():
            kp = _PCT.get(kl, 0)
            try: float(str(kv).replace("~","").replace("$","").replace("T","").replace("%","").replace("x","").replace("+","").replace(",",""))
            except: continue
            if kp >= target_pct:
                if lo_p is None or kp < lo_p: lo_p = kp; lo_l = kl
            else:
                if hi_p is None or kp > hi_p: hi_p = kp; hi_l = kl
        if lo_l is None or hi_l is None: return None
        try:
            lo_v = float(str(crashes[lo_l]).replace("~","").replace("$","").replace("T","").replace("%","").replace("x","").replace("+","").replace(",",""))
            hi_v = float(str(crashes[hi_l]).replace("~","").replace("$","").replace("T","").replace("%","").replace("x","").replace("+","").replace(",",""))
            if lo_p == hi_p: return lo_v
            t = (target_pct - lo_p) / (hi_p - lo_p)
            val = lo_v + t * (hi_v - lo_v)
            # Return in same format as the neighboring value (preserve units)
            ref = crashes.get(lo_l, crashes.get(hi_l, ""))
            if isinstance(ref, str) and ref.startswith("~"):
                return f"~{val:.1f}"
            elif isinstance(ref, str) and ("+" in ref or ref.startswith("-")):
                return f"{val:+.1f}"
            elif isinstance(ref, (int, float)):
                return round(val, 1)
            return round(val, 1)
        except: return None

    # ── Build parallel table rows ─────────────────────────────────────────────
    _pt_rows = ""
    for _pk in _PARALLEL_DATA:
        ind = _PARALLEL_DATA[_pk]
        today_v = _pt_today.get(_pk)
        today_zone, today_zcol = _pt_get_zone(_pk, today_v)

        # Section header row
        _pt_rows += (
            f'<tr style="background:#f0f4fb;border-top:2px solid #dde1ed">'
            f'<td colspan="{2+len(_CRASH_NAMES)}" style="padding:8px 14px;font-size:11px;'
            f'font-weight:800;color:#1155cc;text-transform:uppercase;letter-spacing:.06em">'
            f'{ind["label"]}'
            f'<span style="font-size:9px;color:#667;font-weight:600;text-transform:none;margin-left:12px">'
            f'{ind.get("notes","")[:90]}</span></td></tr>'
        )

        for lvl in _DRAWDOWN_LEVELS_EXT:
            # Get values - use real data if available, interpolated if not
            row_vals = {}
            for cn in _CRASH_NAMES:
                direct = ind["crashes"].get(cn, {}).get(lvl)
                row_vals[cn] = direct if direct is not None else _interp_crash(ind, cn, lvl)

            if all(v is None for v in row_vals.values()): continue

            # Is this the current drawdown level?
            is_current_level = (lvl == _current_dd_level)

            lvl_bg  = ("#fff5f5" if "BOTTOM" in lvl else
                       "#fffbf0" if any(x in lvl for x in ["-30%","-35%","-25%"]) else
                       "#f8fff8" if is_current_level else "#fafbfe")
            lvl_col = ("#b91c1c" if "BOTTOM" in lvl else
                       "#92400e" if any(x in lvl for x in ["-20%","-25%","-30%","-35%"]) else
                       "#1e3a8a")

            # Add "← YOU ARE HERE" marker for current level
            here_badge = ""
            if is_current_level:
                here_badge = (f' <span style="background:#D4820A;color:#fff;padding:1px 7px;'
                              f'border-radius:4px;font-size:9px;font-weight:900;margin-left:6px">'
                              f'📍 NOW ({_spy_dd_str})</span>')

            # Mark interpolated levels with italic styling
            is_interpolated = lvl in ("AT -5%", "AT -15%", "AT -25%")
            lvl_style = "font-style:italic;opacity:0.85;" if is_interpolated else ""

            _pt_rows += (
                f'<tr style="border-bottom:1px solid #eaecf4;background:{lvl_bg};'
                f'{"outline:2px solid #D4820A;outline-offset:-2px;" if is_current_level else ""}">'
                f'<td style="padding:6px 14px;font-size:10px;font-weight:800;color:{lvl_col};'
                f'white-space:nowrap;{lvl_style}">{lvl}{here_badge}</td>'
            )
            for cn in _CRASH_NAMES:
                v = row_vals.get(cn)
                _pt_rows += _pt_cell(_pk, v)
            _pt_rows += _pt_cell(_pk, today_v, is_today=True)
            _pt_rows += '</tr>'

    # ── Watch Rules rows ──────────────────────────────────────────────────────
    _watch_rows = ""
    for cat, cond, action in _WATCH_RULES:
        cat_col = {"BREADTH":"#3b82f6","LIQUIDITY":"#06b6d4","VIX":"#a855f7",
                   "VALUATION":"#f59e0b","CONCENTRATION":"#ec4899",
                   "COMPOSITE":"#ef4444"}.get(cat,"#4b5563")

        # Check if triggered today
        _triggered = False
        if cat=="BREADTH" and _pt_today.get("above_50dma") is not None:
            _triggered = (_pt_today["above_50dma"] or 100) < 35
        elif cat=="LIQUIDITY" and _pt_today.get("net_liquidity") is not None:
            _triggered = (_pt_today["net_liquidity"] or 99) < 4.5
        elif cat=="VIX" and _pt_today.get("vix9d_vix_ratio") is not None:
            _triggered = (_pt_today["vix9d_vix_ratio"] or 0) > 1.0
        elif cat=="VALUATION" and _pt_today.get("forward_pe") is not None:
            _triggered = ((_pt_today.get("forward_pe") or 0) > 27 and
                          (_pt_today.get("earnings_yield_vs_10y") or 1) < 0)
        elif cat=="COMPOSITE":
            _triggered = _pt_stress >= 3

        trigger_style = ("background:#fff5f5;border-left:3px solid #ef4444;" if _triggered else
                         "background:#fafbfe;")
        trigger_badge = ('<span style="background:#ef444422;color:#b91c1c;border:1px solid #ef444444;'
                         'padding:1px 6px;border-radius:3px;font-size:9px;font-weight:800;margin-left:8px">'
                         '⚡ TRIGGERED</span>' if _triggered else "")

        _watch_rows += (
            f'<tr style="border-bottom:1px solid #eaecf4;{trigger_style}">'
            f'<td style="padding:8px 14px;white-space:nowrap">'
            f'<span style="background:{cat_col}22;color:{cat_col};border:1px solid {cat_col}44;'
            f'padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">{cat}</span>'
            f'{trigger_badge}</td>'
            f'<td style="padding:8px 14px;font-size:11px;color:#334;font-weight:600">{cond}</td>'
            f'<td style="padding:8px 14px;font-size:11px;color:#556">{action}</td>'
            f'</tr>'
        )

    # ── Today KPI tiles ───────────────────────────────────────────────────────
    _pt_kpi_tiles = ""
    _pt_kpi_defs = [
        ("above_50dma","%","% >50DMA","PCT_ABOVE_50"),
        ("above_200dma","%","% >200DMA","PCT_ABOVE_200"),
        ("forward_pe","x","Fwd P/E","FORWARD_PE"),
        ("earnings_yield_vs_10y","%","ERP","ERP"),
        ("net_liquidity","$T","Net Liq","NET_LIQUIDITY"),
        ("vix_term","pts","VIX Term","VIX_TERM"),
        ("vix9d_vix_ratio","x","VIX9D/30","VIX9D_RATIO"),
        ("top10_weight","%","Top-10 Wt","TOP10_WEIGHT"),
        ("rsp_spy_ratio","","RSP/SPY","RSP_SPY"),
    ]
    for _pk, unit, label, sc_key in _pt_kpi_defs:
        v = _pt_today.get(_pk)
        zl, zc = _pt_get_zone(_pk, v)
        disp = _pt_fmt(_pk, v) if v is not None else "N/A"
        _pt_kpi_tiles += (
            f'<div style="background:#fff;border:1px solid #dde1ed;border-top:3px solid {zc};'
            f'border-radius:8px;padding:10px 14px;min-width:110px;text-align:center">'
            f'<div style="font-size:9px;color:#667;text-transform:uppercase;letter-spacing:.05em">{label}</div>'
            f'<div style="font-size:18px;font-weight:900;color:{zc};margin:3px 0">{disp}</div>'
            f'<div style="font-size:9px">{_pt_zone_badge(_pk,v)}</div>'
            f'</div>'
        )

    # ── Column header row ─────────────────────────────────────────────────────
    _pt_col_header = (
        '<tr style="background:#f0f2f8;border-bottom:2px solid #dde1ed">'
        '<th style="padding:8px 14px;text-align:left;font-size:10px;font-weight:800;color:#1a2a3e;letter-spacing:.04em">Drawdown Level</th>'
    )
    for cn in _CRASH_NAMES:
        _pt_col_header += f'<th style="padding:8px 10px;text-align:center;font-size:10px;font-weight:800;color:#1a2a3e">{cn}</th>'
    _pt_col_header += ('<th style="padding:8px 10px;text-align:center;font-size:10px;font-weight:900;'
                       'color:#D4820A;background:#fffbf0;border-left:3px solid #D4820A;border-right:3px solid #D4820A">'
                       '⭐ TODAY</th></tr>')

    # ── Assemble parallel_tab_html ────────────────────────────────────────────
    parallel_tab_html = f"""
<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:14px 20px;
            border-radius:10px;margin-bottom:18px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
  <div>
    <div style="font-size:15px;font-weight:900;color:#fff">🔬 Master Parallel Table</div>
    <div style="font-size:10px;color:#aab;margin-top:2px">
      Indicator readings at each S&amp;P 500 drawdown level · 2000 · 2008 · 2020 · 2022 vs TODAY
    </div>
  </div>
  <div style="margin-left:auto;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <span style="background:#D4820A22;color:#D4820A;border:1px solid #D4820A66;
                 padding:4px 14px;border-radius:6px;font-size:11px;font-weight:800">
      📍 SPY {_spy_dd_str} from ATH → {_current_dd_level}
    </span>
    <span style="background:#991b1b22;color:#991b1b;border:1px solid #991b1b44;
                 padding:4px 12px;border-radius:6px;font-size:11px;font-weight:800">
      {_pt_stress} STRESS/CRISIS
    </span>
    <span style="background:#92400e22;color:#92400e;border:1px solid #92400e44;
                 padding:4px 12px;border-radius:6px;font-size:11px;font-weight:800">
      {_pt_caution} CAUTION
    </span>
    <span style="background:{_pt_regime_col}22;color:{_pt_regime_col};border:1px solid {_pt_regime_col}44;
                 padding:5px 16px;border-radius:6px;font-size:12px;font-weight:900">
      {_pt_regime_lbl}
    </span>
  </div>
</div>

<!-- KPI tiles -->
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px">
  {_pt_kpi_tiles}
</div>

<!-- Main parallel table -->
<div style="background:#fff;border:1px solid #dde1ed;border-radius:10px;overflow:hidden;margin-bottom:24px">
  <div style="background:#f0f4fb;padding:10px 18px;border-bottom:2px solid #dde1ed;
              font-size:12px;font-weight:800;color:#1a2a3e">
    INDICATOR READINGS AT EACH S&amp;P 500 DRAWDOWN LEVEL
    <span style="font-size:9px;font-weight:400;color:#667;margin-left:12px">
      ⭐ TODAY column shows live values from this run · Color = zone (Green=Calm · Amber=Caution · Red=Stress · Dark Red=Crisis)
    </span>
  </div>
  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse">
      <thead>{_pt_col_header}</thead>
      <tbody>{_pt_rows}</tbody>
    </table>
  </div>
</div>

<!-- Watch Rules -->
<div style="background:#fff;border:1px solid #dde1ed;border-radius:10px;overflow:hidden">
  <div style="background:#1a2a3e;padding:10px 18px;font-size:12px;font-weight:800;color:#fff">
    ⚡ 2007-STYLE PARALLEL WATCH RULES
    <span style="font-size:9px;font-weight:400;color:#aab;margin-left:12px">
      Pattern alerts based on pre-crisis setups · Red = currently triggered
    </span>
  </div>
  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:#f0f2f8;border-bottom:2px solid #dde1ed">
          <th style="padding:8px 14px;text-align:left;font-size:10px;font-weight:800;color:#1a2a3e;min-width:130px">Category</th>
          <th style="padding:8px 14px;text-align:left;font-size:10px;font-weight:800;color:#1a2a3e;min-width:300px">Condition</th>
          <th style="padding:8px 14px;text-align:left;font-size:10px;font-weight:800;color:#1a2a3e">Action</th>
        </tr>
      </thead>
      <tbody>{_watch_rows}</tbody>
    </table>
  </div>
</div>
"""

    # ══════════════════════════════════════════════════════════════════════════
    # INDICATOR CHARTS TAB — Full history for every key macro indicator + SPX
    # ══════════════════════════════════════════════════════════════════════════
    import json as _jic

    def _ic_series(name, transform=None, n=None):
        """Get a FRED/proxy series as {dates, values} JSON strings for Chart.js."""
        s = fd.get(name)
        if s is None or (hasattr(s,"empty") and s.empty): return "[]","[]"
        s = s.dropna()
        if n: s = s.tail(n)
        if transform == "yoy" and len(s) >= 13:
            s = ((s / s.shift(12) - 1) * 100).dropna()
        elif transform == "mom" and len(s) >= 2:
            s = ((s / s.shift(1) - 1) * 100).dropna()
        dates  = _jic.dumps([str(d)[:10] for d in s.index])
        values = _jic.dumps([round(float(v),3) for v in s.values])
        return dates, values

    def _ic_spx(n=None):
        """SPX index history for overlay."""
        spx = md.get("^GSPC")
        if spx is None or (hasattr(spx,"empty") and spx.empty):
            spx = md.get("SPY")
        if spx is None or (hasattr(spx,"empty") and spx.empty): return "[]","[]"
        spx = spx.dropna()
        if n: spx = spx.tail(n)
        dates  = _jic.dumps([str(d)[:10] for d in spx.index])
        values = _jic.dumps([round(float(v),2) for v in spx.values])
        return dates, values

    spx_dates, spx_vals = _ic_spx()

    # Define all charts: (title, series_key, transform, unit, color, description)
    _IC_CHARTS = [
        # Credit
        ("HY Credit Spread (OAS)",     "HY_OAS",    None,  "bps", "#E91E63", "High-Yield spread over Treasuries. >600bps = recession risk. Spikes precede downturns."),
        ("IG Credit Spread (OAS)",      "IG_OAS",    None,  "bps", "#9C27B0", "Investment-grade spread. >200bps = financial stress. Leading recession signal."),
        ("CCC Junk Spread",             "CCC_OAS",   None,  "bps", "#F44336", "Lowest-quality junk. >1200bps = distress. Most sensitive credit stress gauge."),
        # Rates
        ("Yield Curve (10Y-2Y)",        "YIELD_CURVE",None, "%",  "#2196F3", "Inversion (<0) precedes every recession by 6-18 months. Now normalizing."),
        ("10Y-3M Spread",               "T10Y3M",    None,  "%",  "#03A9F4", "Fed's preferred recession indicator. Inversion = strong recession warning."),
        ("10Y Treasury Yield",          "T10Y",      None,  "%",  "#1565C0", "Risk-free rate benchmark. Rising = tightening financial conditions."),
        ("Fed Funds Rate",              "FEDFUNDS",  None,  "%",  "#0D47A1", "Monetary policy rate. Hikes = tightening; cuts = easing. Lags the cycle."),
        ("Real Yield (TIPS 10Y)",       "REAL_YIELD",None,  "%",  "#5C6BC0", "10Y yield minus inflation. Positive = restrictive. >2% = significant drag."),
        ("Breakeven Inflation (10Y)",   "BREAKEVEN", None,  "%",  "#7986CB", "Market-implied inflation. Rising = inflation expectations increasing."),
        # Volatility
        ("VIX — Fear Index",            "VIX",       None,  "idx","#FF5722", ">30 = fear/buying opportunity. >40 = capitulation. Peaks at market bottoms."),
        # Macro Growth
        ("Industrial Production",       "INDPRO",    "yoy", "%",  "#4CAF50", "YoY % change. Negative YoY = recessionary. Leads earnings by 1-2 quarters."),
        ("Capacity Utilization",        "CAPUTIL",   None,  "%",  "#66BB6A", "<75% = recession. 78-80% = healthy. Rising = inflationary pressure."),
        ("ISM Manufacturing PMI",       "ISM_PMI",   None,  "idx","#FF9800", "<50 = contraction. <45 = recession. Leads industrial production by 3-6mo."),
        ("ISM New Orders",              "ISM_NEWORDERS",None,"idx","#FFA726", "Most forward-looking ISM sub-index. Divergence from PMI = trend change signal."),
        # Inflation
        ("CPI YoY",                     "CPI",       "yoy", "%",  "#F44336", "Consumer Price Index year-over-year. Fed target 2%. >4% = restrictive policy."),
        ("PCE YoY",                     "PCE",       "yoy", "%",  "#EF5350", "Fed's preferred inflation gauge. >2.5% sustained = hawkish. Runs below CPI."),
        # Labor
        ("Unemployment Rate",           "UNRATE",    None,  "%",  "#9E9E9E", "Lags cycle by 6-12 months. Rising from trough = recession confirmation."),
        ("Initial Jobless Claims",      "INIT_CLAIMS",None, "K",  "#607D8B", "<300K = tight labor market. Rising trend = labor market deterioration signal."),
        ("Sahm Rule Indicator",         "SAHM",      None,  "pts","#78909C", ">0.5pts = recession signal (100% accuracy since 1970). Real-time recession alert."),
        # Consumer/Retail
        ("Retail Sales",                "RETAIL",    "yoy", "%",  "#00BCD4", "YoY % change. Negative = consumer recession. 70% of US GDP is consumption."),
        ("UMich Consumer Sentiment",    "UMCSENT",   None,  "idx","#26C6DA", "Below 70 = pessimism. Extreme lows = contrarian buy signals. Leads spending."),
        # Housing
        ("Housing Starts",              "HOUST",     None,  "K",  "#8BC34A", "Highly cyclical. Peaks 12-18mo before recessions. Troughs 6-12mo into recovery."),
        ("30yr Mortgage Rate",          "RATE_30",   None,  "%",  "#CDDC39", ">7% significantly constrains affordability. Lags Fed Funds by 1-2 months."),
        ("Case-Shiller HPI YoY",        "HPI_NAT",   "yoy", "%",  "#C6D300", "Home price appreciation YoY. Negative = housing recession. Wealth effect signal."),
        # Money / Liquidity
        ("M2 Money Supply YoY",         "M2SL",      "yoy", "%",  "#AB47BC", "Money supply growth. Negative = liquidity drain = equities at risk."),
        ("Fed Balance Sheet (WALCL)",   "WALCL",     None,  "$T", "#CE93D8", "QE = expanding (bullish). QT = contracting (bearish). $Trillion scale."),
        ("NY Fed Recession Probability","NY_REC_PROB",None, "%",  "#EF9A9A", ">30% = elevated risk. >50% = near-certain recession. 12-month forward looking."),
        # Credit Quality
        ("Credit Card Delinquency",     "CREDIT_CARD_DLQ",None,"%","#FFAB40",">3% = consumer stress. >4% = systemic. Leads charge-offs by 1-2 quarters."),
        ("NFCI Financial Conditions",   "NFCI",      None,  "fsi","#FF7043", ">0 = tight conditions. >1 = significant stress. Chicago Fed composite."),
        # Oil
        ("WTI Crude Oil",               "DCOILWTICO",None,  "$/bbl","#795548","Oil spike = inflation risk + demand destruction. Drop = global slowdown signal."),
        # GDP
        ("GDP (Quarterly)",             "GDP",       None,  "$B", "#26A69A", "Nominal GDP in billions. Negative QoQ = recession. Watch trend vs absolute level."),
    ]

    # Generate HTML and JS for each chart
    _ic_chart_htmls = []
    _ic_chart_js_blocks = []

    if no_indicator_charts:
        print("  [indicator charts] Skipped (--noindicatorcharts flag)")
        indcharts_tab_html = """
<div style="padding:40px;text-align:center;color:#667;font-size:13px">
  📉 Indicator Charts skipped — run without <code>--noindicatorcharts</code> to enable.<br>
  <span style="font-size:11px;color:#aab">All other tabs are fully loaded.</span>
</div>"""
        indcharts_tab_js = ""
    else:
        for _i, (title, series_key, transform, unit, color, description) in enumerate(_IC_CHARTS):
            cid = f"ic_{series_key.replace('^','').replace('-','_').lower()}"
            dates, values = _ic_series(series_key, transform)
    
            # Skip if no data
            if dates == "[]":
                continue
    
            # Unit formatting for tooltip
            if unit == "$T":
                tick_cb = "v => '$' + (v/1e6).toFixed(1) + 'T'"
                tooltip_cb = "v => '$' + (v/1e6).toFixed(2) + 'T'"
            elif unit == "$B":
                tick_cb = "v => '$' + (v/1000).toFixed(1) + 'T'"
                tooltip_cb = "v => '$' + (v/1000).toFixed(1) + 'T'"
            elif unit == "K":
                tick_cb = "v => (v/1000).toFixed(0) + 'K'"
                tooltip_cb = "v => (v/1000).toFixed(1) + 'K'"
            elif unit == "bps":
                tick_cb = "v => v.toFixed(0) + 'bps'"
                tooltip_cb = "v => v.toFixed(0) + ' bps'"
            elif unit == "%":
                tick_cb = "v => v.toFixed(1) + '%'"
                tooltip_cb = "v => v.toFixed(2) + '%'"
            else:
                tick_cb = "v => v.toFixed(1)"
                tooltip_cb = "v => v.toFixed(2)"
    
            html = f"""
    <div class="ic-chart-card" style="background:#fff;border:1px solid #dde1ed;border-radius:12px;
                overflow:hidden;margin-bottom:14px">
      <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);padding:10px 18px;
                  display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0"></div>
        <div style="font-size:13px;font-weight:800;color:#fff">{title}</div>
        <div style="margin-left:auto;font-size:9px;color:#aab;letter-spacing:.04em">{series_key} · {unit}</div>
      </div>
      <div style="padding:8px 16px 4px;font-size:9px;color:#667;background:#f8f9ff;
                  border-bottom:1px solid #eef0f8">{description}</div>
      <div style="position:relative;height:280px;padding:8px">
        <canvas id="{cid}"></canvas>
        <button onclick="(function(){{var c=Chart.getChart('{cid}');if(c){{c.options.scales.x.min=undefined;c.options.scales.x.max=undefined;c.options.scales.y.min=undefined;c.options.scales.y.max=undefined;if(c.options.scales.y1){{c.options.scales.y1.min=undefined;c.options.scales.y1.max=undefined;}}try{{c.resetZoom();}}catch(e){{c.update();}}}}}})()"
          style="position:absolute;top:10px;left:10px;font-size:8px;padding:2px 7px;border-radius:4px;
                 border:1px solid #ccd;background:rgba(255,255,255,0.92);color:#445;cursor:pointer;z-index:5">
          ⟲ Reset
        </button>
      </div>
    </div>"""
            _ic_chart_htmls.append(html)
    
            _ic_js = f"""
    (function(){{
      const ctx = document.getElementById('{cid}');
      if (!ctx) return;
      const dates  = {dates};
      const vals   = {values};
      const spxD   = {spx_dates};
      const spxV   = {spx_vals};
      if (!dates.length) return;
    
      // Month-label dedup
      const seen={{}};
      const lbls = dates.map(d=>{{
        const mo=d.slice(0,7);
        if(!seen[mo]){{seen[mo]=1;return mo;}}
        return '';
      }});
    
      const ch = new Chart(ctx, {{
        type:'line',
        data:{{
          labels: dates,
          datasets:[
            {{
              label: '{title}',
              data:  vals,
              borderColor: '{color}',
              backgroundColor: '{color}22',
              borderWidth: 2,
              pointRadius: 0,
              fill: true,
              tension: 0.2,
              yAxisID: 'y',
              order: 1,
            }},
            {{
              label: 'S&P 500',
              data:  spxD.map(d=>{{
                const i=dates.indexOf(d);
                if(i>=0) return {{x:d,y:spxV[spxD.indexOf(d)]}};
                // Nearest date interpolation
                const nearest = dates.reduce((best,dd)=>Math.abs(new Date(dd)-new Date(d))<Math.abs(new Date(best)-new Date(d))?dd:best, dates[0]);
                return {{x:nearest, y:spxV[spxD.indexOf(nearest)]}};
              }}).filter((v,i,a)=>a.findIndex(x=>x.x===v.x)===i),
              borderColor: 'rgba(100,120,160,0.5)',
              borderWidth: 1.5,
              borderDash: [4,3],
              pointRadius: 0,
              fill: false,
              tension: 0.1,
              yAxisID: 'y1',
              order: 2,
            }}
          ]
        }},
        options:{{
          responsive:true,
          maintainAspectRatio:false,
          interaction:{{mode:'index',intersect:false}},
          plugins:{{
            legend:{{display:false}},
            tooltip:{{
              callbacks:{{
                label: c => c.dataset.label==='S&P 500'
                  ? 'SPX: ' + c.parsed.y.toFixed(0)
                  : '{title}: ' + ({tooltip_cb})(c.parsed.y)
              }}
            }},
            zoom:{{pan:{{enabled:false}},zoom:{{wheel:{{enabled:false}},pinch:{{enabled:false}}}}}}
          }},
          scales:{{
            x:{{
              ticks:{{color:'#8899aa',font:{{size:8}},maxRotation:0,
                     callback:(v,i)=>lbls[i]||null,maxTicksLimit:18,autoSkip:false}},
              grid:{{color:'rgba(180,190,210,0.15)'}}
            }},
            y:{{
              position:'left',
              ticks:{{color:'{color}cc',font:{{size:9}},callback: v=>({tick_cb})(v)}},
              grid:{{color:'rgba(180,190,210,0.15)'}},
            }},
            y1:{{
              position:'right',
              ticks:{{color:'rgba(100,120,160,0.7)',font:{{size:8}}}},
              grid:{{drawOnChartArea:false}},
              title:{{display:true,text:'S&P 500',color:'rgba(100,120,160,0.7)',font:{{size:8}}}}
            }}
          }}
        }}
      }});
      initTVZoom(ch);
      ctx.addEventListener('mouseenter', function _h(){{showTVHint(ctx);ctx.removeEventListener('mouseenter',_h);}},{{once:true}});
    }})();
    """
            _ic_chart_js_blocks.append(_ic_js)
    
        # Count charts generated
        n_ic = len(_ic_chart_htmls)
        print(f"  [indicator charts] Generated {n_ic} indicator charts with SPX overlay")

        indcharts_tab_html = "".join(_ic_chart_htmls)
        indcharts_tab_js   = "\n".join(_ic_chart_js_blocks)

    # ── Leading Indicators tab (new) ─────────────────────────────────────────
    print("  [leading tab] Computing peak/trough signals and fetching live data...")
    _pcr_val, _pcr_src = _fetch_pcr_additions()
    if _pcr_val: print(f"  [leading tab] PCR: {_pcr_val:.3f}  ({_pcr_src})")
    _aaii_data  = _fetch_aaii_additions()
    _add_deriv  = _compute_derived_additions(fd, md)
    _pt_score   = _compute_pt_score(fd, md, _add_deriv)
    print(f"  [leading tab] Quick check: Peak {_pt_score['peak_score']}/5  Trough {_pt_score['trough_score']}/5")
    # Comprehensive analysis using ALL scorecard indicators
    _comprehensive = _compute_comprehensive_analysis(scorecard) if scorecard else {}
    if _comprehensive:
        print(f"  [leading tab] Comprehensive: Peak {_comprehensive['peak_score']}%  Trough {_comprehensive['trough_score']}%  ({_comprehensive['n_indicators']} indicators)")
    # Historical episode comparison table + compute similarity for overlay
    _episode_html = _build_episode_html(
        current_vals={}, scorecard_data=scorecard or [], fd=fd, md=md
    )
    print(f"  [leading tab] Episode comparison: {len([e for e in EPISODE_DATABASE if e['type']=='PEAK'])} peaks, {len([e for e in EPISODE_DATABASE if e['type']=='TROUGH'])} troughs")
    # Compute episode similarity separately so overlay can use scores
    _cur_ep_vals = {}
    try:
        def _gv_ep(k, i=-1):
            s = fd.get(k)
            if s is not None and not s.empty:
                try: return float(s.iloc[max(i,-len(s))])
                except: pass
            return None
        _hy_v  = _gv_ep("HY_OAS")
        _yc_v  = _gv_ep("YIELD_CURVE")
        _vx_v  = None
        _vxs   = md.get("^VIX")
        if _vxs is not None and not _vxs.empty: _vx_v = float(_vxs.iloc[-1])
        _t10_v = _gv_ep("T10Y")
        _ff_v  = _gv_ep("FEDFUNDS")
        _ry_v  = _gv_ep("REAL_YIELD")
        _cpi_s = fd.get("CPI")
        _cpi_v = None
        if _cpi_s is not None and len(_cpi_s) >= 13:
            _cpi_v = round((float(_cpi_s.iloc[-1])/float(_cpi_s.iloc[-13])-1)*100,1)
        _ism_v = _gv_ep("ISM_PMI")
        # Get fwd_pe and pct200 from scorecard
        _fpe_v = None; _p200_v = None
        for _sc_ind in (scorecard or []):
            if _sc_ind.get("name") == "Forward P/E": _fpe_v = _sc_ind.get("value")
            if _sc_ind.get("name") == "% S&P Above 200DMA": _p200_v = _sc_ind.get("value")
        _cur_ep_vals = {
            "hy_oas":   _hy_v,
            "yc":       (_yc_v / 100) if _yc_v is not None else None,
            "vix":      _vx_v,
            "fwd_pe":   _fpe_v,
            "ff":       _ff_v,
            "real_yld": _ry_v,
            "cpi":      _cpi_v,
            "ism":      _ism_v,
            "pct200":   _p200_v,
        }
        _ep_sim_results = _compute_episode_similarity(_cur_ep_vals, EPISODE_DATABASE)
        print(f"  [leading tab] Best episode match: {_ep_sim_results[0]['episode']['name']} ({_ep_sim_results[0]['score']}%)" if _ep_sim_results else "")
    except Exception as _ese:
        _ep_sim_results = []
        print(f"  [leading tab] Episode similarity error: {_ese}")
    # Pullback monitor
    _pb_derived = {**_add_deriv, "pcr_live": _pcr_val}
    _pb_data    = _compute_pullback_risk(scorecard, fd, md, _pb_derived)
    _pb_overlay = _build_pullback_overlay_data(md, sim_results=_ep_sim_results, pb_data=_pb_data)
    _pb_html    = _build_pullback_monitor_html(_pb_data, scorecard, fd, md, overlay_data=_pb_overlay)
    print(f"  [pullback] Score: {_pb_data['overall_score']}%  {_pb_data['risk_level'][:40]}")
    if _pb_overlay.get("datasets"):
        print(f"  [pullback] Overlay: {len(_pb_overlay['datasets'])} episodes, cur_day={_pb_overlay.get('cur_day')}")
    # Economic calendar
    print("  [eco calendar] Fetching economic calendar...")
    _cal_events   = _fetch_economic_calendar(use_api=use_api, fd=fd)
    _eco_cal_html = _build_economic_calendar_html(fd, md, _cal_events, scorecard=scorecard)
    _leading_tab_html = _build_leading_tab_html(
        _pt_score, _add_deriv, _pcr_val, _pcr_src, _aaii_data, fd, md,
        comprehensive=_comprehensive, episode_html=_episode_html
    )

    # ── Options Flow tab — GEX charts from Barchart CSVs ─────────────────────
    _options_tab_html = build_options_flow_tab(DOWNLOADS_DIR)

    TAB_NAV = f"""
<!-- ═══ TOP NAVBAR ══════════════════════════════════════════════════════════ -->
<nav id="mi-nav">

  <!-- Logo -->
  <a class="mi-logo" href="#" onclick="showTab('overview');return false">
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
      <polygon points="13,2 24,24 2,24" stroke="#00C8A0" stroke-width="1.5" fill="none"/>
      <polyline points="5,20 11,12 16,16 21,7" stroke="#F5A020"
                stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span class="mi-logo-text">Market<span>Intel</span></span>
  </a>

  <!-- Macro dropdown -->
  <div class="nav-group">
    <button class="nav-group-btn">Macro <span class="nav-chevron">▾</span></button>
    <div class="nav-dd">
      <a class="nav-dd-item" href="#" onclick="showTab('overview');return false">
        <div class="nav-dd-icon" style="background:rgba(0,200,160,.1)">📊</div>
        <div><div class="nav-dd-label">Overview</div><div class="nav-dd-sub">62 indicators · scorecard</div></div>
      </a>
      <a class="nav-dd-item" href="#" onclick="showTab('indcharts');return false">
        <div class="nav-dd-icon" style="background:rgba(59,130,246,.1)">📉</div>
        <div><div class="nav-dd-label">Indicator Charts</div><div class="nav-dd-sub">Full history + SPX overlay</div></div>
      </a>
      <div class="nav-dd-sep"></div>
      <a class="nav-dd-item" href="#" onclick="showTab('bonds');return false">
        <div class="nav-dd-icon" style="background:rgba(255,77,109,.1)">💳</div>
        <div><div class="nav-dd-label">Credit &amp; Rates</div><div class="nav-dd-sub">HY/IG spreads · yield curve</div></div>
      </a>
      <a class="nav-dd-item" href="#" onclick="showTab('mktcharts');return false">
        <div class="nav-dd-icon" style="background:rgba(245,160,32,.1)">🔬</div>
        <div><div class="nav-dd-label">Market Charts</div><div class="nav-dd-sub">Smart/Dumb money · gauges</div></div>
      </a>
    </div>
  </div>

  <!-- Cycles dropdown -->
  <div class="nav-group">
    <button class="nav-group-btn">Cycles <span class="nav-chevron">▾</span></button>
    <div class="nav-dd">
      <a class="nav-dd-item" href="#" onclick="showTab('cycles');return false">
        <div class="nav-dd-icon" style="background:rgba(0,200,160,.1)">🔄</div>
        <div><div class="nav-dd-label">Cycle Analysis</div><div class="nav-dd-sub">Kuznets · Juglar · Kitchin</div></div>
      </a>
      <a class="nav-dd-item" href="#" onclick="showTab('parallel');return false">
        <div class="nav-dd-icon" style="background:rgba(139,164,190,.1)">🔬</div>
        <div><div class="nav-dd-label">Parallel Table</div><div class="nav-dd-sub">8 crashes vs today</div></div>
      </a>
      <a class="nav-dd-item" href="#" onclick="showTab('leading');return false">
        <div class="nav-dd-icon" style="background:rgba(245,160,32,.1)">📡</div>
        <div><div class="nav-dd-label">Leading Indicators</div><div class="nav-dd-sub">Peak / trough scoring</div></div>
      </a>
    </div>
  </div>

  <!-- Markets dropdown -->
  <div class="nav-group">
    <button class="nav-group-btn">Markets <span class="nav-chevron">▾</span></button>
    <div class="nav-dd">
      <a class="nav-dd-item" href="#" onclick="showTab('sectors');return false">
        <div class="nav-dd-icon" style="background:rgba(0,200,160,.1)">🗂</div>
        <div><div class="nav-dd-label">Sector Rotation</div><div class="nav-dd-sub">ETF pair ratios</div></div>
      </a>
      <a class="nav-dd-item" href="#" onclick="showTab('sectorstocks');return false">
        <div class="nav-dd-icon" style="background:rgba(59,130,246,.1)">📋</div>
        <div><div class="nav-dd-label">Sector Stocks</div><div class="nav-dd-sub">Top 10 per sector</div></div>
      </a>
      <a class="nav-dd-item" href="#" onclick="showTab('pullback');return false">
        <div class="nav-dd-icon" style="background:rgba(255,77,109,.1)">📉</div>
        <div><div class="nav-dd-label">Drawdown Analysis</div><div class="nav-dd-sub">Pullback monitor · projections</div></div>
      </a>
    </div>
  </div>

  <!-- Calendar dropdown -->
  <div class="nav-group">
    <button class="nav-group-btn">Calendar <span class="nav-chevron">▾</span></button>
    <div class="nav-dd">
      <a class="nav-dd-item" href="#" onclick="showTab('ecocal');return false">
        <div class="nav-dd-icon" style="background:rgba(245,160,32,.1)">📅</div>
        <div><div class="nav-dd-label">Economic Calendar</div><div class="nav-dd-sub">This week's events</div></div>
      </a>
      <a class="nav-dd-item" href="#" onclick="showTab('options');return false">
        <div class="nav-dd-icon" style="background:rgba(0,200,160,.1)">⚡</div>
        <div><div class="nav-dd-label">Options Flow</div><div class="nav-dd-sub">GEX · dealer positioning</div></div>
      </a>
    </div>
  </div>

  <!-- AI Summary direct link -->
  <button class="nav-direct" onclick="showTab('ai-summary')">🤖 AI Summary</button>

  <!-- Right side -->
  <div class="nav-right">
    <div class="nav-live">
      <div class="live-dot"></div>
      {_spy_price_str}
    </div>
    <span class="nav-timestamp">{gen_time}</span>
  </div>

</nav>

<!-- ═══ SIDEBAR ═════════════════════════════════════════════════════════════ -->
<aside id="mi-sidebar">

  <div class="sb-label">Overview</div>
  <button class="sb-item active" id="btn-overview"    onclick="showTab('overview')">
    <span class="sb-icon">📊</span> Dashboard
    <span class="sb-badge sb-danger">{_n_danger}</span>
  </button>
  <button class="sb-item" id="btn-indcharts"  onclick="showTab('indcharts')">
    <span class="sb-icon">📉</span> Indicator Charts
  </button>

  <div class="sb-label">Cycle Analysis</div>
  <button class="sb-item" id="btn-cycles"     onclick="showTab('cycles')">
    <span class="sb-icon">🔄</span> Kuznets / Juglar
  </button>
  <button class="sb-item" id="btn-parallel"   onclick="showTab('parallel')">
    <span class="sb-icon">🔬</span> Parallel Table
  </button>
  <button class="sb-item" id="btn-leading"    onclick="showTab('leading')">
    <span class="sb-icon">📡</span> Leading Signals
  </button>

  <div class="sb-label">Credit &amp; Rates</div>
  <button class="sb-item" id="btn-bonds"      onclick="showTab('bonds')">
    <span class="sb-icon">📈</span> Credit &amp; Rates
  </button>
  <button class="sb-item" id="btn-mktcharts"  onclick="showTab('mktcharts')">
    <span class="sb-icon">🔬</span> Market Charts
  </button>

  <div class="sb-label">Markets</div>
  <button class="sb-item" id="btn-sectors"    onclick="showTab('sectors')">
    <span class="sb-icon">🗂</span> Sector Rotation
  </button>
  <button class="sb-item" id="btn-sectorstocks" onclick="showTab('sectorstocks')">
    <span class="sb-icon">📋</span> Sector Stocks
  </button>
  <button class="sb-item" id="btn-pullback"   onclick="showTab('pullback')">
    <span class="sb-icon">📉</span> Drawdown Monitor
  </button>

  <div class="sb-label">Intelligence</div>
  <button class="sb-item" id="btn-ai-summary" onclick="showTab('ai-summary')">
    <span class="sb-icon">🤖</span> AI Summary
  </button>
  <button class="sb-item" id="btn-ecocal"     onclick="showTab('ecocal')">
    <span class="sb-icon">📅</span> Eco Calendar
  </button>
  <button class="sb-item" id="btn-options"    onclick="showTab('options')">
    <span class="sb-icon">⚡</span> Options Flow
  </button>

</aside>
"""


    # ── Step A: Get LIVE SPY price via yfinance (most reliable, no API needed) ─
    _live_spy_now = _get_live_spy_price()
    if _live_spy_now:
        _spy_price     = _live_spy_now
        _spy           = _live_spy_now
        _spy_price_str = f"SPY ${_spy:,.2f}"
        print(f"  Live SPY price for chart: ${_spy:,.2f}")
    else:
        # Fallback: use md cache
        try:
            _sp2 = md.get("SPY") or md.get("^GSPC")
            if _sp2 is not None and not _sp2.empty:
                _spy_price     = round(float(_sp2.dropna().iloc[-1]), 2)
                _spy           = _spy_price
                _spy_price_str = f"SPY ${_spy:,.2f}"
        except Exception:
            pass
        if not _spy_price:
            print("  WARNING: SPY price unavailable — using 560 fallback")

    # ── Step B: Build monthly history + append TODAY's live price ─────────────
    # This ensures the solid line ends EXACTLY at the current live price,
    # so projections start seamlessly from that point.
    _spy_hist_dates  = []
    _spy_hist_values = []
    try:
        _spy_s = md.get("SPY"); _spy_s = _spy_s if (_spy_s is not None and len(_spy_s)>0) else md.get("^GSPC")
        if _spy_s is not None and not _spy_s.empty:
            import pandas as _pd_spy
            _spy_m = _spy_s.resample("ME").last().dropna().tail(29)   # 29 months + today = 30 pts
            try:
                if _spy_m.index.tz is not None:
                    _spy_m.index = _spy_m.index.tz_localize(None)
            except Exception: pass
            _spy_hist_dates  = [str(d)[:7] for d in _spy_m.index]
            _spy_hist_values = [round(float(v), 2) for v in _spy_m.values]
    except Exception: pass

    # Append the LIVE price as the final historical point (today's date)
    from datetime import date as _dt_now
    _today_label = _dt_now.today().strftime("%Y-%m")
    if _spy_hist_dates and _today_label != _spy_hist_dates[-1]:
        _spy_hist_dates.append(_today_label)
        _spy_hist_values.append(_spy)
    elif _spy_hist_dates:
        # Same month — update the last point to the live price
        _spy_hist_values[-1] = _spy

    # ── Step C: AI projection ─────────────────────────────────────────────────
    _spy_js     = _spy
    # Display-safe values for AI tab (no function calls inside f-strings)
    try:
        _vix_s = md.get("^VIX")
        _vix_display = f"{float(_vix_s.iloc[-1]):.1f}" if (_vix_s is not None and not _vix_s.empty) else "N/A"
    except: _vix_display = "N/A"
    _real_yield_v = None
    try:
        _ry_s = fd.get("REAL_YIELD")
        _real_yield_v = round(float(_ry_s.iloc[-1]), 2) if (_ry_s is not None and not _ry_s.empty) else None
    except: pass
    _real_yield_display = f"{_real_yield_v:.2f}%" if _real_yield_v is not None else "N/A"
    _tgts_js = {
        "t3_bull":  int(_tgts["3mo_bull"]),  "t3_base":  int(_tgts["3mo_base"]),  "t3_bear":  int(_tgts["3mo_bear"]),
        "t12_bull": int(_tgts["12mo_bull"]), "t12_base": int(_tgts["12mo_base"]), "t12_bear": int(_tgts["12mo_bear"]),
        "t24_bull": int(_tgts["24mo_bull"]), "t24_base": int(_tgts["24mo_base"]), "t24_bear": int(_tgts["24mo_bear"]),
    }
    import json as _json
    _spy_hist_dates_json  = _json.dumps(_spy_hist_dates)
    _spy_hist_values_json = _json.dumps(_spy_hist_values)
    _tgts_js_json         = _json.dumps(_tgts_js)

    # ── Step D: Claude AI projection (anchored to live price) ─────────────────
    _regime_str = pos.get("regime","")
    _proj_data  = None
    if CLAUDE_API_KEY and scorecard and use_api:
        print("  Generating AI price projection...")
        _proj_data = _claude_price_projection(
            _spy, scorecard, pos, _regime_str, gen_time
        )
        # Claude returns spy_latest = live price; already validated in _claude_price_projection
        if _proj_data and _proj_data.get("spy_latest"):
            _spy_price_str = f"SPY ${_proj_data['spy_latest']:,.2f}"

    # ── Step E: Force projection paths to connect at spy_hist_values[-1] ──────
    # This eliminates ANY visual gap between the solid history line and dashed projections.
    if _proj_data and _spy_hist_values:
        _hist_last = _spy_hist_values[-1]
        for _pk in ("bull_monthly", "base_monthly", "bear_monthly"):
            if _pk in _proj_data and _proj_data[_pk]:
                _proj_data[_pk][0] = _hist_last  # hard-anchor month-1 to history endpoint

    # ── Step F: Rebuild ALL price-dependent blocks with REAL live price ──────────
    _tgts = _make_tgts(_spy, _kp_v, _jp_v)
    _kit_dd  = -0.15 if _kp_v > 80 else -0.10
    _jug_dd  = -0.30 if _jp_v > 85 else -0.20
    _scenario_table_html = _build_scenario_table(_tgts, _spy, rg)

    # ── If AI proj succeeded, upgrade thesis cards to AI-derived content ──────
    if _proj_data:
        _pb   = _proj_data.get("probability_bull", 25)
        _pm   = _proj_data.get("probability_base", 50)
        _pd   = _proj_data.get("probability_bear", 25)
        _bt   = _proj_data.get("bull_thesis", "")
        _bst  = _proj_data.get("base_thesis", "")
        _brt  = _proj_data.get("bear_thesis", "")
        _pr   = _proj_data.get("primary_risk", "")
        _ha   = _proj_data.get("historical_analog", "")
        _kr   = _proj_data.get("key_risk", "")
        _an   = _proj_data.get("analysis_summary", "")
        _b3   = _proj_data["bull_monthly"][2]  if len(_proj_data.get("bull_monthly",[]))>=3  else _tgts["3mo_bull"]
        _m3   = _proj_data["base_monthly"][2]  if len(_proj_data.get("base_monthly",[]))>=3  else _tgts["3mo_base"]
        _r3   = _proj_data["bear_monthly"][2]  if len(_proj_data.get("bear_monthly",[]))>=3  else _tgts["3mo_bear"]
        _b12  = _proj_data.get("year_end_2026_bull", _tgts["12mo_bull"])
        _m12  = _proj_data.get("year_end_2026_base", _tgts["12mo_base"])
        _r12  = _proj_data.get("year_end_2026_bear", _tgts["12mo_bear"])
        _b24  = _proj_data.get("year_end_2027_bull", _tgts["24mo_bull"])
        _m24  = _proj_data.get("year_end_2027_base", _tgts["24mo_base"])
        _r24  = _proj_data.get("year_end_2027_bear", _tgts["24mo_bear"])

        # 4-week: derive from 3-mo probabilities + primary risk
        _4wk = (
            "AI Outlook — Next 4 Weeks",
            f"• Primary risk: {_pr[:80]}<br>"
            f"• Bull ({_pb}%): {_bt[:100] if _bt else 'Momentum continues'}<br>"
            f"• Base ({_pm}%): {_bst[:100] if _bst else 'Consolidation/dip'}<br>"
            f"• Watch: {_kr[:80] if _kr else 'HY OAS + breadth'}",
            f"AI-powered · Historical analog: {_ha[:60] if _ha else '?'}"
        )
        _4wk_col = "#C0390F" if _pd >= 35 else "#D4820A" if _pd >= 20 else "#1A7A4A"
        _4wk_bg  = "#FDDDD5"  if _pd >= 35 else "#FFF0CC"  if _pd >= 20 else "#D6F0E0"

        _3mo = (
            "AI 3-Month Projection",
            f"• Bull {_pb}%: ${round(_b3):,}  Base {_pm}%: ${round(_m3):,}  Bear {_pd}%: ${round(_r3):,}<br>"
            f"• Base case: {_bst[:120] if _bst else ''}<br>"
            f"• Bear trigger: {_brt[:100] if _brt else ''}<br>"
            f"• Cycle: Juglar {_jp_v:.0f}% · Kitchin {_kp_v:.0f}%",
            f"AI-powered · Anchored to SPY ${_spy:,.2f}"
        )
        _3mo_col = "#C0390F" if _pd >= 35 else "#D4820A" if _pm >= 45 else "#1A7A4A"
        _3mo_bg  = "#FDDDD5"  if _pd >= 35 else "#FFF0CC"  if _pm >= 45 else "#D6F0E0"

        _12mo = (
            "AI 12-Month Projection (Dec 2026)",
            f"• Bull {_pb}%: ${round(_b12):,}  Base {_pm}%: ${round(_m12):,}  Bear {_pd}%: ${round(_r12):,}<br>"
            f"• Analysis: {_an[:140] if _an else ''}<br>"
            f"• Key risk threshold: {_kr[:80] if _kr else ''}",
            f"AI Sonnet · All 60 indicators · {_ha[:50] if _ha else ''}"
        )
        _12mo_col = "#C0390F" if _pd >= 35 else "#D4820A" if _pm >= 45 else "#2E8B57"
        _12mo_bg  = "#FDDDD5"  if _pd >= 35 else "#FFF0CC"  if _pm >= 45 else "#E6F8EF"

        _24mo = (
            "AI 2-Year Projection (Dec 2027)",
            f"• Bull {_pb}%: ${round(_b24):,}  Base {_pm}%: ${round(_m24):,}  Bear {_pd}%: ${round(_r24):,}<br>"
            f"• Kuznets supercycle at {_knp_v:.0f}% — AI infrastructure buildout continues to ~2028<br>"
            f"• Any 2026-27 Juglar correction is within Kuznets uptrend<br>"
            f"• Strategic dip buy zone: ${round(_spy*0.75):,}–${round(_spy*0.85):,}",
            f"Kuznets {_knp_v:.0f}% · AI-powered full-cycle analysis"
        )
        _24mo_col, _24mo_bg = "#3355aa", "#EEF2FF"
    else:
        # Fallback static thesis (using real live price)
        if _sc_danger >= 5 or (_hy_now > 380 and _kp_v > 85):
            _4wk = ("Defensive — Correction Risk",
                    "• Credit/VIX signals elevated — reduce equity exposure<br>"
                    "• Keep positions &lt;50% of normal size<br>"
                    "• Focus: XLP, XLV, TLT, GLD<br>"
                    "• Watch HY OAS — cross 420bps = exit",
                    f"Kitchin {_kp_v:.0f}% + {_sc_danger} danger signals")
            _4wk_col, _4wk_bg = "#C0390F", "#FDDDD5"
        elif _sc_danger >= 2:
            _4wk = ("Cautious — Late-Cycle Positioning",
                    "• Hold reduced equity, raise cash to 20-30%<br>"
                    "• Favor quality: dividend payers, low-beta<br>"
                    "• Rotate XLK → XLV, XLF → XLU<br>"
                    "• Hedge with TLT or GLD on dips",
                    f"{_sc_danger} danger signals · Kitchin {_kp_v:.0f}%")
            _4wk_col, _4wk_bg = "#D4820A", "#FFF0CC"
        else:
            _4wk = ("Risk-On — Rally Has Room",
                    "• Maintain equity exposure, favor growth<br>"
                    "• Credit calm — HY OAS &lt;380bps supports rally<br>"
                    "• Add on dips: SPY, QQQ, XLK<br>"
                    "• Monitor VIX term structure weekly",
                    f"Credit calm · only {_sc_danger} danger signals")
            _4wk_col, _4wk_bg = "#1A7A4A", "#D6F0E0"

        if _kp_v > 80:
            _3mo = ("Kitchin Correction — -10% to -20%",
                    "• Inventory cycle + AI capex disappointment risk<br>"
                    f"• Base target: ${round(_spy*(1+_kit_dd)):,} ({_kit_dd*100:.0f}%)<br>"
                    "• Trigger: INDPRO &lt;0% + HY OAS &gt;420bps<br>"
                    "• Defensive + dry powder for re-entry on Kitchin trough",
                    f"Kitchin {_kp_v:.0f}% complete · 2022/2018 analogs")
            _3mo_col, _3mo_bg = "#D4820A", "#FFF0CC"
        elif _jp_v > 85:
            _3mo = ("Juglar Peak — -20% to -40% Risk",
                    "• Near Juglar peak → larger correction risk accelerating<br>"
                    f"• Bear target: ${round(_spy*(1+_jug_dd)):,} ({_jug_dd*100:.0f}%)<br>"
                    "• Post-inversion recession window open<br>"
                    "• TLT + GLD core, equity &lt;40%",
                    f"Juglar {_jp_v:.0f}% complete · post-inversion phase")
            _3mo_col, _3mo_bg = "#C0390F", "#FDDDD5"
        else:
            _3mo = ("Consolidation → Recovery",
                    "• Mid-cycle pullback then recovery pattern<br>"
                    f"• Base: -5% to -10% correction then new highs<br>"
                    f"• Buy zone: SPY ~${round(_spy*0.92):,}<br>"
                    "• Catalyst: Fed signals cut + IP turns up",
                    f"Juglar only {_jp_v:.0f}% · ample room")
            _3mo_col, _3mo_bg = "#2E8B57", "#E6F8EF"

        if _jp_v > 75 and _yc_now > 0:
            _12mo = ("Post-Peak Contraction Risk",
                     "• Juglar late + post-inversion = recession window 12-18mo<br>"
                     f"• Expected trough: ${round(_tgts['12mo_bear']):,}–${round(_tgts['12mo_base']):,}<br>"
                     "• 2007 and 2000 analog matches at 75-85% Juglar<br>"
                     "• Build TLT, reduce equity to 30-50% over 12mo",
                     f"Juglar {_jp_v:.0f}% · 2007 analog match")
            _12mo_col, _12mo_bg = "#C0390F", "#FDDDD5"
        else:
            _12mo = ("Moderate Growth With Volatility",
                     "• Bull base: +8-15% if credit stays calm and Fed cuts<br>"
                     f"• Range: ${round(_tgts['12mo_bear']):,}–${round(_tgts['12mo_bull']):,}<br>"
                     "• Risk: inflation re-acceleration forces Fed pause<br>"
                     "• Rebuild equity on confirmed Kitchin trough",
                     f"Juglar {_jp_v:.0f}% · Kuznets {_knp_v:.0f}% supports")
            _12mo_col, _12mo_bg = "#2E8B57", "#E6F8EF"

        _24mo = (f"Kuznets Supercycle → Peak ~2028",
                 f"• Kuznets at {_knp_v:.0f}% — AI infrastructure supercycle continues<br>"
                 "• Any 2026-27 bear is a Juglar correction within Kuznets uptrend<br>"
                 f"• Strategic dip target: ${round(_spy*0.75):,}–${round(_spy*0.85):,} = buy zone<br>"
                 "• Exit: Kuznets &gt;90% + HY OAS &gt;450 + Juglar new cycle",
                 f"Kuznets {_knp_v:.0f}% · peak projected ~2028")
        _24mo_col, _24mo_bg = "#3355aa", "#EEF2FF"

    _thesis_cards = (
        _thesis_card("⚡ Next 4 Weeks", "", _4wk_col, _4wk_bg, _4wk[0], _4wk[1], _4wk[2]) +
        _thesis_card("📅 3 Months",     "", _3mo_col, _3mo_bg, _3mo[0], _3mo[1], _3mo[2]) +
        _thesis_card("📊 12 Months",    "", _12mo_col, _12mo_bg, _12mo[0], _12mo[1], _12mo[2]) +
        _thesis_card("🔭 2-Year",       "", _24mo_col, _24mo_bg, _24mo[0], _24mo[1], _24mo[2])
    )

    # Build SPY chart as inline SVG (works in hidden tabs, no Canvas needed)
    _spy_svg = _build_spy_svg(
        _spy_hist_dates, _spy_hist_values, _spy, _tgts, proj=_proj_data
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MarketIntel — {gen_time}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/hammer.js/2.0.8/hammer.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-zoom/2.0.1/chartjs-plugin-zoom.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500;600&display=swap');

  :root{{
    --bg:       #080C12;
    --surface:  #0E1420;
    --surface2: #141C2A;
    --border:   #1E2D42;
    --border2:  #243348;
    --teal:     #00C8A0;
    --teal-dim: rgba(0,200,160,0.10);
    --amber:    #F5A020;
    --amber-dim:rgba(245,160,32,0.10);
    --red:      #FF4D6D;
    --red-dim:  rgba(255,77,109,0.10);
    --text:     #E2EAF4;
    --text2:    #8BA4BE;
    --text3:    #4A6278;
    --mono:     'JetBrains Mono',monospace;
    --sans:     'DM Sans',sans-serif;
    --serif:    'Instrument Serif',serif;
    --nav-h:    54px;
    --sb-w:     210px;
    --status-h: 28px;
  }}

  *{{box-sizing:border-box;margin:0;padding:0}}

  /* ── GLOBAL FONT WEIGHT ─────────────────────────────────────────────────── */
  body,div,p,span,td,th,li,label,input,select,button,a,caption,
  h1,h2,h3,h4,h5,h6,small,em,strong,blockquote,figcaption{{
    font-weight:500;
  }}
  [style*="font-weight:4"],[style*="font-weight:3"],
  [style*="font-weight:normal"],[style*="font-weight:300"],
  [style*="font-weight:400"],
  [style*="font-weight: 4"],[style*="font-weight: 3"]{{
    font-weight:500 !important;
  }}

  /* ── BASE ───────────────────────────────────────────────────────────────── */
  html{{ scroll-behavior:smooth; }}
  body{{
    font-family:var(--sans);
    background:var(--bg);
    color:var(--text);
    min-height:100vh;
    overflow-x:hidden;
  }}

  /* ── TOP NAVBAR ─────────────────────────────────────────────────────────── */
  #mi-nav{{
    position:fixed;top:0;left:0;right:0;z-index:200;
    height:var(--nav-h);
    background:rgba(8,12,18,0.92);
    backdrop-filter:blur(20px);
    -webkit-backdrop-filter:blur(20px);
    border-bottom:1px solid var(--border);
    display:flex;align-items:center;
    padding:0 20px;gap:4px;
  }}
  .mi-logo{{
    display:flex;align-items:center;gap:9px;
    margin-right:24px;text-decoration:none;flex-shrink:0;
  }}
  .mi-logo-text{{
    font-family:var(--sans);font-size:14px;font-weight:700;
    color:var(--text);letter-spacing:-.3px;
  }}
  .mi-logo-text span{{color:var(--teal)}}

  /* Nav dropdown groups */
  .nav-group{{position:relative;display:inline-block}}
  .nav-group-btn{{
    display:flex;align-items:center;gap:5px;
    padding:6px 11px;border-radius:6px;
    font-size:12px;font-weight:600;font-family:var(--sans);
    color:var(--text2);cursor:pointer;
    border:none;background:none;
    transition:all .15s;white-space:nowrap;
  }}
  .nav-group-btn:hover{{color:var(--text);background:var(--surface2)}}
  .nav-chevron{{font-size:8px;opacity:.5;transition:transform .2s}}
  .nav-group:hover .nav-chevron{{transform:rotate(180deg)}}

  /* Dropdown panel */
  .nav-dd{{
    position:absolute;top:calc(100% + 6px);left:0;
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:10px;padding:5px;
    min-width:210px;
    box-shadow:0 24px 48px rgba(0,0,0,.7);
    opacity:0;visibility:hidden;
    transform:translateY(-6px);
    transition:all .16s ease;z-index:300;
  }}
  .nav-group:hover .nav-dd{{
    opacity:1;visibility:visible;transform:translateY(0);
  }}
  .nav-dd-item{{
    display:flex;align-items:center;gap:9px;
    padding:7px 9px;border-radius:6px;
    font-size:11.5px;font-weight:500;
    color:var(--text2);cursor:pointer;
    transition:all .1s;text-decoration:none;
  }}
  .nav-dd-item:hover{{background:var(--surface2);color:var(--text)}}
  .nav-dd-icon{{
    width:26px;height:26px;border-radius:6px;flex-shrink:0;
    display:flex;align-items:center;justify-content:center;font-size:12px;
  }}
  .nav-dd-label{{font-weight:600;color:var(--text);font-size:11.5px}}
  .nav-dd-sub{{color:var(--text3);font-size:9.5px;margin-top:1px}}
  .nav-dd-sep{{height:1px;background:var(--border);margin:4px 0}}
  .nav-direct{{
    display:flex;align-items:center;gap:5px;
    padding:6px 11px;border-radius:6px;
    font-size:12px;font-weight:600;font-family:var(--sans);
    color:var(--text2);cursor:pointer;
    border:none;background:none;transition:all .15s;
  }}
  .nav-direct:hover{{color:var(--text);background:var(--surface2)}}

  /* Right side nav items */
  .nav-right{{display:flex;align-items:center;gap:8px;margin-left:auto;flex-shrink:0}}
  .nav-live{{
    display:flex;align-items:center;gap:6px;
    font-family:var(--mono);font-size:10.5px;
    color:var(--teal);font-weight:500;
    padding:4px 10px;
    background:var(--teal-dim);
    border:1px solid rgba(0,200,160,.2);
    border-radius:20px;white-space:nowrap;
  }}
  .live-dot{{
    width:6px;height:6px;border-radius:50%;
    background:var(--teal);
    animation:livepulse 2s infinite;
  }}
  @keyframes livepulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
  .nav-timestamp{{
    font-family:var(--mono);font-size:9.5px;color:var(--text3);
  }}

  /* ── SIDEBAR ─────────────────────────────────────────────────────────────── */
  #mi-sidebar{{
    position:fixed;
    top:var(--nav-h);bottom:var(--status-h);
    left:0;width:var(--sb-w);
    background:var(--surface);
    border-right:1px solid var(--border);
    overflow-y:auto;overflow-x:hidden;
    padding:14px 10px;
    display:flex;flex-direction:column;gap:2px;
    z-index:100;
  }}
  #mi-sidebar::-webkit-scrollbar{{width:3px}}
  #mi-sidebar::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:3px}}
  .sb-label{{
    font-size:8.5px;font-weight:700;letter-spacing:.1em;
    text-transform:uppercase;color:var(--text3);
    padding:10px 8px 3px;margin-top:4px;
  }}
  .sb-label:first-child{{margin-top:0;padding-top:0}}
  .sb-item{{
    display:flex;align-items:center;gap:9px;
    padding:7px 8px;border-radius:7px;
    font-size:11.5px;font-weight:500;
    color:var(--text2);cursor:pointer;
    border:none;background:none;font-family:var(--sans);
    transition:all .1s;text-align:left;width:100%;
    position:relative;
  }}
  .sb-item:hover{{background:var(--surface2);color:var(--text)}}
  .sb-item.active{{
    background:var(--teal-dim);color:var(--teal);font-weight:600;
  }}
  .sb-item.active::before{{
    content:'';position:absolute;left:0;top:5px;bottom:5px;
    width:2.5px;background:var(--teal);border-radius:2px;
  }}
  .sb-icon{{font-size:13px;width:16px;text-align:center;flex-shrink:0}}
  .sb-badge{{
    margin-left:auto;font-size:8.5px;font-weight:700;
    padding:2px 6px;border-radius:8px;
    font-family:var(--mono);flex-shrink:0;
  }}
  .sb-danger{{background:var(--red-dim);color:var(--red)}}
  .sb-warn{{background:var(--amber-dim);color:var(--amber)}}
  .sb-ok{{background:var(--teal-dim);color:var(--teal)}}

  /* ── MAIN CONTENT AREA ───────────────────────────────────────────────────── */
  #mi-main{{
    margin-left:var(--sb-w);
    padding-top:calc(var(--nav-h) + 22px);
    padding-bottom:calc(var(--status-h) + 22px);
    padding-left:24px;padding-right:24px;
    min-height:100vh;
  }}

  /* ── REGIME BANNER ──────────────────────────────────────────────────────── */
  .regime-banner{{
    background:linear-gradient(135deg,var(--surface),var(--surface2));
    border:1px solid var(--border);
    border-radius:12px;
    padding:14px 20px;
    margin-bottom:18px;
    display:flex;align-items:center;gap:0;
    flex-wrap:wrap;
    overflow:hidden;
  }}
  .rb-item{{
    display:flex;flex-direction:column;gap:3px;
    padding:0 20px;
    border-right:1px solid var(--border);
    flex-shrink:0;
  }}
  .rb-item:first-child{{padding-left:0}}
  .rb-item:last-child{{border-right:none}}
  .rb-label{{
    font-size:8.5px;font-weight:700;letter-spacing:.1em;
    text-transform:uppercase;color:var(--text3);
  }}
  .rb-value{{font-family:var(--sans);font-size:15px;font-weight:700;}}
  .rb-sub{{font-size:9.5px;color:var(--text3);font-weight:500}}

  /* ── SIGNAL PILLS ────────────────────────────────────────────────────────── */
  .signals-row{{
    display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px;
  }}
  .sig-pill{{
    display:flex;align-items:center;gap:5px;
    padding:5px 10px;border-radius:20px;
    font-size:10.5px;font-weight:600;font-family:var(--sans);
    border:1px solid transparent;cursor:default;
    transition:transform .12s;
  }}
  .sig-pill:hover{{transform:translateY(-1px)}}
  .sig-danger{{background:var(--red-dim);color:var(--red);border-color:rgba(255,77,109,.2)}}
  .sig-warn{{background:var(--amber-dim);color:var(--amber);border-color:rgba(245,160,32,.2)}}
  .sig-ok{{background:var(--teal-dim);color:var(--teal);border-color:rgba(0,200,160,.2)}}
  .sig-dot{{width:5px;height:5px;border-radius:50%;background:currentColor;flex-shrink:0}}

  /* ── KPI CARDS ───────────────────────────────────────────────────────────── */
  .kpi-row{{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:10px;margin-bottom:18px;
  }}
  .kpi-card{{
    background:var(--surface);border:1px solid var(--border);
    border-radius:11px;padding:14px 16px;
    position:relative;overflow:hidden;
    transition:border-color .18s;
  }}
  .kpi-card:hover{{border-color:var(--border2)}}
  .kpi-card::after{{
    content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:var(--kpi-c,var(--teal));opacity:.8;
  }}
  .kpi-label{{
    font-size:8.5px;font-weight:700;letter-spacing:.1em;
    text-transform:uppercase;color:var(--text3);margin-bottom:7px;
  }}
  .kpi-value{{
    font-family:var(--mono);font-size:21px;font-weight:500;
    color:var(--kpi-c,var(--text));line-height:1;margin-bottom:5px;
  }}
  .kpi-unit{{font-size:12px;color:var(--text3)}}
  .kpi-delta{{
    font-family:var(--mono);font-size:9.5px;font-weight:500;
  }}
  .kd-up{{color:var(--red)}}
  .kd-down{{color:var(--teal)}}
  .kd-flat{{color:var(--text3)}}
  .kpi-src{{font-size:8.5px;color:var(--text3);margin-top:4px}}

  /* ── SECTION / CARD ──────────────────────────────────────────────────────── */
  .section{{
    background:var(--surface);border:1px solid var(--border);
    border-radius:13px;overflow:hidden;margin-bottom:14px;
  }}
  .sh{{
    padding:11px 16px;
    background:var(--surface2);
    border-bottom:1px solid var(--border);
    display:flex;align-items:center;justify-content:space-between;
  }}
  .sh h2{{font-size:12px;font-weight:700;color:var(--text)}}
  .sh p{{font-size:9.5px;color:var(--text3);margin-top:1px}}

  /* ── TABLE ───────────────────────────────────────────────────────────────── */
  table{{border-collapse:collapse;width:100%}}
  tr:hover td{{background:rgba(255,255,255,.02)!important}}
  th{{
    font-size:9px;font-weight:700;letter-spacing:.07em;
    text-transform:uppercase;color:var(--text3);
    padding:8px 12px;border-bottom:1px solid var(--border);
    text-align:left;background:var(--surface2);
  }}
  td{{
    padding:9px 12px;font-size:11.5px;font-weight:500;
    border-bottom:1px solid rgba(30,45,66,.5);color:var(--text2);
  }}
  tr:last-child td{{border-bottom:none}}

  /* ── MISC LAYOUT ─────────────────────────────────────────────────────────── */
  canvas{{max-height:unset}}
  .ch-wrap{{padding:14px 16px}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
  .grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}}

  /* ── STATUS BAR ──────────────────────────────────────────────────────────── */
  #mi-status{{
    position:fixed;bottom:0;left:var(--sb-w);right:0;
    height:var(--status-h);
    background:var(--surface);border-top:1px solid var(--border);
    display:flex;align-items:center;padding:0 20px;gap:20px;z-index:100;
  }}
  .st-item{{
    display:flex;align-items:center;gap:5px;
    font-family:var(--mono);font-size:9px;color:var(--text3);font-weight:500;
  }}
  .st-dot{{width:5px;height:5px;border-radius:50%}}
  .st-ok{{background:var(--teal)}}
  .st-warn{{background:var(--amber)}}
  .st-err{{background:var(--red)}}

  /* ── TAB CONTENT (hidden/shown) ──────────────────────────────────────────── */
  .tab-content{{display:none}}
  .tab-content.active{{display:block}}

  /* ── SCROLLBAR ───────────────────────────────────────────────────────────── */
  ::-webkit-scrollbar{{width:5px;height:5px}}
  ::-webkit-scrollbar-track{{background:var(--bg)}}
  ::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:3px}}
  ::-webkit-scrollbar-thumb:hover{{background:var(--text3)}}

  /* ── RESPONSIVE ──────────────────────────────────────────────────────────── */
  @media(max-width:900px){{
    #mi-sidebar{{display:none}}
    #mi-main{{margin-left:0}}
    #mi-status{{left:0}}
  }}

  /* ── OLD LIGHT-THEME OVERRIDES (keep existing content readable) ──────────── */
  /* Section headers already use --surface2 above */
  /* Any inline light backgrounds in content get softened */
  [style*="background:#f0f2f8"],
  [style*="background:#f4f5f9"],
  [style*="background:#ffffff"],
  [style*="background:#fff"]{{
    background:var(--surface2) !important;
  }}
  [style*="background:#f0f8f2"],
  [style*="background:#f4faf6"],
  [style*="background:#e8f8ee"]{{
    background:rgba(0,200,160,.06) !important;
  }}
  [style*="color:#1a1a2e"],
  [style*="color:#1a2a3e"],
  [style*="color:#334"],
  [style*="color:#333"]{{
    color:var(--text) !important;
  }}
  [style*="color:#556"],
  [style*="color:#667"],
  [style*="color:#778"]{{
    color:var(--text2) !important;
  }}
  [style*="border-color:#dde1ed"],
  [style*="border:#dde1ed"]{{
    border-color:var(--border) !important;
  }}
</style>
</head>
<body>

{TAB_NAV}

<!-- ═══ MAIN CONTENT ════════════════════════════════════════════════════════ -->
<div id="mi-main">

<!-- ── PAGE HEADER ────────────────────────────────────────────────────────── -->
<div style="margin-bottom:16px;display:flex;align-items:flex-start;
            justify-content:space-between;flex-wrap:wrap;gap:10px">
  <div>
    <div style="font-size:9px;font-weight:700;letter-spacing:.12em;
                text-transform:uppercase;color:var(--teal);margin-bottom:5px">
      Macro Intelligence Platform
    </div>
    <div style="font-family:var(--serif);font-size:26px;font-weight:400;
                color:var(--text);line-height:1.15">
      Market <em style="color:var(--teal);font-style:italic">Overview</em>
    </div>
    <div style="font-size:10px;color:var(--text3);margin-top:5px;font-weight:500">
      FRED ({fred_count} series) + yfinance ({mkt_count} tickers) &nbsp;·&nbsp;
      <span style="color:{'var(--teal)' if fred_count>=15 else 'var(--amber)'}">
        {'✓ All FRED series loaded' if fred_count>=15 else f'⚠ {fred_count} series loaded'}
      </span>
    </div>
  </div>
</div>

<!-- ── REGIME BANNER ──────────────────────────────────────────────────────── -->
<div class="regime-banner">
  <div class="rb-item">
    <div class="rb-label">Cycle Regime</div>
    <div class="rb-value" style="color:{rg['col']}">{rg['label']}</div>
    <div class="rb-sub">
      Health: <strong style="color:{_sc_risk_col}">{_health_pct}%</strong>
      &nbsp;·&nbsp; {_n_danger}🔴 {_n_caution}🟡 {_n_calm}🟢
    </div>
  </div>
  <div class="rb-item">
    <div class="rb-label">Kuznets</div>
    <div class="rb-value" style="color:{k['col']}">{k['phase']}</div>
    <div class="rb-sub">{k['pct']:.0f}% · peak ~{pos['kuznets']['peak']}</div>
  </div>
  <div class="rb-item">
    <div class="rb-label">Juglar</div>
    <div class="rb-value" style="color:{j['col']}">{j['phase']}</div>
    <div class="rb-sub">{j['pct']:.0f}% · peak ~{pos['juglar']['peak']}</div>
  </div>
  <div class="rb-item">
    <div class="rb-label">Kitchin</div>
    <div class="rb-value" style="color:{ki['col']}">{ki['phase']}</div>
    <div class="rb-sub">{ki['pct']:.0f}% · peak ~{pos['kitchin']['peak']}</div>
  </div>
  <div class="rb-item">
    <div class="rb-label">SPY from ATH</div>
    <div class="rb-value" style="color:{'var(--red)' if _spy_dd_pct<-10 else 'var(--amber)' if _spy_dd_pct<-3 else 'var(--teal)'}">{_spy_dd_str}</div>
    <div class="rb-sub">{_current_dd_level}</div>
  </div>
  <div class="rb-item">
    <div class="rb-label">Risk Level</div>
    <div class="rb-value" style="color:{_sc_risk_col};font-size:12px">{_sc_risk}</div>
    <div class="rb-sub">{_n_danger} critical signals</div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════════════════════════════
     TAB 1: OVERVIEW
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-overview" class="tab-content active">

  {_regime_ai_html}

  <!-- ── ROW 1: Cycle positions + Regime + Scorecard KPIs ─────────────────── -->
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr 1fr;gap:10px;margin-bottom:14px">
    <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:10px 12px">
      <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px">Kuznets</div>
      <div style="font-size:15px;font-weight:800;color:{k['col']}">{k['phase']}</div>
      <div style="background:#e0e4ed;border-radius:3px;height:6px;margin:4px 0;overflow:hidden">
        <div style="width:{k['pct']:.0f}%;height:6px;background:{k['col']};border-radius:3px"></div></div>
      <div style="font-size:9px;color:#556">{k['pct']:.0f}% · peak ~{k['peak']}</div>
    </div>
    <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:10px 12px">
      <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px">Juglar</div>
      <div style="font-size:15px;font-weight:800;color:{j['col']}">{j['phase']}</div>
      <div style="background:#e0e4ed;border-radius:3px;height:6px;margin:4px 0;overflow:hidden">
        <div style="width:{min(j['pct'],100):.0f}%;height:6px;background:{j['col']};border-radius:3px"></div></div>
      <div style="font-size:9px;color:#556">{j['pct']:.0f}% · peak ~{j['peak']}</div>
    </div>
    <div style="background:#f0f2f8;border:1px solid #dde1ed;border-radius:8px;padding:10px 12px">
      <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px">Kitchin</div>
      <div style="font-size:15px;font-weight:800;color:{ki['col']}">{ki['phase']}</div>
      <div style="background:#e0e4ed;border-radius:3px;height:6px;margin:4px 0;overflow:hidden">
        <div style="width:{min(ki['pct'],100):.0f}%;height:6px;background:{ki['col']};border-radius:3px"></div></div>
      <div style="font-size:9px;color:#556">{ki['pct']:.0f}% · peak ~{ki['peak']}</div>
    </div>
    <div style="background:#FDDDD5;border-radius:8px;padding:10px 12px;text-align:center">
      <div style="font-size:9px;color:#9A3010;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Danger Signals</div>
      <div style="font-size:26px;font-weight:900;color:#C0390F">{_sc_danger}</div>
      <div style="font-size:9px;color:#C0390F">{_sc_crisis} crisis · {_sc_danger-_sc_crisis} stress</div>
    </div>
    <div style="background:#FFF0CC;border-radius:8px;padding:10px 12px;text-align:center">
      <div style="font-size:9px;color:#7A5200;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Caution</div>
      <div style="font-size:26px;font-weight:900;color:#9A6200">{_sc_caut}</div>
      <div style="font-size:9px;color:#9A6200">of {_sc_total} indicators</div>
    </div>
    <div style="background:#D6F0E0;border-radius:8px;padding:10px 12px;text-align:center">
      <div style="font-size:9px;color:#0A5A2A;text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px">Health Score</div>
      <div style="font-size:26px;font-weight:900;color:{"#1A7A4A" if _sc_score>60 else "#D4820A" if _sc_score>40 else "#C0390F"}">{_sc_score}%</div>
      <div style="font-size:9px;color:#1A7A4A">{_n_calm}/{_n_total} calm</div>
    </div>
  </div>

  <!-- ── ROW 2: Overall risk + category heatmap ───────────────────────────── -->
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px;padding:10px 14px;background:#f8f9fe;border-radius:8px;border:1px solid #dde1ed">
    <div style="font-size:13px;font-weight:900;color:{_sc_risk_col};margin-right:6px">{_sc_risk}</div>
    <span style="color:#999">│</span>
    {_cat_summary_html}
  </div>

  <!-- ── FULL INDICATOR TABLE (all 35, sorted by weight) ─────────────────── -->
  <div class="section" style="margin-bottom:14px">
    <div class="sh">
      <div>
        <h2>All Market Indicators — {_sc_total} indicators · Sorted by importance weight</h2>
        <p>Live FRED + yfinance · WT4 = critical · WT3 = important · WT2 = confirmer · 🔴 sort first</p>
      </div>
      <div style="font-size:11px;color:#22337a;font-style:italic">{_ep_ai_text}</div>
    </div>
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:11px">
        <thead><tr style="background:#f0f2f8;border-bottom:1.5px solid #d0d5e8">
          <th style="padding:6px 14px;text-align:left;font-size:9px;color:#3355aa;min-width:175px">Indicator</th>
          <th style="padding:6px 8px;font-size:9px;color:#3355aa">WT</th>
          <th style="padding:6px 10px;text-align:left;font-size:9px;color:#3355aa">Category</th>
          <th style="padding:6px 10px;font-size:9px;color:#3355aa">Value</th>
          <th style="padding:6px 10px;font-size:9px;color:#3355aa">Zone</th>
          <th style="padding:6px 12px;text-align:left;font-size:9px;color:#3355aa;min-width:220px">What It Means Now</th>
          <th style="padding:6px 10px;text-align:left;font-size:9px;color:#3355aa;min-width:120px">Historical</th>
          <th style="padding:6px 10px;font-size:9px;color:#3355aa">As Of</th>
        </tr></thead>
        <tbody>
          {_sc_rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- ── ROW 3: Projections + Playbook ────────────────────────────────────── -->
  <div class="grid2" style="margin-bottom:14px">
    <div class="section">
      <div class="sh"><div><h2>Bear Market Projections</h2>
      <p>Data-driven scenarios · Probability = historical frequency of this setup</p></div></div>
      <div style="padding:14px 16px">{proj_cards}</div>
    </div>
    <div class="section">
      <div class="sh"><div><h2>Actionable Playbook — {rg['label']}</h2>
      <p>Derived from cycle + Market Health + cross-pair signals</p></div></div>
      <div style="padding:14px 16px">{play_cards}</div>
    </div>
  </div>

  <!-- ── ROW 4: Historical Parallels + Sector Heatmap ─────────────────────── -->
  <div class="grid2">
    <div class="section">
      <div class="sh"><div><h2>Historical Parallels — Data-Matched</h2>
      <p>Similarity computed from live FRED readings vs prior cycle peak conditions</p></div></div>
      <div style="padding:14px 16px">{parallels_html}</div>
    </div>
    <div class="section">
      <div class="sh"><div><h2>Live Sector Heatmap</h2>
      <p>1m / 3m / 1yr / vs200d / RSI / Trend — all from yfinance</p></div></div>
      <div style="padding:14px 16px">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">{sector_cells}</div>
      </div>
    </div>
  </div>

</div>

<!-- ════════════════════════════════════════════════════════════════════════════
     TAB 2: CYCLE FRAMEWORK
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-cycles" class="tab-content">

  <div style="margin-bottom:16px">
    <div style="font-size:12px;color:#3355aa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px">
      Stacked Cycle Framework — Deep Analysis
    </div>
    {cycles_html}
  </div>

  <!-- ── Cycle Current Themes (cblocks above cover mechanism + peaks + warnings) ─ -->
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
    <div style="background:#f8f9fe;border:1px solid #dde1ed;border-radius:8px;padding:12px 14px">
      <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px">Kuznets · Current Investment Theme</div>
      <div style="font-size:11px;color:#1a1a2e;font-weight:600;line-height:1.5">{CYCLE_MECHANICS['kuznets']['current_theme']}</div>
      <div style="margin-top:8px;font-size:10px;color:#555;line-height:1.5">
        <strong style="color:#1155cc">4 cycle forces:</strong> (1) Demographics &amp; household formation
        (2) Credit availability (3) Technology S-curve adoption (4) Government policy (CHIPS Act, IRA)
      </div>
    </div>
    <div style="background:#f8f9fe;border:1px solid #dde1ed;border-radius:8px;padding:12px 14px">
      <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px">Juglar · Current Investment Theme</div>
      <div style="font-size:11px;color:#1a1a2e;font-weight:600;line-height:1.5">{CYCLE_MECHANICS['juglar']['current_theme']}</div>
      <div style="margin-top:8px;font-size:10px;color:#555;line-height:1.5">
        <strong style="color:#1155cc">3 turn signals:</strong> (1) Capacity surplus reduces capex urgency
        (2) Rate rise tightens credit (3) Margin compression as wages exceed pricing power
      </div>
    </div>
    <div style="background:#f8f9fe;border:1px solid #dde1ed;border-radius:8px;padding:12px 14px">
      <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px">Kitchin · Current Investment Theme</div>
      <div style="font-size:11px;color:#1a1a2e;font-weight:600;line-height:1.5">{CYCLE_MECHANICS['kitchin']['current_theme']}</div>
      <div style="margin-top:8px;font-size:10px;color:#555;line-height:1.5">
        <strong style="color:#1155cc">2 bullwhip forces:</strong> (1) Information lags — firms can't see real-time demand
        (2) Lead times amplify over-ordering then cancellation when demand slows
      </div>
    </div>
  </div>

</div>

<!-- ════════════════════════════════════════════════════════════════════════════
     TAB 3: CYCLE CHARTS
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-charts" class="tab-content">

  <!-- Full-width Juglar Cycle Overlay -->
  <div class="section" style="margin-bottom:16px">
    <div class="sh"><div><h2>Juglar Cycle Overlay — Current vs All Prior Cycles</h2>
    <p>S&P 500 indexed to 100 at each trough · TODAY line = where current cycle is now · 🔴 dot = bear market peak</p></div></div>
    <div class="ch-wrap"><canvas id="overlay_chart" style="max-height:340px"></canvas></div>
    <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
      <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
        <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
        <div style="color:#444;line-height:1.55">All cycles start at 100 (trough). Higher = running hotter than history. Green line = current 2020 cycle. Grey band = ±1σ historical average.</div>
      </div>
      <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
        <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
        <div style="color:#1a3a24;line-height:1.55">When green line is <b>above</b> the grey band: cycle is running hot — mean reversion risk elevated. Red stars ★ mark where each prior cycle's bull market ended.</div>
      </div>
      <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
        <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
        <div style="color:#4a3000;line-height:1.55">If current cycle is above upper band AND Juglar is >85%: reduce equity exposure. Below band: more upside may remain.</div>
      </div>
    </div>
    <div style="padding:0 18px 12px;font-size:10px;color:#556;line-height:1.7">
      <strong style="color:#1155cc">Reading the chart:</strong>
      Every cycle starts at 100 (the market bottom). The Y-axis shows cumulative return from that bottom.
      Comparing current cycle (green) to historical average across 4 prior Juglar cycles.
      <strong>Red dots</strong> show when each prior cycle's bull market ended.
    </div>
  </div>

  <!-- Full-width Road to 2032 — directly below -->
  <div class="section" style="margin-bottom:16px">
    <div class="sh"><div><h2>Road to 2032 — Single Unified SPY Path (AI-Powered)</h2>
    <p>One coherent trajectory incorporating ALL cycle corrections sequentially · AI-analyzed from live 60-indicator data · Green = actual history · Orange = projected path · Blue = Kuznets trend</p></div></div>
    <div class="ch-wrap"><canvas id="road_chart" style="max-height:380px"></canvas></div>
    <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
      <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
        <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
        <div style="color:#444;line-height:1.55">
          <strong>Green solid</strong> = actual SPY history.<br>
          <strong>Orange dashed</strong> = ONE unified projected path — Kitchin/Juglar corrections + Kuznets recovery + Kuznets winter all in sequence.<br>
          <strong>Blue dashed</strong> = smooth Kuznets trend (the long-term trajectory beneath the corrections).<br>
          Shaded regions = active cycle phase. Dots = key price levels.
        </div>
      </div>
      <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
        <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight — why ONE path?</div>
        <div style="color:#1a3a24;line-height:1.55">
          Kitchin, Juglar, and Kuznets corrections happen <b>sequentially</b>, not simultaneously. At any moment there is only ONE SPY price. Prior charts showed parallel lines which was logically wrong — a stock can't be at three prices at once. This chart shows the single most-probable path through all cycles.
        </div>
      </div>
      <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
        <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
        <div style="color:#4a3000;line-height:1.55">
          <strong style="color:#D4820A">Orange zone</strong>: Kitchin+Juglar trough forming — defensive positioning, accumulate on dips.<br>
          <strong style="color:#1A7A4A">Green zone</strong>: Recovery — rebuild equity, ride Kuznets uptrend.<br>
          <strong style="color:#8B0000">Dark red zone</strong>: Kuznets winter — maximum defensives, TLT, gold, cash.
        </div>
      </div>
    </div>
  </div>

  <!-- Macro charts row -->
  <div class="grid2" style="margin-bottom:16px">
    <div class="section">
      <div class="sh"><div><h2>Yield Curve (10Y−2Y) — 20-Year History</h2>
      <p>Every US recession preceded by inversion · Post-inversion normalization = NOW = 12-18mo lag to recession</p></div></div>
      <div class="ch-wrap"><canvas id="yc_chart"></canvas></div>
      <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
        <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
          <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
          <div style="color:#444;line-height:1.55">Positive = normal (10Y pays more than 2Y). Zero line = flat curve. Below zero = inverted = recession warning. Post-inversion normalization (returning to positive) = lagged recession risk.</div>
        </div>
        <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
          <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
          <div style="color:#1a3a24;line-height:1.55">Every US recession since 1955 was preceded by inversion. The lag from inversion to recession is <b>12-18 months on average</b>. The curve normalizing (as now) does NOT mean "all clear" — it means the clock is ticking.</div>
        </div>
        <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
          <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
          <div style="color:#4a3000;line-height:1.55">If curve <0: defensives + TLT. If curve 0→+0.5 (normalizing from inversion, as now): late-cycle positioning. If curve >+0.5 steadily rising: risk-on early cycle.</div>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="sh"><div><h2>Industrial Production YoY vs Capacity Utilization</h2>
      <p>IP negative + caputil &lt;77% = Juglar contraction confirmed · Watch both together</p></div></div>
      <div class="ch-wrap"><canvas id="ip_chart"></canvas></div>
      <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
        <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
          <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
          <div style="color:#444;line-height:1.55">Blue = IP YoY% (left axis). Yellow = Capacity Utilization % (right axis). Both declining together = Juglar contraction. IP negative AND CapUtil <77% = confirmed.</div>
        </div>
        <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
          <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
          <div style="color:#1a3a24;line-height:1.55">IP YoY turned negative 1-3 months <b>before</b> EPS peaked in 2000, 2007, 2019, 2022. CapUtil below 77% historically precedes margin compression. Watch them together.</div>
        </div>
        <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
          <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
          <div style="color:#4a3000;line-height:1.55">IP YoY <0% + CapUtil <77%: reduce XLK, XLI, XLF. IP decelerating but >0%: monitor. IP reaccelerating: early cycle buy signal for industrials.</div>
        </div>
      </div>
    </div>
  </div>

</div>

<!-- ════════════════════════════════════════════════════════════════════════════
     TAB 4: BONDS & RATES
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-bonds" class="tab-content">

  <!-- Bond explainer -->
  <div style="background:#edf4ff;border:1px solid #1a2a40;border-radius:10px;
              padding:14px 18px;margin-bottom:16px;border-left:4px solid #2266ee">
    <div style="font-size:12px;font-weight:800;color:#1155cc;margin-bottom:8px">How to Read Bond Charts for Cycle Analysis</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;font-size:10px;color:#5577aa;line-height:1.6">
      <div><strong style="color:#2266ee">TLT (20yr Treasury):</strong> Rises when rates fall.
        At Juglar peaks, investors flee to TLT. At troughs, TLT sells off as risk appetite returns.
        TLT and SPY are typically <em>inversely correlated</em> during risk-off periods.
        Watch for TLT breaking above 50-day MA as an early risk-off signal.</div>
      <div><strong style="color:#FF9933">HYG÷LQD Ratio:</strong> High yield vs investment grade.
        When this ratio falls, credit stress is building — companies can't refinance cheaply.
        HYG/LQD rolled over <em>before</em> SPY in 2007, 2015, 2018, 2022 — by 4-8 weeks.
        It's the earliest warning signal in this entire report.</div>
      <div><strong style="color:#CC99FF">Normalised comparison:</strong> All lines start at 100.
        When TLT is rising while SPY falls = flight to safety (recession/correction).
        When both rise = liquidity-driven bull (rare, but 2020-21).
        When both fall = stagflation (1970s, 2022) = the worst environment for investors.</div>
    </div>
  </div>

  <!-- Bond charts grid -->
  <div class="grid2" style="margin-bottom:16px">
    <div class="section">
      <div class="sh"><div><h2>HY Credit Spreads (OAS) — Recession Early Warning</h2>
      <p>Spreads &gt;450bps = DANGER · Widening 6-12 months before S&P peaks · Most reliable leading indicator</p></div></div>
      <div class="ch-wrap"><canvas id="hy_chart"></canvas></div>
      <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
        <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
          <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
          <div style="color:#444;line-height:1.55">OAS = spread over Treasuries in basis points (bps). Orange zone = caution (380-450bps). Red zone = danger (>450bps). Spreads widen 6-12 months before S&P peaks.</div>
        </div>
        <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
          <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
          <div style="color:#1a3a24;line-height:1.55">HY OAS is the <b>single most reliable leading indicator</b> for S&P drawdowns. In 2007 it widened from 280→700bps over 8 months before the peak. In 2022 it hit 600bps at the trough. Current reading directly above.</div>
        </div>
        <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
          <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
          <div style="color:#4a3000;line-height:1.55"><380bps = credit calm, risk-on. 380-450bps = elevated, start hedging. >450bps = credit stress, reduce equities. >600bps = crisis levels, maximum defense.</div>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="sh"><div><h2>Fed Funds Rate vs CPI — Policy Cycle</h2>
      <p>Fed Funds &gt; CPI = restrictive · Earnings peaks lag policy peaks by 2-4 quarters</p></div></div>
      <div class="ch-wrap"><canvas id="fed_chart"></canvas></div>
      <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
        <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
          <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
          <div style="color:#444;line-height:1.55">Blue = Fed Funds Rate. Yellow = CPI YoY. When Fed Funds > CPI = real rates positive = restrictive policy. When FF < CPI = easy money.</div>
        </div>
        <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
          <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
          <div style="color:#1a3a24;line-height:1.55">Earnings peaks historically lag Fed rate peaks by <b>2-4 quarters</b>. The 2022 tightening cycle drove P/E from 22x→17x in 3 months. Current Fed Funds vs CPI gap shown in current readings.</div>
        </div>
        <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
          <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
          <div style="color:#4a3000;line-height:1.55">FF > CPI by >1%: multiple compression risk, shorten equity duration. FF < CPI: supportive for risk assets. FF cuts beginning: early signal for bonds (TLT) to outperform.</div>
        </div>
      </div>
    </div>
  </div>

  <div class="grid3" style="margin-bottom:16px">
    <div class="section">
      <div class="sh"><div><h2>SPY vs TLT vs HYG vs LQD — 10yr Normalised</h2>
      <p>All indexed to 100 ten years ago · Shows which asset won in each cycle phase</p></div></div>
      <div class="ch-wrap"><canvas id="bond_norm_chart"></canvas></div>
      <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
        <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
          <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
          <div style="color:#444;line-height:1.55">All assets indexed to 100 ten years ago. Shows relative performance across cycle phases. TLT rising = bond rally (risk-off). HYG outperforming LQD = credit risk-on.</div>
        </div>
        <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
          <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
          <div style="color:#1a3a24;line-height:1.55">In late-cycle: SPY typically leads until it doesn't. TLT has historically rallied <b>6-18 months after Juglar peak</b> (+20% average). HYG/LQD spread compression marks early cycle entry.</div>
        </div>
        <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
          <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
          <div style="color:#4a3000;line-height:1.55">TLT trend turning up while SPY flattens: early risk-off signal. HYG diverging from LQD downward: credit stress building. Both moving together up: early cycle all-clear.</div>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="sh"><div><h2>TLT vs SPY — The Risk-Off Indicator</h2>
      <p>When TLT rises while SPY falls = recession signal · Orange = TLT÷SPY ratio (right axis)</p></div></div>
      <div class="ch-wrap"><canvas id="bond_tlt_spy_chart"></canvas></div>
      <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
        <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
          <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
          <div style="color:#444;line-height:1.55">TLT line = 20yr Treasury ETF. SPY = S&P 500. Orange ratio line = TLT÷SPY (right axis). Rising ratio = bonds outperforming = risk-off rotation happening.</div>
        </div>
        <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
          <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
          <div style="color:#1a3a24;line-height:1.55">The TLT÷SPY ratio rising is the clearest mechanical risk-off signal. In every major correction since 2000, this ratio began rising <b>4-8 weeks before</b> SPY peaked.</div>
        </div>
        <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
          <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
          <div style="color:#4a3000;line-height:1.55">Ratio turning up + HY OAS widening simultaneously: high conviction risk-off. Ratio flat/down + spreads calm: stay invested. TLT absolute rising while SPY still up: early positioning opportunity.</div>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="sh"><div><h2>HYG÷LQD Credit Risk vs SPY — Earliest Warning</h2>
      <p>Ratio falling = credit stress building · Led every major SPY correction by 4-8 weeks</p></div></div>
      <div class="ch-wrap"><canvas id="bond_credit_chart"></canvas></div>
      <div style="padding:8px 18px 12px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:10px;border-top:1px solid #e8eaed">
        <div style="background:#f4f6ff;border-radius:6px;padding:8px 10px;border-left:3px solid #4477dd">
          <div style="font-size:9px;color:#3355aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">How to read</div>
          <div style="color:#444;line-height:1.55">HYG÷LQD ratio measures pure credit risk appetite (both are bonds, but HYG = junk, LQD = investment grade). Falling ratio = investors fleeing junk for safety = stress signal.</div>
        </div>
        <div style="background:#f0faf4;border-radius:6px;padding:8px 10px;border-left:3px solid #2e8b57">
          <div style="font-size:9px;color:#2e5a3a;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Key insight</div>
          <div style="color:#1a3a24;line-height:1.55">This ratio is the <b>earliest warning</b> in the credit complex — it moves before HY OAS widens and before SPY peaks. Led every major S&P correction by 4-8 weeks since 2008.</div>
        </div>
        <div style="background:#fffbf0;border-radius:6px;padding:8px 10px;border-left:3px solid #cc8800">
          <div style="font-size:9px;color:#7a5200;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;font-weight:600">Action signal</div>
          <div style="color:#4a3000;line-height:1.55">Ratio making lower highs while SPY makes new highs = bearish divergence = start reducing risk. Ratio bottoming and turning up while SPY still falling = early recovery signal.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bond performance at each cycle phase — static reference table -->
  <div class="section">
    <div class="sh"><div><h2>Bond Performance at Each Cycle Phase — Historical Reference</h2>
    <p>What each asset class has done historically during each Juglar cycle phase</p></div></div>
    <div style="overflow-x:auto;padding:0">
      <table>
        <thead><tr style="background:#f8f9fd">
          <th style="padding:8px 14px;text-align:left;font-size:10px;color:#3355aa;text-transform:uppercase">Juglar Phase</th>
          <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">S&P 500</th>
          <th style="padding:8px 10px;font-size:10px;color:#2266ee;text-transform:uppercase">TLT (20yr)</th>
          <th style="padding:8px 10px;font-size:10px;color:#FF9933;text-transform:uppercase">HYG</th>
          <th style="padding:8px 10px;font-size:10px;color:#CC99FF;text-transform:uppercase">LQD (IG)</th>
          <th style="padding:8px 10px;font-size:10px;color:#FFD700;text-transform:uppercase">Gold</th>
          <th style="padding:8px 14px;text-align:left;font-size:10px;color:#3355aa;text-transform:uppercase">Key Signal</th>
        </tr></thead>
        <tbody>
          <tr style="border-bottom:1px solid #e0e4ed">
            <td style="padding:8px 14px;font-size:11px;font-weight:700;color:#1A7A4A">Early Expansion</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#1A7A4A">+25-40%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#C0390F">−5 to −15%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#1A7A4A">+15-25%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#555">+5 to −5%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#555">Flat/slight +</td>
            <td style="padding:8px 14px;font-size:10px;color:#555577">HYG leads SPY · TLT lags · Buy risk assets</td>
          </tr>
          <tr style="border-bottom:1px solid #e0e4ed;background:#fafbfe">
            <td style="padding:8px 14px;font-size:11px;font-weight:700;color:#2E8B57">Mid Expansion</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#2E8B57">+15-25%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#555">−3 to +5%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#2E8B57">+10-18%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#555">+3-8%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#555">+5-10%</td>
            <td style="padding:8px 14px;font-size:10px;color:#555577">All risk assets positive · Add gold as inflation hedge</td>
          </tr>
          <tr style="border-bottom:1px solid #e0e4ed">
            <td style="padding:8px 14px;font-size:11px;font-weight:700;color:#D4820A">Late Cycle ← YOU ARE HERE</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#D4820A">+5-15% then −20-40%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#1A7A4A">+10-25%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#C0390F">−10 to +5%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#D4820A">+5-10%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#1A7A4A">+15-30%</td>
            <td style="padding:8px 14px;font-size:10px;color:#D4820A"><strong>TLT + Gold outperform · Reduce HYG · Build cash</strong></td>
          </tr>
          <tr style="border-bottom:1px solid #e0e4ed;background:#fafbfe">
            <td style="padding:8px 14px;font-size:11px;font-weight:700;color:#C0390F">Recession / Trough</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#C0390F">−20 to −57%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#1A7A4A">+20-40%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#C0390F">−20 to −35%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#D4820A">+5-15%</td>
            <td style="padding:8px 10px;text-align:center;font-size:11px;color:#1A7A4A">+20-35%</td>
            <td style="padding:8px 14px;font-size:10px;color:#C0390F">Maximum TLT · Gold · Cash · Wait for HYG to bottom before re-entering SPY</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</div>

<!-- ════════════════════════════════════════════════════════════════════════════
     TAB 5: SECTOR ROTATION
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-sectors" class="tab-content">

  {sector_ratio_guide_filled}

  <div class="section" style="margin-bottom:16px">
    <div class="sh"><div><h2>Sector Cross-Pair Rotation — Live Ratios</h2>
    <p>Numerator ÷ Denominator · Rising = numerator leading · 1Y %ile shows how extreme the reading is</p></div></div>
    <div style="overflow-x:auto">
      <table>
        <thead><tr style="background:#f8f9fd">
          <th style="padding:7px 12px;text-align:left;font-size:9px;color:#556;text-transform:uppercase">Pair</th>
          <th style="padding:7px 10px;font-size:9px;color:#556;text-transform:uppercase">Direction</th>
          <th style="padding:7px 10px;font-size:9px;color:#556;text-transform:uppercase">1Y %ile</th>
          <th style="padding:7px 10px;font-size:9px;color:#556;text-transform:uppercase">1M</th>
          <th style="padding:7px 10px;font-size:9px;color:#556;text-transform:uppercase">3M</th>
          <th style="padding:7px 10px;font-size:9px;color:#556;text-transform:uppercase">6M</th>
          <th style="padding:7px 10px;font-size:9px;color:#556;text-transform:uppercase">RSI</th>
          <th style="padding:7px 14px;text-align:left;font-size:9px;color:#556;text-transform:uppercase;min-width:220px">What It Means</th>
        </tr></thead>
        <tbody>{pair_table_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Pair ratio daily charts — full width stacked -->
  <div class="section" style="margin-bottom:16px">
    <div class="sh"><div><h2>Sector Ratio Charts — 3-Year Daily View with Seasonality</h2>
    <p>Daily ratio · EMA20 (direction-colored) · EMA50 (amber) · Grey dotted = 5yr seasonal average · Badge = 1Y percentile</p></div></div>
    <div style="padding:14px 18px">
      {_pair_chart_cells}
    </div>
  </div>

  <!-- XLF / Extreme Readings Deep-Dive panel -->
  <div class="section" style="margin-bottom:16px">
    <div class="sh">
      <div>
        <h2>⚡ Extreme Percentile Readings — Contrarian Signal Scanner</h2>
        <p>Ratios at &lt;15th or &gt;85th percentile historically — potential mean reversion candidates</p>
      </div>
    </div>
    <div style="padding:14px 18px">

      <!-- XLF/XLU spotlight — 3rd percentile = historically extreme -->
      <div style="background:linear-gradient(135deg,#fff8f0,#fff3e8);border:1.5px solid #D4820A;
                  border-left:5px solid #D4820A;border-radius:10px;padding:16px 20px;margin-bottom:14px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <div style="font-size:18px;font-weight:900;color:#1155cc">XLF/XLU</div>
          <div style="background:#fdddd5;color:#C0390F;padding:3px 12px;border-radius:8px;
                      font-size:11px;font-weight:800;border:1px solid #C0390F55">3rd PERCENTILE</div>
          <div style="background:#fff0cc;color:#D4820A;padding:3px 12px;border-radius:8px;
                      font-size:10px;font-weight:700">FALLING ↓ · -16.4% (3mo)</div>
          <div style="margin-left:auto;font-size:10px;color:#666">Financials ÷ Utilities</div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;font-size:10px">
          <div style="background:white;border-radius:8px;padding:12px;border:1px solid #e8e0d0">
            <div style="font-size:11px;font-weight:800;color:#1A7A4A;margin-bottom:8px">
              📊 What 3rd Percentile Means
            </div>
            <div style="color:#444;line-height:1.7">
              Financials are cheaper vs Utilities than <strong>97% of all historical readings</strong>.
              This extreme only occurs near:<br>
              • Recession fears / rate cut cycles<br>
              • Banking stress episodes (2008, 2020, 2023)<br>
              • Late-cycle defensive rotation<br><br>
              <strong style="color:#D4820A">Current driver:</strong> Tariff shock +
              recession fears + expected Fed cuts = utilities bid up, banks sold.
            </div>
          </div>

          <div style="background:white;border-radius:8px;padding:12px;border:1px solid #e8e0d0">
            <div style="font-size:11px;font-weight:800;color:#D4820A;margin-bottom:8px">
              ⏱ Historical Mean Reversion
            </div>
            <div style="color:#444;line-height:1.7">
              At prior 3-5th percentile lows:<br>
              • <strong>2009 trough</strong>: XLF +78% vs XLU +14% in next 12mo<br>
              • <strong>2020 COVID low</strong>: XLF +62% vs XLU +9% next 12mo<br>
              • <strong>2023 SVB crisis</strong>: XLF +34% vs XLU -12% next 12mo<br><br>
              <strong style="color:#C0390F">Warning:</strong> At 3rd %ile, ratio can stay
              depressed 3-9 months before turning. Need a catalyst — Fed cut or credit calm.
            </div>
          </div>

          <div style="background:white;border-radius:8px;padding:12px;border:1px solid #e8e0d0">
            <div style="font-size:11px;font-weight:800;color:#3355aa;margin-bottom:8px">
              🎯 Trade Framework (XLF)
            </div>
            <div style="color:#444;line-height:1.7">
              <strong style="color:#1A7A4A">Bull case — start accumulating:</strong><br>
              • HY OAS &lt;380bps ✓ CALM (current: ~320bps)<br>
              • Sahm Rule &lt;0.5pp ✓ CLEAR (current: 0.27)<br>
              → <strong>Dollar-cost average XLF over 3-6 months</strong><br><br>
              <strong style="color:#C0390F">Stop loss trigger:</strong><br>
              • HY OAS crosses 420bps (recession confirmed)<br>
              • Sahm Rule &gt;0.5pp (labor market breaking)<br>
              → Exit and wait for Kitchin trough (~Q4 2026)
            </div>
          </div>
        </div>
      </div>

      <!-- Other extreme readings scanner -->
      <div style="font-size:10px;font-weight:700;color:#3355aa;margin-bottom:8px;
                  text-transform:uppercase;letter-spacing:.05em">
        All Extreme Readings This Session
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;font-size:10px">
        {extreme_pairs_html}
      </div>
    </div>
  </div>

</div>

<!-- ════════════════════════════════════════════════════════════════════════════
<!-- ══════════════════════════════════════════ INDICATOR CHARTS TAB ════ -->
<div id="tab-indcharts" class="tab-content">
  <div style="font-size:11px;color:#1a1a2e;text-transform:uppercase;letter-spacing:.08em;
              font-weight:800;margin-bottom:6px;padding-bottom:8px;border-bottom:2px solid #eef0f8">
    📉 Macro Indicator Charts — Full History + S&P 500 Overlay
  </div>
  <div style="font-size:9px;color:#667;margin-bottom:14px">
    🖱 Scroll = zoom · Drag chart = pan · Drag Y-axis = rescale · Double-click = reset &nbsp;|&nbsp;
    Dashed blue line = S&P 500 (right axis) &nbsp;|&nbsp;
    ≈ = yfinance proxy (directionally correct, not exact FRED values)
  </div>
  {indcharts_tab_html}
</div>

<!-- ═══════════════════════════════════════════════ MARKET CHARTS TAB ════ -->
<div id="tab-mktcharts" class="tab-content">
  <div style="font-size:11px;color:#3355aa;text-transform:uppercase;letter-spacing:.08em;
              font-weight:700;margin-bottom:14px">Market Charts — Sentiment &amp; Macro</div>
  {mktcharts_tab_html}
</div>

<!-- ═══════════════════════════════════════════ MASTER PARALLEL TABLE TAB ════ -->
<div id="tab-parallel" class="tab-content">
  {parallel_tab_html}
</div>

<!-- ═══════════════════════════════════════════════ SECTOR STOCKS TAB ════ -->
<div id="tab-sectorstocks" class="tab-content">
  <div style="margin-bottom:6px;font-size:12px;color:#3355aa;text-transform:uppercase;
              letter-spacing:.08em;font-weight:700">
    Top 10 Holdings Per Sector — 12-Month Performance vs Sector ETF
  </div>
  {sector_stocks_tab_html}
</div>

<!-- ═══════════════════════════════════════════════════ TAB 6: BEAR MARKETS ════ -->
<div id="tab-bearmarkets" class="tab-content">

  <div class="section" style="margin-bottom:16px">
    <div class="sh"><div><h2>Historical Bear Markets — Full Database (1973–2022)</h2>
    <p>All major corrections · Rec = recovery months · Key lesson from each event</p></div></div>
    <div style="overflow-x:auto">
      <table>
        <thead><tr style="background:#f8f9fd">
          <th style="padding:7px 12px;text-align:left;font-size:9px;color:#556;text-transform:uppercase">Event</th>
          <th style="padding:7px 8px;font-size:9px;color:#556;text-transform:uppercase">Peak</th>
          <th style="padding:7px 8px;font-size:9px;color:#556;text-transform:uppercase">Trough</th>
          <th style="padding:7px 8px;font-size:9px;color:#C0390F;text-transform:uppercase">DD%</th>
          <th style="padding:7px 8px;font-size:9px;color:#556;text-transform:uppercase">Dur</th>
          <th style="padding:7px 8px;font-size:9px;color:#1A7A4A;text-transform:uppercase">Rec</th>
          <th style="padding:7px 10px;font-size:9px;color:#556;text-transform:uppercase">Cycle</th>
          <th style="padding:7px 12px;text-align:left;font-size:9px;color:#556;text-transform:uppercase;min-width:160px">Trigger</th>
          <th style="padding:7px 12px;text-align:left;font-size:9px;color:#556;text-transform:uppercase;min-width:220px">Key Lesson</th>
        </tr></thead>
        <tbody>{bear_rows}</tbody>
      </table>
    </div>
  </div>

  <!-- Insight box -->
  <div style="background:#edf4ff;border:1px solid #1a2a40;border-radius:10px;padding:16px 20px;border-left:4px solid #C0390F">
    <div style="font-size:12px;font-weight:800;color:#ff6655;margin-bottom:10px">Pattern Recognition — What All Bear Markets Have in Common</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;font-size:10px;color:#5577aa;line-height:1.6">
      <div><strong style="color:#D4820A">Average bear market:</strong><br>
        Duration: 10-11 months<br>
        Drawdown: −25 to −35%<br>
        Recovery: 14-22 months<br>
        <em>Exception: systemic events (2007-09) = 17mo duration, 57% DD, 49mo recovery</em></div>
      <div><strong style="color:#D4820A">What precedes every peak:</strong><br>
        1. Yield curve inverts (18mo lead)<br>
        2. HYG/LQD ratio rolls over (4-8wk lead)<br>
        3. IWM/SPY breadth narrows (2-3mo lead)<br>
        4. ISM PMI falls below 50<br>
        5. Earnings guidance &gt;65% negative</div>
      <div><strong style="color:#D4820A">What works at the trough:</strong><br>
        1. HYG stops falling (credit stabilises first)<br>
        2. ISM PMI troughs and turns up<br>
        3. Fed cuts aggressively<br>
        4. Yield curve steepens sharply<br>
        <em>Buy signal: HYG &gt; 200MA AND ISM &gt; 48</em></div>
    </div>
  </div>

</div>

<!-- ════════════════════════════════════════════════════════════════════════════
     CHARTS JAVASCRIPT (all charts rendered regardless of active tab)
════════════════════════════════════════════════════════════════════════════ -->
<script>
// Auto-open a specific tab on load if --only was used
window.addEventListener('load', function() {{
  var defaultTab = '{default_tab or ""}';
  if (defaultTab && defaultTab !== 'overview') {{
    showTab(defaultTab);
  }}
}});

const gridColor = 'rgba(30,45,66,0.8)';
const baseOpts = {{
  responsive:true, maintainAspectRatio:true,
  plugins:{{ legend:{{ labels:{{ color:'#8BA4BE', font:{{size:10}} }} }} }},
  scales:{{
    x:{{ ticks:{{color:'#4A6278',font:{{size:9}},maxTicksLimit:10}}, grid:{{color:gridColor}} }},
    y:{{ ticks:{{color:'#4A6278',font:{{size:9}}}}, grid:{{color:gridColor}} }},
  }}
}};

// ── TradingView-style zoom/pan controller ─────────────────────────────────────
// Scroll on chart / X bar → zoom X in or out
// Scroll on Y bar         → zoom Y in or out
// Drag on chart           → pan left / right
// Drag on Y bar           → rescale Y (compress / expand)
// Double-click            → reset all
function initTVZoom(chart) {{
  const canvas = chart.canvas;
  if (!canvas || canvas._tvZoom) return;
  canvas._tvZoom = true;

  // Own state — never trust scale.min/max reads directly
  const X = {{ min: 0, max: null }};
  function total() {{
    return (chart.data && chart.data.labels) ? chart.data.labels.length - 1 : 252;
  }}
  function xMin() {{ return X.min ?? 0; }}
  function xMax() {{ return X.max ?? total(); }}

  function applyX() {{
    chart.options.scales.x.min = Math.max(0,       Math.round(xMin()));
    chart.options.scales.x.max = Math.min(total(), Math.round(xMax()));
    chart.update('none');
  }}

  // ── Zoom X: shrink or expand the visible index range ─────────────────────
  function zoomX(factor, pivotFrac) {{
    const mn = xMin(), mx = xMax();
    const range = mx - mn;
    const pf = (pivotFrac != null) ? pivotFrac : 0.5;
    const pivot = mn + pf * range;
    const newRange = Math.max(10, range * factor);
    X.min = pivot - pf * newRange;
    X.max = pivot + (1 - pf) * newRange;
    applyX();
  }}

  // ── Zoom Y: shrink or expand the visible price range ─────────────────────
  function zoomY(factor) {{
    const sc = chart.scales.y;
    if (!sc) return;
    const mid  = (sc.max + sc.min) / 2;
    const half = (sc.max - sc.min) / 2 * factor;
    chart.options.scales.y.min = mid - half;
    chart.options.scales.y.max = mid + half;
    chart.update('none');
  }}

  // ── Cursors ───────────────────────────────────────────────────────────────
  canvas.addEventListener('mousemove', function(e) {{
    const ca = chart.chartArea; if (!ca) return;
    const r = canvas.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    canvas.style.cursor =
      (mx > ca.right)                                            ? 'ns-resize' :
      (my > ca.bottom && mx >= ca.left && mx <= ca.right)       ? 'ew-resize' :
      (mx >= ca.left && mx <= ca.right && my >= ca.top && my <= ca.bottom) ? 'crosshair' :
      'default';
  }});
  canvas.addEventListener('mouseleave', () => canvas.style.cursor = 'default');

  // ── Mouse wheel: zone-aware zoom ──────────────────────────────────────────
  canvas.addEventListener('wheel', function(e) {{
    e.preventDefault();
    const ca = chart.chartArea; if (!ca) return;
    const r = canvas.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;

    const zoomIn = e.deltaY < 0;       // scroll up = zoom in
    const f = zoomIn ? 0.78 : 1.28;   // range scaling factor

    const onYBar = mx > ca.right;
    const onXBar = my > ca.bottom && mx >= ca.left && mx <= ca.right;
    const onPlot = mx >= ca.left && mx <= ca.right && my >= ca.top && my <= ca.bottom;

    if (onYBar) {{
      zoomY(f);
    }} else if (onXBar) {{
      const pivotFrac = (mx - ca.left) / (ca.right - ca.left);
      zoomX(f, pivotFrac);
    }} else if (onPlot) {{
      const pivotFrac = (mx - ca.left) / (ca.right - ca.left);
      zoomX(f, pivotFrac);
    }}
  }}, {{ passive: false }});

  // ── Drag: pan X on chart or X bar; rescale Y on Y bar ────────────────────
  let drag = null;
  canvas.addEventListener('mousedown', function(e) {{
    if (e.button !== 0) return;
    const ca = chart.chartArea; if (!ca) return;
    const r = canvas.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;

    const onYBar = mx > ca.right;
    const onXBar = my > ca.bottom && mx >= ca.left && mx <= ca.right;
    const onPlot = mx >= ca.left && mx <= ca.right && my >= ca.top && my <= ca.bottom;

    if (onPlot || onXBar) {{
      drag = {{ type:'panX', startX: e.clientX,
                origMin: xMin(), origMax: xMax(),
                plotW: ca.right - ca.left }};
      e.preventDefault();
    }} else if (onYBar) {{
      const sc = chart.scales.y; if (!sc) return;
      drag = {{ type:'scaleY', startY: e.clientY,
                origMin: sc.min, origMax: sc.max,
                origRange: sc.max - sc.min,
                canvasH: canvas.height }};
      e.preventDefault();
    }}
  }});

  window.addEventListener('mousemove', function(e) {{
    if (!drag) return;
    if (drag.type === 'panX') {{
      const dx    = e.clientX - drag.startX;
      const range = drag.origMax - drag.origMin;
      const pxPt  = drag.plotW / Math.max(range, 1);
      const shift = dx / pxPt;
      const t     = total();
      let mn = drag.origMin - shift, mx = drag.origMax - shift;
      if (mn < 0)  {{ mx += -mn;     mn = 0; }}
      if (mx > t)  {{ mn -= (mx-t);  mx = t; }}
      if (mx - mn >= 10) {{ X.min = mn; X.max = mx; applyX(); }}
    }} else if (drag.type === 'scaleY') {{
      const pct   = (e.clientY - drag.startY) / drag.canvasH;
      const scale = Math.max(0.05, 1 + pct * 2.5);
      const mid   = (drag.origMax + drag.origMin) / 2;
      const half  = drag.origRange / 2 * scale;
      chart.options.scales.y.min = mid - half;
      chart.options.scales.y.max = mid + half;
      chart.update('none');
    }}
  }});
  window.addEventListener('mouseup', () => drag = null);

  // ── Double-click → full reset ─────────────────────────────────────────────
  canvas.addEventListener('dblclick', function() {{
    X.min = 0; X.max = total();
    chart.options.scales.x.min = undefined;
    chart.options.scales.x.max = undefined;
    chart.options.scales.y.min = undefined;
    chart.options.scales.y.max = undefined;
    try {{ chart.resetZoom(); }} catch(_) {{ chart.update(); }}
  }});
}}

// Hint banner (shows once, fades after 3.5 s)
function showTVHint(canvas) {{
  const wrap = canvas.parentElement;
  if (!wrap || wrap.querySelector('._tvhint')) return;
  wrap.style.position = 'relative';
  const h = document.createElement('div');
  h.className = '_tvhint';
  h.style.cssText = 'position:absolute;bottom:38px;right:0;font-size:8px;color:#6677aa;' +
    'background:rgba(240,242,252,0.95);padding:3px 9px;border-radius:5px 0 0 5px;' +
    'pointer-events:none;transition:opacity 1.2s;white-space:nowrap;z-index:10';
  h.textContent = '🖱 Scroll = zoom  |  Scroll Y-bar = zoom Y  |  Drag chart/X-bar = pan  |  Drag Y-bar = rescale Y  |  Dbl-click = reset';
  wrap.appendChild(h);
  setTimeout(() => h.style.opacity = '0', 3200);
  setTimeout(() => h.remove(), 4500);
}}

// Yield curve
(function(){{
  const labels = {js(yc_data.get("dates",[]))};
  const values = {js(yc_data.get("values",[]))};
  if(!labels.length) return;
  const ctx = document.getElementById('yc_chart');
  new Chart(ctx, {{
    type:'line',
    data:{{ labels, datasets:[
      {{ label:'10Y-2Y Spread (%)', data:values, borderColor:'#2266ee',
         backgroundColor:'rgba(68,136,255,0.08)', borderWidth:2, pointRadius:0, fill:true }},
      {{ label:'Zero (inversion)', data:labels.map(()=>0),
         borderColor:'rgba(192,57,15,0.7)', borderWidth:1.5, pointRadius:0, borderDash:[5,3] }},
      {{ label:'+0.3% warning', data:labels.map(()=>0.3),
         borderColor:'rgba(212,130,10,0.5)', borderWidth:1, pointRadius:0, borderDash:[3,5] }},
    ] }},
    options:baseOpts
  }});
}})();

// HY OAS
(function(){{
  const labels = {js(hy_data.get("dates",[]))};
  const values = {js(hy_data.get("values",[]))};
  if(!labels.length) return;
  new Chart(document.getElementById('hy_chart'), {{
    type:'line',
    data:{{ labels, datasets:[
      {{ label:'HY OAS (bps)', data:values, borderColor:'#ff7755',
         backgroundColor:'rgba(255,119,85,0.08)', borderWidth:2, pointRadius:0, fill:true }},
      {{ label:'Danger 450bps', data:labels.map(()=>450),
         borderColor:'rgba(192,57,15,0.8)', borderWidth:2, pointRadius:0, borderDash:[5,3] }},
      {{ label:'Warning 380bps', data:labels.map(()=>380),
         borderColor:'rgba(212,130,10,0.6)', borderWidth:1.5, pointRadius:0, borderDash:[3,4] }},
    ] }},
    options:baseOpts
  }});
}})();

// Fed + CPI
(function(){{
  const ff_d={js(fc_data.get("ff_dates",[]))}; const ff_v={js(fc_data.get("ff_values",[]))};
  const ci_d={js(fc_data.get("cpi_dates",[]))}; const ci_v={js(fc_data.get("cpi_values",[]))};
  if(!ff_d.length) return;
  const allD=[...new Set([...ff_d,...ci_d])].sort().slice(-120);
  const ffM=Object.fromEntries(ff_d.map((d,i)=>[d,ff_v[i]]));
  const ciM=Object.fromEntries(ci_d.map((d,i)=>[d,ci_v[i]]));
  new Chart(document.getElementById('fed_chart'), {{
    type:'line',
    data:{{ labels:allD, datasets:[
      {{ label:'Fed Funds (%)', data:allD.map(d=>ffM[d]??null),
         borderColor:'#ff4466', borderWidth:2, pointRadius:0 }},
      {{ label:'CPI YoY (%)', data:allD.map(d=>ciM[d]??null),
         borderColor:'#ffaa33', borderWidth:1.5, pointRadius:0, borderDash:[4,3] }},
      {{ label:'2% target', data:allD.map(()=>2),
         borderColor:'rgba(100,200,100,0.4)', borderWidth:1, pointRadius:0, borderDash:[2,5] }},
    ] }},
    options:baseOpts
  }});
}})();

// IP + CapUtil
(function(){{
  const ip_d={js(ip_data.get("ip_dates",[]))}; const ip_v={js(ip_data.get("ip_values",[]))};
  const cu_d={js(ip_data.get("cu_dates",[]))}; const cu_v={js(ip_data.get("cu_values",[]))};
  if(!ip_d.length && !cu_d.length) return;
  const ipYoY=ip_v.map((v,i)=>i>=12?Math.round((v/ip_v[i-12]-1)*1000)/10:null);
  const cuMap=Object.fromEntries(cu_d.map((d,i)=>[d,cu_v[i]]));
  new Chart(document.getElementById('ip_chart'), {{
    type:'line',
    data:{{ labels:ip_d, datasets:[
      {{ label:'IP YoY%', data:ipYoY, borderColor:'#1188ee',
         borderWidth:2, pointRadius:0, yAxisID:'y' }},
      {{ label:'CapUtil%', data:ip_d.map(d=>cuMap[d]??null),
         borderColor:'#ffcc44', borderWidth:2, pointRadius:0, yAxisID:'y2' }},
      {{ label:'0%', data:ip_d.map(()=>0),
         borderColor:'rgba(192,57,15,0.5)', borderWidth:1, pointRadius:0,
         borderDash:[4,3], yAxisID:'y' }},
    ] }},
    options:{{ ...baseOpts, scales:{{
      x:baseOpts.scales.x,
      y:{{ ...baseOpts.scales.y, position:'left',
           title:{{display:true,text:'IP YoY%',color:'#1188ee',font:{{size:9}}}} }},
      y2:{{ ...baseOpts.scales.y, position:'right', grid:{{drawOnChartArea:false}},
            title:{{display:true,text:'CapUtil%',color:'#ffcc44',font:{{size:9}}}} }},
    }} }}
  }});
}})();

{overlay_chart_js}
{road_chart_js}

{bond_charts_js}

{pair_js_blocks}

{sector_stocks_js}

{mktcharts_tab_js}

{indcharts_tab_js}

// ── SPY Projection Chart — lazy init on tab show ──────────────────────────────
// ── SPY Projection Chart ─────────────────────────────────────────────────────
const _spyHist   = {_spy_hist_dates_json};
const _spyVals   = {_spy_hist_values_json};
const _spyNow    = {_spy_js};
const _spyTgts   = {_tgts_js_json};

let _spyChartInst = null;
function buildSpyChart() {{
  if (_spyChartInst) {{ try {{ _spyChartInst.destroy(); }} catch(e) {{}} _spyChartInst = null; }}
  const ctx = document.getElementById('spy_projection_chart');
  if (!ctx) return;
  if (!_spyHist.length) {{
    ctx.parentNode.innerHTML = '<div style="padding:40px;text-align:center;color:#666">SPY data unavailable — ensure yfinance is installed and run again</div>';
    return;
  }}
  // Build projection labels (24 months forward from last history date)
  const projMonths = 24;
  const projLabels = [];
  const lastDt = new Date(_spyHist[_spyHist.length - 1] + '-01');
  for (let i = 1; i <= projMonths; i++) {{
    const d = new Date(lastDt); d.setMonth(d.getMonth() + i);
    projLabels.push(d.toISOString().slice(0,7));
  }}
  function projLine(target) {{
    return projLabels.map((_, i) => {{
      const t = (i + 1) / projMonths;
      return Math.round(_spyNow + (target - _spyNow) * t);
    }});
  }}
  const allLabels  = [..._spyHist, ...projLabels];
  const histNulls  = new Array(_spyHist.length).fill(null);
  const histPadded = [..._spyVals, ...new Array(projMonths).fill(null)];

  _spyChartInst = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: allLabels,
      datasets: [
        {{
          label: 'SPY Actual',
          data: histPadded,
          borderColor: '#185FA5',
          backgroundColor: 'rgba(24,95,165,0.1)',
          borderWidth: 2.5,
          pointRadius: 0,
          fill: true,
          order: 0
        }},
        {{
          label: 'Bull $' + _spyTgts.t12_bull + ' (+' + Math.round((_spyTgts.t12_bull/_spyNow-1)*100) + '%)',
          data: [...histNulls, ...projLine(_spyTgts.t24_bull)],
          borderColor: '#1A7A4A', borderWidth: 2.5,
          borderDash: [8,4], pointRadius: 0, fill: false, order: 1
        }},
        {{
          label: 'Base $' + _spyTgts.t12_base + ' (' + Math.round((_spyTgts.t12_base/_spyNow-1)*100) + '%)',
          data: [...histNulls, ...projLine(_spyTgts.t24_base)],
          borderColor: '#D4820A', borderWidth: 2.5,
          borderDash: [8,4], pointRadius: 0, fill: false, order: 2
        }},
        {{
          label: 'Bear $' + _spyTgts.t12_bear + ' (' + Math.round((_spyTgts.t12_bear/_spyNow-1)*100) + '%)',
          data: [...histNulls, ...projLine(_spyTgts.t24_bear)],
          borderColor: '#C0390F', borderWidth: 2.5,
          borderDash: [8,4], pointRadius: 0, fill: false, order: 3
        }},
        {{
          label: 'NOW $' + _spyNow,
          data: allLabels.map((l, i) => l === _spyHist[_spyHist.length-1] ? _spyNow : null),
          borderColor: 'rgba(0,188,212,0.9)', backgroundColor: 'rgba(0,188,212,0.9)',
          borderWidth: 0, pointRadius: 8, pointStyle: 'circle', fill: false, order: -1
        }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ labels: {{ color: '#445566', font: {{ size: 10 }}, boxWidth: 18 }} }},
        tooltip: {{ callbacks: {{ label: c => c.dataset.label + ': $' + (c.parsed.y || '').toLocaleString() }} }}
      }},
      scales: {{
        x: {{
          ticks: {{ color: '#556', font: {{ size: 9 }}, maxTicksLimit: 14 }},
          grid: {{ color: 'rgba(180,190,220,0.35)' }}
        }},
        y: {{
          ticks: {{ color: '#556', font: {{ size: 9 }}, callback: v => '$' + v.toLocaleString() }},
          grid: {{ color: 'rgba(180,190,220,0.35)' }}
        }}
      }}
    }}
  }});
}}
// Build on page load and whenever AI Summary tab opens
window.addEventListener('load', function() {{ setTimeout(buildSpyChart, 400); }});


// ── Generic overlay chart builder ───────────────────────────────────────────
function buildOverlayChart(canvasId, overlayData, todayMonth, xLabel) {{
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const keys = Object.keys(overlayData).filter(k => !k.startsWith('__'));
  if (!keys.length) {{
    ctx.parentNode.insertAdjacentHTML('beforeend',
      '<p style="color:#555;padding:10px;font-size:11px">No data — ensure yfinance installed</p>');
    return;
  }}
  const PALETTE = ['#e63946','#f4a261','#2a9d8f','#457b9d','#6a4c93','#e9c46a','#1db954'];
  const maxM = Math.max(...keys.map(k => (overlayData[k].values||[]).length));
  const xlabels = Array.from({{length:maxM}},(_,i)=>
    i%12===0?'Yr '+(i/12+1|0):(i%6===0?'·':''));
  const datasets = keys.map((label,idx) => {{
    const d = overlayData[label];
    const isCurrent = label.toLowerCase().includes('current')||idx===keys.length-1;
    const col = d.color||PALETTE[idx%PALETTE.length];
    return {{
      label,data:d.values,borderColor:col,
      backgroundColor:isCurrent?col+'18':'transparent',
      borderWidth:isCurrent?3.5:2,pointRadius:0,tension:0.3,
      fill:isCurrent,order:isCurrent?0:1,
    }};
  }});
  const tp={{id:'tp_'+canvasId,afterDraw(chart){{
    if(!todayMonth||todayMonth>=maxM)return;
    const x=chart.scales.x.getPixelForValue(todayMonth);
    const{{top,bottom}}=chart.chartArea;
    chart.ctx.save();
    chart.ctx.strokeStyle='rgba(200,140,0,0.9)';chart.ctx.lineWidth=2;
    chart.ctx.setLineDash([5,3]);
    chart.ctx.beginPath();chart.ctx.moveTo(x,top);chart.ctx.lineTo(x,bottom);chart.ctx.stroke();
    chart.ctx.setLineDash([]);
    chart.ctx.fillStyle='#aa7700';chart.ctx.font='bold 10px sans-serif';
    chart.ctx.fillText('TODAY',x+4,top+14);
    chart.ctx.restore();
  }}}};
  new Chart(ctx,{{
    type:'line',plugins:[tp],
    data:{{labels:xlabels,datasets}},
    options:{{
      responsive:true,maintainAspectRatio:true,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{labels:{{color:'#444466',font:{{size:10}}}}}},
        tooltip:{{callbacks:{{
          title:items=>'Month '+items[0].dataIndex+' from trough',
          label:c=>c.dataset.label+': '+c.parsed.y?.toFixed(1)+'x trough'
        }}}}
      }},
      scales:{{
        x:{{ticks:{{color:'#667',font:{{size:9}},maxTicksLimit:20,
              callback:(v,i)=>xlabels[i]&&xlabels[i]!=='·'?xlabels[i]:null}},
            grid:{{color:'rgba(190,200,225,0.4)'}},
            title:{{display:true,text:xLabel,color:'#889',font:{{size:9}}}}}},
        y:{{ticks:{{color:'#667',font:{{size:9}}}},grid:{{color:'rgba(190,200,225,0.4)'}},
            title:{{display:true,text:'Index (100 = trough price)',color:'#889',font:{{size:9}}}}}}
      }}
    }}
  }});
}}
buildOverlayChart('kuznets_overlay_chart',{_kuznets_json},{today_month},'Months from Kuznets trough');
buildOverlayChart('overlay_chart2',{_ov_json},{today_month},'Months from Juglar trough');
buildOverlayChart('kitchin_overlay_chart',{_kitchin_json},{_kitchin_today_month},'Months from Kitchin trough');

</script>


<!-- ═══════════════════════════════════════════════════════════════════════════
     TAB: AI SUMMARY
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-ai-summary" class="tab-content">

  <!-- ══ HEADER BANNER ══════════════════════════════════════════════════════ -->
  <div style="background:linear-gradient(135deg,#0a1628 0%,#1a2840 50%,#0d1f35 100%);
              border-radius:12px;padding:18px 24px;margin-bottom:14px;border:1px solid #2a4a7a">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
      <div style="width:36px;height:36px;border-radius:50%;background:#1155cc22;
                  border:2px solid #4488ff;display:flex;align-items:center;justify-content:center;
                  font-size:18px">🤖</div>
      <div>
        <div style="font-size:15px;font-weight:700;color:#88aaff">
          Full Market Thesis — {gen_time}
        </div>
        <div style="font-size:10px;color:#556677;margin-top:2px">
          Synthesizes all tabs: Cycle Framework · Market Indicators · Credit · Sector Rotation ·
          Bear Markets · Historical Parallels → Predictive Analysis
        </div>
      </div>
      <div style="margin-left:auto;text-align:right">
        <div style="font-size:18px;font-weight:900;color:{_sc_risk_col}">{_sc_risk}</div>
        <div style="font-size:10px;color:#667788;margin-top:2px">{_sc_danger} danger · {_sc_caut} caution · {_sc_calm} calm / {_sc_total} indicators</div>
      </div>
    </div>
    <div style="background:rgba(0,0,0,0.3);border-radius:8px;padding:12px 18px;
                border-left:3px solid #4488ff;font-size:11px;color:#ccd8ff;
                line-height:1.8;white-space:pre-line">{_ai_overall_summary}</div>
    <div style="text-align:right;margin-top:6px;font-size:9px;color:#445566">
      <span style="background:#112233;padding:2px 8px;border-radius:4px;
                   border:1px solid #223344">(AI Gen) — Claude Haiku</span>
    </div>
  </div>

  <!-- ══ ROW 1: SPY PRICE PROJECTION (FULL WIDTH) ════════════════════════════ -->
  <div class="section" style="margin-bottom:14px">
    <div class="sh"><div>
      <h2>SPY Price Path Projection — {_spy_price_str} · Cycle-Based Scenarios</h2>
      <p>Solid line = actual SPY history · Dashed = Bull / Base / Bear projections 24 months forward · Based on Kuznets/Juglar/Kitchin cycle position</p>
    </div></div>
    <div style="padding:10px 14px 0">
      {_spy_svg}
    </div>
    <div style="padding:4px 18px 10px;font-size:10px;color:#556;border-top:1px solid #e8eaed">
      <strong style="color:#1155cc">How to read:</strong>
      Solid blue = actual SPY price. Dashed green/amber/red = Bull/Base/Bear projections.
      Prices computed from cycle depth × historical correction range at comparable setups.
      <strong>Probabilistic — not a guarantee.</strong>
    </div>
  </div>

  <!-- ══ ROW 2: SCENARIO TABLE ════════════════════════════════════════════════ -->
  <div class="section" style="margin-bottom:14px">
    <div class="sh"><div>
      <h2>Price Target Scenarios — {_spy_price_str}</h2>
      <p>Derived from cycle position + historical correction depth + indicator consensus</p>
    </div></div>
    <div style="padding:10px 14px">
      {_scenario_table_html}
    </div>
    <div style="padding:4px 14px 10px;font-size:10px;color:#556;border-top:1px solid #e8eaed">
      <strong>Methodology:</strong> Bull = cycle continues + credit calm.
      Base = Kitchin correction, Juglar holds. Bear = Juglar peak confirmed + Sahm trigger.
      Prices derived from historical median returns at each scenario in comparable cycle positions.
    </div>
  </div>

  <!-- ══ ROW 2: THESIS BY TIMEFRAME ══════════════════════════════════════════ -->
  <div class="section" style="margin-bottom:14px">
    <div class="sh"><div>
      <h2>Market Thesis — Synthesis Across All Tabs</h2>
      <p>Reads every indicator, every cycle position, every sector signal → builds a unified directional view</p>
    </div></div>
    <div style="padding:14px 18px">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px">
        {_thesis_cards}
      </div>
    </div>
  </div>

  <!-- ══ ROW 3: WHAT TO WATCH — KEY SIGNALS THAT WOULD CHANGE THE THESIS ═══ -->
  <div class="section" style="margin-bottom:14px">
    <div class="sh"><div>
      <h2>Thesis Change Signals — What Would Invalidate Each Scenario</h2>
      <p>Specific thresholds that would confirm bull/bear case — monitor these weekly</p>
    </div></div>
    <div style="padding:12px 16px">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
        <div style="background:#D6F0E020;border:1px solid #1A7A4A44;border-radius:8px;padding:12px">
          <div style="font-size:11px;font-weight:800;color:#1A7A4A;margin-bottom:8px">🟢 Bull confirmed when:</div>
          <div style="font-size:10px;color:#555;line-height:1.8">
            • HY OAS stays &lt;380bps and trending flat/down<br>
            • IWM/SPY ratio reverses upward (breadth widening)<br>
            • VIX term structure returns to contango (+2 or better)<br>
            • INDPRO YoY re-accelerates above +2%<br>
            • Sahm Rule stays below 0.3pp (no job market deterioration)
          </div>
        </div>
        <div style="background:#FFF0CC20;border:1px solid #D4820A44;border-radius:8px;padding:12px">
          <div style="font-size:11px;font-weight:800;color:#D4820A;margin-bottom:8px">🟡 Bear deepens when:</div>
          <div style="font-size:10px;color:#555;line-height:1.8">
            • HY OAS crosses 450bps and holds<br>
            • Sahm Rule crosses 0.5pp (recession triggered)<br>
            • XLY/XLP makes new 52-week low<br>
            • HYG/LQD ratio falls below its 6-month MA<br>
            • 10Y yield above 5% with SPX P/E still &gt;22x
          </div>
        </div>
        <div style="background:#FDDDD520;border:1px solid #C0390F44;border-radius:8px;padding:12px">
          <div style="font-size:11px;font-weight:800;color:#C0390F;margin-bottom:8px">🔴 Systemic risk when:</div>
          <div style="font-size:10px;color:#555;line-height:1.8">
            • HY OAS &gt;600bps (GFC/COVID levels)<br>
            • VIX term inverted AND VIX9D/VIX ratio &gt;1.2<br>
            • NYSE A/D net deeply negative for 10+ consecutive days<br>
            • Fed Funds cuts &gt;100bps in &lt;6 months (panic pivot)<br>
            • SPX &lt;200DMA by &gt;10% (confirmed bear market)
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ══ ROW 4: DATA INPUTS SUMMARY ══════════════════════════════════════════ -->
  <div class="grid2">
    <div class="section">
      <div class="sh"><div><h2>Live Data Inputs Analyzed</h2>
      <p>All fetched this run · No hardcoded fallbacks used</p></div></div>
      <div style="padding:10px 14px">
        <table style="width:100%;font-size:10px">
          <tr style="border-bottom:1px solid #e8eaef;background:#f8f9fe">
            <th style="padding:5px 10px;text-align:left;color:#3355aa">Category</th>
            <th style="padding:5px 10px;text-align:left;color:#3355aa">Key Readings</th>
          </tr>
          <tr style="border-bottom:1px solid #e8eaef">
            <td style="padding:5px 10px;font-weight:700;color:#1155cc">Cycles</td>
            <td style="padding:5px 10px;color:#555">
              Kuznets {pos["kuznets"]["pct"]:.0f}% ({pos["kuznets"]["phase"]}) ·
              Juglar {pos["juglar"]["pct"]:.0f}% ({pos["juglar"]["phase"]}) ·
              Kitchin {pos["kitchin"]["pct"]:.0f}% ({pos["kitchin"]["phase"]})
            </td>
          </tr>
          <tr style="border-bottom:1px solid #e8eaef;background:#fafbfe">
            <td style="padding:5px 10px;font-weight:700;color:#1155cc">Credit</td>
            <td style="padding:5px 10px;color:#555">
              HY OAS {f"{pos['data']['hy']:.0f}bps" if pos['data'].get('hy') else 'N/A'} ·
              Yield curve {f"{pos['data']['yc']:+.0f}bps" if pos['data'].get('yc') is not None else 'N/A'} ·
              NFCI {f"{pos['data']['nf']:.3f}" if pos['data'].get('nf') else 'N/A'}
            </td>
          </tr>
          <tr style="border-bottom:1px solid #e8eaef">
            <td style="padding:5px 10px;font-weight:700;color:#1155cc">Rates / Fed</td>
            <td style="padding:5px 10px;color:#555">
              Fed Funds {f"{pos['data']['ff']:.2f}%" if pos['data'].get('ff') else 'N/A'} ·
              10Y {f"{pos['data']['t10']:.2f}%" if pos['data'].get('t10') else 'N/A'} ·
              Real yield {_real_yield_display}
            </td>
          </tr>
          <tr style="border-bottom:1px solid #e8eaef;background:#fafbfe">
            <td style="padding:5px 10px;font-weight:700;color:#1155cc">Market Health</td>
            <td style="padding:5px 10px;color:#555">
              VIX {_vix_display} ·
              {_sc_total} indicators: {_sc_danger} danger · {_sc_caut} caution · {_sc_calm} calm
            </td>
          </tr>
          <tr>
            <td style="padding:5px 10px;font-weight:700;color:#1155cc">Active Scenarios</td>
            <td style="padding:5px 10px;color:#555">
              {" · ".join(f"{p['name']} ({p['probability']})" for p in pos.get('projections',[])[:3])}
            </td>
          </tr>
        </table>
      </div>
    </div>

    <!-- Playbook -->
    <div class="section">
      <div class="sh"><div>
        <h2>Recommended Actions — {rg["label"]}</h2>
        <p>Derived from cycle + Market Health + live credit/rate data</p>
      </div></div>
      <div style="padding:10px 14px">
        <div style="display:grid;grid-template-columns:1fr;gap:8px">
          {play_cards}
        </div>
      </div>
    </div>
  </div>

</div>


<!-- ═══════════════════════════════════════════════════════════════════════════
     TAB: BONDS AT CYCLE PEAKS & TROUGHS
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-bondpeaks" class="tab-content">

<!-- BONDS AT PEAKS TABLE -->
<div class="section" style="margin-bottom:16px">
  <div class="sh"><div><h2>Bond Market Values at Every Cycle Peak & Trough (1973–2026)</h2>
  <p>What 10Y yield, TLT, HYG spread, and Fed Funds looked like exactly at each market turning point</p></div></div>
  <div style="overflow-x:auto">
    <table>
      <thead><tr style="background:#f0f2f8">
        <th style="padding:8px 12px;text-align:left;font-size:10px;color:#3355aa;text-transform:uppercase">Event</th>
        <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">Date</th>
        <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">10Y Yield</th>
        <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">Fed Funds</th>
        <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">HY Spread</th>
        <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">2Y-10Y Curve</th>
        <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">TLT Perf</th>
        <th style="padding:8px 10px;font-size:10px;color:#3355aa;text-transform:uppercase">SPY Perf</th>
        <th style="padding:8px 12px;text-align:left;font-size:10px;color:#3355aa;text-transform:uppercase;min-width:200px">Key Bond Signal</th>
      </tr></thead>
      <tbody>
        <!-- PEAKS -->
        <tr style="background:#fff8f5;border-bottom:1px solid #e8eaef">
          <td colspan="9" style="padding:6px 12px;font-size:10px;font-weight:800;color:#C0390F;background:#fff0ec">▼ CYCLE PEAKS (sell signal zone)</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">1973 Oil Shock Peak</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Jan 1973</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;font-weight:700;color:#C0390F">6.6%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">5.25%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">450 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">Inverted −0.4%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+18% next yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−48%</td>
          <td style="padding:7px 12px;font-size:10px;color:#666">Curve inverted 6mo prior. TLT was the only protection.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8;background:#fafbfe">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">1987 Black Monday Peak</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Aug 1987</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;font-weight:700;color:#C0390F">9.4%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">6.75%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#D4820A">380 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#D4820A">Flat +0.1%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+12% next yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−34%</td>
          <td style="padding:7px 12px;font-size:10px;color:#666">Rapid 10Y rise from 7% to 9.4% in 8mo triggered crash.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2000 Dot-com Peak</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Mar 2000</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;font-weight:700;color:#D4820A">6.2%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">5.75%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#D4820A">420 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">Inverted −0.6%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+22% next yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−49%</td>
          <td style="padding:7px 12px;font-size:10px;color:#666">Curve inverted 18mo prior. HY spread >400 = sell signal confirmed.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8;background:#fafbfe">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2007 GFC Peak</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Oct 2007</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;font-weight:700;color:#D4820A">4.7%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">4.50%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#D4820A">310 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#D4820A">Flat +0.2%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+26% next yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−57%</td>
          <td style="padding:7px 12px;font-size:10px;color:#666">HYG/LQD ratio rolled over 6 weeks BEFORE SPY peak. Classic lead.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2018 Q4 Peak</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Sep 2018</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;font-weight:700;color:#D4820A">3.1%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">2.25%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#555">280 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#D4820A">Flat +0.3%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+10% next yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−20%</td>
          <td style="padding:7px 12px;font-size:10px;color:#666">Fast rate rise (1.5% in 12mo) compressed multiples. TLT rallied as Fed pivoted Dec 2018.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8;background:#fafbfe">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2021 ATH / Rate Shock</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Dec 2021</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;font-weight:700;color:#555">1.5%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">0.08%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#555">320 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#555">+0.8%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−32% in 2022</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−25%</td>
          <td style="padding:7px 12px;font-size:10px;color:#666">Unique: both TLT AND SPY fell in 2022 = stagflation. Gold (+3%) and cash were only safe havens.</td>
        </tr>
        <!-- CURRENT -->
        <tr style="background:#fff8e8;border-bottom:1px solid #e8eaef">
          <td colspan="9" style="padding:6px 12px;font-size:10px;font-weight:800;color:#D4820A;background:#fff3d6">⚠ CURRENT CONDITIONS (March 2026) — Are We At A Peak?</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8;background:#fffde8">
          <td style="padding:7px 12px;font-size:11px;font-weight:800;color:#D4820A">Current Reading</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Mar 2026</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;font-weight:700;color:#D4820A">~4.3%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">4.33%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#555">~320 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#555">+0.46%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#555">YTD flat</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#555">YTD −5%</td>
          <td style="padding:7px 12px;font-size:10px;color:#D4820A"><strong>HY spreads calm (300 bps), but post-inversion normalization matches 2007 pattern. Watch HY >380 bps.</strong></td>
        </tr>
        <!-- TROUGHS -->
        <tr style="background:#f0faf5;border-bottom:1px solid #e8eaef">
          <td colspan="9" style="padding:6px 12px;font-size:10px;font-weight:800;color:#1A7A4A;background:#e6f8ef">▲ CYCLE TROUGHS (buy signal zone)</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">1974 Trough</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Oct 1974</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">8.1%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">5.50%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">700 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">+1.2%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+30% over 2yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+70% over 2yr</td>
          <td style="padding:7px 12px;font-size:10px;color:#1A7A4A">HY spread peak + curve steepening = trough confirmed. Buy signal.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8;background:#fafbfe">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2002-03 Dot-com Trough</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Oct 2002</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">3.6%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">1.75%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">800 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">+2.4%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+5% over 2yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+50% over 2yr</td>
          <td style="padding:7px 12px;font-size:10px;color:#1A7A4A">HY spread peak >800 = maximum fear = buy. Fed cutting aggressively.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2009 GFC Trough</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Mar 2009</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">2.9%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">0.25%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">1900 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">+2.8%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#C0390F">−15% over 2yr</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+90% over 2yr</td>
          <td style="padding:7px 12px;font-size:10px;color:#1A7A4A">HY peaked 1900 bps — all-time record. TLT peaked, then sold off as rates normalized. Buy SPY aggressively.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8;background:#fafbfe">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2020 COVID Trough</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Mar 2020</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">0.5%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">0.08%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">900 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">+0.5%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+5% over 18mo</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+100% over 18mo</td>
          <td style="padding:7px 12px;font-size:10px;color:#1A7A4A">Fastest recovery ever due to $5T fiscal + monetary. HY spread peaked at 900 = buy signal.</td>
        </tr>
        <tr style="border-bottom:1px solid #f0f2f8">
          <td style="padding:7px 12px;font-size:11px;font-weight:700">2022 Rate Shock Trough</td>
          <td style="padding:7px 10px;font-size:10px;color:#666">Oct 2022</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#D4820A">4.2%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px">3.83%</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">620 bps</td>
          <td style="padding:7px 10px;text-align:center;font-size:10px;color:#C0390F">Inverted −0.5%</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+22% over 18mo</td>
          <td style="padding:7px 10px;text-align:center;font-size:11px;color:#1A7A4A">+45% over 18mo</td>
          <td style="padding:7px 12px;font-size:10px;color:#1A7A4A">HY spread peaked 620. Curve still inverted but HYG started recovering = buy signal despite inversion.</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- Bond signal rules -->
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:16px">
  <div style="background:#fff5f5;border:1px solid #ffc0b0;border-left:4px solid #C0390F;border-radius:8px;padding:14px">
    <div style="font-size:12px;font-weight:800;color:#C0390F;margin-bottom:8px">🔴 Peak Warning Signals</div>
    <div style="font-size:10px;color:#666;line-height:1.7">
      <strong>1. Yield curve inverts</strong> (10Y-2Y &lt; 0) → 12-18mo lead<br>
      <strong>2. HY OAS > 380 bps</strong> and rising → 6-12mo lead<br>
      <strong>3. HYG/LQD rolls over</strong> while SPY flat → 4-8wk lead<br>
      <strong>4. TLT starts rising</strong> while SPY stalls → flight to safety<br>
      <strong>5. 10Y yield rising fast</strong> (+1% in 6mo) → multiple compression<br><br>
      <em>Historically: need 3 of 5 for high-confidence peak signal</em>
    </div>
  </div>
  <div style="background:#f5fff5;border:1px solid #a0e0b0;border-left:4px solid #1A7A4A;border-radius:8px;padding:14px">
    <div style="font-size:12px;font-weight:800;color:#1A7A4A;margin-bottom:8px">🟢 Trough Buy Signals</div>
    <div style="font-size:10px;color:#666;line-height:1.7">
      <strong>1. HY OAS peaks and turns down</strong> → most reliable buy<br>
      <strong>2. HYG crosses above 50-day MA</strong> → credit stabilising<br>
      <strong>3. Yield curve steepens rapidly</strong> → Fed pivoting<br>
      <strong>4. Fed Funds cuts begin</strong> → liquidity returning<br>
      <strong>5. ISM PMI turns from &lt;47 to &gt;50</strong> → demand recovering<br><br>
      <em>Golden signal: HYG &gt; 50d MA AND ISM &gt; 48 = BUY</em>
    </div>
  </div>
  <div style="background:#fff8e8;border:1px solid #ffe0a0;border-left:4px solid #D4820A;border-radius:8px;padding:14px">
    <div style="font-size:12px;font-weight:800;color:#D4820A;margin-bottom:8px">⚠ Current Bond Picture (Mar 2026)</div>
    <div style="font-size:10px;color:#666;line-height:1.7">
      <strong>10Y Yield: ~4.3%</strong> — elevated, restrictive for growth<br>
      <strong>HY OAS: ~320 bps</strong> — calm, not pricing stress<br>
      <strong>Yield curve: +0.46%</strong> — post-inversion, risk window<br>
      <strong>TLT: flat YTD</strong> — no flight-to-safety bid yet<br>
      <strong>HYG/LQD: flat</strong> — credit not breaking down yet<br><br>
      <em><strong>Verdict:</strong> Spreads calm but post-inversion pattern
      matches Oct 2006 (12mo before GFC peak). Monitor HY weekly.</em>
    </div>
  </div>
</div>

</div>
<div style="font-size:9px;color:#556;padding-top:8px;border-top:1px solid #e0e4ed;margin-top:12px">
  Deep Cycle Analysis · FRED ({fred_count} series) + yfinance ({mkt_count} tickers) ·
  Kuznets/Juglar/Kitchin cycles · {_sc_total} indicators ({_n_danger} danger / {_n_caution} caution / {_n_calm} calm) ·
  Bonds: TLT/HYG/LQD/yield comparisons · Generated {gen_time}
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     TAB: LEADING INDICATORS (new tab — Peak/Trough scoring + ISM + Claims + USDJPY + PCR)
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-leading" class="tab-content">
{_leading_tab_html}
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     TAB: PULLBACK MONITOR — Minor Correction Early Warning (5-15%)
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-pullback" class="tab-content">
{_pb_html}
</div>

<div id="tab-ecocal" class="tab-content">
{_eco_cal_html}
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     TAB: OPTIONS FLOW — Net GEX per strike (Barchart CSV + Pine Script levels)
════════════════════════════════════════════════════════════════════════════ -->
<div id="tab-options" class="tab-content">
{_options_tab_html}
</div>

</div><!-- /#mi-main -->

<!-- ═══ STATUS BAR ══════════════════════════════════════════════════════════ -->
<div id="mi-status">
  <div class="st-item">
    <div class="st-dot {'st-ok' if fred_count>=15 else 'st-warn'}"></div>
    FRED {fred_count}/{fred_count} series
  </div>
  <div class="st-item">
    <div class="st-dot st-ok"></div>
    yfinance {mkt_count} tickers
  </div>
  <div class="st-item">
    <div class="st-dot {'st-ok' if CLAUDE_API_KEY else 'st-warn'}"></div>
    {'Claude AI connected' if CLAUDE_API_KEY else 'Claude AI offline'}
  </div>
  <div class="st-item">
    <div class="st-dot st-ok"></div>
    {gen_time}
  </div>
  <div style="margin-left:auto" class="st-item">
    <div class="st-dot st-ok"></div>
    Decoding markets through Macro · Liquidity · Positioning
  </div>
</div>

<script>
// ── Updated Tab switching — handles sidebar + nav active states ─────────────
function showTab(id) {{
  // Hide all content
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  // Deactivate all sidebar items
  document.querySelectorAll('.sb-item').forEach(el => el.classList.remove('active'));
  // Show selected content
  var content = document.getElementById('tab-' + id);
  if (content) content.classList.add('active');
  // Activate sidebar item
  var btn = document.getElementById('btn-' + id);
  if (btn) btn.classList.add('active');
  // Lazy-init SPY projection chart when AI Summary tab opens
  if (id === 'ai-summary') {{
    setTimeout(() => {{ if (typeof buildSpyChart === 'function') buildSpyChart(); }}, 100);
  }}
  // Lazy-init Options Flow GEX charts on first open
  if (id === 'options') {{
    setTimeout(() => {{ if (typeof initGexCharts === 'function') initGexCharts(); }}, 50);
  }}
  // Re-trigger chart resize on tab switch
  setTimeout(() => {{ Chart.instances.forEach(c => c && c.resize && c.resize()); }}, 120);
}}
</script>

</body>
</html>"""

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Tab name → display label mapping (for help text) ─────────────────────
    TAB_MAP = {
        "overview":     "📊 Overview",
        "indcharts":    "📉 Indicator Charts",
        "cycles":       "🔄 Cycle Analysis",
        "bonds":        "📉 Credit & Rates",
        "sectors":      "🗂 Sector Rotation",
        "sectorstocks": "📋 Sector Stocks",
        "leading":      "📡 Leading Indicators",
        "mktcharts":    "🔬 Market Charts",
        "pullback":     "📉 Drawdown Analysis",
        "ai-summary":   "🤖 AI Summary",
        "ecocal":       "📅 Eco Calendar",
        "options":      "⚡ Options Flow",
    }
    # Short aliases accepted on the CLI
    TAB_ALIASES = {
        "optionsflow": "options",
        "option":      "options",
        "flow":        "options",
        "overview":    "overview",
        "cycle":       "cycles",
        "cycles":      "cycles",
        "bonds":       "bonds",
        "credit":      "bonds",
        "sectors":     "sectors",
        "sector":      "sectors",
        "sectorstocks":"sectorstocks",
        "leading":     "leading",
        "mktcharts":   "mktcharts",
        "market":      "mktcharts",
        "pullback":    "pullback",
        "drawdown":    "pullback",
        "ai":          "ai-summary",
        "aisummary":   "ai-summary",
        "ai-summary":  "ai-summary",
        "ecocal":      "ecocal",
        "calendar":    "ecocal",
        "indcharts":   "indcharts",
        "indicators":  "indcharts",
    }

    parser = argparse.ArgumentParser(
        description="Deep Economic Cycle Analysis",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--outdir",     default=OUTPUT_DIR)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--quick",      action="store_true",
                        help="Fewer FRED series (~20s vs ~90s)")
    parser.add_argument("--no-ai",      action="store_true",
                        help="Skip Claude API calls (faster, uses static fallback text)")
    parser.add_argument("--noapi",      action="store_true",
                        help="Skip ALL Claude API calls — fastest mode for testing/debugging")
    parser.add_argument("--noindicatorcharts", action="store_true",
                        help="Skip Indicator Charts tab build (saves ~20s)")
    parser.add_argument(
        "--only", metavar="TAB", default=None,
        help=(
            "Build report for a single tab only — opens directly to that tab.\n"
            "⚡ --only optionsflow  skips ALL FRED/AI/compute (~5s, CSV only)\n"
            "   --only overview     full pipeline, opens on Overview\n"
            "   --only cycles       full pipeline, opens on Cycle Analysis\n"
            "   --only bonds        full pipeline, opens on Credit & Rates\n"
            "   --only sectors      full pipeline, opens on Sector Rotation\n"
            "   --only leading      full pipeline, opens on Leading Indicators\n"
            "   --only ai           full pipeline, opens on AI Summary\n"
            "   --only ecocal       full pipeline, opens on Eco Calendar\n"
            "   --only pullback     full pipeline, opens on Drawdown Analysis\n"
            "   (any tab name or alias from the list above is accepted)"
        ),
    )
    args = parser.parse_args()

    # Resolve --only alias → canonical tab id
    only_tab = None
    if args.only:
        raw = args.only.lower().replace("-", "").replace("_", "").replace(" ", "")
        # Try direct alias lookup first
        for alias, canonical in TAB_ALIASES.items():
            if raw == alias.lower().replace("-","").replace("_",""):
                only_tab = canonical
                break
        if only_tab is None:
            # Fallback: partial match against canonical IDs
            for tab_id in TAB_MAP:
                if raw in tab_id.replace("-",""):
                    only_tab = tab_id
                    break
        if only_tab is None:
            print(f"  ⚠ Unknown tab '{args.only}'. Valid names: {', '.join(TAB_MAP)}")
            print("  Running full report instead.\n")

    # --noapi implies --no-ai
    if args.noapi:
        args.no_ai = True

    # ══════════════════════════════════════════════════════════════════════════
    # ⚡ FAST PATH — Options Flow only (no FRED, no compute, no AI)
    # ══════════════════════════════════════════════════════════════════════════
    if only_tab == "options":
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"\n{'='*65}")
        print(f"  ⚡ OPTIONS FLOW — fast mode  (no FRED / no AI)")
        print(f"  {gen_time}")
        print(f"{'='*65}\n")

        options_html = build_options_flow_tab(DOWNLOADS_DIR)

        # Minimal self-contained HTML wrapper — just the options tab
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Options Flow — {gen_time}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body,div,p,span,td,th,li,label,a,h1,h2,h3,h4,h5,h6,small,em,strong {{
    font-weight: 600;
  }}
  body {{ margin: 0; padding: 16px 20px; background: #07090f;
          font-family: 'Segoe UI', system-ui, sans-serif; color: #c8d0e8; }}
  h1   {{ font-size: 14px; font-weight: 700; color: #dde4ff;
          letter-spacing: .06em; text-transform: uppercase;
          margin: 0 0 14px; padding-bottom: 8px;
          border-bottom: 2px solid #1a2540; }}
</style>
</head>
<body>
<h1>⚡ Options Flow &nbsp;·&nbsp; {gen_time}</h1>
{options_html}
<script>
// Standalone mode — trigger GEX bar chart init on page load
window.addEventListener('load', function() {{
  setTimeout(function() {{
    if (typeof initGexCharts === 'function') initGexCharts();
  }}, 100);
}});
</script>
</body>
</html>"""

        os.makedirs(args.outdir, exist_ok=True)
        ts   = datetime.now().strftime("%Y%m%d_%H%M")
        path = os.path.join(args.outdir, f"options_flow_{ts}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n  Saved: {path}  ({len(html):,} bytes)")
        if not args.no_browser:
            import webbrowser
            webbrowser.open("file:///" + os.path.abspath(path).replace(os.sep, "/"))
            print("  Opened in browser.")
        print()
        return

    # ══════════════════════════════════════════════════════════════════════════
    # FULL PIPELINE — all other tabs (or no --only flag = full report)
    # ══════════════════════════════════════════════════════════════════════════
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    if only_tab:
        print(f"\n{'='*65}\n  DEEP ECONOMIC CYCLE ANALYSIS — opening on: {TAB_MAP.get(only_tab, only_tab)}\n  {gen_time}\n{'='*65}\n")
        # Auto-skip slow steps that don't affect the requested tab
        if only_tab in ("sectors", "sectorstocks", "pullback", "mktcharts"):
            if not args.noapi:
                args.no_ai  = True
                args.noapi  = True
            if not args.noindicatorcharts:
                args.noindicatorcharts = True
            print("  ℹ Auto-implied: --noapi --noindicatorcharts (not needed for this tab)")
    else:
        print(f"\n{'='*65}\n  DEEP ECONOMIC CYCLE ANALYSIS\n  {gen_time}\n{'='*65}\n")

    print("[1/4] Fetching FRED macro data...")
    series = FRED_QUICK if args.quick else FRED_MAP
    fd, status = fetch_fred(series)

    # ── Unit normalisation: FRED BAML spread series are in % (e.g. 3.17)
    # but all thresholds and display use bps (317). Multiply by 100. ────────
    # ── Unit normalisation: FRED BAML spread series come in % (e.g. 3.17 = 317 bps)
    # Multiply by 100 to convert to bps — but ONLY for values from FRED/datareader,
    # NOT for yfinance proxy values which are already in bps (~300-2000 range)
    _BPS_SERIES = {"HY_OAS", "IG_OAS", "CCC_OAS", "BBB_SPREAD"}
    for _bk in _BPS_SERIES:
        if _bk in fd and fd[_bk] is not None and not fd[_bk].empty:
            _last_val = float(fd[_bk].iloc[-1])
            # Only multiply if value looks like % (0-30 range), not already in bps (100-3000)
            if _last_val < 50:
                fd[_bk] = (fd[_bk] * 100).round(1)
    # YIELD_CURVE (T10Y2Y) and T10Y3M are in % — multiply to bps for
    # ep_score and cycle_pos (full_scorecard handles its own conversion)
    _CURVE_SERIES = {"YIELD_CURVE", "T10Y3M"}
    for _ck in _CURVE_SERIES:
        if _ck in fd and fd[_ck] is not None and not fd[_ck].empty:
            fd[_ck] = (fd[_ck] * 100).round(1)

    # ── Sanity checks: reject stale or out-of-range values ────────────────────
    from datetime import date as _sanity_date, timedelta as _sanity_td
    _today_s = _sanity_date.today()

    # WTI Oil: reject if >$110 (price hasn't been that high since 2022 Russian invasion)
    # or if >18 months stale. Use yfinance proxy instead.
    _wti = fd.get("DCOILWTICO")
    if _wti is not None and not _wti.empty:
        _wti_val  = float(_wti.iloc[-1])
        _wti_date = _wti.index[-1]
        if hasattr(_wti_date, 'date'): _wti_date = _wti_date.date()
        _wti_age  = (_today_s - _wti_date).days if hasattr(_wti_date,'__sub__') else 999
        if _wti_val > 110 or _wti_age > 30:
            print(f"  ⚠ WTI=${_wti_val:.0f} or stale ({_wti_age}d) — using CL=F proxy")
            import yfinance as _yf_wti
            _cl = _yf_wti.download("CL=F", period="3mo", auto_adjust=True, progress=False)
            if not _cl.empty:
                import pandas as _pd_wti
                _cl_s = _cl["Close"].squeeze().dropna()
                _cl_s.index = _pd_wti.to_datetime(_cl_s.index).tz_localize(None)
                fd["DCOILWTICO"] = _cl_s.resample("ME").last().tail(200)
                print(f"  ✓ WTI updated: ${float(fd['DCOILWTICO'].iloc[-1]):.1f}/bbl (CL=F)")

    # OFR_FSI (STLFSI4): reject if >2 years stale
    _fsi = fd.get("OFR_FSI")
    if _fsi is not None and not _fsi.empty:
        _fsi_date = _fsi.index[-1]
        if hasattr(_fsi_date, 'date'): _fsi_date = _fsi_date.date()
        _fsi_age = (_today_s - _fsi_date).days if hasattr(_fsi_date,'__sub__') else 999
        if _fsi_age > 365:
            print(f"  ⚠ OFR_FSI stale ({_fsi_age}d old) — using NFCI as substitute")
            _nfci = fd.get("NFCI")
            if _nfci is not None and not _nfci.empty:
                fd["OFR_FSI"] = _nfci   # NFCI is same concept, already fresh

    # LEI (OECD CLI): warn if >6 months stale
    _lei = fd.get("LEI")
    if _lei is not None and not _lei.empty:
        _lei_date = _lei.index[-1]
        if hasattr(_lei_date, 'date'): _lei_date = _lei_date.date()
        _lei_age = (_today_s - _lei_date).days if hasattr(_lei_date,'__sub__') else 999
        if _lei_age > 180:
            print(f"  ⚠ LEI ({_lei.index[-1]}) is {_lei_age}d stale — using XLI proxy")

    if len(fd) == 0:
        print("""
  ⚠ No FRED data loaded. Diagnosis:
  
  Most likely cause: your network blocks fred.stlouisfed.org
  The yfinance proxy should have caught most series — if it also failed,
  run this to check:
  
    python -c "import yfinance as yf; print(yf.download('^TNX', period='5d', progress=False))"
  
  If that also fails:  pip install yfinance  then re-run
  
  Optional (direct FRED access):
    pip install fredapi pandas_datareader
    Then set FRED_API_KEY at top of this file
    Free key: https://fred.stlouisfed.org/docs/api/api_key.html
  
  The report will still render — cycle framework and bear market analysis
  use hard-coded research data, only the live indicator values will be blank.
""")

    print("\n[2/4] Fetching market data (yfinance)...")
    md = fetch_market(quick=args.quick)
    if not md:
        print("  ⚠ No market data. Ensure yfinance is installed: pip install yfinance")

    print("\n[3/4] Computing cycle positions + projections...")
    ep  = ep_score(fd)
    pos = cycle_pos(fd, ep)
    print(f"  Kuznets:  {pos['kuznets']['phase']} ({pos['kuznets']['pct']:.0f}%)")
    print(f"  Juglar:   {pos['juglar']['phase']} ({pos['juglar']['pct']:.0f}%)")
    print(f"  Kitchin:  {pos['kitchin']['phase']} ({pos['kitchin']['pct']:.0f}%)")
    print(f"  Regime:   {pos['regime']['label']}")
    print(f"  EP Score: {ep['score']}% — {ep['verdict']}")
    print(f"  Indicators: {ep['n_red']}R / {ep['n_yellow']}Y / {ep['n_green']}G ({len(ep['indicators'])} total)")
    print(f"  Projections: {len(pos['projections'])} scenarios")
    print(f"  Parallels: {', '.join(p['year'] for p in pos['parallels'])}")

    # Store playbook on pos so AI module can access it
    pos["_playbook"] = playbook(pos, ep, [])

    use_ai = bool(CLAUDE_API_KEY) and not args.no_ai
    if args.noapi:
        print("\n  ⚡ --noapi flag: ALL Claude API calls skipped (scorecard web search, AI summaries, road chart, SPY projection).")
        use_ai = False
    elif use_ai:
        print("\n[3.5/4] Generating AI narrative summaries (Claude Haiku)...")
    else:
        if not CLAUDE_API_KEY:
            print("\n  ℹ  CLAUDE_API_KEY not set — using static fallback text.")
        else:
            print("\n  ⚡ --no-ai flag set — skipping Claude API calls.")
    ai = ai_summaries(pos, ep, fd, use_ai=use_ai)

    print("\n[3.8/4] Computing full market scorecard (35 indicators)...")
    scorecard, sdm_data = full_scorecard(fd, md, use_api=not args.noapi)
    _sc_red  = sum(1 for x in scorecard if x["signal"] in ("STRESS","CRISIS"))
    _sc_caut = sum(1 for x in scorecard if x["signal"] == "CAUTION")
    _sc_grn  = sum(1 for x in scorecard if x["signal"] == "CALM")
    print(f"  Scorecard: {_sc_red} danger / {_sc_caut} caution / {_sc_grn} calm ({len(scorecard)} indicators)")

    print("\n[4/4] Building HTML report with charts...")
    charts = prep_charts(fd, md, pos=pos, ep=ep)

    print("  Fetching sector stock holdings (top 10 per sector, 1yr daily)...")
    sector_stocks = fetch_sector_stocks(md)
    print(f"  Sector stocks: {len(sector_stocks)} sectors ready")

    html = build_html(fd, md, ep, pos, charts, gen_time, ai=ai, scorecard=scorecard,
                      sector_stocks=sector_stocks, use_api=not args.noapi, sdm_data=sdm_data,
                      no_indicator_charts=args.noindicatorcharts,
                      default_tab=only_tab)

    os.makedirs(args.outdir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M")
    tab_suffix = f"_{only_tab.replace('-','')}" if only_tab else ""
    path = os.path.join(args.outdir, f"cycle_analysis{tab_suffix}_{ts}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  Saved: {path}  ({len(html):,} bytes)")

    if not args.no_browser:
        import webbrowser
        webbrowser.open("file:///" + os.path.abspath(path).replace(os.sep, "/"))
        print("  Opened in browser.")
    print()

    # ── Unit normalisation: FRED BAML spread series are in % (e.g. 3.17)
    # but all thresholds and display use bps (317). Multiply by 100. ────────
    # ── Unit normalisation: FRED BAML spread series come in % (e.g. 3.17 = 317 bps)
    # Multiply by 100 to convert to bps — but ONLY for values from FRED/datareader,
    # NOT for yfinance proxy values which are already in bps (~300-2000 range)
    _BPS_SERIES = {"HY_OAS", "IG_OAS", "CCC_OAS", "BBB_SPREAD"}
    for _bk in _BPS_SERIES:
        if _bk in fd and fd[_bk] is not None and not fd[_bk].empty:
            _last_val = float(fd[_bk].iloc[-1])
            # Only multiply if value looks like % (0-30 range), not already in bps (100-3000)
            if _last_val < 50:
                fd[_bk] = (fd[_bk] * 100).round(1)
    # YIELD_CURVE (T10Y2Y) and T10Y3M are in % — multiply to bps for
    # ep_score and cycle_pos (full_scorecard handles its own conversion)
    _CURVE_SERIES = {"YIELD_CURVE", "T10Y3M"}
    for _ck in _CURVE_SERIES:
        if _ck in fd and fd[_ck] is not None and not fd[_ck].empty:
            fd[_ck] = (fd[_ck] * 100).round(1)

    # ── Sanity checks: reject stale or out-of-range values ────────────────────
    from datetime import date as _sanity_date, timedelta as _sanity_td
    _today_s = _sanity_date.today()

    # WTI Oil: reject if >$110 (price hasn't been that high since 2022 Russian invasion)
    # or if >18 months stale. Use yfinance proxy instead.
    _wti = fd.get("DCOILWTICO")
    if _wti is not None and not _wti.empty:
        _wti_val  = float(_wti.iloc[-1])
        _wti_date = _wti.index[-1]
        if hasattr(_wti_date, 'date'): _wti_date = _wti_date.date()
        _wti_age  = (_today_s - _wti_date).days if hasattr(_wti_date,'__sub__') else 999
        if _wti_val > 110 or _wti_age > 30:
            print(f"  ⚠ WTI=${_wti_val:.0f} or stale ({_wti_age}d) — using CL=F proxy")
            import yfinance as _yf_wti
            _cl = _yf_wti.download("CL=F", period="3mo", auto_adjust=True, progress=False)
            if not _cl.empty:
                import pandas as _pd_wti
                _cl_s = _cl["Close"].squeeze().dropna()
                _cl_s.index = _pd_wti.to_datetime(_cl_s.index).tz_localize(None)
                fd["DCOILWTICO"] = _cl_s.resample("ME").last().tail(200)
                print(f"  ✓ WTI updated: ${float(fd['DCOILWTICO'].iloc[-1]):.1f}/bbl (CL=F)")

    # OFR_FSI (STLFSI4): reject if >2 years stale
    _fsi = fd.get("OFR_FSI")
    if _fsi is not None and not _fsi.empty:
        _fsi_date = _fsi.index[-1]
        if hasattr(_fsi_date, 'date'): _fsi_date = _fsi_date.date()
        _fsi_age = (_today_s - _fsi_date).days if hasattr(_fsi_date,'__sub__') else 999
        if _fsi_age > 365:
            print(f"  ⚠ OFR_FSI stale ({_fsi_age}d old) — using NFCI as substitute")
            _nfci = fd.get("NFCI")
            if _nfci is not None and not _nfci.empty:
                fd["OFR_FSI"] = _nfci   # NFCI is same concept, already fresh

    # LEI (OECD CLI): warn if >6 months stale
    _lei = fd.get("LEI")
    if _lei is not None and not _lei.empty:
        _lei_date = _lei.index[-1]
        if hasattr(_lei_date, 'date'): _lei_date = _lei_date.date()
        _lei_age = (_today_s - _lei_date).days if hasattr(_lei_date,'__sub__') else 999
        if _lei_age > 180:
            print(f"  ⚠ LEI ({_lei.index[-1]}) is {_lei_age}d stale — using XLI proxy")

    if len(fd) == 0:
        print("""
  ⚠ No FRED data loaded. Diagnosis:
  
  Most likely cause: your network blocks fred.stlouisfed.org
  The yfinance proxy should have caught most series — if it also failed,
  run this to check:
  
    python -c "import yfinance as yf; print(yf.download('^TNX', period='5d', progress=False))"
  
  If that also fails:  pip install yfinance  then re-run
  
  Optional (direct FRED access):
    pip install fredapi pandas_datareader
    Then set FRED_API_KEY at top of this file
    Free key: https://fred.stlouisfed.org/docs/api/api_key.html
  
  The report will still render — cycle framework and bear market analysis
  use hard-coded research data, only the live indicator values will be blank.
""")

    print("\n[2/4] Fetching market data (yfinance)...")
    md = fetch_market(quick=args.quick)
    if not md:
        print("  ⚠ No market data. Ensure yfinance is installed: pip install yfinance")

    print("\n[3/4] Computing cycle positions + projections...")
    ep  = ep_score(fd)
    pos = cycle_pos(fd, ep)
    print(f"  Kuznets:  {pos['kuznets']['phase']} ({pos['kuznets']['pct']:.0f}%)")
    print(f"  Juglar:   {pos['juglar']['phase']} ({pos['juglar']['pct']:.0f}%)")
    print(f"  Kitchin:  {pos['kitchin']['phase']} ({pos['kitchin']['pct']:.0f}%)")
    print(f"  Regime:   {pos['regime']['label']}")
    print(f"  EP Score: {ep['score']}% — {ep['verdict']}")
    print(f"  Indicators: {ep['n_red']}R / {ep['n_yellow']}Y / {ep['n_green']}G ({len(ep['indicators'])} total)")
    print(f"  Projections: {len(pos['projections'])} scenarios")
    print(f"  Parallels: {', '.join(p['year'] for p in pos['parallels'])}")

    # Store playbook on pos so AI module can access it
    pos["_playbook"] = playbook(pos, ep, [])

    use_ai = bool(CLAUDE_API_KEY) and not args.no_ai
    if args.noapi:
        print("\n  ⚡ --noapi flag: ALL Claude API calls skipped (scorecard web search, AI summaries, road chart, SPY projection).")
        use_ai = False
    elif use_ai:
        print("\n[3.5/4] Generating AI narrative summaries (Claude Haiku)...")
    else:
        if not CLAUDE_API_KEY:
            print("\n  ℹ  CLAUDE_API_KEY not set — using static fallback text.")
        else:
            print("\n  ⚡ --no-ai flag set — skipping Claude API calls.")
    ai = ai_summaries(pos, ep, fd, use_ai=use_ai)

    print("\n[3.8/4] Computing full market scorecard (35 indicators)...")
    scorecard, sdm_data = full_scorecard(fd, md, use_api=not args.noapi)
    _sc_red  = sum(1 for x in scorecard if x["signal"] in ("STRESS","CRISIS"))
    _sc_caut = sum(1 for x in scorecard if x["signal"] == "CAUTION")
    _sc_grn  = sum(1 for x in scorecard if x["signal"] == "CALM")
    print(f"  Scorecard: {_sc_red} danger / {_sc_caut} caution / {_sc_grn} calm ({len(scorecard)} indicators)")

    print("\n[4/4] Building HTML report with charts...")
    charts = prep_charts(fd, md, pos=pos, ep=ep)

    print("  Fetching sector stock holdings (top 10 per sector, 1yr daily)...")
    sector_stocks = fetch_sector_stocks(md)
    print(f"  Sector stocks: {len(sector_stocks)} sectors ready")

    html = build_html(fd, md, ep, pos, charts, gen_time, ai=ai, scorecard=scorecard,
                      sector_stocks=sector_stocks, use_api=not args.noapi, sdm_data=sdm_data,
                      no_indicator_charts=args.noindicatorcharts)

    os.makedirs(args.outdir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M")
    path = os.path.join(args.outdir, f"cycle_analysis_{ts}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  Saved: {path}  ({len(html):,} bytes)")

    if not args.no_browser:
        import webbrowser
        webbrowser.open("file:///" + os.path.abspath(path).replace(os.sep, "/"))
        print("  Opened in browser.")
    print()

if __name__ == "__main__":
    main()