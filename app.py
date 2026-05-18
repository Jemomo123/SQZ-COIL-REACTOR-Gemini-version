import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import logging
from streamlit_autorefresh import st_autorefresh

# --- LOGGING CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- MOBILE UI CONFIG ---
st.set_page_config(page_title="Jeremiah Edge Pro", layout="centered")
st_autorefresh(interval=30000, key="datarefresh")

st.markdown("""
    <style>
    .stAlert { padding: 0.8rem; border-radius: 10px; }
    .stContainer { border: 1px solid #444; padding: 12px; border-radius: 10px; margin-bottom: 12px; }
    .status-dim { color: #888; font-size: 0.75rem; }
    .regime-table { width:100%; border-collapse: collapse; margin-bottom: 15px; }
    .regime-table th, .regime-table td { padding: 8px; border: 1px solid #444; text-align: left; font-size: 0.85rem; }
    .regime-table th { background-color: #262730; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-aligned { background-color: #10b981; color: white; }
    .badge-counter { background-color: #ef4444; color: white; }
    .badge-range { background-color: #3b82f6; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 JEREMIAH EDGE PRO")

# --- CENTRALIZED CLUSTER ---
EXCHANGE_CHAIN = [
    {"name": "Binance", "obj": ccxt.binance({'enableRateLimit': True})},
    {"name": "OKX",     "obj": ccxt.okx({'enableRateLimit': True})},
    {"name": "MEXC",    "obj": ccxt.mexc({'enableRateLimit': True})},
    {"name": "GateIO",  "obj": ccxt.gateio({'enableRateLimit': True})}
]

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
TIMEFRAMES = ['3m', '5m', '15m'] 
REGIME_TIMEFRAMES = ['15m', '1h', '4h']
SQZ_LIMIT = 0.001 

# ==============================================================================
# SINGLE SOURCE OF TRUTH (SSoT) PART 1: JEREMIAH COMPRESSION ENGINE
# ==============================================================================
def is_jeremiah_compressed(c, s20, s100, s200):
    """Centralized gatekeeper for mathematical volatility compression."""
    all_together = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s100)/s20 <= SQZ_LIMIT)
    special_one = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s200)/s20 <= SQZ_LIMIT)
    return all_together or special_one

# ==============================================================================
# SINGLE SOURCE OF TRUTH (SSoT) PART 2: BTC MARKET REGIME ENGINE
# ==============================================================================
def detect_market_regime(df):
    """
    Centralized Single Source of Truth for Institutional Market Structure.
    Strictly forbidden from using or calling compression variables.
    """
    if len(df) < 200:  # Validates deep dataset availability
        return "TRANSITIONAL", "INSUFFICIENT DATA"
    
    curr = df.iloc[-1]
    
    # 1. Slope Vectors (Directional Persistence)
    s20_lookback = 5
    ma20_slope = (df['s20'].iloc[-1] - df['s20'].iloc[-s20_lookback]) / s20_lookback
    
    # Threshold based on directional standard deviation fraction
    ma20_flat = abs(ma20_slope) < (df['c'].rolling(14).std().iloc[-1] * 0.02)
    
    # 2. Structural Highs/Lows (Pivots over 20 candles)
    recent_df = df.iloc[-20:]
    higher_highs = df['h'].iloc[-1] >= recent_df['h'].median()
    lower_lows = df['l'].iloc[-1] <= recent_df['l'].median()
    
    # 3. Rotational & Candle Overlap Metrics
    overlap_count = sum((df['h'].iloc[i] > df['l'].iloc[i-1]) and (df['l'].iloc[i] < df['h'].iloc[i-1]) for i in range(-5, 0))
    oscillating = sum((df['c'].iloc[i] > df['s20'].iloc[i] and df['c'].iloc[i-1] < df['s20'].iloc[i-1]) or 
                      (df['c'].iloc[i] < df['s20'].iloc[i] and df['c'].iloc[i-1] > df['s20'].iloc[i-1]) for i in range(-10, 0))

    # 4. ATR Displacement (Breakout Validity & Volatility Realization)
    atr = (df['h'] - df['l']).rolling(14).mean().iloc[-1]
    recent_mid = recent_df['c'].median()
    is_contained = abs(curr['c'] - recent_mid) < (2 * atr)
    
    # --- RIGID ALGORITHMIC CLASSIFICATION PIPELINE ---
    
    # A. TRENDING_UP
    if (ma20_slope > 0 and curr['c'] > curr['s20'] and curr['s20'] > curr['s100'] and higher_highs and oscillating < 4):
        return "TRENDING_UP", "CLEAN TREND"
        
    # B. TRENDING_DOWN
    if (ma20_slope < 0 and curr['c'] < curr['s20'] and curr['s20'] < curr['s100'] and lower_lows and oscillating < 4):
        return "TRENDING_DOWN", "CLEAN TREND"
        
    # C. RANGE_EXPANSION
    if not is_contained and abs(curr['c'] - curr['o']) > (1.5 * atr):
        if (curr['c'] > curr['o'] and ma20_slope > 0) or (curr['c'] < curr['o'] and ma20_slope < 0):
            return "RANGE_EXPANSION", "STRUCTURAL RELEASE"

    # D. RANGING
    if ma20_flat or overlap_count >= 3 or oscillating >= 4:
        return "RANGING", "INTERNAL BOX"

    # E. TRANSITIONAL
    return "TRANSITIONAL", "MOMENTUM REBALANCING"


# ==============================================================================
# SECURE ACQUISITION LAYER
# ==============================================================================
def safe_fetch_ohlcv(symbol, tf, limit=210):
    for exchange_info in EXCHANGE_CHAIN:
        try:
            ex_obj = exchange_info["obj"]
            name = exchange_info["name"]
            fetch_symbol = symbol if name != "OKX" else symbol.replace("/", "-")
            
            bars = ex_obj.fetch_ohlcv(fetch_symbol, timeframe=tf, limit=limit)
            df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['s20'] = df['c'].rolling(20).mean()
            df['s100'] = df['c'].rolling(100).mean()
            df['s200'] = df['c'].rolling(200).mean()
            return df.dropna().reset_index(drop=True), name
        except Exception as e:
            continue
    return None, None

def get_timeframe_signal(symbol, tf, btc_regimes):
    df, source_name = safe_fetch_ohlcv(symbol, tf, limit=210)
    if df is None:
        return {"status": "fail"}
        
    cluster_candles = []
    wobble_count = 0
    for i in range(len(df)-2, 0, -1):
        row = df.iloc[i]
        if is_jeremiah_compressed(row['c'], row['s20'], row['s100'], row['s200']):
            cluster_candles.append(row)
            wobble_count = 0 
        else:
            wobble_count += 1
            if wobble_count > 1: break 
            
    has_valid_cluster = len(cluster_candles) >= 1
    curr = df.iloc[-1]
    is_currently_sqz = is_jeremiah_compressed(curr['c'], curr['s20'], curr['s100'], curr['s200'])

    found_expansion = False
    direction = None
    context_flags = []

    if has_valid_cluster and not is_currently_sqz:
        is_moving = abs(curr['c'] - curr['s20'])/curr['c'] > SQZ_LIMIT
        curr_body = abs(curr['c'] - curr['o'])
        avg_cluster_body = sum(abs(row['c'] - row['o']) for row in cluster_candles) / len(cluster_candles)
        
        if is_moving and curr_body > avg_cluster_body:
            if curr['c'] > curr['o'] and curr['c'] > curr['s20']:
                direction = "BULLISH"; found_expansion = True
            elif curr['c'] < curr['o'] and curr['c'] < curr['s20']:
                direction = "BEARISH"; found_expansion = True

    # --- SSoT INTEGRATION: CONTEXT-AWARE CONFLATION ---
    if found_expansion and btc_regimes:
        h4_state = btc_regimes.get("4h", {}).get("state", "TRANSITIONAL")
        h1_state = btc_regimes.get("1h", {}).get("state", "TRANSITIONAL")
        
        if (direction == "BULLISH" and h4_state == "TRENDING_UP") or (direction == "BEARISH" and h4_state == "TRENDING_DOWN"):
            context_flags.append("<span class='badge badge-aligned'>ALIGNED WITH 4H TREND</span>")
        elif h4_state in ["TRENDING_UP", "TRENDING_DOWN"]:
            context_flags.append("<span class='badge badge-counter'>COUNTER-TREND RELEASE</span>")
            
        if h1_state == "RANGING":
            context_flags.append("<span class='badge badge-range'>INSIDE 1H STRUCTURAL BOX</span>")
        elif h1_state == "RANGE_EXPANSION":
            context_flags.append("<span class='badge badge-aligned'>1H BREAKOUT ATTEMPT</span>")

    return {
        "sqz": is_currently_sqz, "expansion": found_expansion, 
        "dir": direction, "price": curr['c'], "status": "ok", 
        "source": source_name, "context": " ".join(context_flags)
    }

# ==============================================================================
# UI INTERFACE PRODUCTION
# ==============================================================================

# --- PART 2 APPLICATION DISPLAY: BTC REGIME ENGINE ---
st.markdown("### 📡 Centralized BTC Market Regime (SSoT Part 2)")
btc_regimes = {}

# --- UPDATE 1: REGIME ENGINE FETCH DEPTH SET TO 210 ---
for tf in REGIME_TIMEFRAMES:
    btc_df, _ = safe_fetch_ohlcv('BTC/USDT', tf, limit=210)  # Upgraded fetch depth to eliminate INSUFFICIENT DATA
    if btc_df is not None:
        state, structure = detect_market_regime(btc_df)
        btc_regimes[tf] = {"state": state, "structure": structure}

if btc_regimes:
    html_table = "<table class='regime-table'><thead><tr><th>TIMEFRAME</th><th>REGIME STATE</th><th>STRUCTURE CHARACTER</th></tr></thead><tbody>"
    for tf in REGIME_TIMEFRAMES:
        if tf in btc_regimes:
            state = btc_regimes[tf]["state"]
            struct = btc_regimes[tf]["structure"]
            color = "#10b981" if "UP" in state else "#ef4444" if "DOWN" in state else "#3b82f6" if "RANGE" in state else "#888888"
            html_table += f"<tr><td><b>{tf}</b></td><td style='color:{color}; font-weight:bold;'>{state}</td><td>{struct}</td></tr>"
    html_table += "</tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)
else:
    st.error("🚨 SSoT Regime Query Failed.")

st.divider()

# --- CORES SIGNAL DISPLAY ---
st.subheader("🏹 Context-Aware Strategy Monitor")
found_signal = False
outages = []

for symbol in SYMBOLS:
    tf_results = {}
    for tf in TIMEFRAMES:
        res = get_timeframe_signal(symbol, tf, btc_regimes)
        if res["status"] == "ok":
            tf_results[tf] = res
        else:
            outages.append(f"{symbol} {tf}")

    if not tf_results: continue

    is_mega = all(tf_results.get(tf, {}).get("sqz", False) for tf in TIMEFRAMES)
    
    if is_mega or any(res["sqz"] or res["expansion"] for res in tf_results.values()):
        found_signal = True
        display_price = next((res["price"] for res in tf_results.values()), "N/A")
        
        with st.container():
            st.write(f"### {symbol} | ${display_price}")
            if is_mega: st.error("🚨 MEGA SQZ: Triple Timeframe Compression")
            
            for tf in TIMEFRAMES:
                res = tf_results.get(tf)
                if not res: continue
                source_tag = f"<span class='status-dim'>[{res['source']}]</span>"
                
                if res["expansion"]:
                    st.success(f"**{tf} {res['dir']} RELEASE:** Elephant Bar (1x Body) {source_tag}<br>{res['context']}", unsafe_allow_html=True)
                
                # --- UPDATE 2: ACTIVE JEREMIAH COMPRESSION FORMAT FIX ---
                elif res["sqz"]:
                    st.markdown(f"🧬 **{tf}:** Active Jeremiah Compression {source_tag}", unsafe_allow_html=True)

if not found_signal:
    st.info("Scanning... No Jeremiah Edge clusters detected.")

st.divider()
st.caption(f"Heartbeat: {pd.Timestamp.now().strftime('%H:%M:%S')} | Double SSoT Enforcement Matrix")
