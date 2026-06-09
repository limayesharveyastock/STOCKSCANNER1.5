import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor
from kiteconnect import KiteConnect

# --- 1. UI & APP SETUP ---
st.set_page_config(page_title="NIFTY 50 Algo Scanner", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    h1, h2 { color: #FFD700 !important; text-align: center; }
    .dataframe { text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Structural Algo Scanner: Trending vs Volatile")

# --- 2. KITE API CONNECTION ---
@st.cache_resource
def get_kite():
    # Ensure you have your secrets configured in .streamlit/secrets.toml
    try:
        kite = KiteConnect(api_key=st.secrets["api_key"])
        kite.set_access_token(st.secrets["access_token"])
        return kite
    except Exception as e:
        st.error(f"Kite Connect Error: {e}")
        return None

def get_instrument_lookup(kite):
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error("Failed to fetch instruments. Check API connection.")
        return {}

# --- 3. INDICATOR MATH ---
def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # Trend Indicators
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    
    # Pivot Points (Auto 20-period lookback) & Fibonacci (0.382)
    df['Pivot'] = (df['high'].rolling(20).mean() + df['low'].rolling(20).mean() + df['close'].rolling(20).mean()) / 3
    high_max = df['high'].rolling(20).max()
    low_min = df['low'].rolling(20).min()
    
    df['R1'] = df['Pivot'] + (0.382 * (high_max - low_min))
    df['S1'] = df['Pivot'] - (0.382 * (high_max - low_min))
    
    return df

# --- 4. TRADING SIGNAL & RISK LOGIC ---
def trading_signal_logic(df, india_vix):
    if len(df) < 20: 
        return {"Signal": "⚪ HOLD", "Target": 0.0, "Stoploss": 0.0}
    
    latest = df.iloc[-1]
    price = latest['close']
    
    # MODE 1: TRENDING MARKET (VIX < 15)
    if india_vix < 15:
        # BUY: Price > 1% above VWMA 9 AND VWMA 9 > VWMA 26
        if price > (1.01 * latest['VWMA_9']) and latest['VWMA_9'] > latest['VWMA_26']:
            target = price * 1.015
            sl = price * (1 - (0.015 / 1.5)) # Mathematically forces 1.5:1 ratio
            return {"Signal": "🟢 BUY", "Target": round(target, 2), "Stoploss": round(sl, 2)}
            
        # SELL: Price < 1% below VWMA 9 AND VWMA 9 < VWMA 26
        elif price < (0.99 * latest['VWMA_9']) and latest['VWMA_9'] < latest['VWMA_26']:
            target = price * 0.985
            sl = price * (1 + (0.015 / 1.5)) # Mathematically forces 1.5:1 ratio
            return {"Signal": "🔴 SELL", "Target": round(target, 2), "Stoploss": round(sl, 2)}

    # MODE 2: SIDEWAYS / VOLATILE MARKET (VIX >= 15)
    else:
        pivot, r1, s1 = latest['Pivot'], latest['R1'], latest['S1']
        midpoint = pivot + ((r1 - pivot) * 0.5) # 50% between R1 and P
        
        # BUY: Using S1 as Stoploss, R1 as Target. Filter: Do not buy if price > 50% between R1 and P
        if price < midpoint: 
            return {"Signal": "🟢 BUY", "Target": round(r1, 2), "Stoploss": round(s1, 2)}
            
        # SELL: Using R1 as Stoploss, S1 as Target. Filter: Do not sell if price < 50% between R1 and P
        elif price > midpoint:
            return {"Signal": "🔴 SELL", "Target": round(s1, 2), "Stoploss": round(r1, 2)}

    # Default Fallback
    return {"Signal": "⚪ HOLD", "Target": 0.0, "Stoploss": 0.0}

# --- 5. PARALLEL SCANNER ---
def execute_parallel_scan(meta_df, token_lookup, kite, india_vix):
    scan_results = []
    
    def worker(row):
        symbol = str(row['Ticker']).strip()
        token = token_lookup.get(symbol)
        if not token: return None
        
        try:
            # Fetch 15m historical data for the last 5 days
            to_date = datetime.now()
            from_date = to_date - timedelta(days=5)
            
            hist = kite.historical_data(
                instrument_token=token, 
                from_date=from_date.strftime('%Y-%m-%d'), 
                to_date=to_date.strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            if not hist: return None
            
            df = calculate_indicators(pd.DataFrame(hist))
            signal_data = trading_signal_logic(df, india_vix)
            
            return {
                "Stock": symbol, 
                "LTP": round(df.iloc[-1]['close'], 2),
                "Signal": signal_data["Signal"], 
                "Target": signal_data["Target"], 
                "Stoploss": signal_data["Stoploss"]
            }
        except Exception:
            return None

    # Execute threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = [r for r in executor.map(worker, [r for _, r in meta_df.iterrows()]) if r]
        
    return results

# --- 6. MAIN EXECUTION & UI RENDERING ---
def run_integrated_pipeline():
    st.sidebar.header("⚙️ Scanner Controls")
    
    # File Uploader for your stock list (Ensure it has a 'Ticker' column)
    uploaded_file = st.sidebar.file_uploader("Upload Stock List (CSV)", type="csv")
    
    # Manual VIX Input
    india_vix = st.sidebar.number_input("Current India VIX", min_value=0.0, value=14.0, step=0.1)
    st.sidebar.info(f"Current Mode: {'Trending (VWMA)' if india_vix < 15 else 'Volatile (Pivot/Fib)'}")
    
    if uploaded_file and st.sidebar.button("🚀 Run Scanner"):
        meta_df = pd.read_csv(uploaded_file)
        
        if 'Ticker' not in meta_df.columns:
            st.error("CSV must contain a column named 'Ticker'")
            return
            
        kite = get_kite()
        if not kite: return
        
        with st.spinner("Connecting to Kite and fetching data..."):
            token_lookup = get_instrument_lookup(kite)
            
            if not token_lookup: return
            
            results = execute_parallel_scan(meta_df, token_lookup, kite, india_vix)
            
            if results:
                st.success("Scan Complete!")
                results_df = pd.DataFrame(results)
                
                # Split into actionable vs non-actionable signals for cleaner UI
                actionable = results_df[results_df["Signal"] != "⚪ HOLD"]
                holds = results_df[results_df["Signal"] == "⚪ HOLD"]
                
                st.subheader("🔥 Actionable Signals")
                st.dataframe(actionable, use_container_width=True, hide_index=True)
                
                with st.expander("View Stocks on HOLD"):
                    st.dataframe(holds, use_container_width=True, hide_index=True)
            else:
                st.warning("No data retrieved or scan failed.")

if __name__ == "__main__":
    run_integrated_pipeline()
