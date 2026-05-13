import streamlit as st
import pandas as pd
import ccxt
from streamlit_autorefresh import st_autorefresh

# --- MOBILE UI CONFIG ---
st.set_page_config(page_title="Jeremiah Edge", layout="centered")

# Auto-refresh every 30 seconds to keep data live
st_autorefresh(interval=30000, key="datarefresh")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.5rem; }
    .stAlert { padding: 0.5rem; }
    </style>
""", unsafe_base_with_rows=True)

st.title("🏹 Jeremiah Edge")

# --- FAST ENGINE ---
EXCHANGE = ccxt.mexc()
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
TIMEFRAMES = ['3m', '5m', '15m']
SQZ_LIMIT = 0.001 # 0.1%

def get_signal(symbol, tf):
    try:
        # Fetch minimum candles for SMA200
        bars = EXCHANGE.fetch_ohlcv(symbol, timeframe=tf, limit=201)
        df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        
        c = df['c'].iloc[-1]
        s20 = df['c'].rolling(20).mean().iloc[-1]
        s100 = df['c'].rolling(100).mean().iloc[-1]
        s200 = df['c'].rolling(200).mean().iloc[-1]

        # Squeeze Logic
        sqz_100 = abs(c - s20)/c <= SQZ_LIMIT and abs(s20 - s100)/s20 <= SQZ_LIMIT
        sqz_200 = abs(c - s20)/c <= SQZ_LIMIT and abs(s20 - s200)/s20 <= SQZ_LIMIT
        
        # Expansion (Elephant Bar) Logic
        prev_c = df['c'].iloc[-2]
        prev_s20 = df['c'].rolling(20).mean().iloc[-2]
        was_sqz = abs(prev_c - prev_s20)/prev_c <= SQZ_LIMIT
        is_expansion = was_sqz and abs(c - s20)/c > SQZ_LIMIT

        return {"sqz": sqz_100 or sqz_200, "expansion": is_expansion, "price": c}
    except:
        return None

# --- SCANNER LOOP ---
cols = st.columns(1) # Stacked for mobile
active_alerts = []

for symbol in SYMBOLS:
    tf_data = {}
    for tf in TIMEFRAMES:
        res = get_signal(symbol, tf)
        if res: tf_data[tf] = res

    # Logic: MEGA SQZ
    is_mega = all(tf_data[t]["sqz"] for t in TIMEFRAMES if t in tf_data)
    
    # Logic: Expansion
    expansion_tfs = [t for t, d in tf_data.items() if d["expansion"]]

    if is_mega or expansion_tfs:
        with st.container(border=True):
            st.subheader(f"🔥 {symbol}")
            if is_mega:
                st.error("MEGA SQZ: 3m + 5m + 15m COMPRESSION")
            for t in expansion_tfs:
                st.success(f"EXPANSION: {t} Elephant Bar")
            st.caption(f"Price: {tf_data['3m']['price']}")

st.caption("Last Update: " + pd.Timestamp.now().strftime("%H:%M:%S"))
