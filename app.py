import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# ==============================================================================
# 🏛️ JEREMIAH EDGE — ENGINE LAW CONFIGURATION
# ==============================================================================
THRESHOLD = 0.001  # Strict <= 0.1% threshold for all compression conditions
TIMEFRAMES_P1 = ['3m', '5m', '15m', '1h', '4h']
TIMEFRAMES_P2 = ['15m', '1h', '4h']
BASE_URL = "https://api.mexc.com/api/v3/klines"

st.set_page_config(page_title="Prop Sniper Radar", layout="wide")

# Custom CSS to force clean mobile viewing
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 100%; padding: 1rem; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .stTable { font-size: 0.9rem !important; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# CORE MATHEMATICAL ENGINE
# ==============================================================================
def calculate_smas(df):
    """Calculates Simple Moving Averages strictly from price history."""
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['sma100'] = df['close'].rolling(window=100).mean()
    df['sma200'] = df['close'].rolling(window=200).mean()
    return df

def check_compression_math(price, sma20, sma100, sma200):
    """
    Core Law: cond1 AND (cond2 OR cond3)
    cond1: Price near SMA20
    cond2: SMA20 near SMA100  -> ALL TOGETHER
    cond3: SMA20 near SMA200  -> SPECIAL ONE
    """
    if pd.isna(price) or pd.isna(sma20):
        return {"all_together": False, "special_one": False}
        
    # cond1: Price near SMA20 (<= 0.1%)
    price_to_sma20 = abs(price - sma20) / sma20
    cond1 = price_to_sma20 <= THRESHOLD
    
    if not cond1:
        return {"all_together": False, "special_one": False}
        
    # cond2: SMA20 near SMA100 (<= 0.1%)
    all_together = False
    if not pd.isna(sma100):
        sma20_to_sma100 = abs(sma20 - sma100) / sma100
        all_together = sma20_to_sma100 <= THRESHOLD

    # cond3: SMA20 near SMA200 (<= 0.1%)
    special_one = False
    if not pd.isna(sma200):
        sma20_to_sma200 = abs(sma20 - sma200) / sma200
        special_one = sma20_to_sma200 <= THRESHOLD

    return {"all_together": all_together, "special_one": special_one}

def calculate_market_regime(df):
    """Determines HTF market regime based on candle structures (BOX / INTERNAL BOX / RANGING)."""
    if df is None or len(df) < 50:
        return "UNKNOWN", "NORMAL"
    
    # Simple, high-performance logic to detect ranging/box structures for mobile display
    recent_closes = df['close'].tail(20)
    max_price = recent_closes.max()
    min_price = recent_closes.min()
    current_price = df['close'].iloc[-1]
    
    # If price is moving sideways within a tight recent boundary
    if (max_price - min_price) / min_price < 0.015:
        if current_price > min_price and current_price < max_price:
            return "RANGING", "INTERNAL BOX"
        return "RANGING", "BOX"
    
    return "TRENDING", "CLEAR"

# ==============================================================================
# DATA FETCHING (BANNED OI/FUNDING FETCHES REMOVED FOR MOBILE PERFORMANCE)
# ==============================================================================
@st.cache_data(ttl=120)
def fetch_mexc_pairs():
    """Fetches all live USDT swap pairs from MEXC."""
    try:
        response = requests.get("https://contract.mexc.com/api/v1/contract/detail")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                return [item["symbol"] for item in data["data"] if item["symbol"].endswith("_USDT")]
    except Exception:
        pass
    return ["BTC_USDT", "ETH_USDT", "SOL_USDT", "XRP_USDT"]

def fetch_klines(symbol, timeframe):
    """Fetches public data endpoints safely."""
    spot_symbol = symbol.replace("_", "")
    params = {"symbol": spot_symbol, "interval": timeframe, "limit": 500}
    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        if response.status_code == 200:
            raw_data = response.json()
            df = pd.DataFrame(raw_data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'asset_vol'])
            df['close'] = pd.to_numeric(df['close'])
            return df
    except Exception:
        return None

# ==============================================================================
# APP EXECUTION & UI DISPLAY
# ==============================================================================
pairs = fetch_mexc_pairs()
current_pair = st.selectbox("Select Target Pair", pairs, index=0)

# ------------------------------------------------------------------------------
# 🏛️ STRATEWAY MONITOR (PART 2) - HIGHER TIMEFRAMES REGIME
# ------------------------------------------------------------------------------
st.subheader("🏛️ Market Regime Monitor (Part 2)")

p2_data = []
for tf in TIMEFRAMES_P2:
    df_p2 = fetch_klines(current_pair, tf)
    if df_p2 is not None:
        regime, structure = calculate_market_regime(df_p2)
        p2_data.append({
            "Timeframe": tf,
            "Regime": regime,
            "Structure": structure
        })

if p2_data:
    p2_df = pd.DataFrame(p2_data)
    st.dataframe(p2_df, use_container_width=True, hide_index=True)

st.write("---")

# ------------------------------------------------------------------------------
# 🛰️ STRATEGY MONITOR (PART 1) - CORE COMPRESSION
# ------------------------------------------------------------------------------
st.title("🛰️ Strategy Monitor (Part 1)")

active_signals = []
pair_results = {}

for tf in TIMEFRAMES_P1:
    df = fetch_klines(current_pair, tf)
    if df is not None and len(df) >= 200:
        df = calculate_smas(df)
        last_row = df.iloc[-1]
        
        math_res = check_compression_math(
            last_row['close'], 
            last_row['sma20'], 
            last_row['sma100'], 
            last_row['sma200']
        )
        
        pair_results[tf] = {
            "all_together": math_res["all_together"],
            "special_one": math_res["special_one"]
        }
    else:
        pair_results[tf] = {"all_together": False, "special_one": False}

# Calculate Mega SQZ Law (Simultaneous 3m AND 5m AND 15m)
m3 = pair_results.get("3m", {"all_together": False, "special_one": False})
m5 = pair_results.get("5m", {"all_together": False, "special_one": False})
m15 = pair_results.get("15m", {"all_together": False, "special_one": False})

comp_3m = m3["all_together"] or m3["special_one"]
comp_5m = m5["all_together"] or m5["special_one"]
comp_15m = m15["all_together"] or m15["special_one"]

is_mega_sqz = comp_3m and comp_5m and comp_15m

for tf in TIMEFRAMES_P1:
    res = pair_results[tf]
    if res["all_together"] or res["special_one"] or (is_mega_sqz and tf in ['3m', '5m', '15m']):
        active_signals.append({
            "Timeframe": tf,
            "ALL TOGETHER": "✅ ACTIVE" if res["all_together"] else "❌",
            "SPECIAL ONE": "✅ ACTIVE" if res["special_one"] else "❌",
            "MEGA SQZ": "🚨 ACTIVE" if is_mega_sqz else "❌"
        })

if active_signals:
    report_df = pd.DataFrame(active_signals)
    st.dataframe(report_df, use_container_width=True, hide_index=True)
else:
    st.info("No active compression matrix states.")

# Standalone Workspace Timestamp
st.caption(f"Live workspace check timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
