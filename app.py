import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")
st.title("🚀 NIFTY 50 Multi-Dimensional Scanner")

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

# Fundamental Data Matrix for Nifty 50 Stocks
STOCK_METADATA = {
    "ADANIENT": {"Industry": "Conglomerate", "Promoter%": 72.6},
    "ADANIPORTS": {"Industry": "Infrastructure", "Promoter%": 65.9},
    "APOLLOHOSP": {"Industry": "Healthcare", "Promoter%": 29.3},
    "ASIANPAINT": {"Industry": "Consumer Goods", "Promoter%": 52.6},
    "AXISBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0}, # Institutionally held
    "BAJAJ-AUTO": {"Industry": "Automobile", "Promoter%": 55.1},
    "BAJFINANCE": {"Industry": "Banking & Finance", "Promoter%": 55.4},
    "BAJAJFINSV": {"Industry": "Banking & Finance", "Promoter%": 60.7},
    "BEL": {"Industry": "Defense & Capital Goods", "Promoter%": 51.1},
    "BHARTIARTL": {"Industry": "Telecom", "Promoter%": 53.8},
    "BPCL": {"Industry": "Energy & Oil", "Promoter%": 53.0},
    "BRITANNIA": {"Industry": "FMCG", "Promoter%": 50.5},
    "CIPLA": {"Industry": "Pharmaceuticals", "Promoter%": 33.5},
    "COALINDIA": {"Industry": "Energy & Oil", "Promoter%": 63.1},
    "DRREDDY": {"Industry": "Pharmaceuticals", "Promoter%": 26.7},
    "EICHERMOT": {"Industry": "Automobile", "Promoter%": 49.2},
    "GRASIM": {"Industry": "Materials & Cement", "Promoter%": 42.8},
    "HCLTECH": {"Industry": "Information Technology", "Promoter%": 64.3},
    "HDFCBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0},
    "HDFCLIFE": {"Industry": "Banking & Finance", "Promoter%": 50.4},
    "HEROMOTOCO": {"Industry": "Automobile", "Promoter%": 34.8},
    "HINDALCO": {"Industry": "Metals & Mining", "Promoter%": 34.6},
    "HINDUNILVR": {"Industry": "FMCG", "Promoter%": 61.9},
    "ICICIBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0},
    "INDUSINDBK": {"Industry": "Banking & Finance", "Promoter%": 15.9},
    "INFY": {"Industry": "Information Technology", "Promoter%": 14.8},
    "ITC": {"Industry": "FMCG", "Promoter%": 0.0},
    "JSWSTEEL": {"Industry": "Metals & Mining", "Promoter%": 44.8},
    "KOTAKBANK": {"Industry": "Banking & Finance", "Promoter%": 25.9},
    "LT": {"Industry": "Defense & Capital Goods", "Promoter%": 0.0},
    "LTIM": {"Industry": "Information Technology", "Promoter%": 68.6},
    "M&M": {"Industry": "Automobile", "Promoter%": 19.3},
    "MARUTI": {"Industry": "Automobile", "Promoter%": 58.2},
    "MAXHEALTH": {"Industry": "Healthcare", "Promoter%": 23.8},
    "NESTLEIND": {"Industry": "FMCG", "Promoter%": 62.8},
    "NTPC": {"Industry": "Energy & Oil", "Promoter%": 51.1},
    "ONGC": {"Industry": "Energy & Oil", "Promoter%": 58.9},
    "POWERGRID": {"Industry": "Energy & Oil", "Promoter%": 51.3},
    "RELIANCE": {"Industry": "Energy & Oil", "Promoter%": 50.4},
    "SBILIFE": {"Industry": "Banking & Finance", "Promoter%": 55.4},
    "SBIN": {"Industry": "Banking & Finance", "Promoter%": 57.5},
    "SUNPHARMA": {"Industry": "Pharmaceuticals", "Promoter%": 54.5},
    "TATACONSUM": {"Industry": "FMCG", "Promoter%": 33.6},
    "TATAMOTORS": {"Industry": "Automobile", "Promoter%": 46.4},
    "TATASTEEL": {"Industry": "Metals & Mining", "Promoter%": 33.2},
    "TCS": {"Industry": "Information Technology", "Promoter%": 71.8},
    "TECHM": {"Industry": "Information Technology", "Promoter%": 34.6},
    "TITAN": {"Industry": "Consumer Goods", "Promoter%": 52.9},
    "ULTRACEMCO": {"Industry": "Materials & Cement", "Promoter%": 59.9},
    "WIPRO": {"Industry": "Information Technology", "Promoter%": 72.8},
    "JIOFIN": {"Industry": "Banking & Finance", "Promoter%": 47.7}
}

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

