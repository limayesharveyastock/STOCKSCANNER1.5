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

# Fundamental Data Matrix updated with PE, PB, and ROCE (%) values
STOCK_METADATA = {
    "ADANIENT": {"Industry": "Conglomerate", "Promoter%": 72.6, "PE": 92.4, "PB": 9.2, "ROCE": 9.8},
    "ADANIPORTS": {"Industry": "Infrastructure", "Promoter%": 65.9, "PE": 35.1, "PB": 4.8, "ROCE": 13.2},
    "APOLLOHOSP": {"Industry": "Healthcare", "Promoter%": 29.3, "PE": 88.7, "PB": 9.4, "ROCE": 11.7},
    "ASIANPAINT": {"Industry": "Consumer Goods", "Promoter%": 52.6, "PE": 54.3, "PB": 15.1, "ROCE": 29.4},
    "AXISBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 12.8, "PB": 1.9, "ROCE": 10.2},
    "BAJAJ-AUTO": {"Industry": "Automobile", "Promoter%": 55.1, "PE": 32.4, "PB": 9.8, "ROCE": 31.6},
    "BAJFINANCE": {"Industry": "Banking & Finance", "Promoter%": 55.4, "PE": 28.9, "PB": 4.4, "ROCE": 11.8},
    "BAJAJFINSV": {"Industry": "Banking & Finance", "Promoter%": 60.7, "PE": 31.2, "PB": 3.9, "ROCE": 11.5},
    "BEL": {"Industry": "Defense & Capital Goods", "Promoter%": 51.1, "PE": 48.5, "PB": 11.2, "ROCE": 26.3},
    "BHARTIARTL": {"Industry": "Telecom", "Promoter%": 53.8, "PE": 61.2, "PB": 6.4, "ROCE": 12.4},
    "BPCL": {"Industry": "Energy & Oil", "Promoter%": 53.0, "PE": 14.2, "PB": 2.1, "ROCE": 17.1},
    "BRITANNIA": {"Industry": "FMCG", "Promoter%": 50.5, "PE": 52.1, "PB": 28.4, "ROCE": 49.2},
    "CIPLA": {"Industry": "Pharmaceuticals", "Promoter%": 33.5, "PE": 24.6, "PB": 3.8, "ROCE": 18.3},
    "COALINDIA": {"Industry": "Energy & Oil", "Promoter%": 63.1, "PE": 9.8, "PB": 3.4, "ROCE": 52.1},
    "DRREDDY": {"Industry": "Pharmaceuticals", "Promoter%": 26.7, "PE": 18.9, "PB": 3.1, "ROCE": 20.4},
    "EICHERMOT": {"Industry": "Automobile", "Promoter%": 49.2, "PE": 29.7, "PB": 7.2, "ROCE": 27.5},
    "GRASIM": {"Industry": "Materials & Cement", "Promoter%": 42.8, "PE": 42.1, "PB": 2.2, "ROCE": 8.4},
    "HCLTECH": {"Industry": "Information Technology", "Promoter%": 64.3, "PE": 26.4, "PB": 6.1, "ROCE": 28.7},
    "HDFCBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 18.2, "PB": 2.6, "ROCE": 10.8},
    "HDFCLIFE": {"Industry": "Banking & Finance", "Promoter%": 50.4, "PE": 78.4, "PB": 7.8, "ROCE": 9.4},
    "HEROMOTOCO": {"Industry": "Automobile", "Promoter%": 34.8, "PE": 23.1, "PB": 4.9, "ROCE": 25.1},
    "HINDALCO": {"Industry": "Metals & Mining", "Promoter%": 34.6, "PE": 15.4, "PB": 1.7, "ROCE": 11.6},
    "HINDUNILVR": {"Industry": "FMCG", "Promoter%": 61.9, "PE": 58.2, "PB": 11.4, "ROCE": 27.3},
    "ICICIBANK": {"Industry": "Banking & Finance", "Promoter%": 0.0, "PE": 17.5, "PB": 3.1, "ROCE": 11.3},
    "INDUSINDBK": {"Industry": "Banking & Finance", "Promoter%": 15.9, "PE": 13.1, "PB": 1.8, "ROCE": 9.9},
    "INFY": {"Industry": "Information Technology", "Promoter%": 14.8, "PE": 24.1, "PB": 7.4, "ROCE": 37.2},
    "ITC": {"Industry": "FMCG", "Promoter%": 0.0, "PE": 26.8, "PB": 7.2, "ROCE": 39.1},
    "JSWSTEEL": {"Industry": "Metals & Mining", "Promoter%": 44.8, "PE": 28.2, "PB": 2.8, "ROCE": 12.1},
    "KOTAKBANK": {"Industry": "Banking & Finance", "Promoter%": 25.9, "PE": 19.1, "PB": 2.9, "ROCE": 11.1},
    "LT": {"Industry": "Defense & Capital Goods", "Promoter%": 0.0, "PE": 37.4, "PB": 4.9, "ROCE": 14.8},
    "LTIM": {"Industry": "Information Technology", "Promoter%": 68.6, "PE": 33.7, "PB": 7.8, "ROCE": 28.4},
    "M&M": {"Industry": "Automobile", "Promoter%": 19.3, "PE": 30.2, "PB": 5.1, "ROCE": 18.2},
    "MARUTI": {"Industry": "Automobile", "Promoter%": 58.2, "PE": 27.4, "PB": 4.6, "ROCE": 21.3},
    "MAXHEALTH": {"Industry": "Healthcare", "Promoter%": 23.8, "PE": 91.3, "PB": 8.7, "ROCE": 13.1},
    "NESTLEIND": {"Industry": "FMCG", "Promoter%": 62.8, "PE": 76.4, "PB": 24.1, "ROCE": 56.4},
    "NTPC": {"Industry": "Energy & Oil", "Promoter%": 51.1, "PE": 18.9, "PB": 2.4, "ROCE": 11.8},
    "ONGC": {"Industry": "Energy & Oil", "Promoter%": 58.9, "PE": 8.4, "PB": 1.1, "ROCE": 14.3},
    "POWERGRID": {"Industry": "Energy & Oil", "Promoter%": 51.3, "PE": 16.2, "PB": 3.1, "ROCE": 12.9},
    "RELIANCE": {"Industry": "Energy & Oil", "Promoter%": 50.4, "PE": 26.5, "PB": 2.3, "ROCE": 10.1},
    "SBILIFE": {"Industry": "Banking & Finance", "Promoter%": 55.4, "PE": 82.1, "PB": 11.1, "ROCE": 12.1},
    "SBIN": {"Industry": "Banking & Finance", "Promoter%": 57.5, "PE": 10.4, "PB": 1.6, "ROCE": 10.5},
    "SUNPHARMA": {"Industry": "Pharmaceuticals", "Promoter%": 54.5, "PE": 36.8, "PB": 4.9, "ROCE": 16.4},
    "TATACONSUM": {"Industry": "FMCG", "Promoter%": 33.6, "PE": 68.2, "PB": 4.2, "ROCE": 9.1},
    "TATAMOTORS": {"Industry": "Automobile", "Promoter%": 46.4, "PE": 11.6, "PB": 3.8, "ROCE": 19.4},
    "TATASTEEL": {"Industry": "Metals & Mining", "Promoter%": 33.2, "PE": 45.3, "PB": 1.9, "ROCE": 9.2},
    "TCS": {"Industry": "Information Technology", "Promoter%": 71.8, "PE": 30.1, "PB": 13.2, "ROCE": 51.4},
    "TECHM": {"Industry": "Information Technology", "Promoter%": 34.6, "PE": 44.2, "PB": 4.1, "ROCE": 17.2},
    "TITAN": {"Industry": "Consumer Goods", "Promoter%": 52.9, "PE": 85.4, "PB": 19.8, "ROCE": 23.5},
    "ULTRACEMCO": {"Industry": "Materials & Cement", "Promoter%": 59.9, "PE": 41.2, "PB": 4.8, "ROCE": 12.8},
    "WIPRO": {"Industry": "Information Technology", "Promoter%": 72.8, "PE": 22.9, "PB": 4.6, "ROCE": 21.1},
    "JIOFIN": {"Industry": "Banking & Finance", "Promoter%": 47.7, "PE": 122.4, "PB": 1.8, "ROCE": 4.9}
}

