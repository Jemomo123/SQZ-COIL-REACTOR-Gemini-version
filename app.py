import os
import time
import requests
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==============================================================================
# 🏛️ JEREMIAH EDGE ARCHITECTURE LAW: CONFIGURATION & MOBILE WORKSPACE SETTINGS
# ==============================================================================
st.set_page_config(
    page_title="JEREMIAH EDGE SCANNER", 
    layout="centered",  # Optimal for mobile rendering windows
    initial_sidebar_state="collapsed"
)

# Target Constants
EXCHANGE_API_URL = "https://api.mexc.com/api/v3/klines"
# 🟩 SCALPING AND SWING TIMEFRAME SEPARATORS
TIMEFRAMES = ["2m", "5m", "15m"]
SWING_TIMEFRAMES = ["1h", "4h", "1d"]  # Dedicated Swing Channels
THRESHOLD = 0.001  # Hard steel wall ceiling: <= 0.1%

# 📋 THE NEW NOTEBOOK WATCHLIST POOL (25 Tokens) - FULLY UPDATED
WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "PEPEUSDT", "BONKUSDT",
    "SHIBUSDT", "USELESSUSDT", "SPACEUSDT", "MOVEUSDT", "ZECUSDT",
    "SPXUSDT", "PEOPLEUSDT", "PENGUUSDT", "FARTCOINUSDT", "LINEAUSDT",
    "MEMEUSDT", "PUMPUSDT", "AIXBTUSDT", "BRETTUSDT", "FOGOUSDT",
    "GOOGLUSDT", "FLOKIUSDT", "IWMUSDT", "MOODENGUSDT", "NEARUSDT"
]

# 🧠 IN-MEMORY CACHE REPOSITORY FOR SINGLE-SCAN CYCLE ELIMINATION
candle_cache = {}

# ==============================================================================
# DATA CALCULATION PIPELINE (HIGH-PRECISION MATH ENGINE)
# ==============================================================================
def calculate_sma(prices, period):
    """Calculates pure mathematical Simple Moving Average."""
    return pd.Series(prices).rolling(window=period).mean().iloc[-1]

def fetch_mexc_candles(symbol, timeframe):
    """
    High-integrity historical bar engine with Supreme Failover Protection and Single-Scan Caching.
    Primary Route: MEXC Public REST API
    Failover Route: OKX v5 Public REST API
    """
    if (symbol, timeframe) in candle_cache:
        return candle_cache[(symbol, timeframe)]

    mexc_tf = "60m" if timeframe == "1h" else timeframe
    
    okx_tf_map = {
        "2m": "2m", "3m": "3m", "5m": "5m", "15m": "15m",
        "1h": "1H", "60m": "1H", "4h": "4H", "1d": "1D"
    }

    # 1️⃣ PRIMARY CONNECTION LINE: Attempt Live Fetch from MEXC
    mexc_params = {"symbol": symbol, "interval": mexc_tf, "limit": 250}
    try:
        response = requests.get(EXCHANGE_API_URL, params=mexc_params, timeout=3)
        if response.status_code == 200:
            data = response.json()
            candle_cache[(symbol, timeframe)] = data
            return data
    except Exception:
        pass

    # 2️⃣ AUTOMATIC SHIELD FAILOVER LINE: Triggers immediately if MEXC fails
    try:
        okx_symbol = symbol.replace("USDT", "-USDT") if "USDT" in symbol and "-" not in symbol else symbol
        okx_interval = okx_tf_map.get(timeframe, "1H")
        okx_params = {"instId": okx_symbol, "bar": okx_interval, "limit": "250"}
        
        okx_response = requests.get("https://www.okx.com/api/v5/market/candles", params=okx_params, timeout=3)
        if okx_response.status_code == 200:
            raw_data = okx_response.json()
            if raw_data.get("code") == "0" and "data" in raw_data:
                mexc_formatted_data = []
                for bar in raw_data["data"]:
                    mexc_formatted_data.insert(0, [bar[0], bar[1], bar[2], bar[3], bar[4]])
                candle_cache[(symbol, timeframe)] = mexc_formatted_data
                return mexc_formatted_data
    except Exception:
        pass

    return None

