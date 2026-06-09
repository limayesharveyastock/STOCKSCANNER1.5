import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")

# --- HIGH-CONTRAST BLACK TERMINAL STYLING ---
st.markdown("""
<style>
    /* Dark Terminal Background & Base Font Configuration */
    .stApp { background-color: #000000; color: #E0E0E0; }
    
    /* Headers & Component Subtitles - Yellow Courier */
    h1, h2, h3, [data-testid="stHeader"] { color: #FFD700 !important; text-align: center; font-family: 'Courier New', monospace; font-weight: bold; }
    
    /* Grid View Styling - Charcoal Surface Container with High Contrast Elements */
    div[data-testid="stDataFrame"] {
        background-color: #1E1E1E !important;
        border: 1px solid #444444;
        border-radius: 4px;
        padding: 5px;
    }
    
    /* Force Raw Data Cells to Output Pure High-Contrast White */
    div[data-testid="stDataFrame"] * {
        color: #FFFFFF !important;
    }
    
    /* Streamlit Metric Value Adjustments */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-family: 'Courier New', monospace; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #B0B0B0 !important; font-size: 13px !important; }
    
    /* Custom High Contrast Filter Configurator Panel Labels */
    .stRadio > label, .stSelectbox > label { color: #FFD700 !important; font-family: 'Courier New', monospace; }
    
    /* System Synchronization Push Button */
    .stButton>button {
        background-color: #222222 !important;
        color: #FFD700 !important;
        border: 1px solid #FFD700 !important;
        font-weight: bold !important;
        font-family: 'Courier New', monospace !important;
        border-radius: 4px !important;
    }
    .stButton>button:hover {
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 NIFTY 50 Blue-Chip Multi-Timeframe Structural Scanner")

# Initialize Kite connection
@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

# Dynamically fetch and map active NSE instrument tokens
@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        # FIX: Keep instrument_token as an int! Zerodha historical API will reject strings.
        return {inst['tradingsymbol']: int(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

# Fetch Live India VIX Value
def get_india_vix(kite, token_lookup):
    try:
        vix_token = token_lookup.get("INDIA VIX")
        if not vix_token:
            return 14.5  # Realistic historical floor fallback
        quote = kite.quote(f"NSE:INDIA VIX")
        if quote and f"NSE:INDIA VIX" in quote:
            return float(quote[f"NSE:INDIA VIX"]["last_price"])
        return 14.5
    except Exception:
        return 14.5

# Load Nifty 50 structural matrix with intelligent column normalization
def load_metadata():
    csv_path = "stock_metadata.csv"
    
    nifty50_universe = {
        "ADANIENT": {"Industry": "Metals & Mining", "Promoter": 72.6, "PE": 45.2, "Ind_PE": 24.1, "PB": 4.2, "ROCE": 12.5},
        "ADANIPORTS": {"Industry": "Infrastructure / Services", "Promoter": 65.3, "PE": 33.1, "Ind_PE": 28.5, "PB": 3.9, "ROCE": 14.8},
        "APOLLOHOSP": {"Industry": "Healthcare", "Promoter": 29.3, "PE": 78.4, "Ind_PE": 38.2, "PB": 9.1, "ROCE": 16.2},
        "ASIANPAINT": {"Industry": "Consumer Durables", "Promoter": 52.6, "PE": 55.4, "Ind_PE": 51.2, "PB": 14.2, "ROCE": 34.1},
        "AXISBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 14.1, "Ind_PE": 15.2, "PB": 2.1, "ROCE": 11.2},
        "BAJAJ-AUTO": {"Industry": "Automobile", "Promoter": 55.0, "PE": 31.2, "Ind_PE": 26.4, "PB": 8.4, "ROCE": 30.5},
        "BAJFINANCE": {"Industry": "Financial Services", "Promoter": 54.7, "PE": 28.3, "Ind_PE": 22.1, "PB": 5.8, "ROCE": 17.4},
        "BAJAJFINSV": {"Industry": "Financial Services", "Promoter": 60.7, "PE": 33.4, "Ind_PE": 22.1, "PB": 4.1, "ROCE": 14.9},
        "BEL": {"Industry": "Capital Goods", "Promoter": 51.1, "PE": 42.6, "Ind_PE": 35.4, "PB": 7.8, "ROCE": 26.3},
        "BHARTIARTL": {"Industry": "Telecommunication", "Promoter": 53.1, "PE": 52.1, "Ind_PE": 41.3, "PB": 8.9, "ROCE": 18.2},
        "BPCL": {"Industry": "Oil & Gas", "Promoter": 53.0, "PE": 11.4, "Ind_PE": 12.8, "PB": 1.7, "ROCE": 22.1},
        "BRITANNIA": {"Industry": "FMCG", "Promoter": 50.5, "PE": 54.3, "Ind_PE": 44.2, "PB": 28.1, "ROCE": 48.6},
        "CIPLA": {"Industry": "Healthcare", "Promoter": 33.4, "PE": 29.6, "Ind_PE": 31.4, "PB": 4.3, "ROCE": 21.3},
        "COALINDIA": {"Industry": "Oil & Gas", "Promoter": 63.1, "PE": 9.2, "Ind_PE": 12.8, "PB": 3.4, "ROCE": 54.2},
        "DRREDDY": {"Industry": "Healthcare", "Promoter": 26.7, "PE": 18.9, "Ind_PE": 31.4, "PB": 3.1, "ROCE": 24.5},
        "EICHERMOT": {"Industry": "Automobile", "Promoter": 49.2, "PE": 29.1, "Ind_PE": 26.4, "PB": 7.2, "ROCE": 27.8},
        "GRASIM": {"Industry": "Construction Materials", "Promoter": 42.7, "PE": 44.1, "Ind_PE": 32.1, "PB": 1.9, "ROCE": 9.4},
        "HCLTECH": {"Industry": "Information Technology", "Promoter": 60.8, "PE": 25.4, "Ind_PE": 28.2, "PB": 6.1, "ROCE": 28.9},
        "HDFCBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 18.2, "Ind_PE": 15.2, "PB": 2.6, "ROCE": 12.1},
        "HDFCLIFE": {"Industry": "Financial Services", "Promoter": 50.4, "PE": 61.2, "Ind_PE": 55.4, "PB": 4.8, "ROCE": 14.2},
        "HINDALCO": {"Industry": "Metals & Mining", "Promoter": 34.6, "PE": 16.3, "Ind_PE": 18.4, "PB": 1.8, "ROCE": 13.1},
        "HINDUNILVR": {"Industry": "FMCG", "Promoter": 61.9, "PE": 56.2, "Ind_PE": 44.2, "PB": 11.4, "ROCE": 39.5},
        "ICICIBANK": {"Industry": "Financial Services", "Promoter": 0.0, "PE": 17.4, "Ind_PE": 15.2, "PB": 3.1, "ROCE": 13.4},
        "INDUSINDBK": {"Industry": "Financial Services", "Promoter": 16.5, "PE": 13.2, "Ind_PE": 15.2, "PB": 1.8, "ROCE": 11.7},
        "INFY": {"Industry": "Information Technology", "Promoter": 14.8, "PE": 24.1, "Ind_PE": 28.2, "PB": 7.4, "ROCE": 37.2},
        "INDIGO": {"Industry": "Infrastructure / Services", "Promoter": 57.3, "PE": 21.4, "Ind_PE": 25.1, "PB": 5.2, "ROCE": 22.4},
        "ITC": {"Industry": "FMCG", "Promoter": 0.0, "PE": 26.4, "Ind_PE": 44.2, "PB": 7.9, "ROCE": 38.7},
        "JSWSTEEL": {"Industry": "Metals & Mining", "Promoter": 44.8, "PE": 27.2, "Ind_PE": 18.4, "PB": 3.2, "ROCE": 14.1},
        "JIOFIN": {"Industry": "Financial Services", "Promoter": 47.1, "PE": 120.5, "Ind_PE": 22.1, "PB": 2.1, "ROCE": 6.2},
        "KOTAKBANK": {"Industry": "Financial Services", "Promoter": 25.9, "PE": 19.1, "Ind_PE": 15.2, "PB": 2.9, "ROCE": 12.8},
        "LT": {"Industry": "Construction", "Promoter": 0.0, "PE": 36.4, "Ind_PE": 31.2, "PB": 4.8, "ROCE": 15.1},
        "M&M": {"Industry": "Automobile", "Promoter": 19.3, "PE": 28.4, "Ind_PE": 26.4, "PB": 4.9, "ROCE": 19.2},
        "MARUTI": {"Industry": "Automobile", "Promoter": 58.2, "PE": 27.5, "Ind_PE": 26.4, "PB": 5.1, "ROCE": 21.4},
        "MAXHEALTH": {"Industry": "Healthcare", "Promoter": 23.1, "PE": 68.2, "Ind_PE": 38.2, "PB": 8.4, "ROCE": 15.5},
        "NESTLEIND": {"Industry": "FMCG", "Promoter": 62.8, "PE": 74.2, "Ind_PE": 44.2, "PB": 21.4, "ROCE": 58.1},
        "NTPC": {"Industry": "Power", "Promoter": 51.1, "PE": 17.5, "Ind_PE": 19.4, "PB": 2.4, "ROCE": 11.9},
        "ONGC": {"Industry": "Oil & Gas", "Promoter": 58.9, "PE": 8.1, "Ind_PE": 12.8, "PB": 1.1, "ROCE": 14.5},
        "POWERGRID": {"Industry": "Power", "Promoter": 51.3, "PE": 16.2, "Ind_PE": 19.4, "PB": 2.9, "ROCE": 12.4},
        "RELIANCE": {"Industry": "Oil & Gas", "Promoter": 50.3, "PE": 26.1, "Ind_PE": 12.8, "PB": 2.4, "ROCE": 10.2},
        "SBILIFE": {"Industry": "Financial Services", "Promoter": 55.4, "PE": 78.1, "Ind_PE": 55.4, "PB": 9.5, "ROCE": 13.1},
        "SBIN": {"Industry": "Financial Services", "Promoter": 57.5, "PE": 10.4, "Ind_PE": 15.2, "PB": 1.6, "ROCE": 11.8},
        "SHRIRAMFIN": {"Industry": "Financial Services", "Promoter": 25.4, "PE": 14.8, "Ind_PE": 22.1, "PB": 2.2, "ROCE": 15.4},
        "SUNPHARMA": {"Industry": "Healthcare", "Promoter": 54.5, "PE": 36.2, "Ind_PE": 31.4, "PB": 4.9, "ROCE": 17.2},
        "TATACONSUM": {"Industry": "FMCG", "Promoter": 34.4, "PE": 64.1, "Ind_PE": 44.2, "PB": 4.1, "ROCE": 9.8},
        "TATAMOTORS": {"Industry": "Automobile", "Promoter": 46.4, "PE": 11.5, "Ind_PE": 26.4, "PB": 3.2, "ROCE": 20.1},
        "TATASTEEL": {"Industry": "Metals & Mining", "Promoter": 33.2, "PE": 38.4, "Ind_PE": 18.4, "PB": 1.7, "ROCE": 10.5},
        "TCS": {"Industry": "Information Technology", "Promoter": 72.4, "PE": 29.5, "Ind_PE": 28.2, "PB": 12.8, "ROCE": 51.4},
        "TECHM": {"Industry": "Information Technology", "Promoter": 35.1, "PE": 48.2, "Ind_PE": 28.2, "PB": 3.8, "ROCE": 15.9},
        "TITAN": {"Industry": "Consumer Durables", "Promoter": 52.9, "PE": 82.1, "Ind_PE": 51.2, "PB": 19.4, "ROCE": 25.1},
        "TRENT": {"Industry": "Retail", "Promoter": 37.0, "PE": 145.2, "Ind_PE": 68.4, "PB": 28.4, "ROCE": 24.3},
        "ULTRACEMCO": {"Industry": "Construction Materials", "Promoter": 60.0, "PE": 41.2, "Ind_PE": 32.1, "PB": 4.7, "ROCE": 13.8},
        "UPL": {"Industry": "Chemicals", "Promoter": 32.4, "PE": 22.1, "Ind_PE": 19.5, "PB": 1.5, "ROCE": 11.1},
        "WIPRO": {"Industry": "Information Technology", "Promoter": 72.9, "PE": 23.4, "Ind_PE": 28.2, "PB": 3.4, "ROCE": 21.2}
    }

    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if not df.empty and ("Ticker" in df.columns or "Symbol" in df.columns):
                rename_map = {
                    "Symbol": "Ticker",
                    "Promoter Holding (%)": "Promoter_Percent",
                    "Promoter Holding": "Promoter_Percent",
                    "Stock PE": "Stock_PE",
                    "PE": "Stock_PE",
                    "Industry PE": "Industry_PE",
                    "Price to Book": "PB",
                    "P/B": "PB"
                }
                df = df.rename(columns=rename_map)
                df = df[df["Ticker"].isin(nifty50_universe.keys())]
                return df
        except Exception as e:
            st.error(f"⚠️ CSV parsing error: {e}")

    fallback_data = [{
        "Ticker": ticker, "Industry": data["Industry"], "Promoter_Percent": data["Promoter"],
        "Stock_PE": data["PE"], "Industry_PE": data["Ind_PE"], "PB": data["PB"], "ROCE": data["ROCE"],
        "52W_High": 2000.0, "52W_Low": 1000.0, "5Y_High": 3000.0, "5Y_Low": 500.0
    } for ticker, data in nifty50_universe.items()]
    return pd.DataFrame(fallback_data)

def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # Structural Core Indicators
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # Volume Moving Averages
    df['VOL_MA_20'] = ta.sma(df['volume'], length=20)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    
    # Calculate Pivot Matrix for Mean-Reversion Sideways Logic (Fibonacci, 20-period lookback)
    df['Pivot'] = (df['high'].rolling(20).mean() + df['low'].rolling(20).mean() + df['close'].rolling(20).mean()) / 3
    high_max = df['high'].rolling(20).max()
    low_min = df['low'].rolling(20).min()
    df['R1'] = df['Pivot'] + (0.382 * (high_max - low_min))
    df['S1'] = df['Pivot'] - (0.382 * (high_max - low_min))
    
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

def get_crossover_signal(df):
    if len(df) < 3:
        return "No Cross"
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    prev_2 = df.iloc[-3]
    
    if prev['VWMA_9'] <= prev['VWMA_26'] and latest['VWMA_9'] > latest['VWMA_26']:
        return "🔥 9 CROSSES 26 FROM BELOW"
    elif prev['VWMA_9'] >= prev['VWMA_26'] and latest['VWMA_9'] < latest['VWMA_26']:
        return "❄️ 9 CROSSES 26 FROM ABOVE"
        
    if prev_2['VWMA_9'] <= prev_2['VWMA_26'] and prev['VWMA_9'] > prev['VWMA_26']:
        return "🔥 9 CROSSES 26 FROM BELOW (1 Bar Ago)"
    elif prev_2['VWMA_9'] >= prev_2['VWMA_26'] and prev['VWMA_9'] < prev['VWMA_26']:
        return "❄️ 9 CROSSES 26 FROM ABOVE (1 Bar Ago)"
        
    return "No Cross"

def trading_signal_logic(df, india_vix):
    if len(df) < 20:
        return [{"Signal": "HOLD", "Target": 0.0, "Stoploss": 0.0}]
        
    latest = df.iloc[-1]
    signals = []
    price = latest['close']

    # --- Trending Market Logic (IndiaVIX < 15) ---
    if india_vix < 15:
        if price > 1.01 * latest['VWMA_9'] and latest['VWMA_9'] > latest['VWMA_26']:
            target = price * 1.015   
            stoploss = price * (1 - (0.015 / 1.5))  
            signals.append({"Signal": "BUY", "Target": round(target, 2), "Stoploss": round(stoploss, 2)})
        elif price < 0.99 * latest['VWMA_9'] and latest['VWMA_9'] < latest['VWMA_26']:
            target = price * 0.985   
            stoploss = price * (1 + (0.015 / 1.5))
            signals.append({"Signal": "SELL", "Target": round(target, 2), "Stoploss": round(stoploss, 2)})

    # --- Sideways/Volatile Market Logic (IndiaVIX ≥ 15) ---
    else:
        pivot = latest['Pivot']
        r1 = latest['R1']
        s1 = latest['S1']
        midpoint = pivot + (r1 - pivot) * 0.5

        if price <= midpoint:  
            target = r1
            stoploss = price - (r1 - price) / 1.5  
            signals.append({"Signal": "BUY", "Target": round(target, 2), "Stoploss": round(stoploss, 2)})
        elif price >= midpoint:  
            target = s1
            stoploss = price + (price - s1) / 1.5  
            signals.append({"Signal": "SELL", "Target": round(target, 2), "Stoploss": round(stoploss, 2)})

    if not signals:
        signals.append({"Signal": "HOLD", "Target": round(price, 2), "Stoploss": round(price, 2)})
        
    return signals

@st.cache_data(ttl=14400)
def get_daily_macro_data(_kite, token, symbol):
    try:
        hist_1d = _kite.historical_data(
            token, 
            from_date=(datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d'),
            to_date=datetime.now().strftime('%Y-%m-%d'), 
            interval="day"
        )
        if not hist_1d or len(hist_1d) < 40:
            return None
        df_1d = pd.DataFrame(hist_1d)
        df_1d = calculate_indicators(df_1d)
        latest_1d = df_1d.iloc[-1]
        
        # FIX: Robustly fetch Supertrend column prefix to avoid IndexError crashes
        st_cols = latest_1d.filter(like='SUPERT_')
        st_val = float(st_cols.iloc[0]) if not st_cols.empty else float(latest_1d['close'])
        
        vwma_cross_signal_1d = get_crossover_signal(df_1d)
        
        above_1d = df_1d['VWMA_9'] > df_1d['VWMA_26']
        cross_mask_1d = above_1d != above_1d.shift()
        cross_mask_1d.iloc[0] = False
        cross_df_1d = df_1d[cross_mask_1d]
        last_cross_price_1d = float(cross_df_1d['close'].iloc[-1]) if not cross_df_1d.empty else float(latest_1d['close'])

        curr_price = float(latest_1d['close'])
        if float(latest_1d['volume']) > float(latest_1d['VOL_MA_50']) and float(latest_1d['RSI']) > 60 and curr_price > last_cross_price_1d:
            trend_1d = "🟢 BULLISH"
        elif float(latest_1d['volume']) > float(latest_1d['VOL_MA_50']) and float(latest_1d['RSI']) < 40 and curr_price < last_cross_price_1d:
            trend_1d = "🔴 BEARISH"
        else:
            trend_1d = "⚪ NEUTRAL"

        return {
            "RSI_1D": float(latest_1d['RSI']),
            "VOL_MA_1D": float(latest_1d['VOL_MA_50']),
            "VOLUME_1D": float(latest_1d['volume']),
            "SUPERTREND_1D": st_val,
            "VWMA_50_1D": float(latest_1d['VWMA_50']),
            "VWMA_100_1D": float(latest_1d['VWMA_100']),
            "VWMA_CROSS_SIGNAL_1D": vwma_cross_signal_1d,
            "VWMA_CROSS_PRICE_1D": last_cross_price_1d,
            "TREND_STATUS_1D": trend_1d,
            "df_raw": df_1d
        }
    except Exception as e:
        print(f"❌ Error in get_daily_macro_data for {symbol}: {e}")
        return None

def execute_parallel_scan(meta_df, token_lookup, kite, india_vix):
    scan_results = []
    
    def worker(row):
        symbol = str(row['Ticker']).strip()
        token = token_lookup.get(symbol)
        if not token:
            return None
        try:
            daily_data = get_daily_macro_data(kite, token, symbol)
            if not daily_data:
                return None
                
            hist_15m = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            if not hist_15m or len(hist_15m) < 40:
                return None
                
            df_15m = pd.DataFrame(hist_15m)
            df_15m = calculate_indicators(df_15m)
            latest_15m = df_15m.iloc[-1]
            
            # Strict delay pacing inside worker to guarantee compliance with 3-req/sec limit across threads
            time.sleep(0.4) 
            
            rsi_15m = latest_15m['RSI']
            vol_ma_15m = latest_15m['VOL_MA_20']  
            curr_vol_15m = latest_15m['volume']
            curr_price_15m = latest_15m['close']
            
            vwma_cross_signal_15m = get_crossover_signal(df_15m)

            above_15m = df_15m['VWMA_9'] > df_15m['VWMA_26']
            cross_mask_15m = above_15m != above_15m.shift()
            cross_mask_15m.iloc[0] = False
            cross_df_15m = df_15m[cross_mask_15m]
            last_cross_price_15m = float(cross_df_15m['close'].iloc[-1]) if not cross_df_15m.empty else float(latest_15m['close'])

            if curr_vol_15m > vol_ma_15m and rsi_15m > 60 and curr_price_15m > last_cross_price_15m: 
                trend_15m = "🟢 BULLISH"
            elif curr_vol_15m > vol_ma_15m and rsi_15m < 40 and curr_price_15m < last_cross_price_15m: 
                trend_15m = "🔴 BEARISH"
            else: 
                trend_15m = "⚪ NEUTRAL"
                
            st_cols = latest_15m.filter(like='SUPERT_')
            st_15m = st_cols.iloc[0] if not st_cols.empty else curr_price_15m

            trade_calc_df = df_15m if trend_15m != "⚪ NEUTRAL" else daily_data["df_raw"]
            derived_signals = trading_signal_logic(trade_calc_df, india_vix)
            primary_signal = derived_signals[0] if derived_signals else {"Signal": "HOLD", "Target": 0.0, "Stoploss": 0.0}

            return {
                "Stock Name": symbol,
                "Industry": row.get("Industry", "Blue-Chip Core"),
                "Promoter Holding (%)": row.get("Promoter_Percent", 0.0),
                "Stock PE": row.get("Stock_PE", 0.0),
                "Industry PE": row.get("Industry_PE", 0.0),
                "PB": row.get("PB", 0.0),
                "ROCE": row.get("ROCE", 0.0),
                "LTP": round(curr_price_15m, 2),
                
                "VIX Strategy Order": primary_signal["Signal"],
                "Calculated Target": primary_signal["Target"],
                "Calculated Stoploss": primary_signal["Stoploss"],
                
                "VWMA Cross Indicator (15M)": vwma_cross_signal_15m,
                "VWMA Cross Price (15M)": round(last_cross_price_15m, 2),
                "Trend Status (15M)": trend_15m,
                "RSI (15M)": round(rsi_15m, 2),
                "Vol MA (15M)": round(vol_ma_15m, 1),
                "Supertrend (15M)": round(st_15m, 2),
                "VWMA 9 (15M)": round(latest_15m['VWMA_9'], 2),
                "VWMA 26 (15M)": round(latest_15m['VWMA_26'], 2),
                
                "VWMA Cross Indicator (1D)": daily_data["VWMA_CROSS_SIGNAL_1D"],
                "VWMA Cross Price (1D)": round(daily_data["VWMA_CROSS_PRICE_1D"], 2),
                "Trend Status (1D)": daily_data["TREND_STATUS_1D"],
                "RSI (1D)": round(daily_data["RSI_1D"], 2),
                "Vol MA (1D)": round(daily_data["VOL_MA_1D"], 1),
                "Supertrend (1D)": round(daily_data["SUPERTREND_1D"], 2)
            }
        except Exception as e:
            # FIX: Print exact failure traces to console output so we aren't completely blind!
            print(f"❌ Worker exception for asset {symbol}: {e}")
            return None

    # Lowered max_workers to 2 to enforce strict Zerodha spacing safety limits
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(worker, row) for _, row in meta_df.iterrows()]
        for future in as_completed(futures):
            res = future.get_result() if hasattr(future, 'get_result') else future.result()
            if res:
                scan_results.append(res)
                
    return scan_results

def run_integrated_pipeline():
    meta_df = load_metadata()
    if meta_df is None:
        return
        
    kite = get_kite()
    token_lookup = get_instrument_lookup()
    india_vix = get_india_vix(kite, token_lookup)
    
    if "master_df" not in st.session_state:
        st.session_state.master_df = None
    if "last_run" not in st.session_state:
        st.session_state.last_run = None
        
    current_time = time.time()
    should_scan = False
    
    if st.session_state.master_df is None:
        should_scan = True
    elif st.session_state.last_run is not None and (current_time - st.session_state.last_run) >= 900:
        should_scan = True
        
    c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 2])
    with c_btn1:
        if st.button("🔄 Force Re-Scan Nifty 50", use_container_width=True):
            should_scan = True
    with c_btn2:
        if st.session_state.last_run:
            last_time_str = datetime.fromtimestamp(st.session_state.last_run).strftime('%H:%M:%S')
            st.write(f"⏱️ Matrix sync verified at: **{last_time_str}**")
    with c_btn3:
        st.write(f"📊 Live Market Volatility (**INDIA VIX**): `{india_vix}`")
            
    if should_scan:
        with st.spinner("🚀 Scanning Nifty 50 assets concurrently..."):
            results = execute_parallel_scan(meta_df, token_lookup, kite, india_vix)
            if results:
                st.session_state.master_df = pd.DataFrame(results)
                st.session_state.last_run = current_time
                st.rerun()

    if st.session_state.master_df is None or st.session_state.master_df.empty:
        st.warning("No data found or scanner is currently loading empty data fields.")
        return
        
    master_df = st.session_state.master_df
    
    tab1, tab2 = st.tabs(["📊 Technical Multi-Timeframe Scanner", "🏢 Structural Bifurcation View"])
    
    with tab1:
        st.subheader("⚙️ Timeframe Filter Configurator")
        active_tf = st.radio("Select Active Scanner Frame Layer:", ["15 Minute", "1 Day"], horizontal=True)
        
        suffix = " (15M)" if active_tf == "15 Minute" else " (1D)"
        trend_col = f"Trend Status{suffix}"
        
        if trend_col not in master_df.columns:
            st.error(f"Critical Error: Column '{trend_col}' not found. Relaunching scan...")
            return
            
        bullish_df = master_df[master_df[trend_col] == "🟢 BULLISH"]
        bearish_df = master_df[master_df[trend_col] == "🔴 BEARISH"]
        neutral_df = master_df[master_df[trend_col] == "⚪ NEUTRAL"]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nifty 50 Actives", len(master_df))
        c2.metric("Bullish Vol Surges", len(bullish_df))
        c3.metric("Bearish Vol Breaks", len(bearish_df))
        c4.metric("Consolidation Grid", len(neutral_df))
        
        st.divider()
        
        if active_tf == "15 Minute":
            tech_display_cols = [
                "Stock Name", "LTP", "VIX Strategy Order", "Calculated Target", "Calculated Stoploss",
                "VWMA Cross Indicator (15M)", "VWMA Cross Price (15M)", "RSI (15M)", "Supertrend (15M)"
            ]
        else:
            tech_display_cols = [
                "Stock Name", "LTP", "VIX Strategy Order", "Calculated Target", "Calculated Stoploss",
                "VWMA Cross Indicator (1D)", "VWMA Cross Price (1D)", "RSI (1D)", "Supertrend (1D)"
            ]
        
        tech_display_cols = [col for col in tech_display_cols if col in master_df.columns]
        
        st.subheader(f"🔥 Momentum Surge Buy Signals ({active_tf})")
        if not bullish_df.empty:
            st.dataframe(bullish_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No bullish breakouts verified for Nifty 50 assets right now.")

        st.subheader(f"❄️ Momentum Breakdown Short Signals ({active_tf})")
        if not bearish_df.empty:
            st.dataframe(bearish_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No short breakdown triggers detected across the index.")
            
        st.subheader(f"⚖️ Neutral / Structural Rotation Grid ({active_tf})")
        if not neutral_df.empty:
            st.dataframe(neutral_df[tech_display_cols], use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("🔍 Valuation & Ownership Filter Matrix")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            all_industries = ["All Industries"] + sorted(list(master_df["Industry"].unique()))
            selected_industry = st.selectbox("Sector Classification:", all_industries)
        with f_col2:
            master_df["Promoter Tier"] = master_df["Promoter Holding (%)"].apply(
                lambda x: "High (>50%)" if x >= 50.0 else ("Medium (30%-50%)" if x >= 30.0 else "Low/Institutional (<30%)")
            )
            all_tiers = ["All Tiers", "High (>50%)", "Medium (30%-50%)", "Low/Institutional (<30%)"]
            selected_tier = st.selectbox("Insider Stake Strength:", all_tiers)
            
        bifurcated_df = master_df.copy()
        if selected_industry != "All Industries":
            bifurcated_df = bifurcated_df[bifurcated_df["Industry"] == selected_industry]
        if selected_tier != "All Tiers":
            bifurcated_df = bifurcated_df[bifurcated_df["Promoter Tier"] == selected_tier]
            
        display_cols = ["Stock Name", "Industry", "Promoter Holding (%)", "Stock PE", "Industry PE", "PB", "ROCE"]
        display_cols = [col for col in display_cols if col in bifurcated_df.columns]
        
        if not bifurcated_df.empty:
            st.dataframe(bifurcated_df[display_cols].sort_values(by=["Industry", "Promoter Holding (%)"], ascending=[True, False]), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    run_integrated_pipeline()
