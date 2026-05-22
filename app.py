import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import time
from streamlit_autorefresh import st_autorefresh

# ==============================================================================
# ABSOLUTE SYSTEM CONFIGURATION & RATE LIMIT CONTROLS
# ==============================================================================
st.set_page_config(page_title="Jeremiah Edge Pro", layout="centered")
st_autorefresh(interval=35000, key="datarefresh")

# Permanent Asset List (Exactly 25 Assets Monitored Mobile-First)
BIG_CAPS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'LINK/USDT', 'NEAR/USDT', 'SUI/USDT']
MEMECOINS = ['DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT', 'PENGU/USDT', 'BOME/USDT', 'POPCAT/USDT', 'MEW/USDT', 'BRETT/USDT', 'TURBO/USDT', 'MOG/USDT', 'MEME/USDT', 'MYRO/USDT']
ALL_SYMBOLS = BIG_CAPS + MEMECOINS

TIMEFRAMES = ['3m', '5m', '15m']
REGIME_TIMEFRAMES = ['15m', '1h', '4h']

# Initialize Signal Memory Protection (3-minute debounce lock)
if "SIGNAL_MEMORY" not in st.session_state:
    st.session_state["SIGNAL_MEMORY"] = {}

# --- HIGH-CONTRAST SUNLIGHT READABLE UI LAYOUT ---
st.markdown("""
    <style>
    .stAlert { padding: 0.8rem; border-radius: 10px; }
    .stContainer { border: 2px solid #cbd5e1; padding: 14px; border-radius: 10px; margin-bottom: 14px; background-color: #ffffff; }
    .status-dim { color: #64748b; font-size: 0.8rem; font-weight: bold; }
    
    /* Sun-Readable Table Design */
    .regime-table { width:100%; border-collapse: collapse; margin-bottom: 15px; background-color: #ffffff; }
    .regime-table th { background-color: #0f172a; color: #ffffff !important; padding: 10px; border: 2px solid #0f172a; font-size: 0.85rem; font-weight: 900; text-align: left; }
    .regime-table td { padding: 10px; border: 1px solid #cbd5e1; text-align: left; font-size: 0.85rem; color: #0f172a !important; font-weight: bold; }
    
    /* High-Contrast Badges */
    .badge-sqz { background-color: #2563eb; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-weight: 900; font-size: 0.8rem; }
    .badge-mega { background-color: #dc2626; color: #ffffff; padding: 6px 12px; border-radius: 6px; font-weight: 900; font-size: 0.9rem; }
    .badge-expansion { background-color: #16a34a; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-weight: 900; font-size: 0.8rem; }
    .badge-hole { background-color: #ea580c; color: #ffffff; padding: 4px 8px; border-radius: 4px; font-weight: 900; font-size: 0.8rem; border: 2px solid #0f172a; }
    
    .section-header { padding: 10px 14px; border-radius: 6px; font-weight: 900; font-size: 1rem; margin-top: 20px; margin-bottom: 14px; letter-spacing: 0.5px; border: 2px solid #0f172a; }
    .header-meme { background-color: #c084fc; color: #0f172a; }
    .header-big { background-color: #fde047; color: #0f172a; }
    .empty-notice { color: #64748b; font-weight: bold; padding: 8px; font-size: 0.85rem; border: 1px dashed #cbd5e1; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏹 JEREMIAH EDGE PRO")

# --- LIGHTWEIGHT SAFE CCXT EXCHANGE POOL ENGINE ---
EXCHANGE_CHAIN = [
    {"name": "Binance Futures", "obj": ccxt.binance({'enableRateLimit': True, 'timeout': 5000, 'options': {'defaultType': 'future'}})},
    {"name": "OKX Futures",     "obj": ccxt.okx({'enableRateLimit': True, 'timeout': 5000, 'options': {'defaultType': 'swap'}})},
    {"name": "MEXC Futures",    "obj": ccxt.mexc({'enableRateLimit': True, 'timeout': 5000, 'options': {'defaultType': 'swap'}})},
    {"name": "GateIO Futures",  "obj": ccxt.gateio({'enableRateLimit': True, 'timeout': 5000, 'options': {'defaultType': 'swap'}})}
]

def safe_fetch_ohlcv(symbol, tf, limit=150):
    """Bulletproof futures-only lightweight OHLCV fetcher."""
    for exchange_info in EXCHANGE_CHAIN:
        try:
            ex_obj = exchange_info["obj"]
            name = exchange_info["name"]
            fetch_symbol = symbol if "OKX" not in name else symbol.replace("/", "-")
            
            bars = ex_obj.fetch_ohlcv(fetch_symbol, timeframe=tf, limit=limit)
            if not bars: continue
            
            df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            df['s20'] = df['c'].rolling(20).mean()
            df['s100'] = df['c'].rolling(100).mean()
            df['s200'] = df['c'].rolling(200).mean()
            df = df.dropna().reset_index(drop=True)
            return df, name
        except Exception:
            continue
    return None, None

# ==============================================================================
# ENGINE PART 2: BTC MARKET REGIME ENGINE (Pure Context Overlay, Informational Only)
# ==============================================================================
def detect_market_regime(df):
    available_rows = len(df)
    if available_rows < 30: return "TRANSITIONAL", "INSUFFICIENT DATA"
    curr = df.iloc[-1]
    
    # SMA20 Slope Calculation
    s20_lookback = min(5, max(2, available_rows // 20))
    ma20_slope = (df['s20'].iloc[-1] - df['s20'].iloc[-s20_lookback]) / s20_lookback
    ma20_flat = abs(ma20_slope) < (df['c'].rolling(min(14, available_rows)).std().iloc[-1] * 0.02)
    
    # Structure Highs/Lows
    structure_window = min(20, available_rows)
    recent_df = df.iloc[-structure_window:]
    higher_highs = df['h'].iloc[-1] >= recent_df['h'].median()
    lower_lows = df['l'].iloc[-1] <= recent_df['l'].median()
    
    # Candle Overlap and Oscillation Counts
    overlap_count = sum((df['h'].iloc[i] > df['l'].iloc[i-1]) and (df['l'].iloc[i] < df['h'].iloc[i-1]) for i in range(-min(5, available_rows - 1), 0))
    oscillating = sum((df['c'].iloc[i] > df['s20'].iloc[i] and df['c'].iloc[i-1] < df['s20'].iloc[i-1]) or 
                      (df['c'].iloc[i] < df['s20'].iloc[i] and df['c'].iloc[i-1] > df['s20'].iloc[i-1]) for i in range(-min(10, available_rows - 1), 0))

    # ATR Containment Calculation
    atr = (df['h'] - df['l']).rolling(min(14, available_rows)).mean().iloc[-1]
    is_contained = abs(curr['c'] - recent_df['c'].median()) < (2 * atr)
    
    if (ma20_slope > 0 and curr['c'] > curr['s20'] and curr['s20'] > curr['s100'] and higher_highs and oscillating < 4):
        return "TRENDING_UP", "CLEAN TREND"
    if (ma20_slope < 0 and curr['c'] < curr['s20'] and curr['s20'] < curr['s100'] and lower_lows and oscillating < 4):
        return "TRENDING_DOWN", "CLEAN TREND"
    if not is_contained and abs(curr['c'] - curr['o']) > (1.5 * atr):
        if (curr['c'] > curr['o'] and ma20_slope > 0) or (curr['c'] < curr['o'] and ma20_slope < 0):
            return "RANGE_EXPANSION", "STRUCTURAL RELEASE"
    if ma20_flat or overlap_count >= 3 or oscillating >= 4:
        return "RANGING", "INTERNAL BOX"

    return "TRANSITIONAL", "MOMENTUM REBALANCING"

# --- RUN PART 2 FIRST & CACHE INTERNALLY ---
st.markdown("### 📡 Centralized BTC Market Regime (SSoT Part 2)")
btc_regimes = {}

for tf in REGIME_TIMEFRAMES:
    btc_df, _ = safe_fetch_ohlcv('BTC/USDT', tf, limit=500)
    if btc_df is not None:
        state, structure = detect_market_regime(btc_df)
        btc_regimes[tf] = {"state": state, "structure": structure}

if btc_regimes:
    html_table = "<table class='regime-table'><thead><tr><th>TIMEFRAME</th><th>REGIME STATE</th><th>STRUCTURE CHARACTER</th></tr></thead><tbody>"
    for tf in REGIME_TIMEFRAMES:
        if tf in btc_regimes:
            state = btc_regimes[tf]["state"]
            struct = btc_regimes[tf]["structure"]
            color = "#16a34a" if "UP" in state else "#dc2626" if "DOWN" in state else "#2563eb" if "RANGE" in state else "#475569"
            html_table += f"<tr><td><b>{tf}</b></td><td style='color:{color}; font-weight:black;'>{state}</td><td>{struct}</td></tr>"
    html_table += "</tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)
else:
    st.error("Failed to load Centralized BTC Engine. Re-attempting connection link...")

st.divider()
st.subheader("🏹 Strategy Monitor")
progress_bar = st.empty()

# ==============================================================================
# ENGINE PART 1: JEREMIAH COMPRESSION ENGINE (Independent Logic Creator)
# ENGINE PART 3: LIQUIDITY SHIELD ENGINE (Context Move Quality Evaluator)
# ==============================================================================

def is_jeremiah_compressed(c, s20, s100, s200):
    """Core strict math check: close to s20 is <= 0.1%, and either s100 or s200 is bound inside 0.1%."""
    cond1 = (abs(c - s20) / c) <= 0.001
    cond2 = (abs(s20 - s100) / s20) <= 0.001
    cond3 = (abs(s20 - s200) / s20) <= 0.001
    return cond1 and (cond2 or cond3)

def scan_asset_matrix(symbol):
    """Executes isolated timeline check for a single asset across targets."""
    timeframe_payloads = {}
    
    for tf in TIMEFRAMES:
        df, src_name = safe_fetch_ohlcv(symbol, tf, limit=150)
        if df is None or len(df) < 20: continue
        
        # Pull tracking history behind the active bar
        cluster_candles = []
        wobble_count = 0
        for i in range(len(df)-2, 0, -1):
            row = df.iloc[i]
            if is_jeremiah_compressed(row['c'], row['s20'], row['s100'], row['s200']):
                cluster_candles.append(row)
                wobble_count = 0
            else:
                wobble_count += 1
                if wobble_count > 1: break # Squeeze sequence broken
                
        curr = df.iloc[-1]
        is_currently_sqz = is_jeremiah_compressed(curr['c'], curr['s20'], curr['s100'], curr['s200'])
        
        found_expansion = False
        direction = None
        curr_body = abs(curr['c'] - curr['o'])
        
        # --- PART 1 PURE UNBIASED EXPANSION DETECTOR ---
        if len(cluster_candles) >= 1 and not is_currently_sqz:
            avg_cluster_body = sum(abs(r['c'] - r['o']) for r in cluster_candles) / len(cluster_candles)
            
            # Strict 1x Body Expansion Rule. No blocks, no filters.
            if curr_body > avg_cluster_body:
                if curr['c'] > curr['o'] and curr['c'] > curr['s20']:
                    direction = "BULLISH"
                    found_expansion = True
                elif curr['c'] < curr['o'] and curr['c'] < curr['s20']:
                    direction = "BEARISH"
                    found_expansion = True
                    
        # Filter dead records immediately to preserve mobile browser memory
        if not is_currently_sqz and not found_expansion:
            continue
            
        # --- PART 3 LIQUIDITY SHIELD DETECTOR (Informational Warning Only) ---
        is_liquidity_hole = False
        if curr['v'] > 0:
            curr_efficiency = curr_body / curr['v']
            historical_bodies = abs(df['c'].iloc[-21:-1] - df['o'].iloc[-21:-1])
            historical_volumes = df['v'].iloc[-21:-1].replace(0, 1)
            avg_historical_efficiency = (historical_bodies / historical_volumes).mean()
            
            if curr_efficiency > (avg_historical_efficiency * 1.8):
                is_liquidity_hole = True
                
        # Handle 3-minute Anti-Spam Memory Layout Locks
        sig_key = f"{symbol}_{tf}"
        if found_expansion:
            last_alert_time = st.session_state["SIGNAL_MEMORY"].get(sig_key, 0)
            if time.time() - last_alert_time < 180:
                found_expansion = False # Internal debounce, keeps core tracking intact
            else:
                st.session_state["SIGNAL_MEMORY"][sig_key] = time.time()
                
        timeframe_payloads[tf] = {
            "sqz": is_currently_sqz,
            "expansion": found_expansion,
            "dir": direction,
            "source": src_name,
            "hole": is_liquidity_hole,
            "price": curr['c']
        }
        
    return timeframe_payloads

# ==============================================================================
# HIGH-SPEED EXECUTION CYCLE & PRESENTATION LAYER
# ==============================================================================
meme_signals = []
bigcap_signals = []

for idx, symbol in enumerate(ALL_SYMBOLS):
    progress_bar.markdown(f"⏳ *Scanning Matrix Block {idx+1}/25:* **{symbol}**")
    results = scan_asset_matrix(symbol)
    if not results: continue
    
    # MEGA SQZ Mathematical Verification Engine
    is_mega_sqz = all(results.get(tf, {}).get("sqz", False) for tf in TIMEFRAMES)
    display_price = next((res["price"] for res in results.values()), "N/A")
    
    payload = {"symbol": symbol, "price": display_price, "is_mega": is_mega_sqz, "timeframes": results}
    if symbol in MEMECOINS:
        meme_signals.append(payload)
    else:
        bigcap_signals.append(payload)
        
    # Micro-pacing delay protects server IP from multi-exchange throttle traps
    time.sleep(0.04)

progress_bar.empty()

# --- DISPLAY STREAM 1: MEMECOIN PERPETUALS ---
st.markdown('<div class="section-header header-meme">🔮 VOLATILE MEMECOIN FUTURES (15 ASSETS)</div>', unsafe_allow_html=True)
if not meme_signals:
    st.markdown("<p class='empty-notice'>⚡ No active compression or expansion matrix states in Memecoin Futures.</p>", unsafe_allow_html=True)
else:
    for sig in meme_signals:
        with st.container():
            st.write(f"### {sig['symbol']} | ${sig['price']}")
            if sig['is_mega']: 
                st.markdown("<span class='badge-mega'>🚨 MEGA SQZ: SIMULTANEOUS TRIPLE TIMEFRAME COMPRESSION</span><br><br>", unsafe_allow_html=True)
                
            for tf, res in sig['timeframes'].items():
                src_lbl = f"<span class='status-dim'>[{res['source']}]</span>"
                macro_tf = "15m" if tf in ["3m", "5m"] else "1h"
                btc_state = btc_regimes.get(macro_tf, {}).get("state", "UNKNOWN")
                
                if res['expansion']:
                    st.markdown(f"💥 **{tf} {res['dir']} RELEASE** Elephant Candle detected {src_lbl}", unsafe_allow_html=True)
                    # Engines report completely independently as pure side-by-side strings
                    st.markdown(f"↳ <span class='badge-expansion'>PART 1 SIGNAL VALID</span> | Context: *BTC {macro_tf} is {btc_state}*", unsafe_allow_html=True)
                    if res['hole']:
                        st.markdown("↳ <span class='badge-hole'>⚠️ PART 3 WARNING: LIQUIDITY HOLE DETECTED</span> (Thin orderbook, futures-driven)", unsafe_allow_html=True)
                    st.write("")
                elif res['sqz'] and not sig['is_mega']:
                    st.markdown(f"<span class='badge-sqz'>🧬 {tf} COMPRESSION ACTIVE</span> Close bound near MAs {src_lbl}", unsafe_allow_html=True)

# --- DISPLAY STREAM 2: INSTITUTIONAL BIG CAPS ---
st.markdown('<div class="section-header header-big">👑 INSTITUTIONAL BIG CAPS (10 ASSETS)</div>', unsafe_allow_html=True)
if not bigcap_signals:
    st.markdown("<p class='empty-notice'>⭐ No active compression or expansion matrix states in Big Caps.</p>", unsafe_allow_html=True)
else:
    for sig in bigcap_signals:
        with st.container():
            st.write(f"### {sig['symbol']} | ${sig['price']}")
            if sig['is_mega']: 
                st.markdown("<span class='badge-mega'>🚨 MEGA SQZ: SIMULTANEOUS TRIPLE TIMEFRAME COMPRESSION</span><br><br>", unsafe_allow_html=True)
                
            for tf, res in sig['timeframes'].items():
                src_lbl = f"<span class='status-dim'>[{res['source']}]</span>"
                macro_tf = "15m" if tf in ["3m", "5m"] else "1h"
                btc_state = btc_regimes.get(macro_tf, {}).get("state", "UNKNOWN")
                
                if res['expansion']:
                    st.markdown(f"💥 **{tf} {res['dir']} RELEASE** Elephant Candle detected {src_lbl}", unsafe_allow_html=True)
                    st.markdown(f"↳ <span class='badge-expansion'>PART 1 SIGNAL VALID</span> | Context: *BTC {macro_tf} is {btc_state}*", unsafe_allow_html=True)
                    if res['hole']:
                        st.markdown("↳ <span class='badge-hole'>⚠️ PART 3 WARNING: LIQUIDITY HOLE DETECTED</span> (Thin orderbook, futures-driven)", unsafe_allow_html=True)
                    st.write("")
                elif res['sqz'] and not sig['is_mega']:
                    st.markdown(f"<span class='badge-sqz'>🧬 {tf} COMPRESSION ACTIVE</span> Close bound near MAs {src_lbl}", unsafe_allow_html=True)

st.divider()
st.caption(f"Heartbeat: {pd.Timestamp.now().strftime('%H:%M:%S')} | JEREMIAH EDGE PRO SSoT V10 Stable Production Engine")
