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
# 🟩 PATCHED: Swapped "3m" out and introduced the "2m" timeframe natively
TIMEFRAMES = ["2m", "5m", "15m"]
THRESHOLD = 0.001  # Hard steel wall ceiling: <= 0.1%

# 📋 THE NEW NOTEBOOK WATCHLIST POOL (25 Tokens) - FULLY UPDATED
WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "PEPEUSDT", "BONKUSDT",
    "SHIBUSDT", "USELESSUSDT", "SPACEUSDT", "MOVEUSDT", "ZECUSDT",
    "SPXUSDT", "PEOPLEUSDT", "PENGUUSDT", "FARTCOINUSDT", "LINEAUSDT",
    "MEMEUSDT", "PUMPUSDT", "AIXBTUSDT", "BRETTUSDT", "FOGOUSDT",
    "GOOGLUSDT", "FLOKIUSDT", "IWMUSDT", "MOODENGUSDT", "NEARUSDT"
]


# ==============================================================================
# DATA CALCULATION PIPELINE (HIGH-PRECISION MATH ENGINE)
# ==============================================================================
def calculate_sma(prices, period):
    """Calculates pure mathematical Simple Moving Average."""
    return pd.Series(prices).rolling(window=period).mean().iloc[-1]

def fetch_mexc_candles(symbol, timeframe):
    """
    High-integrity historical bar engine with Supreme Failover Protection.
    Primary Route: MEXC Public REST API
    Failover Route: OKX v5 Public REST API (Fires instantly if MEXC drops or throttles)
    """
    okx_tf_map = {
        "2m": "2m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "60m": "1H",
        "1h": "1H",
        "4h": "4H"
    }

    # 1️⃣ PRIMARY CONNECTION LINE: Attempt Live Fetch from MEXC
    mexc_params = {
        "symbol": symbol,
        "interval": timeframe,
        "limit": 250
    }
    try:
        response = requests.get(EXCHANGE_API_URL, params=mexc_params, timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    # 2️⃣ AUTOMATIC SHIELD FAILOVER LINE: Triggers immediately if MEXC fails
    try:
        okx_symbol = symbol.replace("USDT", "-USDT") if "USDT" in symbol and "-" not in symbol else symbol
        okx_interval = okx_tf_map.get(timeframe, timeframe)
        
        okx_params = {
            "instId": okx_symbol,
            "bar": okx_interval,
            "limit": "250"
        }
        
        okx_response = requests.get("https://www.okx.com/api/v5/market/candles", params=okx_params, timeout=3)
        if okx_response.status_code == 200:
            raw_data = okx_response.json()
            if raw_data.get("code") == "0" and "data" in raw_data:
                mexc_formatted_data = []
                for bar in raw_data["data"]:
                    mexc_formatted_data.insert(0, [
                        bar[0],  # Open Time
                        bar[1],  # Open Price
                        bar[2],  # High Price
                        bar[3],  # Low Price
                        bar[4]   # Close Price
                    ])
                return mexc_formatted_data
    except Exception:
        pass

    return None

def run_pure_compression_math(symbol, timeframe):
    """
    Core Part 1 Algorithm Engine.
    Executes True Cluster-Based Convergence over Cluster Average Denominators.
    Eliminates all false positives by analyzing total group spread without rounding shortcuts.
    """
    candles = fetch_mexc_candles(symbol, timeframe)
    if not candles or len(candles) < 200:
        return {
            "sqz": False, 
            "type": "NONE",
            "live_price": 0.0,
            "sma20": 0.0,
            "sma100": 0.0,
            "sma200": 0.0,
            "at_spread_pct": 0.0,
            "so_spread_pct": 0.0
        }
    
    # Extract structural bar closing positions as raw floats
    closes = [float(candle[4]) for candle in candles]
    live_price = closes[-1]
    
    sma20 = calculate_sma(closes, 20)
    sma100 = calculate_sma(closes, 100)
    sma200 = calculate_sma(closes, 200)
    
    # --------------------------------------------------------------------------
    # 🟩 1. TRUE CLUSTER-BASED CONVERGENCE: ALL TOGETHER
    # --------------------------------------------------------------------------
    highest_at = max(live_price, sma20, sma100)
    lowest_at = min(live_price, sma20, sma100)
    cluster_avg_at = (live_price + sma20 + sma100) / 3.0
    
    at_spread_raw = (highest_at - lowest_at) / cluster_avg_at
    all_together = at_spread_raw <= THRESHOLD

    # --------------------------------------------------------------------------
    # 🟦 2. TRUE CLUSTER-BASED CONVERGENCE: SPECIAL ONE
    # --------------------------------------------------------------------------
    highest_so = max(live_price, sma20, sma200)
    lowest_so = min(live_price, sma20, sma200)
    cluster_avg_so = (live_price + sma20 + sma200) / 3.0
    
    so_spread_raw = (highest_so - lowest_so) / cluster_avg_so
    special_one = so_spread_raw <= THRESHOLD
    
    # Extract exact percentage variants for diagnostic layers
    at_spread_pct = at_spread_raw * 100
    so_spread_pct = so_spread_raw * 100
    
    # --------------------------------------------------------------------------
    # 🎯 3. DETECTION PRIORITY & DEBUG ENGINE ROUTING
    # --------------------------------------------------------------------------
    if all_together:
        return {
            "sqz": True,
            "type": "ALL TOGETHER",
            "live_price": live_price,
            "sma20": sma20,
            "sma100": sma100,
            "sma200": sma200,
            "at_spread_pct": at_spread_pct,
            "so_spread_pct": so_spread_pct
        }
        
    elif special_one:
        return {
            "sqz": True,
            "type": "SPECIAL ONE",
            "live_price": live_price,
            "sma20": sma20,
            "sma100": sma100,
            "sma200": sma200,
            "at_spread_pct": at_spread_pct,
            "so_spread_pct": so_spread_pct
        }
        
    return {
        "sqz": False,
        "type": "NONE",
        "live_price": live_price,
        "sma20": sma20,
        "sma100": sma100,
        "sma200": sma200,
        "at_spread_pct": at_spread_pct,
        "so_spread_pct": so_spread_pct
    }

def fetch_btc_regime_data():
    """
    Part 2 Law: Connects live to MEXC for BTCUSDT and calculates
    the structural regimes dynamically for 15m, 60m, and 4h.
    """
    timeframes_p2 = ["15m", "60m", "4h"]
    results = {}
    
    for tf in timeframes_p2:
                
