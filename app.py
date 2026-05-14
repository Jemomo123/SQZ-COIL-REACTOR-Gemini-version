import streamlit as st
import pandas as pd
import ccxt
from streamlit_autorefresh import st_autorefresh

# --- MOBILE UI CONFIG ---
st.set_page_config(page_title="Jeremiah Edge", layout="centered")
st_autorefresh(interval=30000, key="datarefresh")

st.markdown("""
    <style>
    .stAlert { padding: 0.8rem; border-radius: 10px; }
    .stContainer { border: 1px solid #444; padding: 10px; border-radius: 10px; margin-bottom: 12px; }
    .tf-badge { font-weight: bold; padding: 2px 6px; border-radius: 4px; background: #333; }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 JEREMIAH EDGE")

# --- CORE SETTINGS ---
EXCHANGE = ccxt.mexc()
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
TIMEFRAMES = ['3m', '5m', '15m']
SQZ_LIMIT = 0.001  # 0.1% Threshold

# ==============================================================================
# MASTER VALIDATION FUNCTION (THE SINGLE SOURCE OF TRUTH)
# ==============================================================================
def is_jeremiah_compressed(c, s20, s100, s200):
    """
    CENTRAL ENFORCEMENT: The only place where Jeremiah Edge math lives.
   
    """
    # 1. ALL TOGETHER: Price + SMA20 + SMA100 within 0.1%
    all_together = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s100)/s20 <= SQZ_LIMIT)
    
    # 2. SPECIAL ONE: Price + SMA20 + SMA200 within 0.1%
    special_one = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s200)/s20 <= SQZ_LIMIT)
    
    return all_together or special_one

# ==============================================================================
# INDEPENDENT SIGNAL ENGINE
# ==============================================================================
def get_timeframe_signal(symbol, tf):
    """Processes each timeframe as a standalone tradable environment."""
    try:
        bars = EXCHANGE.fetch_ohlcv(symbol, timeframe=tf, limit=210)
        df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        
        df['s20'] = df['c'].rolling(20).mean()
        df['s100'] = df['c'].rolling(100).mean()
        df['s200'] = df['c'].rolling(200).mean()
        df = df.dropna().reset_index(drop=True)

        # 1. RECURSIVE CLUSTER DETECTION (Calls Master SSoT)
        cluster_candles = []
        wobble_count = 0
        
        for i in range(len(df)-2, 0, -1):
            row = df.iloc[i]
            if is_jeremiah_compressed(row['c'], row['s20'], row['s100'], row['s200']):
                cluster_candles.append(row)
                wobble_count = 0 
            else:
                wobble_count += 1
                if wobble_count > 1: # Wobble Tolerance
                    break
        
        has_valid_cluster = len(cluster_candles) >= 1
        
        # 2. CURRENT STATE (Calls Master SSoT)
        curr = df.iloc[-1]
        is_currently_sqz = is_jeremiah_compressed(curr['c'], curr['s20'], curr['s100'], curr['s200'])

        # 3. INDEPENDENT EXPANSION VALIDATION
        found_expansion = False
        direction = None
        
        if has_valid_cluster and not is_currently_sqz:
            is_moving = abs(curr['c'] - curr['s20'])/curr['c'] > SQZ_LIMIT
            curr_body = abs(curr['c'] - curr['o'])
            avg_cluster_body = sum(abs(row['c'] - row['o']) for row in cluster_candles) / len(cluster_candles)
            
            # 1x Body Expansion Rule
            if is_moving and curr_body > avg_cluster_body:
                if curr['c'] > curr['o'] and curr['c'] > curr['s20']:
                    direction = "BULLISH"
                    found_expansion = True
                elif curr['c'] < curr['o'] and curr['c'] < curr['s20']:
                    direction = "BEARISH"
                    found_expansion = True

        return {
            "sqz": is_currently_sqz,
            "expansion": found_expansion,
            "dir": direction,
            "price": curr['c']
        }
    except:
        return None

# ==============================================================================
# UI & INDEPENDENT MONITORING
# ==============================================================================
st.subheader("📡 Independent Timeframe Monitor")
found_signal = False

for symbol in SYMBOLS:
    tf_results = {}
    for tf in TIMEFRAMES:
        res = get_timeframe_signal(symbol, tf)
        if res: tf_results[tf] = res

    # MEGA SQZ: Higher-order condition (all TFs currently compressed)
    is_mega = all(tf_results[tf]["sqz"] for tf in TIMEFRAMES if tf in tf_results)
    
    # Check if ANY TF has an expansion or squeeze signal
    if is_mega or any(tf_results[tf]["sqz"] or tf_results[tf]["expansion"] for tf in tf_results):
        found_signal = True
        with st.container():
            st.write(f"### {symbol} | ${tf_results['3m']['price']}")
            
            if is_mega:
                st.error("🚨 MEGA SQZ: All-Timeframe Cluster Confirmed")
            
            # Display signals independently by timeframe
            for tf in TIMEFRAMES:
                res = tf_results.get(tf)
                if not res: continue
                
                if res["expansion"]:
                    color = "green" if res["dir"] == "BULLISH" else "red"
                    st.success(f"**{tf} {res['dir']} RELEASE:** Elephant Bar (1x Body Expansion)")
                elif res["sqz"]:
                    st.info(f"**{tf}:** Active Jeremiah Compression Zone")

if not found_signal:
    st.info("Scanning... No Jeremiah Edge clusters detected in 3m, 5m, or 15m.")

st.divider()
st.caption(f"Heartbeat: {pd.Timestamp.now().strftime('%H:%M:%S')} | Architecture: Decentralized SSoT Enforcement")
