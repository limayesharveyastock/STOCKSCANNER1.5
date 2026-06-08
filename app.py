import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")
st.title("🚀 NIFTY 200 Production-Grade Multi-Timeframe Scanner")

# Initialize Kite connection
@st.cache_resource
def get_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

# Dynamically fetch and map all active NSE instrument tokens
@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = get_kite()
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

# Secure Loading Engine for CSV Metadata
def load_metadata():
    csv_path = "stock_metadata.csv"
    if not os.path.exists(csv_path):
        st.error(f"🚨 Critical Failure: '{csv_path}' not found in runtime workspace directory.")
        st.info("Please execute your boilerplate generator script to create the configuration repository.")
        return None
    return pd.read_csv(csv_path)

def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50)
    
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="900s")
def run_integrated_pipeline():
    meta_df = load_metadata()
    if meta_df is None:
        return
        
    kite = get_kite()
    token_lookup = get_instrument_lookup()
    
    scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(meta_df)
    
    for index, row in meta_df.iterrows():
        symbol = str(row['Ticker']).strip()
        status_text.text(f"Syncing Vector {index + 1}/{total_stocks}: {symbol}...")
        progress_bar.progress((index + 1) / total_stocks)
        
        token = token_lookup.get(symbol)
        if not token:
            continue
        
        try:
            # Fetch 15-Minute Structural Frame
            hist_15m = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            # Fetch 1-Day Macro Frame
            hist_1d = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="day"
            )
            
            if not hist_15m or len(hist_15m) < 110 or not hist_1d or len(hist_1d) < 110:
                continue
                
            df_15m = pd.DataFrame(hist_15m)
            df_15m = calculate_indicators(df_15m)
            latest_15m = df_15m.iloc[-1]
            
            df_1d = pd.DataFrame(hist_1d)
            df_1d = calculate_indicators(df_1d)
            latest_1d = df_1d.iloc[-1]
            
            # Technical Metrics Evaluation Logic
            rsi_15m = latest_15m['RSI']
            vol_ma_15m = latest_15m['VOL_MA_50']
            curr_vol_15m = latest_15m['volume']
            
            if curr_vol_15m > vol_ma_15m and rsi_15m > 60: trend_15m = "🟢 BULLISH"
            elif curr_vol_15m > vol_ma_15m and rsi_15m < 40: trend_15m = "🔴 BEARISH"
            else: trend_15m = "⚪ NEUTRAL"
            
            rsi_1d = latest_1d['RSI']
            vol_ma_1d = latest_1d['VOL_MA_50']
            curr_vol_1d = latest_1d['volume']
            
            if curr_vol_1d > vol_ma_1d and rsi_1d > 60: trend_1d = "🟢 BULLISH"
            elif curr_vol_1d > vol_ma_1d and rsi_1d < 40: trend_1d = "🔴 BEARISH"
            else: trend_1d = "⚪ NEUTRAL"
                
            st_15m = latest_15m.filter(like='SUPERT_').iloc[0]
            st_1d = latest_1d.filter(like='SUPERT_').iloc[0]
            
            scan_results.append({
                "Stock Name": symbol,
                "Industry": row["Industry"],
                "Promoter Holding (%)": row["Promoter_Percent"],
                "Stock PE": row["Stock_PE"],
                "Industry PE": row["Industry_PE"],
                "PB": row["PB"],
                "ROCE": row["ROCE"],
                "52W High": row["52W_High"],
                "52W Low": row["52W_Low"],
                "5Y High": row["5Y_High"],
                "5Y Low": row["5Y_Low"],
                "LTP": round(latest_15m['close'], 2),
                
                # Multi-Timeframe Mappings
                "RSI (15M)": round(rsi_15m, 2),
                "Vol MA (15M)": round(vol_ma_15m, 1),
                "Supertrend (15M)": round(st_15m, 2),
                "Trend Status (15M)": trend_15m,
                "VWMA 50 (15M)": round(latest_15m['VWMA_50'], 2),
                "VWMA 100 (15M)": round(latest_15m['VWMA_100'], 2),
                
                "RSI (1D)": round(rsi_1d, 2),
                "Vol MA (1D)": round(vol_ma_1d, 1),
                "Supertrend (1D)": round(st_1d, 2),
                "Trend Status (1D)": trend_1d,
                "VWMA 50 (1D)": round(latest_1d['VWMA_50'], 2),
                "VWMA 100 (1D)": round(latest_1d['VWMA_100'], 2),
            })
            time.sleep(0.25) # Maintained to safely avoid Kite Connect throttle boundaries
            
        except Exception as e:
            time.sleep(0.25)
            continue

    progress_bar.empty()
    status_text.empty()
    
    if not scan_results:
        st.warning("Empty output across processing pipeline.")
        return
        
    master_df = pd.DataFrame(scan_results)
    
    tab1, tab2 = st.tabs(["📊 Technical Multi-Timeframe Scanner", "🏢 Structural Bifurcation View"])
    
    # --- TAB 1: WORKSPACE INTERACTION ---
    with tab1:
        st.subheader("⚙️ Timeframe Filter Configurator")
        active_tf = st.radio("Select Active Scanner Frame Layer:", ["15 Minute", "1 Day"], horizontal=True)
        
        suffix = " (15M)" if active_tf == "15 Minute" else " (1D)"
        trend_col = f"Trend Status{suffix}"
        
        bullish_df = master_df[master_df[trend_col] == "🟢 BULLISH"]
        bearish_df = master_df[master_df[trend_col] == "🔴 BEARISH"]
        neutral_df = master_df[master_df[trend_col] == "⚪ NEUTRAL"]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Scanned Portfolio", len(master_df))
        c2.metric("Bullish Vol Breakouts", len(bullish_df))
        c3.metric("Bearish Vol Breakdowns", len(bearish_df))
        c4.metric("Neutral / Consolidation Grid", len(neutral_df))
        
        st.divider()
        
        tech_display_cols = [
            "Stock Name", "LTP", f"VWMA 50{suffix}", f"VWMA 100{suffix}", 
            f"RSI{suffix}", f"Vol MA{suffix}", f"Supertrend{suffix}"
        ]
        
        st.subheader(f"🔥 Vol Surge Buy Signals ({active_tf})")
        if not bullish_df.empty:
            st.dataframe(bullish_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No breakouts verified for current index list.")
            
        st.divider()
        
        st.subheader(f"❄️ Vol Surge Sell Signals ({active_tf})")
        if not bearish_df.empty:
            st.dataframe(bearish_df[tech_display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No downside trend vectors matching criteria.")
            
        st.divider()
        
        st.subheader(f"⚖️ Neutral Baseline Matrix ({active_tf})")
        if not neutral_df.empty:
            st.dataframe(neutral_df[tech_display_cols], use_container_width=True, hide_index=True)

    # --- TAB 2: SECTOR PROFILE ANALYSIS ---
    with tab2:
        st.subheader("🔍 Valuation & Ownership Filter Matrix")
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            all_industries = ["All Industries"] + sorted(list(master_df["Industry"].unique()))
            selected_industry = st.selectbox("Filter Sector Classification:", all_industries)
            
        with f_col2:
            master_df["Promoter Tier"] = master_df["Promoter Holding (%)"].apply(
                lambda x: "High (>50%)" if x >= 50.0 else ("Medium (30%-50%)" if x >= 30.0 else "Low/Institutional (<30%)")
            )
            all_tiers = ["All Tiers", "High (>50%)", "Medium (30%-50%)", "Low/Institutional (<30%)"]
            selected_tier = st.selectbox("Filter Insider Stake Strength:", all_tiers)
            
        bifurcated_df = master_df.copy()
        if selected_industry != "All Industries":
            bifurcated_df = bifurcated_df[bifurcated_df["Industry"] == selected_industry]
        if selected_tier != "All Tiers":
            bifurcated_df = bifurcated_df[bifurcated_df["Promoter Tier"] == selected_tier]
            
        st.divider()
        
        display_cols = [
            "Stock Name", "Industry", "Promoter Holding (%)", 
            "Stock PE", "Industry PE", "PB", "ROCE", 
            "52W High", "52W Low", "5Y High", "5Y Low"
        ]
        
        if not bifurcated_df.empty:
            st.dataframe(
                bifurcated_df[display_cols].sort_values(by=["Industry", "Promoter Holding (%)"], ascending=[True, False]),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No portfolios pass matching criteria filters.")
            
    st.write(f"Pipeline Refresh Complete | Current System Matrix Sync: {datetime.now().strftime('%H:%M:%S')}")

run_integrated_pipeline()
                                                              
