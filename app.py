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
        "Stock_PE": data["PE"], "Industry_PE": data["Ind_PE"], "PB": data["PB"], "ROCE": data["ROCE"]
    } for ticker, data in nifty50_universe.items()]
    return pd.DataFrame(fallback_data)

# --- CLEAN INDICATOR ENGINE ---
def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    # Lean indicator configuration
    df['VWMA_9'] = ta.vwma(df['close'], df['volume'], length=9)
    df['VWMA_26'] = ta.vwma(df['close'], df['volume'], length=26)
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df

def get_current_cross_state(df):
    if len(df) < 2: return "No Cross"
    latest, prev = df.iloc[-1], df.iloc[-2]
    if prev['VWMA_9'] <= prev['VWMA_26'] and latest['VWMA_9'] > latest['VWMA_26']: return "🔥 BULLISH CROSS"
    if prev['VWMA_9'] >= prev['VWMA_26'] and latest['VWMA_9'] < latest['VWMA_26']: return "❄️ BEARISH CROSS"
    return "🟢 Above" if latest['VWMA_9'] > latest['VWMA_26'] else "🔴 Below"

def get_last_crossover_details(df):
    """
    Looks back through historical records to extract the exact point of index intersection.
    Returns: (Crossover Value, Crossover Type, Distance in Bars/Days)
    """
    if len(df) < 2: return 0.0, "No Cross", 0
    df = df.copy().dropna(subset=['VWMA_9', 'VWMA_26']).reset_index(drop=True)
    
    df['diff'] = df['VWMA_9'] - df['VWMA_26']
    df['sign'] = (df['diff'] > 0).astype(int)
    crosses = df[df['sign'] != df['sign'].shift(1)].iloc[1:]
    
    if not crosses.empty:
        last_cross_row = crosses.iloc[-1]
        bars_ago = len(df) - 1 - crosses.index[-1]
        c_type = "🔥 Bullish" if last_cross_row['VWMA_9'] > last_cross_row['VWMA_26'] else "❄️ Bearish"
        
        # TARGET CHANGE: Extract indicator crossing price value itself instead of the candle close
        cross_value = round(last_cross_row['VWMA_9'], 2)
        return cross_value, c_type, int(bars_ago)
    return 0.0, "No Cross", 0

# --- DATA STREAM COMPILER ---
def execute_parallel_scan(meta_df, token_lookup, kite):
    scan_results = []
    
    def worker(row):
        symbol = str(row['Ticker']).strip()
        token = token_lookup.get(symbol)
        if not token: return None
        try:
            # Dual historical sequence fetch
            hist_1d = kite.historical_data(token, from_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="day")
            hist_15m = kite.historical_data(token, from_date=(datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'), to_date=datetime.now().strftime('%Y-%m-%d'), interval="15minute")
            
            if not hist_1d or not hist_15m: return None
            
            df_1d = calculate_indicators(pd.DataFrame(hist_1d))
            df_15m = calculate_indicators(pd.DataFrame(hist_15m))
            
            latest_15m = df_15m.iloc[-1]
            latest_1d = df_1d.iloc[-1]
            ltp = round(float(latest_15m['close']), 2)
            
            # Extract precise timeframe cross intersection price barriers
            cross_val_15m, cross_type_15m, bars_ago_15m = get_last_crossover_details(df_15m)
            cross_val_1d, cross_type_1d, days_ago_1d = get_last_crossover_details(df_1d)
            
            # Formulate the 1% buffer borders relative to indicator value crossing
            within_15m = "🎯 YES" if (cross_val_15m * 0.99) <= ltp <= (cross_val_15m * 1.01) else "No"
            within_1d = "🎯 YES" if (cross_val_1d * 0.99) <= ltp <= (cross_val_1d * 1.01) else "No"
            
            return {
                "Stock Name": symbol,
                "Industry": row.get("Industry", "Blue-Chip Core"),
                "Promoter Holding (%)": row.get("Promoter_Percent", 0.0),
                "Stock PE": row.get("Stock_PE", 0.0),
                "Industry PE": row.get("Industry_PE", 0.0),
                "PB": row.get("PB", 0.0),
                "ROCE": row.get("ROCE", 0.0),
                "LTP": ltp,
                
                # Tactical 15-Minute Metrics
                "RSI (15M)": round(latest_15m['RSI'], 2),
                "VWMA Cross (15M)": get_current_cross_state(df_15m),
                "Last Cross Value (15M)": cross_val_15m,
                "Last Cross Type (15M)": f"{cross_type_15m} ({bars_ago_15m} bars ago)",
                "Within 1% of Cross (15M)": within_15m,
                
                # Strategic Daily Metrics
                "RSI (1D)": round(latest_1d['RSI'], 2),
                "VWMA Cross (1D)": get_current_cross_state(df_1d),
                "Last Cross Value (1D)": cross_val_1d,
                "Last Cross Type (1D)": f"{cross_type_1d} ({days_ago_1d} days ago)",
                "Within 1% of Cross (1D)": within_1d
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, row) for _, row in meta_df.iterrows()]
        for future in as_completed(futures):
            res = future.result()
            if res: scan_results.append(res)
                
    return scan_results

# --- INTERACTIVE DASHBOARD VIEW ---
@st.fragment(run_every="900s")
def run_integrated_pipeline():
    meta_df = load_metadata()
    if meta_df is None or meta_df.empty: return
        
    kite = get_kite()
    token_lookup = get_instrument_lookup()
    
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
        with st.spinner("🚀 Scanning multi-timeframe records concurrently..."):
            results = execute_parallel_scan(meta_df, token_lookup, kite)
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
                "Stock Name", "LTP", "VWMA Cross (15M)", "Last Cross Value (15M)", 
                "Last Cross Type (15M)", "Within 1% of Cross (15M)", "RSI (15M)"
            ]
        else:
            tech_display_cols = [
                "Stock Name", "LTP", "VWMA Cross (1D)", "Last Cross Value (1D)", 
                "Last Cross Type (1D)", "Within 1% of Cross (1D)", "RSI (1D)"
            ]
            
        st.subheader(f"⚡ Proximity Alerts Near Cross Target ({active_tf})")
        if not near_cross_df.empty:
            st.dataframe(near_cross_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info(f"No active assets are consolidation-testing within 1% of historical {active_tf} crossover levels.")
            
        st.subheader(f"📋 Complete Index Tracker Overview ({active_tf})")
        st.dataframe(master_df[tech_display_cols].sort_values(by=tech_display_cols[3], ascending=False), use_container_width=True, hide_index=True)

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
                