def calculate_atr_volatility(symbol, timeframe="15m", period=14):
    """Calculates pure percentage-based volatility reusing cached candles to protect network speed."""
    candles = fetch_mexc_candles(symbol, timeframe)
    if not candles or len(candles) < (period + 1):
        return 0.0
        
    cleaned_candles = [candle[:5] for candle in candles]
    df = pd.DataFrame(cleaned_candles, columns=['time', 'open', 'high', 'low', 'close'])
    df[['high', 'low', 'close']] = df[['high', 'low', 'close']].astype(float)
    
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    atr_val = df['tr'].rolling(window=period).mean().iloc[-1]
    latest_close = df['close'].iloc[-1]
    
    return (atr_val / latest_close) * 100 if latest_close > 0 else 0.0

def run_pure_compression_math(symbol, timeframe):
    """
    Core Part 1 Algorithm Engine.
    Executes True Cluster-Based Convergence with complete precision debug array telemetry.
    """
    candles = fetch_mexc_candles(symbol, timeframe)
    if not candles or len(candles) < 200:
        return {
            "sqz": False, "type": "NONE", "live_price": 0.0,
            "sma20": 0.0, "sma100": 0.0, "sma200": 0.0,
            "at_spread_pct": 0.0, "so_spread_pct": 0.0,
            "cluster_high": 0.0, "cluster_low": 0.0
        }
    
    closes = [float(candle[4]) for candle in candles]
    live_price = closes[-1]
    
    sma20 = calculate_sma(closes, 20)
    sma100 = calculate_sma(closes, 100)
    sma200 = calculate_sma(closes, 200)
    
    # 🟩 1. ALL TOGETHER CONVERGENCE
    highest_at = max(live_price, sma20, sma100)
    lowest_at = min(live_price, sma20, sma100)
    cluster_avg_at = (live_price + sma20 + sma100) / 3.0
    at_spread_raw = (highest_at - lowest_at) / cluster_avg_at
    all_together = at_spread_raw <= THRESHOLD

    # 🟦 2. SPECIAL ONE CONVERGENCE
    highest_so = max(live_price, sma20, sma200)
    lowest_so = min(live_price, sma20, sma200)
    cluster_avg_so = (live_price + sma20 + sma200) / 3.0
    so_spread_raw = (highest_so - lowest_so) / cluster_avg_so
    special_one = so_spread_raw <= THRESHOLD
    
    at_spread_pct = at_spread_raw * 100
    so_spread_pct = so_spread_raw * 100
    
    if all_together:
        return {
            "sqz": True, "type": "ALL TOGETHER",
            "live_price": live_price, "sma20": sma20, "sma100": sma100, "sma200": sma200,
            "at_spread_pct": at_spread_pct, "so_spread_pct": so_spread_pct,
            "cluster_high": float(highest_at), "cluster_low": float(lowest_at)
        }
    elif special_one:
        return {
            "sqz": True, "type": "SPECIAL ONE",
            "live_price": live_price, "sma20": sma20, "sma100": sma100, "sma200": sma200,
            "at_spread_pct": at_spread_pct, "so_spread_pct": so_spread_pct,
            "cluster_high": float(highest_so), "cluster_low": float(lowest_so)
        }
        
    return {
        "sqz": False, "type": "NONE",
        "live_price": live_price, "sma20": sma20, "sma100": sma100, "sma200": sma200,
        "at_spread_pct": at_spread_pct, "so_spread_pct": so_spread_pct,
        "cluster_high": float(highest_at if at_spread_raw < so_spread_raw else highest_so),
        "cluster_low": float(lowest_at if at_spread_raw < so_spread_raw else lowest_so)
    }

def fetch_btc_regime_data():
    """Calculates structural BTC regimes dynamically using single-point caching channels."""
    timeframes_p2 = ["15m", "1h", "4h"]
    results = {}
    
    for tf in timeframes_p2:
        candles = fetch_mexc_candles("BTCUSDT", tf)
        if not candles or len(candles) < 50:
            results[tf] = {"regime": "UNKNOWN", "character": "DATA ERROR"}
            continue
            
        closes = [float(candle[4]) for candle in candles]
        current_price = closes[-1]
        recent_window = closes[-20:]
        max_boundary = max(recent_window)
        min_boundary = min(recent_window)
        range_width = (max_boundary - min_boundary) / min_boundary
        sma20 = pd.Series(closes).rolling(window=20).mean().iloc[-1]
        
        if range_width <= 0.015:
            if abs(current_price - sma20) / sma20 <= 0.002:
                results[tf] = {"regime": "RANGING", "character": "INTERNAL BOX"}
            else:
                results[tf] = {"regime": "RANGING", "character": "BOX"}
        else:
            results[tf] = {"regime": "TRENDING", "character": "CLEAR"}
            
    return results

