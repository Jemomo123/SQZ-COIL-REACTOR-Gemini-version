import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import logging
import time
from streamlit_autorefresh import st_autorefresh

# --- LOGGING CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- MOBILE UI CONFIG ---
st.set_page_config(page_title="Jeremiah Edge Pro", layout="centered")
st_autorefresh(interval=35000, key="datarefresh")

st.markdown("""
    <style>
    .stAlert { padding: 0.8rem; border-radius: 10px; }
    .stContainer { border: 1px solid #444; padding: 12px; border-radius: 10px; margin-bottom: 12px; }
    .status-dim { color: #555555; font-size: 0.8rem; font-weight: bold; }
    .regime-table { width:100%; border-collapse: collapse; margin-bottom: 15px; }
    .regime-table th, .regime-table td { padding: 8px; border: 1px solid #444; text-align: left; font-size: 0.85rem; }
    .regime-table th { background-color: #262730; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-aligned { background-color: #10b981; color: white; }
    .badge-counter { background-color: #ef4444; color: white; }
    .badge-range { background-color: #3b82f6; color: white; }
    .shield-box { 
        background-color: rgba(59, 130, 246, 0.12); 
        border: 2px solid #3b82f6; 
        padding: 10px; 
        border-radius: 8px; 
        margin-bottom: 15px;
        font-size: 0.85rem;
        color: #1e3a8a;
    }
    .section-header {
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: 900;
        font-size: 0.95rem;
        margin-top: 18px;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
    }
    /* HIGH CONTRAST THEME FOR MOBILE LIGHT/DARK VIEWPORTS */
    .header-meme { background-color: #a855f7; border: 2px solid #7e22ce; color: #ffffff; }
    .header-big { background-color: #eab308; border: 2px solid #b45309; color: #000000; }
    .empty-notice { color: #222222; font-weight: bold; padding: 5px 10px; font-size: 0.85rem; }
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

# --- BIFURCATED WATCHLIST STRUCTURE ---
BIG_CAPS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 
    'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'NEAR/USDT', 'SUI/USDT'
]

MEMECOINS = [
    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 
    'FLOKI/USDT', 'PENGU/USDT', 'BOME/USDT', 'POPCAT/USDT', 'MEW/USDT', 
    'BRETT/USDT', 'TURBO/USDT', 'MOG/USDT', 'MEME/USDT', 'MYRO/USDT'
]

ALL_SYMBOLS = BIG_CAPS + MEMECOINS
TIMEFRAMES = ['3m', '5m', '15m'] 
REGIME_TIMEFRAMES = ['15m', '1h', '4h']
SQZ_LIMIT = 0.001 

# ==============================================================================
# SSoT PART 1: JEREMIAH COMPRESSION ENGINE
# ==============================================================================
def is_jeremiah_compressed(c, s20, s100, s200):
    all_together = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s100)/s20 <= SQZ_LIMIT)
    special_one = (abs(c - s20)/c <= SQZ_LIMIT) and (abs(s20 - s200)/s20 <= SQZ_LIMIT)
    return all_together or special_one

# ==============================================================================
# SSoT PART 2: BTC MARKET REGIME ENGINE
# ==============================================================================
def detect_market_regime(df):
    available_rows = len(df)
    if available_rows < 50: 
        return "TRANSITIONAL", "INSUFFICIENT DATA"
    curr = df.iloc[-1]
    
    s20_lookback = min(5, max(2, available_rows // 20))
    ma20_slope = (df['s20'].iloc[-1] - df['s20'].iloc[-s20_lookback]) / s20_lookback
    ma20_flat = abs(ma20_slope) < (df['c'].rolling(min(14, available_rows)).std().iloc[-1] * 0.02)
    
    structure_window = min(20, available_rows)
    recent_df = df.iloc[-structure_window:]
    higher_highs = df['h'].iloc[-1] >= recent_df['h'].median()
    lower_lows = df['l'].iloc[-1] <= recent_df['l'].median()
    
    overlap_window = min(5, available_rows - 1)
    overlap_count = sum((df['h'].iloc[i] > df['l'].iloc[i-1]) and (df['l'].iloc[i] < df['h'].iloc[i-1]) for i in range(-overlap_window, 0))
    
    osc_window = min(10, available_rows - 1)
    oscillating = sum((df['c'].iloc[i] > df['s20'].iloc[i] and df['c'].iloc[i-1] < df['s20'].iloc[i-1]) or 
                      (df['c'].iloc[i] < df['s20'].iloc[i] and df['c'].iloc[i-1] > df['s20'].iloc[i-1]) for i in range(-osc_window, 0))

    atr_window = min(14, available_rows)
    atr = (df['h'] - df['l']).rolling(atr_window).mean().iloc[-1]
    recent_mid = recent_df['c'].median()
    is_contained = abs(curr['c'] - recent_mid) < (2 * atr)
    
    if (ma20_slope > 0 and curr['c'] > curr['s20'] and curr['s20'] > curr['s100'] and higher_highs and oscillating < 4):
        return "TRENDING_UP", "CLEAN TREND"
    if (ma20_slope < 0 and curr['c'] < curr['s20'] and curr['s20'] < curr['s100'] and lower_lows and oscillating < 4):
        return "TRENDING_DOWN", "CLEAN TREND"
    if not is_contained && abs(curr['c'] - curr['o']) > (1.5 * atr):
        if (curr['c'] > curr['o'] and ma20_slope > 0) or (curr['c'] < curr['o'] and ma20_slope < 0):
            return "RANGE_EXPANSION", "STRUCTURAL RELEASE"
    if ma20_flat or overlap_count >= 3 or oscillating >= 4:
        return "RANGING", "INTERNAL BOX"

    return "TRANSITIONAL", "MOMENTUM REBALANCING"

# ==============================================================================
# SECURE DATA ACQUISITION ENGINE
# ==============================================================================
def safe_fetch_ohlcv(symbol, tf, limit):
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
            df = df.dropna().reset_index(drop=True)
            
            time.sleep(0.04) 
            return df, name
        except Exception:
            continue
    return None, None

def get_timeframe_signal(symbol, tf, btc_regimes):
    df, source_name = safe_fetch_ohlcv(symbol, tf, limit=210) 
    if df is None or len(df) < 25:
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
    is_liquidity_hole = False
    curr_efficiency = 0.0
    avg_historical_efficiency = 0.0

    target_macro_tf = "15m" if tf in ["3m", "5m"] else "1h"
    macro_data = btc_regimes.get(target_macro_tf, {"state": "TRANSITIONAL"})
    macro_state = macro_data.get("state", "TRANSITIONAL")

    curr_body = abs(curr['c'] - curr['o'])
    if has_valid_cluster and not is_currently_sqz:
        is_moving = abs(curr['c'] - curr['s20'])/curr['c'] > SQZ_LIMIT
        avg_cluster_body = sum(abs(row['c'] - row['o']) for row in cluster_candles) / len(cluster_candles)
        
        if is_moving and curr_body > avg_cluster_body:
            if curr['c'] > curr['o'] and curr['c'] > curr['s20']:
                direction = "BULLISH"; found_expansion = True
            elif curr['c'] < curr['o'] and curr['c'] < curr['s20']:
                direction = "BEARISH"; found_expansion = True

    # --- PART 3 SCANNER ENGINE ---
    if curr['v'] > 0:
        curr_efficiency = curr_body / curr['v']
        historical_bodies = abs(df['c'].iloc[-21:-1] - df['o'].iloc[-21:-1])
        historical_volumes = df['v'].iloc[-21:-1].replace(0, 1)
        avg_historical_efficiency = (historical_bodies / historical_volumes).mean()
        
        if found_expansion and curr_efficiency > (avg_historical_efficiency * 1.8):
            is_liquidity_hole = True

    if found_expansion:
        if is_liquidity_hole:
            context_flags.append("<span class='badge' style='background-color: #f59e0b; color: black; font-weight: bold;'>⚠️ LIQUIDITY HOLE</span>")
        else:
            if (direction == "BULLISH" and macro_state == "TRENDING_UP") or (direction == "BEARISH" and macro_state == "TRENDING_DOWN"):
                context_flags.append(f"<span class='badge badge-aligned'>ALIGNED BTC {target_macro_tf.upper()}</span>")
            elif macro_state in ["TRENDING_UP", "TRENDING_DOWN"]:
                context_flags.append(f"<span class='badge badge-counter'>COUNTER BTC {target_macro_tf.upper()}</span>")
            if macro_state == "RANGING":
                context_flags.append(f"<span class='badge badge-range'>IN BTC {target_macro_tf.upper()} BOX</span>")

    return {
        "sqz": is_currently_sqz, "expansion": found_expansion, 
        "dir": direction, "price": curr['c'], "status": "ok", 
        "source": source_name, "context": " ".join(context_flags),
        "hole": is_liquidity_hole,
        "curr_ver": curr_efficiency,
        "base_ver": avg_historical_efficiency
    }

# ==============================================================================
# UI INTERFACE DEPLOYMENT
# ==============================================================================

st.markdown("### 📡 Centralized BTC Market Regime (SSoT Part 2)")
btc_regimes = {}

for tf in REGIME_TIMEFRAMES:
    btc_df, _ = safe_fetch_ohlcv('BTC/USDT', tf, limit=600)
    if btc_df is not None:
        state, structure = detect_market_regime(btc_df)
        btc_regimes[tf] = {"state": state, "structure": structure}

if btc_regimes:
    html_table = "<table class='regime-table'><thead><tr><th>TIMEFRAME</th><th>REGIME STATE</th><th>STRUCTURE CHARACTER</th></tr></thead><tbody>"
    for tf in REGIME_TIMEFRAMES:
        if tf in btc_regimes:
            state = btc_regimes[tf]["state"]
            struct = btc_regimes[tf]["structure"]
            color = "#10b981" if "UP" in state else "#ef4444" if "DOWN" in state else "#3b82f6" if "RANGE" in state else "#555555"
            html_table += f"<tr><td><b>{tf}</b></td><td style='color:{color}; font-weight:bold;'>{state}</td><td>{struct}</td></tr>"
    html_table += "</tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)

# --- VISIBLE PART 3 SHIELD BADGE ---
st.markdown(f"""
    <div class="shield-box">
        🛡️ <b>PART 3 LIQUIDITY SHIELD ACTIVE</b><br>
        <span style="color: #333333; font-size: 0.8rem; font-weight: bold;">
            Monitoring 10 Institutional Assets & 15 Meme Futures Assets. Pinned to 1.8x Delta Limit.
        </span>
    </div>
""", unsafe_allow_html=True)

st.divider()

st.subheader("🏹 Strategy Monitor")

meme_signals = []
bigcap_signals = []
btc_monitored_stats = []

for symbol in ALL_SYMBOLS:
    tf_results = {}
    for tf in TIMEFRAMES:
        res = get_timeframe_signal(symbol, tf, btc_regimes)
        if res["status"] == "ok":
            tf_results[tf] = res
            if tf == '3m' and symbol == 'BTC/USDT':
                btc_monitored_stats = (res["curr_ver"], res["base_ver"])

    if not tf_results: continue
    is_mega = all(tf_results.get(tf, {}).get("sqz", False) for tf in TIMEFRAMES)
    
    if is_mega or any(res["sqz"] or res["expansion"] for res in tf_results.values()):
        display_price = next((res["price"] for res in tf_results.values()), "N/A")
        
        signal_payload = {
            "symbol": symbol,
            "price": display_price,
            "is_mega": is_mega,
            "timeframes": tf_results
        }
        
        if symbol in MEMECOINS:
            meme_signals.append(signal_payload)
        else:
            bigcap_signals.append(signal_payload)

# --- DISPLAY RENDER LOOP 1: MEMECOIN FUTURES SECTION ---
st.markdown('<div class="section-header header-meme">🔮 VOLATILE MEMECOIN FUTURES (15 ASSETS)</div>', unsafe_allow_html=True)
if not meme_signals:
    st.markdown("<p class='empty-notice'>⚡ No active compressions or expansions in Memecoins.</p>", unsafe_allow_html=True)
else:
    for sig in meme_signals:
        with st.container():
            st.write(f"### {sig['symbol']} | ${sig['price']}")
            if sig['is_mega']: st.error("🚨 MEGA SQZ: Triple Timeframe Compression")
            for tf in TIMEFRAMES:
                res = sig['timeframes'].get(tf)
                if not res: continue
                source_tag = f"<span class='status-dim'>[{res['source']}]</span>"
                
                if res["expansion"]:
                    bg_color = "rgba(245, 158, 11, 0.15)" if res["hole"] else "rgba(168, 85, 247, 0.15)"
                    border_color = "#f59e0b" if res["hole"] else "#7e22ce"
                    title_text = f"⚠️ <b>{tf} {res['dir']} HOLLOW RELEASE:</b>" if res["hole"] else f"💥 <b>{tf} {res['dir']} RELEASE:</b>"
                    st.markdown(f'<div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; border-left: 5px solid {border_color}; margin-bottom: 8px; color: #000000;">{title_text} Elephant Bar {source_tag}<br>{res["context"]}</div>', unsafe_allow_html=True)
                elif res["sqz"]:
                    st.markdown(f"🧬 **{tf}:** Active Jeremiah Compression {source_tag}", unsafe_allow_html=True)

# --- DISPLAY RENDER LOOP 2: INSTITUTIONAL BIG CAPS SECTION ---
st.markdown('<div class="section-header header-big">👑 INSTITUTIONAL BIG CAPS (10 ASSETS)</div>', unsafe_allow_html=True)
if not bigcap_signals:
    st.markdown("<p class='empty-notice'>⭐ No active compressions or expansions in Big Caps.</p>", unsafe_allow_html=True)
else:
    for sig in bigcap_signals:
        with st.container():
            st.write(f"### {sig['symbol']} | ${sig['price']}")
            if sig['is_mega']: st.error("🚨 MEGA SQZ: Triple Timeframe Compression")
            for tf in TIMEFRAMES:
                res = sig['timeframes'].get(tf)
                if not res: continue
                source_tag = f"<span class='status-dim'>[{res['source']}]</span>"
                
                if res["expansion"]:
                    bg_color = "rgba(245, 158, 11, 0.15)" if res["hole"] else "rgba(16, 185, 129, 0.15)"
                    border_color = "#f59e0b" if res["hole"] else "#10b981"
                    title_text = f"⚠️ <b>{tf} {res['dir']} HOLLOW RELEASE:</b>" if res["hole"] else f"💥 <b>{tf} {res['dir']} RELEASE:</b>"
                    st.markdown(f'<div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; border-left: 5px solid {border_color}; margin-bottom: 8px; color: #000000;">{title_text} Elephant Bar {source_tag}<br>{res["context"]}</div>', unsafe_allow_html=True)
                elif res["sqz"]:
                    st.markdown(f"🧬 **{tf}:** Active Jeremiah Compression {source_tag}", unsafe_allow_html=True)

# --- LIVE RECON FEED DATA ---
if btc_monitored_stats:
    st.markdown(f"""
        <p style="font-size: 0.8rem; color: #111111; margin-top:20px; font-weight: bold;">
            📊 Live Book Feed (BTC 3m) | Run: {btc_monitored_stats[0]:.5f} vs Shield Target: {(btc_monitored_stats[1]*1.8):.5f}
        </p>
    """, unsafe_allow_html=True)

st.divider()
st.caption(f"Heartbeat: {pd.Timestamp.now().strftime('%H:%M:%S')} | SSoT V9 (High Contrast Mobile Interface)")
