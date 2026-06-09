import streamlit as st
from kiteconnect import KiteConnect
import pandas as pd

# --- CONNECTION ---
def get_kite():
    try:
        # Pulls from the Cloud Secrets tab
        kite = KiteConnect(api_key=st.secrets["api_key"])
        kite.set_access_token(st.secrets["access_token"])
        return kite
    except Exception as e:
        st.error(f"Secret Error: {e}")
        return None

# --- UI & SCAN ---
st.title("Scanner Debugger")
kite = get_kite()

if st.button("Force Re-Scan"):
    if kite:
        try:
            # We use a hardcoded list to bypass any CSV/Metadata errors
            symbols = ["NSE:RELIANCE", "NSE:TCS", "NSE:INFY"]
            st.write("Attempting to fetch data for:", symbols)
            
            data = kite.ltp(symbols)
            
            if data:
                st.success("Connection Successful!")
                # Convert dict to dataframe for display
                df = pd.DataFrame(data).T
                st.dataframe(df)
            else:
                st.error("API returned empty data. Access Token might be invalid.")
        except Exception as e:
            st.error(f"Kite Error: {e}")
            st.write("If you see TokenException, update your access_token in Settings > Secrets.")
    else:
        st.error("Could not connect to Kite.")
