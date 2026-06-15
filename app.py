import os
import time
import requests
import pandas as pd
import streamlit as st

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
# 🟩 PATCHED: Swapped "3m" out and introduced the "2m" timeframe natively
TIMEFRAMES = ["2m", "5m", "15m"]
THRESHOLD = 0.001  # Hard steel wall ceiling: <= 0.1%

# 📋 THE RESTORED VERIFIED WATCHLIST POOL (25 Tokens) - LOCKED BY SUPREME LAW
# 📋 THE NEW NOTEBOOK WATCHLIST POOL (25 Tokens) - FULLY UPDATED
WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "PEPEUSDT", "BONKUSDT",
    "SHIBUSDT", "USELESSUSDT", "SPACEUSDT", "MOVEUSDT", "ZECUSDT",
    "SPXUSDT", "PEOPLEUSDT", "PENGUUSDT", "FARTCOINUSDT", "LINEAUSDT",
    "MEMEUSDT", "PUMPUSDT", "AIXBTUSDT", "BRETTUSDT", "FOGOUSDT",
    "GOOGLUSDT", "FLOKIUSDT", "IWMUSDT", "MOODENGUSDT", "NEARUSDT"
]


# ==============================================================================
# DATA CALCULATION PIPELINE (HIGH-PRECISION MATH ENGINE)
# ==============================================================================
def calculate_sma(prices, period):
    """Calculates pure mathematical Simple Moving Average."""
    return pd.Series(prices).rolling(window=period).mean().iloc[-1]

