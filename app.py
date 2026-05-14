import streamlit as st
import pandas as pd
import ccxt
import logging
import time
from streamlit_autorefresh import st_autorefresh

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- MOBILE UI ---
st.set_page_config(page_title="Jeremiah Edge", layout="centered")
st_autorefresh(interval=30000, key="datarefresh")

st.markdown("""
    <style>
    .stAlert { padding: 0.8rem; border-radius: 10px; }
    .stContainer { border: 1px solid #444; padding: 10px; border-radius: 10px; margin-bottom: 12px; }
    .status-dim { color: #888; font-size: 0.75rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 JEREMIAH EDGE")

# --- FAILOVER CHAIN ---
EXCHANGE_CHAIN = [
    {"name": "Binance", "obj": ccxt.binance({'enableRateLimit': True})},
    {"name": "OKX",     "obj": ccxt.okx({'enableRateLimit': True})},
    {"name": "MEXC",    "obj": ccxt.mexc({'enableRateLimit': True})},
    {"name": "GateIO",  "obj": ccxt.gateio({'enableRateLimit': True})}
]

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
TIMEFRAMES = ['3m', '5m', '15m'] 
SQZ_LIMIT = 0.001 

# MASTER VALIDATION (SSoT)
def is_jeremiah_compressed(c, s20, s100, s200):
    all_together = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s100)/s20 <= SQZ_LIMIT)
    special_one = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s200)/s20 <= SQZ_LIMIT)
    return all_together or special_one

# DATA ENGINE
def fetch_and_process(exchange_info, symbol, tf):
    ex_obj = exchange_info["obj"]
    name = exchange_info["name"]
    fetch_symbol = symbol if name != "OKX" else symbol.replace("/", "-")
    
    bars = ex_obj.fetch_ohlcv(fetch_symbol, timeframe=tf, limit=210)
    df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
    
    df['s20'] = df['c'].rolling(20).mean()
    df['s100'] = df['c'].rolling(100).mean()
    df['s200'] = df['c'].rolling(200).mean()
    df = df.dropna().reset_index(drop=True)

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
    if has_valid_cluster and not is_currently_sqz:
        is_moving = abs(curr['c'] - curr['s20'])/curr['c'] > SQZ_LIMIT
        curr_body = abs(curr['c'] - curr['o'])
        avg_cluster_body = sum(abs(row['c'] - row['o']) for row in cluster_candles) / len(cluster_candles)
        
        if is_moving and curr_body > avg_cluster_body:
            if curr['c'] > curr['o'] and curr['c'] > curr['s20']:
                direction = "BULLISH"; found_expansion = True
            elif curr['c'] < curr['o'] and curr['c'] < curr['s20']:
                direction = "BEARISH"; found_expansion = True

    return {"sqz": is_currently_sqz, "expansion": found_expansion, "dir": direction, "price": curr['c'], "status": "ok", "source": name}

def get_timeframe_signal(symbol, tf):
    for exchange_info in EXCHANGE_CHAIN:
        try:
            return fetch_and_process(exchange_info, symbol, tf)
        except:
            continue 
    return {"status": "fail"}

# UI MONITORING
st.subheader("📡 Automatic Failover Cluster")
found_signal = False
outages = []

for symbol in SYMBOLS:
    tf_results = {}
    for tf in TIMEFRAMES:
        res = get_timeframe_signal(symbol, tf)
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
                    st.success(f"**{tf} {res['dir']} RELEASE:** Elephant Bar (1x Body) {source_tag}")
                elif res["sqz"]:
                    st.info(f"**{tf}:** Active Jeremiah Compression {source_tag}")

if not found_signal:
    st.info("Scanning... No Jeremiah Edge clusters detected.")

st.divider()
st.caption(f"Heartbeat: {pd.Timestamp.now().strftime('%H:%M:%S')} | Source of Truth Architecture")