def scan_single_asset(asset):
    """Thread worker engine performing calculations inside an isolated, parallel tracking state."""
    local_results = {}
    for tf in TIMEFRAMES + SWING_TIMEFRAMES:
        local_results[tf] = run_pure_compression_math(asset, tf)
    vol_rating = calculate_atr_volatility(asset, timeframe="15m", period=14)
    return asset, local_results, vol_rating


# ==============================================================================
# STREAMLIT USER INTERFACE VIEWPORT
# ==============================================================================

st.markdown("## 🛰️ Centralized BTC Market Regime (SSoT Part 2)")

# Wipe cache fresh at the start of a clean dashboard viewport loop execution
candle_cache.clear()

btc_data = fetch_btc_regime_data()

regime_table = f"""
| TIMEFRAME | REGIME STATE | STRUCTURE CHARACTER |
| :--- | :--- | :--- |
| 15m | **{btc_data.get('15m', {}).get('regime', 'UNKNOWN')}** | {btc_data.get('15m', {}).get('character', 'DATA ERROR')} |
| 1h  | **{btc_data.get('1h', {}).get('regime', 'UNKNOWN')}** | {btc_data.get('1h', {}).get('character', 'DATA ERROR')}   |
| 4h  | **{btc_data.get('4h', {}).get('regime', 'UNKNOWN')}** | {btc_data.get('4h', {}).get('character', 'DATA ERROR')}   |
"""
st.markdown(regime_table)
st.markdown("---")

st.markdown("## 🏹 Strategy Monitor")

# Alert tracking architecture
all_together_alerts = []
special_one_alerts = []
mega_sqz_alerts = []

swing_at_alerts = []
swing_so_alerts = []
swing_mega_alerts = []

high_vol_confluence_alerts = []
volatility_ranking = {}
scan_results = {}

# ⚡ VISIBLE PARALLEL SCAN ENGINE: PROGRESS UPDATES DIRECT TO SCREEN
progress_text = st.empty()
completed_count = 0

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(scan_single_asset, asset): asset for asset in WATCHLIST}
    
    for future in as_completed(futures):
        asset = futures[future]
        completed_count += 1
        # Displays exactly which item out of 25 is running right now on your screen!
        progress_text.markdown(f"⏳ *Scanning Watchlist Item {completed_count}/25:*\n### {asset}")
        
        asset_name, local_results, vol_rating = future.result()
        scan_results[asset_name] = local_results
        volatility_ranking[asset_name] = vol_rating

# 🏛️ POST-SCAN SIGNAL ANALYSIS AND RE-ROUTING PIPELINE
for asset in WATCHLIST:
    is_mega_sqz = (
        scan_results[asset]["2m"]["sqz"]
        and scan_results[asset]["5m"]["sqz"]
        and scan_results[asset]["15m"]["sqz"]
    )
    is_swing_mega = (
        scan_results[asset]["1h"]["sqz"]
        and scan_results[asset]["4h"]["sqz"]
        and scan_results[asset]["1d"]["sqz"]
    )
    
    # Pack Scalping signals safely
    if is_mega_sqz:
        mega_sqz_alerts.append(asset)
    else:
        for tf in TIMEFRAMES:
            if scan_results[asset][tf]["sqz"]:
                alert_entry = f"**{asset}** ({tf})"
                if scan_results[asset][tf]["type"] == "ALL TOGETHER":
                    all_together_alerts.append(alert_entry)
                elif scan_results[asset][tf]["type"] == "SPECIAL ONE":
                    special_one_alerts.append(alert_entry)

    # Pack Swing signals safely
    if is_swing_mega:
        swing_mega_alerts.append(asset)
    else:
        for tf in SWING_TIMEFRAMES:
            if scan_results[asset][tf]["sqz"]:
                swing_entry = f"**{asset}** ({tf})"
                if scan_results[asset][tf]["type"] == "ALL TOGETHER":
                    swing_at_alerts.append(swing_entry)
                elif scan_results[asset][tf]["type"] == "SPECIAL ONE":
                    swing_so_alerts.append(swing_entry)

progress_text.markdown(f"✅ *Watchlist Scan Complete (25/25 Assets Cached & Calculated)*")

# Sort Volatility to discover Top 3 immediately 
sorted_vol = sorted(volatility_ranking.items(), key=lambda x: x[1], reverse=True)
top_3_symbols = [item[0] for item in sorted_vol[:3]] if len(sorted_vol) >= 3 else []