@st.fragment(run_every="900s") # Auto-refresh every 15 minutes
def run_integrated_pipeline():
    kite = get_kite()
    token_lookup = get_instrument_lookup()
    nifty_50_symbols = list(STOCK_METADATA.keys())
    
    scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(nifty_50_symbols)
    
    for index, symbol in enumerate(nifty_50_symbols):
        status_text.text(f"Scanning {index + 1}/{total_stocks}: {symbol}...")
        progress_bar.progress((index + 1) / total_stocks)
        
        token = token_lookup.get(symbol)
        if not token:
            continue
        
        try:
            hist = kite.historical_data(
                token, 
                from_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                to_date=datetime.now().strftime('%Y-%m-%d'), 
                interval="15minute"
            )
            
            if not hist or len(hist) < 110:
                continue
                
            df = pd.DataFrame(hist)
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            
            rsi_val = latest['RSI']
            curr_volume = latest['volume']
            vol_ma_val = latest['VOL_MA_50']
            
            if pd.isna(rsi_val) or pd.isna(vol_ma_val):
                continue
            
            # Pure Technical Strategy Conditions
            if curr_volume > vol_ma_val and rsi_val > 60:
                trend = "🟢 BULLISH"
            elif curr_volume > vol_ma_val and rsi_val < 40:
                trend = "🔴 BEARISH"
            else:
                trend = "⚪ NEUTRAL"
                
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            
            # Fetch Fundamental Mappings safely
            meta = STOCK_METADATA.get(symbol, {"Industry": "Other", "Promoter%": 0.0})
            p_holding = meta["Promoter%"]
            
            # Categorize Promoter Strength Tier
            if p_holding >= 50.0:
                p_tier = "High (>50%)"
            elif p_holding >= 30.0:
                p_tier = "Medium (30%-50%)"
            else:
                p_tier = "Low/Institutional (<30%)"
            
            scan_results.append({
                "Stock Name": symbol,
                "Industry": meta["Industry"],
                "Promoter Holding (%)": p_holding,
                "Promoter Tier": p_tier,
                "LTP": round(latest['close'], 2),
                "VWMA 50": round(latest['VWMA_50'], 2),
                "VWMA 100": round(latest['VWMA_100'], 2),
                "RSI (14)": round(rsi_val, 2),
                "Volume": int(curr_volume),
                "Vol MA (50)": round(vol_ma_val, 1),
                "Supertrend": round(supertrend_val, 2),
                "Trend Status": trend
            })
            time.sleep(0.15)
            
        except Exception as e:
            time.sleep(0.15)
            continue

    progress_bar.empty()
    status_text.empty()
    
    if not scan_results:
        st.warning("No data retrieved during scan.")
        return
        
    master_df = pd.DataFrame(scan_results)
    
    # ------------------ STYLED TABS FOR SEPARATION ------------------
    tab1, tab2 = st.tabs(["📊 Technical Strategy Scanner", "🏢 Structural Bifurcation View"])
    
    # --- TAB 1: THE ORIGINAL SCANNER ---
    with tab1:
        bullish_df = master_df[master_df["Trend Status"] == "🟢 BULLISH"]
        bearish_df = master_df[master_df["Trend Status"] == "🔴 BEARISH"]
        neutral_df = master_df[master_df["Trend Status"] == "⚪ NEUTRAL"]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Scanned", len(master_df))
        c2.metric("Vol Spike + RSI > 60", len(bullish_df))
        c3.metric("Vol Spike + RSI < 40", len(bearish_df))
        c4.metric("Consolidating/No Vol", len(neutral_df))
        
        st.divider()
        
        # Original columns list for the clean technical look
        tech_cols = ["Stock Name", "LTP", "VWMA 50", "VWMA 100", "RSI (14)", "Volume", "Vol MA (50)", "Supertrend"]
        
        st.subheader("🔥 Volume Backed Bullish Breakouts")
        if not bullish_df.empty:
            st.dataframe(bullish_df[tech_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently matching volume surge and strong bullish momentum.")
            
        st.divider()
        
        st.subheader("❄️ Volume Backed Bearish Breakdowns")
        if not bearish_df.empty:
            st.dataframe(bearish_df[tech_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No stocks currently matching volume surge and distribution momentum.")
            
        st.divider()
        
        st.subheader("⚖️ Neutral Zone")
        if not neutral_df.empty:
            st.dataframe(neutral_df[tech_cols], use_container_width=True, hide_index=True)

    # --- TAB 2: INDUSTRY & PROMOTER BIFURCATION ---
    with tab2:
        st.subheader("🔍 Structural Filter Matrix")
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            all_industries = ["All Industries"] + sorted(list(master_df["Industry"].unique()))
            selected_industry = st.selectbox("Filter by Industry Sector:", all_industries)
            
        with f_col2:
            all_tiers = ["All Tiers", "High (>50%)", "Medium (30%-50%)", "Low/Institutional (<30%)"]
            selected_tier = st.selectbox("Filter by Promoter Skin-in-the-Game:", all_tiers)
            
        # Dynamically filter the master frame based on structural selections
        bifurcated_df = master_df.copy()
        if selected_industry != "All Industries":
            bifurcated_df = bifurcated_df[bifurcated_df["Industry"] == selected_industry]
        if selected_tier != "All Tiers":
            bifurcated_df = bifurcated_df[bifurcated_df["Promoter Tier"] == selected_tier]
            
        # UI Metrics for the bifurcation view
        bc1, bc2 = st.columns(2)
        bc1.metric("Matches Found", len(bifurcated_df))
        bc2.write(f"Showing results for **{selected_industry}** with **{selected_tier}** Promoter holdings.")
        
        st.divider()
        
        # Data View for Grouped structures
        display_cols = ["Stock Name", "Industry", "Promoter Holding (%)", "Trend Status", "LTP", "RSI (14)", "Volume", "Supertrend"]
        
        if not bifurcated_df.empty:
            st.dataframe(
                bifurcated_df[display_cols].sort_values(by=["Industry", "Promoter Holding (%)"], ascending=[True, False]),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No assets match the combined Industry and Promoter criteria selected above.")
            
    st.write(f"Last data pipeline compilation complete at: {datetime.now().strftime('%H:%M:%S')}")

run_integrated_pipeline()
            
