import streamlit as st
import pandas as pd
import ccxt
from streamlit_autorefresh import st_autorefresh

# --- MOBILE UI CONFIG ---
st.set_page_config(page_title="Jeremiah Edge", layout="centered")

# Auto-refresh every 30 seconds to keep data live on your mobile browser
st_autorefresh(interval=30000, key="datarefresh")

# Corrected CSS styling for mobile visibility
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.5rem; }
    .stAlert { padding: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 Jeremiah Edge")

# --- FAST ENGINE ---
EXCHANGE = ccxt.mexc()
# Manual list for stability as requested
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
TIMEFRAMES = ['3m', '5m', '15m']
SQZ_LIMIT = 0.001  # Strict 0.1% compression threshold

def get_signal(symbol, tf):
    try:
        # Fetch minimum candles for SMA20, 100, and 200
        bars = EXCHANGE.fetch_ohlcv(symbol, timeframe=tf, limit=201)
        df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        
        c = df['c'].iloc[-1]
        s20 = df['c'].rolling(20).mean().iloc[-1]
        s100 = df['c'].rolling(100).mean().iloc[-1]
        s200 = df['c'].rolling(200).mean().iloc[-1]

        # 1. ALL TOGETHER (Price + 20 + 100)
        sqz_100 = abs(c - s20)/c <= SQZ_LIMIT and abs(s20 - s100)/s20 <= SQZ_LIMIT
        
        # 2. SPECIAL ONE (Price + 20 + 200)
        sqz_200 = abs(c - s20)/c <= SQZ_LIMIT and abs(s20 - s200)/s20 <= SQZ_LIMIT
        
        # 4. ELEPHANT BAR (Expansion Check)
        prev_c = df['c'].iloc[-2]
        prev_s20 = df['c'].rolling(20).mean().iloc[-2]
        was_sqz = abs(prev_c - prev_s20)/prev_c <= SQZ_LIMIT
        is_expansion = was_sqz and abs(c - s20)/c > SQZ_LIMIT

        return {"sqz": sqz_100 or sqz_200, "expansion": is_expansion, "price": c}
    except:
        return None

# --- SCANNER DISPLAY ---
st.subheader("📡 Live Market Scan")
status_placeholder = st.empty()
found_signal = False

# Loop through each coin and check for compression/expansion
for symbol in SYMBOLS:
    tf_data = {}
    for tf in TIMEFRAMES:
        res = get_signal(symbol, tf)
        if res:
            tf_data[tf] = res

    # 3. MEGA SQZ: Triggered if squeeze appears on all timeframes
    is_mega = all(tf_data[t]["sqz"] for t in TIMEFRAMES if t in tf_data)
    
    # Detect which timeframes have an expansion candle
    expansion_tfs = [t for t, d in tf_data.items() if d["expansion"]]

    # UI output if a signal is found
    if is_mega or expansion_tfs:
        found_signal = True
        with st.container(border=True):
            st.write(f"### 🔥 {symbol}")
            if is_mega:
                st.error("MEGA SQZ: 3m + 5m + 15m COMPRESSION")
            for t in expansion_tfs:
                st.success(f"EXPANSION: {t} Elephant Bar")
            st.caption(f"Current Price: {tf_data['3m']['price']}")

# If no signals meet the strict 0.1% rule, show a status message
if not found_signal:
    st.info("Scanning... No 0.1% compression clusters found right now.")

st.divider()
st.caption("Last Heartbeat: " + pd.Timestamp.now().strftime("%H:%M:%S"))
