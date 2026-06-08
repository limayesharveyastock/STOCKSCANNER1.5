import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")
st.title("🎯 NIFTY 50 Blue-Chip Multi-Timeframe Structural Scanner")

# --- INITIALIZATION ---
@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

def fetch_india_vix(kite):
    """Fetches live India VIX level to determine active structural regime."""
    try:
        vix_data = kite.ltp("NSE:INDIA VIX")
        return float(vix_data["NSE:INDIA VIX"]["last_price"])
    except Exception:
        return 14.5  # Strategic baseline fallback if API throttling occurs

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
                    "Symbol": "Ticker", "Promoter Holding (%)": "Promoter_Percent",
                    "Promoter Holding": "Promoter_Percent", "Stock PE": "Stock_PE",
                    "PE": "Stock_PE", "Industry PE": "Industry_PE", "Price to Book": "PB", "P/B": "PB"
                }
                df = df.rename(columns=rename_map)
                df = df[df["Ticker"].isin(nifty50_universe.keys())]
                return df
        except Exception as e:
            st.error(f"⚠️ CSV parsing error: {e}")

    fallback_data = [{
        "Ticker": ticker, "Industry": data["Industry"], "Promoter_Percent": data["Promoter"],
        "Stock_PE": data["PE"], "Industry_PE": data["Ind_PE"], "PB": data["PB"], "ROCE": data["ROCE"]
    } for ticker, data in nifty50_universe.items()]
    return pd.DataFrame(fallback_data)

# --- TECHNICAL METRICS ENGINE ---
def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def calculate_session_pivots(df_1d):
    """Calculates true Fibonacci Pivots using previous day session metrics to match Zerodha Kite charts exactly."""
    if len(df_1d) < 2:
        return 0.0, 0.0, 0.0
    
    # Extract the last fully completed daily session candle
    prev_day = df_1d.iloc[-2]
    high_val = float(prev_day['high'])
    low_val = float(prev_day['low'])
    close_val = float(prev_day['close'])
    
    p = (high_val + low_val + close_val) / 3.0
    r1 = p + 0.382 * (high_val - low_val)
    s1 = p - 0.382 * (high_val - low_val)
    return round(p, 2), round(r1, 2), round(s1, 2)

def get_last_crossover_details(df):
    if len(df) < 2: return 0.0, "No Cross", 0
    df = df.copy().dropna(subset=['VWMA_9', 'VWMA_26']).reset_index(drop=True)
    df['diff'] = df['VWMA_9'] - df['VWMA_26']
    df['sign'] = (df['diff'] > 0).astype(int)
    crosses = df[df['sign'] != df['sign'].shift(1)].iloc[1:]
    
    if not crosses.empty:
        last_cross_row = crosses.iloc[-1]
        bars_ago = len(df) - 1 - crosses.index[-1]
        c_type = "🔥 Bullish" if last_cross_row['VWMA_9'] > last_cross_row['VWMA_26'] else "❄️ Bearish"
        return round(last_cross_row['VWMA_9'], 2), c_type, int(bars_ago)
    return 0.0, "No Cross", 0