# 🏛️ SECTION D EXTRACTION LOGIC
for asset in top_3_symbols:
    if asset in mega_sqz_alerts:
        high_vol_confluence_alerts.append(f"🔥 **{asset}** is in a **HIGH-VOLATILITY MEGA SQUEEZE** across all scalping frames!")
    if asset in swing_mega_alerts:
        high_vol_confluence_alerts.append(f"🔥 **{asset}** is in a **HIGH-VOLATILITY SWING MEGA SQUEEZE** across all macro frames!")
        
    for tf in TIMEFRAMES + SWING_TIMEFRAMES:
        if scan_results[asset].get(tf, {}).get("sqz"):
            sqz_type = scan_results[asset][tf]["type"]
            high_vol_confluence_alerts.append(f"🔥 **{asset}** has an active **{sqz_type} SQUEEZE** on the **{tf}** timeframe!")

# --------------------------------------------------------------------------
# 🔥 AUTOMATED LEADERBOARD LAYER: THE MOST VOLATILE PAIRS
# --------------------------------------------------------------------------
st.markdown("### 🔥 High-Volatility Vol Index Leaders (15m)")

st.markdown(
    """
    <style>
    [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; }
    [data-testid="stMetric"] { width: min-content !important; min-width: 30% !important; }
    </style>
    """,
    unsafe_allow_html=True
)

if sorted_vol and len(sorted_vol) >= 3:
    top_3 = sorted_vol[:3]
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label=f"🥇 1st: {top_3[0][0]}", value=f"{top_3[0][1]:.2f}%")
    with col2: st.metric(label=f"🥈 2nd: {top_3[1][0]}", value=f"{top_3[1][1]:.2f}%")
    with col3: st.metric(label=f"🥉 3rd: {top_3[2][0]}", value=f"{top_3[2][1]:.2f}%")
else:
    st.info("Calculating initial volatility trends...")

st.markdown("---")

# ==============================================================================
# UNFILTERED REPORTING VIEWPORT INTERFACES
# ==============================================================================

# --------------------------------------------------------------------------
# SECTION A: SCALPING CHANNELS (2m, 5m, 15m)
# --------------------------------------------------------------------------
st.markdown("### ⚡ Scalping Squeezes")

if mega_sqz_alerts:
    for mega_asset in mega_sqz_alerts:
        st.error(f"🚨 **{mega_asset} SCALPING MEGA SQZ ACTIVE** 🚨")

if not mega_sqz_alerts and not all_together_alerts and not special_one_alerts:
    st.info("No active high-velocity compression states detected.")
else:
    if all_together_alerts: st.success(f"🟩 **ALL TOGETHER COMPRESSION:** {', '.join(all_together_alerts)}")
    if special_one_alerts: st.warning(f"🟦 **SPECIAL ONE COMPRESSION:** {', '.join(special_one_alerts)}")

st.markdown("---")

# --------------------------------------------------------------------------
# SECTION B: DEDICATED SWING TRADING MATRIX (1h, 4h, 1d)
# --------------------------------------------------------------------------
st.markdown("### 🏹 Swing Trade Compressions")

if swing_mega_alerts:
    for swing_mega_asset in swing_mega_alerts:
        st.error(f"🐳 **{swing_mega_asset} SWING MEGA SQZ ACTIVE (1h+4h+1d)** 🐳")

if not swing_mega_alerts and not swing_at_alerts and not swing_so_alerts:
    st.info("No macro swing trade setups detected on 1h, 4h, or 1d channels.")
else:
    if swing_at_alerts: st.success(f"🟢 **SWING ALL TOGETHER:** {', '.join(swing_at_alerts)}")
    if swing_so_alerts: st.warning(f"🔵 **SWING SPECIAL ONE:** {', '.join(swing_so_alerts)}")

st.markdown("---")

# --------------------------------------------------------------------------
# 🎯 SECTION D: HIGH-VOLATILITY EXPLOSIVE SETUPS (CONFLUENCE ENGINE)
# --------------------------------------------------------------------------
st.markdown("### 🎯 Section D: High-Volatility Explosive Setups")

if high_vol_confluence_alerts:
    # 🔒 ORDER-PRESERVING DEDUPLICATION PATCH
    unique_confluence_alerts = list(dict.fromkeys(high_vol_confluence_alerts))
    for alert in unique_confluence_alerts:
        st.error(alert)
else:
    st.info("Plain English: None of the Top 3 high-volatility leaders are currently squeezing.")

st.caption(f"Live workspace check timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
