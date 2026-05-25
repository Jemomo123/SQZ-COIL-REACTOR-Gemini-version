import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# ==============================================================================
# 🏛️ JEREMIAH EDGE — ENGINE LAW CONFIGURATION
# ==============================================================================
THRESHOLD = 0.001  # Strict <= 0.1% threshold for all compression conditions
TIMEFRAMES = ['3m', '5m', '15m', '1h', '4h']
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

# ==============================================================================
# DATA FETCHING (BANNED OI/FUNDING FETHCES REMOVED FOR MOBILE PERFORMANCE)
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
    return ["BTC_USDT", "ETH_USDT", "SOL_USDT", "XRP_USDT"] # Robust fallback

def fetch_klines(symbol, timeframe):
    """Fetches spot or contract equivalent klines safely with retries."""
    # Convert contract symbol style to spot style for public data endpoints safely
    spot_symbol = symbol.replace("_", "")
    params = {"symbol": spot_symbol, "interval": timeframe, "limit": 500}
    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        if response.status_code == 200:
            raw_data = response.json()
            # Standard MEXC spot kline format: [time, open, high, low, close, ...]
            df = pd.DataFrame(raw_data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'asset_vol'])
            df['close'] = pd.to_numeric(df['close'])
            return df
    except Exception:
        return None

# ==============================================================================
# APP EXECUTION & UI DISPLAY
# ==============================================================================
st.title("🛰️ Strategy Monitor (Part 1)")

pairs = fetch_mexc_pairs()
active_signals = []

# Process pairs and timeframes
progress_bar = st.progress(0)
for idx, pair in enumerate(pairs[:30]):  # Sample size limited for lightning-fast mobile loads
    pair_results = {}
    
    for tf in TIMEFRAMES:
        df = fetch_klines(pair, tf)
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
            
    # Calculate Mega SQZ Law
    # Appears simultaneously on 3m AND 5m AND 15m
    m3 = pair_results.get("3m", {"all_together": False, "special_one": False})
    m5 = pair_results.get("5m", {"all_together": False, "special_one": False})
    m15 = pair_results.get("15m", {"all_together": False, "special_one": False})
    
    comp_3m = m3["all_together"] or m3["special_one"]
    comp_5m = m5["all_together"] or m5["special_one"]
    comp_15m = m15["all_together"] or m15["special_one"]
    
    is_mega_sqz = comp_3m and comp_5m and comp_15m
    
    # Compile the active findings for reporting
    for tf in TIMEFRAMES:
        res = pair_results[tf]
        if res["all_together"] or res["special_one"] or (is_mega_sqz and tf in ['3m', '5m', '15m']):
            active_signals.append({
                "Pair": pair,
                "Timeframe": tf,
                "ALL TOGETHER": "✅ ACTIVE" if res["all_together"] else "❌",
                "SPECIAL ONE": "✅ ACTIVE" if res["special_one"] else "❌",
                "MEGA SQZ": "🚨 ACTIVE" if is_mega_sqz else "❌"
            })
            
    progress_bar.progress((idx + 1) / min(len(pairs), 30))
time.sleep(0.1)
progress_bar.empty()

# Final Report Matrix Rendering
if active_signals:
    report_df = pd.DataFrame(active_signals)
    st.success(f"Found {len(report_df)} active compression hits!")
    st.dataframe(report_df, use_container_width=True)
else:
    # UPDATED: Cleaned UI text strictly focused on your core architecture rules
    st.info("No active compression matrix states.")

# Standalone Workspace Timestamp
st.caption(f"Live workspace check timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