def calculate_indicators(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])
    
    df['VWMA_50'] = ta.vwma(df['close'], df['volume'], length=50)
    df['VWMA_100'] = ta.vwma(df['close'], df['volume'], length=100)
    df['RSI'] = ta.rsi(df['close'], length=14)
    df['VOL_MA_50'] = ta.sma(df['volume'], length=50) # Explicitly confirmed 50 Length
    
    st_data = ta.supertrend(df['high'], df['low'], df['close'], length=7, multiplier=3)
    df = pd.concat([df, st_data], axis=1)
    return df

@st.fragment(run_every="900s")
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
            
            if curr_volume > vol_ma_val and rsi_val > 60:
                trend = "🟢 BULLISH"
            elif curr_volume > vol_ma_val and rsi_val < 40:
                trend = "🔴 BEARISH"
            else:
                trend = "⚪ NEUTRAL"
                
            supertrend_val = latest.filter(like='SUPERT_').iloc[0]
            
            meta = STOCK_METADATA.get(symbol, {"Industry": "Other", "Promoter%": 0.0, "PE": 0.0, "PB": 0.0, "ROCE": 0.0})
            p_holding = meta["Promoter%"]
            
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
                "Stock PE": meta["PE"],
                "PB": meta["PB"],
                "ROCE": meta["ROCE"],
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
    
    tab1, tab2 = st.tabs(["📊 Technical Strategy Scanner", "🏢 Structural Bifurcation View"])
    
    # --- TAB 1: THE OLD SCANNER (UNTOUCHED TECHNICAL STRATEGY) ---
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

    # --- TAB 2: UPDATED STRUCTURAL BIFURCATION VIEW ---
    with tab2:
        st.subheader("🔍 Structural Filter Matrix")
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            all_industries = ["All Industries"] + sorted(list(master_df["Industry"].unique()))
            selected_industry = st.selectbox("Filter by Industry Sector:", all_industries)
            
        with f_col2:
            all_tiers = ["All Tiers", "High (>50%)", "Medium (30%-50%)", "Low/Institutional (<30%)"]
            selected_tier = st.selectbox("Filter by Promoter Skin-in-the-Game:", all_tiers)
            
        bifurcated_df = master_df.copy()
        if selected_industry != "All Industries":
            bifurcated_df = bifurcated_df[bifurcated_df["Industry"] == selected_industry]
        if selected_tier != "All Tiers":
            bifurcated_df = bifurcated_df[bifurcated_df["Promoter Tier"] == selected_tier]
            
        bc1, bc2 = st.columns(2)
        bc1.metric("Matches Found", len(bifurcated_df))
        bc2.write(f"Showing results for **{selected_industry}** with **{selected_tier}** Promoter holdings.")
        
        st.divider()
        
        # Supertrend removed; Stock PE, PB, and ROCE added to display mapping
        display_cols = [
            "Stock Name", "Industry", "Promoter Holding (%)", "Trend Status", 
            "LTP", "RSI (14)", "Stock PE", "PB", "ROCE"
        ]
        
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
    
