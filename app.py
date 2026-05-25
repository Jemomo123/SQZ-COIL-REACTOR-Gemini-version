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
TIMEFRAMES = ["3m", "5m", "15m"]
THRESHOLD = 0.001  # Hard steel wall ceiling: <= 0.1%

# Full Matrix Asset Pool (25 Tokens)
MATRIX_ASSETS = [
    "BOMEUSDT", "POPCATUSDT", "SHIBUSDT", "DOGEUSDT", "PEPEUSDT", 
    "WIFUSDT", "SOLUSDT", "BTCUSDT", "ETHUSDT", "BONKUSDT",
    "FLOKIUSDT", "MEMEUSDT", "ORDIUSDT", "SATSUSDT", "RATSUSDT",
    "JUPUSDT", "PYTHUSDT", "TIAUSDT", "INJUSDT", "SEIUSDT",
    "SUIUSDT", "APTUSDT", "OPUSDT", "ARBUSDT", "LINKUSDT"
]

# ==============================================================================
# DATA CALCULATION PIPELINE
# ==============================================================================
def calculate_sma(prices, period):
    """Calculates pure mathematical Simple Moving Average."""
    return pd.Series(prices).rolling(window=period).mean().iloc[-1]

def fetch_mexc_candles(symbol, timeframe):
    """Fetches high-integrity historical bars from MEXC public channels."""
    params = {
        "symbol": symbol,
        "interval": timeframe,
        "limit": 250  # Must be sufficient to construct deep SMA200 metrics
    }
    try:
        response = requests.get(EXCHANGE_API_URL, params=params, timeout=3)
        if response.status_code == 200:
            return response.json()
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
    Part 2: Centralized BTC Market Regime Mock Feed.
    This component returns structural tracking markers for interface presentation.
    """
    return {
        "15m": {"regime": "RANGING", "character": "INTERNAL BOX"},
        "1h": {"regime": "RANGING", "character": "INTERNAL BOX"},
        "4h": {"regime": "RANGING", "character": "INTERNAL BOX"}
    }

# ==============================================================================
# STREAMLIT USER INTERFACE VIEWPORT (MOBILE RUNTIME ENVIRONMENT)
# ==============================================================================
st.markdown("### 🏛 *Centralized BTC Market Regime (SSoT Part 2)*")

# Render Part 2 Interface Layout Matrix Box
btc_data = fetch_btc_regime_data()
regime_table = f"""
| TIMEFRAME | REGIME STATE | STRUCTURE CHARACTER |
| :--- | :--- | :--- |
| **15m** | `{btc_data['15m']['regime']}` | {btc_data['15m']['character']} |
| **1h** | `{btc_data['1h']['regime']}` | {btc_data['1h']['character']} |
| **4h** | `{btc_data['4h']['regime']}` | {btc_data['4h']['character']} |
"""
st.markdown(regime_table)
st.markdown("---")

st.markdown("### 📡 *Strategy Monitor (Part 1)*")

# Initialize active tracking structures
all_together_alerts = []
special_one_alerts = []
mega_sqz_alerts = []

# Progressive scanning status window object for tracking loops
progress_text = st.empty()
scan_results = {}

# Background execution matrix loop block
for idx, asset in enumerate(MATRIX_ASSETS, 1):
    progress_text.markdown(f"⏳ *Scanning Matrix Block {idx}/25: {asset}*")
    
    scan_results[asset] = {}
    
    for tf in TIMEFRAMES:
        res = run_pure_compression_math(asset, tf)
        scan_results[asset][tf] = res
        
    # 🏛️ CODE LAW VALIDATION: MEGA SQZ ANALYSIS
    is_mega_sqz = (
        scan_results[asset]["3m"]["sqz"]
        and scan_results[asset]["5m"]["sqz"]
        and scan_results[asset]["15m"]["sqz"]
    )
    
    if is_mega_sqz:
        mega_sqz_alerts.append(asset)
    else:
        # Sort out distinct components when timelines do not fully overlap
        for tf in TIMEFRAMES:
            if scan_results[asset][tf]["sqz"]:
                alert_entry = f"**{asset}** ({tf})"
                if scan_results[asset][tf]["type"] == "ALL TOGETHER":
                    all_together_alerts.append(alert_entry)
                elif scan_results[asset][tf]["type"] == "SPECIAL ONE":
                    special_one_alerts.append(alert_entry)

# Sweep status container clean
progress_text.empty()

# ==============================================================================
# UNFILTERED REPORTING VIEWPORT INTERFACES
# ==============================================================================

# 1. MEGA SQZ PRESENTATION BANNER LAYER
if mega_sqz_alerts:
    for mega_asset in mega_sqz_alerts:
        st.error(f"🚨 **{mega_asset} MEGA SQZ SYSTEM LOCK: ACTIVE** 🚨")

# 2. STANDARD LOGIC REPORTING TIERS
if not mega_sqz_alerts and not all_together_alerts and not special_one_alerts:
    st.info("No active compression or expansion matrix states.")
else:
    if all_together_alerts:
        st.success(f"🟩 **ALL TOGETHER COMPRESSION ACTIVE:** {', '.join(all_together_alerts)}")
        
    if special_one_alerts:
        st.warning(f"🟦 **SPECIAL ONE COMPRESSION ACTIVE:** {', '.join(special_one_alerts)}")

st.caption(f"Live workspace check timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