# --- DATA COMPILER ---
def execute_parallel_scan(meta_df, token_lookup, kite, india_vix):
    scan_results = []
    
    def worker(row):
        symbol = str(row['Ticker']).strip()
        token = token_lookup.get(symbol)
        if not token: return None
        try:
            hist_1d = kite.historical_data(token, from_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="day")
            hist_15m = kite.historical_data(token, from_date=(datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="15minute")
            
            if not hist_1d or not hist_15m: return None
            
            df_1d = calculate_indicators(pd.DataFrame(hist_1d))
            df_15m = calculate_indicators(pd.DataFrame(hist_15m))
            
            # Anchor calculations from standard previous daily session to match Kite
            p_val, r1_val, s1_val = calculate_session_pivots(df_1d)
            
            timeframes = {"15M": df_15m, "1D": df_1d}
            stock_data = {
                "Stock Name": symbol,
                "Industry": row.get("Industry", "Blue-Chip Core"),
                "Promoter Holding (%)": row.get("Promoter_Percent", 0.0),
                "Stock PE": row.get("Stock_PE", 0.0),
                "Industry PE": row.get("Industry_PE", 0.0),
                "PB": row.get("PB", 0.0),
                "ROCE": row.get("ROCE", 0.0),
                "LTP": round(float(df_15m.iloc[-1]['close']), 2)
            }
            
            for tf_suffix, df_tf in timeframes.items():
                latest = df_tf.iloc[-1]
                ltp = round(float(latest['close']), 2)
                v9 = float(latest['VWMA_9'])
                v26 = float(latest['VWMA_26'])
                rsi = float(latest['RSI'])
                
                cross_val, cross_type, periods_ago = get_last_crossover_details(df_tf)
                
                signal = "⚪ NEUTRAL"
                target_val = 0.0
                sl_val = 0.0
                
                # --- MARKET REGIME EXECUTION ENGINE ---
                if india_vix < 15.0:
                    # TRENDING CONDITIONS
                    if ltp > (1.01 * v9) and v9 > v26:
                        signal = "🟢 BUY"
                        target_val = round(ltp * 1.015, 2)
                        sl_val = round(ltp * 0.99, 2)      # Maining strict 1.5:1 ratio layout
                    elif ltp < (0.99 * v9) and v9 < v26:
                        signal = "🔴 SELL"
                        target_val = round(ltp * 0.985, 2)
                        sl_val = round(ltp * 1.01, 2)
                else:
                    # SIDEWAYS / VOLATILE CONDITIONS (Pivots Match Kite Indicators)
                    mid_r1_p = (r1_val + p_val) / 2.0
                    mid_s1_p = (s1_val + p_val) / 2.0
                    
                    is_bullish = ("Bullish" in cross_type or (v9 > v26)) and rsi > 50
                    is_bearish = ("Bearish" in cross_type or (v9 < v26)) and rsi < 50
                    
                    if is_bullish:
                        # Structural Filter Check: Price cannot be more than 50% between P and R1
                        if ltp <= mid_r1_p:
                            signal = "🟢 BUY"
                            target_val = r1_val
                            target_dist = r1_val - ltp
                            sl_val = round(ltp - (target_dist / 1.5), 2)  # Extrapolates 1.5:1 Risk-Reward Floor
                    elif is_bearish:
                        # Structural Filter Check: Price cannot be lower than 50% between P and S1
                        if ltp >= mid_s1_p:
                            signal = "🔴 SELL"
                            target_val = s1_val
                            target_dist = ltp - s1_val
                            sl_val = round(ltp + (target_dist / 1.5), 2)  # Extrapolates 1.5:1 Risk-Reward Ceiling
                
                within_cross = "🎯 YES" if (cross_val * 0.99) <= ltp <= (cross_val * 1.01) else "No"
                
                stock_data.update({
                    f"Action Signal ({tf_suffix})": signal,
                    f"Target ({tf_suffix})": target_val,
                    f"StopLoss ({tf_suffix})": sl_val,
                    f"RSI ({tf_suffix})": round(rsi, 2),
                    f"Last Cross Value ({tf_suffix})": cross_val,
                    f"Last Cross Type ({tf_suffix})": f"{cross_type} ({periods_ago} periods ago)",
                    f"Within 1% of Cross ({tf_suffix})": within_cross,
                    f"P / R1 / S1 ({tf_suffix})": f"{p_val} | {r1_val} | {s1_val}"
                })
                
            return stock_data
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, row) for _, row in meta_df.iterrows()]
        for future in as_completed(futures):
            res = future.result()
            if res: scan_results.append(res)
                
    return scan_results

