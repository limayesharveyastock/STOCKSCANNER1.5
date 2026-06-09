import streamlit as st
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from kiteconnect import KiteConnect

st.set_page_config(layout="wide")

# --- Styling omitted for brevity ---

st.title("🎯 NIFTY 50 Blue-Chip Multi-Timeframe Structural Scanner")

# ✅ Token-aware Kite connection
@st.cache_resource
def get_kite(api_key: str, access_token: str):
    kite = KiteConnect(api_key=api_key, timeout=15)
    kite.set_access_token(access_token)
    return kite

def init_kite():
    api_key = st.secrets["api_key"]
    access_token = st.secrets["access_token"]
    kite = get_kite(api_key, access_token)

    # Token validity check
    try:
        kite.profile()  # lightweight call to verify token
    except Exception as e:
        st.error(f"❌ Invalid/expired token: {e}")
        return None
    return kite

# ✅ Instrument lookup depends on fresh Kite session
@st.cache_data(ttl=86400)
def get_instrument_lookup():
    kite = init_kite()
    if kite is None:
        return {}
    try:
        instruments = kite.instruments("NSE")
        return {inst['tradingsymbol']: str(inst['instrument_token']) for inst in instruments}
    except Exception as e:
        st.error(f"Error fetching instrument master from Kite: {e}")
        return {}

# --- Metadata loader unchanged ---

# --- Indicator calculation unchanged ---

# --- Signal generator unchanged ---

# --- Daily macro data unchanged ---

# --- Parallel scanner unchanged ---

@st.fragment(run_every="900s")
def run_integrated_pipeline():
    meta_df = load_metadata()
    if meta_df is None:
        return
        
    kite = init_kite()
    if kite is None:
        st.warning("⚠️ Scanner halted due to invalid token.")
        return

    token_lookup = get_instrument_lookup()
    
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
        
    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("🔄 Force Re-Scan Nifty 50", use_container_width=True):
            should_scan = True
    with c_btn2:
        if st.session_state.last_run:
            last_time_str = datetime.fromtimestamp(st.session_state.last_run).strftime('%H:%M:%S')
            st.write(f"⏱️ Matrix sync verified at: **{last_time_str}**")
            
    if should_scan:
        with st.spinner("🚀 Scanning Nifty 50 assets concurrently..."):
            results = execute_parallel_scan(meta_df, token_lookup, kite)
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
        active_tf = st.radio("Select timeframe", ["15M", "1D"])
        st.dataframe(master_df)