def fetch_mexc_candles(symbol, timeframe):
    """
    High-integrity historical bar engine with Supreme Failover Protection.
    Primary Route: MEXC Public REST API
    Failover Route: OKX v5 Public REST API (Fires instantly if MEXC drops or throttles)
    """
    # Timeframe string translation map for OKX native parameters
    okx_tf_map = {
        "2m": "2m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "60m": "1H",
        "1h": "1H",
        "4h": "4H"
    }

    # 1️⃣ PRIMARY CONNECTION LINE: Attempt Live Fetch from MEXC
    mexc_params = {
        "symbol": symbol,
        "interval": timeframe,
        "limit": 250
    }
    try:
        response = requests.get(EXCHANGE_API_URL, params=mexc_params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass  # Bypass immediately to shield the phone UI from freezes

    # 2️⃣ AUTOMATIC SHIELD FAILOVER LINE: Triggers immediately if MEXC fails
    try:
        # Reformat asset tracking names to OKX structural syntax (e.g. BTCUSDT -> BTC-USDT)
        okx_symbol = symbol.replace("USDT", "-USDT") if "USDT" in symbol and "-" not in symbol else symbol
        okx_interval = okx_tf_map.get(timeframe, timeframe)
        
        okx_params = {
            "instId": okx_symbol,
            "bar": okx_interval,
            "limit": "250"
        }
        
        # Pull from public OKX verification channel
        okx_response = requests.get("https://www.okx.com/api/v5/market/candles", params=okx_params, timeout=3)
        if okx_response.status_code == 200:
            raw_data = okx_response.json()
            if raw_data.get("code") == "0" and "data" in raw_data:
                mexc_formatted_data = []
                # OKX streams newest-to-oldest; reverse index arrays to match core calculation algorithms
                for bar in raw_data["data"]:
                    mexc_formatted_data.insert(0, [
                        bar[0],  # Open Time
                        bar[1],  # Open Price
                        bar[2],  # High Price
                        bar[3],  # Low Price
                        bar[4]   # Close Price (Aligned perfectly to Index 4)
                    ])
                return mexc_formatted_data
    except Exception:
        pass

    return None

def run_pure_compression_math(symbol, timeframe):
    """
    Core Part 1 Algorithm Engine.
    Executes the ultimate rule: cond1 AND (cond2 OR cond3)
    Enforces a strict 4-decimal rounding check to guarantee numbers like 0.109% fail.
    
    CRITICAL SMA200 LAW:
    - Banned/Ignored entirely from ALL TOGETHER equations.
    - Active ONLY in determining whether the SPECIAL ONE has occurred.
    """
    candles = fetch_mexc_candles(symbol, timeframe)
    if not candles or len(candles) < 200:
        return {"sqz": False, "type": "NONE"}
    
    # Extract structural bar closing positions
    closes = [float(candle[4]) for candle in candles]
    live_price = closes[-1]
    
    sma20 = calculate_sma(closes, 20)
    sma100 = calculate_sma(closes, 100)
    sma200 = calculate_sma(closes, 200)
    
    # Calculate exact distance ratios rounded strictly to 4 decimal places
    price_to_sma20 = round(abs(live_price - sma20) / live_price, 4)
    sma20_to_sma100 = round(abs(sma20 - sma100) / sma20, 4)
    sma20_to_sma200 = round(abs(sma20 - sma200) / sma20, 4)
    
    # cond1: Price near SMA20 (Must be strictly <= 0.001)
    cond1 = price_to_sma20 <= THRESHOLD
    
    # cond2: SMA20 near SMA100 (ALL TOGETHER - SMA200 is completely blind here)
    cond2 = sma20_to_sma100 <= THRESHOLD
    
    # cond3: SMA20 near SMA200 (SPECIAL ONE - SMA200 is active ONLY here)
    cond3 = sma20_to_sma200 <= THRESHOLD
    
    # Route matching rules independently without cross-talk or visual stacking checks
    if cond1 and cond2:
        return {"sqz": True, "type": "ALL TOGETHER"}
    elif cond1 and cond3:
        return {"sqz": True, "type": "SPECIAL ONE"}
        
    return {"sqz": False, "type": "NONE"}

def fetch_btc_regime_data():
    """
    Part 2 Law: Connects live to MEXC for BTCUSDT and calculates
    the structural regimes dynamically for 15m, 60m, and 4h.
    """
    timeframes_p2 = ["15m", "60m", "4h"]
    results = {}
    
    for tf in timeframes_p2:
        time.sleep(0.15)  # Pacing safety rule remains untouched
        candles = fetch_mexc_candles("BTCUSDT", tf)
        if not candles or len(candles) < 50:
            results[tf] = {"regime": "UNKNOWN", "character": "DATA ERROR"}
            continue
            
        closes = [float(candle[4]) for candle in candles]
        current_price = closes[-1]
        
        # Calculate recent boundary range (last 20 candles)
        recent_window = closes[-20:]
        max_boundary = max(recent_window)
        min_boundary = min(recent_window)
        range_width = (max_boundary - min_boundary) / min_boundary
        
        # Calculate basic 20 SMA for internal box tracking
        sma20 = pd.Series(closes).rolling(window=20).mean().iloc[-1]
        
        # 1.5% threshold determines if it's trapped in a Box or Trending Clear
        if range_width <= 0.015:
            if abs(current_price - sma20) / sma20 <= 0.002:
                results[tf] = {"regime": "RANGING", "character": "INTERNAL BOX"}
            else:
                results[tf] = {"regime": "RANGING", "character": "BOX"}
        else:
            results[tf] = {"regime": "TRENDING", "character": "CLEAR"}
            
    return results


# ==============================================================================
# STREAMLIT USER INTERFACE VIEWPORT (RESTORED TO ORIGINAL SSoT LAYOUT)
# ==============================================================================

# RESTORED TITLE & ICON SPECIFICALLY
st.markdown("## 🛰️ Centralized BTC Market Regime (SSoT Part 2)")

# Pull calculations dynamically out of the live dictionary
btc_data = fetch_btc_regime_data()

regime_table = f"""
| TIMEFRAME | REGIME STATE | STRUCTURE CHARACTER |
| :--- | :--- | :--- |
| 15m | **{btc_data.get('15m', {}).get('regime', 'UNKNOWN')}** | {btc_data.get('15m', {}).get('character', 'DATA ERROR')} |
| 60m | **{btc_data.get('60m', {}).get('regime', 'UNKNOWN')}** | {btc_data.get('60m', {}).get('character', 'DATA ERROR')}  |
| 4h  | **{btc_data.get('4h', {}).get('regime', 'UNKNOWN')}** | {btc_data.get('4h', {}).get('character', 'DATA ERROR')}  |
"""
st.markdown(regime_table)
st.markdown("---")

st.markdown("## 🏹 Strategy Monitor")

# Initialize active tracking structures
all_together_alerts = []
special_one_alerts = []
mega_sqz_alerts = []

# Progressive scanning status window object for tracking loops
progress_text = st.empty()
scan_results = {}

# Background execution matrix loop block directly scanning the WATCHLIST
for idx, asset in enumerate(WATCHLIST, 1):
    progress_text.markdown(f"⏳ *Scanning Watchlist Item {idx}/25:*\n### {asset}")
    
    scan_results[asset] = {}
    
    for tf in TIMEFRAMES:
        res = run_pure_compression_math(asset, tf)
        scan_results[asset][tf] = res
        
    # 🏛️ CODE LAW VALIDATION: MEGA SQZ ANALYSIS
    # 🟩 PATCHED: Validates the live "2m" structural matrix key cleanly
    is_mega_sqz = (
        scan_results[asset]["2m"]["sqz"]
        and scan_results[asset]["5m"]["sqz"]
        and scan_results[asset]["15m"]["sqz"]
    )
    
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

# Keep the tracker display settled cleanly on the completed list
progress_text.markdown(f"✅ *Watchlist Scan Complete (25/25 Assets Checked)*")

# ==============================================================================
# UNFILTERED REPORTING VIEWPORT INTERFACES (PART 1 OUTPUT)
# ==============================================================================

# 1. MEGA SQZ PRESENTATION BANNER LAYER
if mega_sqz_alerts:
    for mega_asset in mega_sqz_alerts:
        st.error(f"🚨 **{mega_asset} MEGA SQZ SYSTEM LOCK: ACTIVE** 🚨")

# 2. STANDARD LOGIC REPORTING TIERS - PATCHED AND VERIFIED
if not mega_sqz_alerts and not all_together_alerts and not special_one_alerts:
    st.info("No active MEGA SQZ, ALL TOGETHER, or SPECIAL ONE states detected.")
else:
    if all_together_alerts:
        st.success(f"🟩 **ALL TOGETHER COMPRESSION ACTIVE:** {', '.join(all_together_alerts)}")
        
    if special_one_alerts:
        st.warning(f"🟦 **SPECIAL ONE COMPRESSION ACTIVE:** {', '.join(special_one_alerts)}")

st.caption(f"Live workspace check timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