# --- INTERACTIVE DASHBOARD VIEW ---
def run_integrated_pipeline():
    meta_df = load_metadata()
    if meta_df is None or meta_df.empty: return
        
    kite = get_kite()
    token_lookup = get_instrument_lookup()
    india_vix = fetch_india_vix(kite)
    
    vix_color = "🟢" if india_vix < 15.0 else "🟠"
    regime_str = "**TRENDING METRICS** (VIX < 15)" if india_vix < 15.0 else "**KITE PIVOT STRUCTURE** (VIX ≥ 15)"
    
    st.sidebar.markdown("### 🛠️ Live Volatility Guard")
    st.sidebar.markdown(f"**India VIX LTP:** {vix_color} `{india_vix}`")
    st.sidebar.markdown(f"**Active Ruleset:** {regime_str}")
    st.sidebar.markdown("🔒 *Enforced Target-to-StopLoss Ratio: 1.5 : 1*")
    
    if "master_df" not in st.session_state: st.session_state.master_df = None
    if "last_run" not in st.session_state: st.session_state.last_run = None
        
    current_time = time.time()
    should_scan = st.session_state.master_df is None or (st.session_state.last_run and (current_time - st.session_state.last_run) >= 900)
        
    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("🔄 Force Re-Scan Nifty 50", use_container_width=True): should_scan = True
    with c_btn2:
        if st.session_state.last_run:
            st.write(f"⏱️ Matrix sync verified at: **{datetime.fromtimestamp(st.session_state.last_run).strftime('%H:%M:%S')}**")
            
    if should_scan:
        with st.spinner("🚀 Syncing indicators to match live Kite terminal data..."):
            results = execute_parallel_scan(meta_df, token_lookup, kite, india_vix)
            if results:
                st.session_state.master_df = pd.DataFrame(results)
                st.session_state.last_run = current_time
                st.rerun()

    if st.session_state.master_df is None: return
    master_df = st.session_state.master_df
    
    tab1, tab2 = st.tabs(["📊 Technical Multi-Timeframe Scanner", "🏢 Structural Bifurcation View"])
    
    with tab1:
        st.subheader("⚙️ Timeframe Filter Configurator")
        active_tf = st.radio("Select Active Scanner Frame Layer:", ["15 Minute", "1 Day"], horizontal=True)
        
        suffix = " (15M)" if active_tf == "15 Minute" else " (1D)"
        near_cross_col = f"Within 1% of Cross{suffix}"
        near_cross_df = master_df[master_df[near_cross_col] == "🎯 YES"]
        
        c1, c2 = st.columns(2)
        c1.metric("Nifty 50 Inspected Assets", len(master_df))
        c2.metric(f"Assets within 1% Value Border {suffix}", len(near_cross_df))
        
        st.divider()
        
        if active_tf == "15 Minute":
            tech_display_cols = [
                "Stock Name", "Action Signal (15M)", "LTP", "Target (15M)", "StopLoss (15M)",
                "Last Cross Value (15M)", "Last Cross Type (15M)", "Within 1% of Cross (15M)", "P / R1 / S1 (15M)"
            ]
        else:
            tech_display_cols = [
                "Stock Name", "Action Signal (1D)", "LTP", "Target (1D)", "StopLoss (1D)",
                "Last Cross Value (1D)", "Last Cross Type (1D)", "Within 1% of Cross (1D)", "P / R1 / S1 (1D)"
            ]
            
        st.subheader(f"⚡ Actionable Structural Signals & Alerts ({active_tf})")
        signals_df = master_df[master_df[tech_display_cols[1]].isin(["🟢 BUY", "🔴 SELL"])]
        if not signals_df.empty:
            st.dataframe(signals_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info(f"No assets meet the current criteria under the {regime_str} structure.")
            
        st.subheader(f"📋 Complete Index Tracker Overview ({active_tf})")
        st.dataframe(master_df[tech_display_cols].sort_values(by=tech_display_cols[1], ascending=True), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("🔍 Valuation & Ownership Filter Matrix")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected_industry = st.selectbox("Sector Classification:", ["All Industries"] + sorted(list(master_df["Industry"].unique())))
        with f_col2:
            selected_tier = st.selectbox("Insider Stake Strength:", ["All Tiers", "High (>50%)", "Medium (30%-50%)", "Low/Institutional (<30%)"])
            
        bifurcated_df = master_df.copy()
        if selected_industry != "All Industries":
            bifurcated_df = bifurcated_df[bifurcated_df["Industry"] == selected_industry]
        if selected_tier != "All Tiers":
            master_df["Promoter Tier"] = master_df["Promoter Holding (%)"].apply(lambda x: "High (>50%)" if x >= 50.0 else ("Medium (30%-50%)" if x >= 30.0 else "Low/Institutional (<30%)"))
            bifurcated_df = bifurcated_df[master_df["Promoter Tier"] == selected_tier]
            
        display_cols = ["Stock Name", "Industry", "Promoter Holding (%)", "Stock PE", "Industry PE", "PB", "ROCE", "LTP"]
        if not bifurcated_df.empty:
            st.dataframe(bifurcated_df[display_cols].sort_values(by=["Industry", "Promoter Holding (%)"], ascending=[True, False]), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    run_integrated_pipeline()
